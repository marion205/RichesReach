"""
Management command to seed mock backtest data for testing the Backtest Viewer screen.

Usage:
    python manage.py seed_mock_backtests
    python manage.py seed_mock_backtests --reset  # Delete existing backtests first
    python manage.py seed_mock_backtests --user-email user@example.com  # For specific user
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta, datetime
from decimal import Decimal
import random
import json
import logging

from core.raha_models import Strategy, StrategyVersion, RAHABacktestRun

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed mock RAHA backtest data for UI testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing backtests before seeding'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to create backtests for (defaults to first user or creates test user)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of backtests to create (default: 5)'
        )

    def generate_equity_curve(self, start_equity: float, days: int, win_rate: float, volatility: float = 0.02) -> list:
        """
        Generate a realistic equity curve with some randomness.
        
        Args:
            start_equity: Starting equity (e.g., 10000)
            days: Number of days in backtest
            win_rate: Win rate (0-1) - affects overall trend
            volatility: Daily volatility (default 2%)
        
        Returns:
            List of {timestamp, equity} points
        """
        equity_curve = []
        current_equity = start_equity
        start_date = date.today() - timedelta(days=days)
        
        # Overall trend: positive if win_rate > 0.5, negative otherwise
        trend = (win_rate - 0.5) * 0.001  # Small daily trend
        
        for i in range(days):
            # Random daily return with some trend
            daily_return = random.gauss(trend, volatility)
            
            # Add some mean reversion (equity tends to return to trend)
            if current_equity < start_equity * 0.9:
                daily_return += 0.0005  # Slight recovery
            elif current_equity > start_equity * 1.1:
                daily_return -= 0.0005  # Slight pullback
            
            current_equity *= (1 + daily_return)
            
            # Ensure equity doesn't go negative
            current_equity = max(current_equity, start_equity * 0.5)
            
            timestamp = (start_date + timedelta(days=i)).isoformat()
            equity_curve.append({
                'timestamp': timestamp,
                'equity': round(current_equity, 2)
            })
        
        return equity_curve

    def calculate_metrics_from_equity_curve(self, equity_curve: list, start_equity: float) -> dict:
        """
        Calculate realistic metrics from an equity curve.
        
        Args:
            equity_curve: List of {timestamp, equity} points
            start_equity: Starting equity
        
        Returns:
            Dictionary of metrics
        """
        if not equity_curve:
            return {}
        
        equities = [point['equity'] for point in equity_curve]
        end_equity = equities[-1]
        
        # Calculate returns
        total_return = (end_equity - start_equity) / start_equity
        
        # Calculate max drawdown
        peak = start_equity
        max_drawdown = 0
        for equity in equities:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Simulate trade statistics based on overall performance
        win_rate = 0.45 + (total_return * 0.3)  # Win rate between 0.45-0.75 based on return
        win_rate = max(0.35, min(0.85, win_rate))  # Clamp between 35% and 85%
        
        # Estimate total trades (roughly 1-3 trades per day)
        days = len(equity_curve)
        total_trades = random.randint(days, days * 3)
        winning_trades = int(total_trades * win_rate)
        losing_trades = total_trades - winning_trades
        
        # Calculate average win/loss based on expectancy
        # If total return is positive, avg win should be larger than avg loss
        if total_return > 0:
            avg_win = abs(total_return * start_equity / winning_trades) if winning_trades > 0 else 0
            avg_loss = avg_win * 0.6  # Avg loss is 60% of avg win (good R-multiple)
        else:
            avg_loss = abs(total_return * start_equity / losing_trades) if losing_trades > 0 else 0
            avg_win = avg_loss * 0.8  # Avg win is 80% of avg loss (bad R-multiple)
        
        # Ensure minimum values
        avg_win = max(avg_win, 50)
        avg_loss = max(avg_loss, 50)
        
        # Calculate expectancy (R-multiple)
        expectancy = (win_rate * (avg_win / avg_loss)) - ((1 - win_rate) * 1.0)
        
        # Calculate profit factor
        total_wins = avg_win * winning_trades
        total_losses = avg_loss * losing_trades
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Calculate Sharpe ratio (simplified - higher if consistent returns)
        returns = [(equities[i] - equities[i-1]) / equities[i-1] for i in range(1, len(equities))]
        if len(returns) > 1:
            mean_return = sum(returns) / len(returns)
            std_return = (sum((r - mean_return) ** 2 for r in returns) / len(returns)) ** 0.5
            sharpe_ratio = (mean_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
            sharpe_ratio = max(-2, min(3, sharpe_ratio))  # Clamp between -2 and 3
        else:
            sharpe_ratio = 0.5
        
        return {
            'winRate': round(win_rate, 4),
            'sharpeRatio': round(sharpe_ratio, 2),
            'maxDrawdown': round(-max_drawdown, 4),  # Negative value
            'expectancy': round(expectancy, 2),
            'totalTrades': total_trades,
            'winningTrades': winning_trades,
            'losingTrades': losing_trades,
            'avgWin': round(avg_win, 2),
            'avgLoss': round(avg_loss, 2),
            'profitFactor': round(profit_factor, 2),
            'totalReturn': round(total_return, 4),
        }

    def handle(self, *args, **options):
        reset = options.get('reset', False)
        user_email = options.get('user_email')
        count = options.get('count', 5)
        
        # Get or create user
        if user_email:
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ User with email {user_email} not found'))
                return
        else:
            # Get first user or create test user
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.WARNING('⚠️  No users found. Creating test user...'))
                user = User.objects.create_user(
                    email='test@richesreach.com',
                    username='testuser',
                    password='testpass123'
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Created test user: {user.email}'))
        
        if reset:
            self.stdout.write(self.style.WARNING('🗑️  Deleting existing backtests...'))
            RAHABacktestRun.objects.filter(user=user).delete()
            self.stdout.write(self.style.SUCCESS('✅ Deleted existing backtests'))
        
        # Get strategy versions
        strategy_versions = list(StrategyVersion.objects.all())
        if not strategy_versions:
            self.stdout.write(self.style.ERROR('❌ No strategy versions found. Run seed_raha_strategies first.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n🌱 Seeding {count} mock backtests for {user.email}...\n'))
        
        symbols = ['SPY', 'QQQ', 'AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN', 'GOOGL']
        timeframes = ['5m', '15m', '1h']
        statuses = ['COMPLETED', 'COMPLETED', 'COMPLETED', 'RUNNING', 'PENDING']  # Mostly completed
        
        with transaction.atomic():
            for i in range(count):
                # Random strategy version
                strategy_version = random.choice(strategy_versions)
                
                # Random symbol
                symbol = random.choice(symbols)
                
                # Random timeframe
                timeframe = random.choice(timeframes)
                
                # Random date range (last 30-90 days)
                days_back = random.randint(30, 90)
                end_date = date.today() - timedelta(days=random.randint(1, 7))
                start_date = end_date - timedelta(days=days_back)
                
                # Random status (mostly completed)
                status = random.choice(statuses)
                
                # Generate equity curve
                start_equity = random.choice([10000, 25000, 50000, 100000])
                win_rate = random.uniform(0.45, 0.75)  # Realistic win rates
                equity_curve = self.generate_equity_curve(start_equity, days_back, win_rate)
                
                # Calculate metrics
                metrics = self.calculate_metrics_from_equity_curve(equity_curve, start_equity)
                
                # Create backtest
                backtest = RAHABacktestRun.objects.create(
                    user=user,
                    strategy_version=strategy_version,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    parameters={
                        'risk_per_trade': random.choice([0.01, 0.02, 0.03]),
                        'orb_minutes': random.choice([15, 30, 60]) if 'ORB' in strategy_version.strategy.name else None,
                    },
                    metrics=metrics,
                    equity_curve=equity_curve,
                    trade_log=[],  # Empty for now
                    completed_at=timezone.now() if status == 'COMPLETED' else None,
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ Created: {strategy_version.strategy.name} on {symbol} '
                        f'({start_date} to {end_date}) - {status}'
                    )
                )
                if metrics:
                    self.stdout.write(
                        f'     Win Rate: {metrics["winRate"]*100:.1f}% | '
                        f'Sharpe: {metrics["sharpeRatio"]:.2f} | '
                        f'Return: {metrics["totalReturn"]*100:.1f}%'
                    )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {count} mock backtests!\n'))
        self.stdout.write(
            self.style.SUCCESS(
                f'📱 View them in the app: Pro/Labs → Backtest Results'
            )
        )

