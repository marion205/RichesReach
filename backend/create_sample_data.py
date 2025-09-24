#!/usr/bin/env python3
"""
Create Sample Data for Swing Trading Platform
Generates realistic OHLCV data and indicators for testing
"""

import os
import sys
import django
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.models import OHLCV, Signal, TraderScore, BacktestStrategy, BacktestResult, SwingWatchlist
from core.swing_trading.indicators import TechnicalIndicators
from django.contrib.auth.models import User
from decimal import Decimal

def create_sample_ohlcv_data():
    """Create sample OHLCV data for testing"""
    print("📊 Creating sample OHLCV data...")
    
    # Create sample data for AAPL
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    timeframes = ['1d', '5m', '1h']
    
    for symbol in symbols:
        for timeframe in timeframes:
            print(f"  Creating data for {symbol} {timeframe}...")
            
            # Generate realistic price data
            np.random.seed(42)  # For reproducible data
            
            # Create date range
            if timeframe == '1d':
                dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
                base_price = 150.0
                volatility = 0.02
            elif timeframe == '1h':
                dates = pd.date_range(start='2024-01-01', end='2024-01-02', freq='H')
                base_price = 150.0
                volatility = 0.01
            else:  # 5m
                dates = pd.date_range(start='2024-01-01', end='2024-01-01 23:59', freq='5T')
                base_price = 150.0
                volatility = 0.005
            
            # Generate price data
            returns = np.random.normal(0, volatility, len(dates))
            prices = [base_price]
            
            for ret in returns[1:]:
                new_price = prices[-1] * (1 + ret)
                prices.append(max(new_price, 1.0))  # Ensure positive prices
            
            # Create OHLCV data
            ohlcv_data = []
            for i, (date, close) in enumerate(zip(dates, prices)):
                # Generate realistic OHLC from close price
                daily_range = close * volatility
                high = close + np.random.uniform(0, daily_range)
                low = close - np.random.uniform(0, daily_range)
                open_price = prices[i-1] if i > 0 else close
                
                # Ensure OHLC relationships are correct
                high = max(high, open_price, close)
                low = min(low, open_price, close)
                
                # Generate volume
                volume = int(np.random.uniform(1000000, 10000000))
                
                ohlcv_data.append({
                    'symbol': symbol,
                    'timestamp': date,
                    'timeframe': timeframe,
                    'open_price': Decimal(str(round(open_price, 2))),
                    'high_price': Decimal(str(round(high, 2))),
                    'low_price': Decimal(str(round(low, 2))),
                    'close_price': Decimal(str(round(close, 2))),
                    'volume': volume,
                })
            
            # Bulk create OHLCV records
            OHLCV.objects.bulk_create([
                OHLCV(**data) for data in ohlcv_data
            ])
            
            print(f"    ✅ Created {len(ohlcv_data)} records for {symbol} {timeframe}")
    
    print("✅ Sample OHLCV data created successfully!")

def calculate_indicators():
    """Calculate technical indicators for the sample data"""
    print("🔢 Calculating technical indicators...")
    
    ti = TechnicalIndicators()
    
    # Get all OHLCV data
    ohlcv_records = OHLCV.objects.all().order_by('symbol', 'timeframe', 'timestamp')
    
    # Group by symbol and timeframe
    for symbol in ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']:
        for timeframe in ['1d', '5m', '1h']:
            records = ohlcv_records.filter(symbol=symbol, timeframe=timeframe)
            
            if records.count() < 50:  # Need enough data for indicators
                continue
            
            print(f"  Calculating indicators for {symbol} {timeframe}...")
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'open': float(r.open_price),
                'high': float(r.high_price),
                'low': float(r.low_price),
                'close': float(r.close_price),
                'volume': r.volume,
            } for r in records])
            
            # Calculate indicators
            df['ema_12'] = ti.ema(df['close'], 12)
            df['ema_26'] = ti.ema(df['close'], 26)
            df['rsi_14'] = ti.rsi(df['close'], 14)
            df['atr_14'] = ti.atr(df, 14)
            df['volume_sma_20'] = ti.sma(df['volume'], 20)
            
            # Update records with calculated indicators
            for i, record in enumerate(records):
                if i < len(df):
                    record.ema_12 = Decimal(str(round(df.iloc[i]['ema_12'], 2))) if not pd.isna(df.iloc[i]['ema_12']) else None
                    record.ema_26 = Decimal(str(round(df.iloc[i]['ema_26'], 2))) if not pd.isna(df.iloc[i]['ema_26']) else None
                    record.rsi_14 = Decimal(str(round(df.iloc[i]['rsi_14'], 2))) if not pd.isna(df.iloc[i]['rsi_14']) else None
                    record.atr_14 = Decimal(str(round(df.iloc[i]['atr_14'], 2))) if not pd.isna(df.iloc[i]['atr_14']) else None
                    record.volume_sma_20 = int(df.iloc[i]['volume_sma_20']) if not pd.isna(df.iloc[i]['volume_sma_20']) else None
                    record.save()
            
            print(f"    ✅ Updated {records.count()} records with indicators")
    
    print("✅ Technical indicators calculated successfully!")

def create_sample_signals():
    """Create sample trading signals"""
    print("📡 Creating sample trading signals...")
    
    # Get OHLCV data with indicators
    ohlcv_records = OHLCV.objects.filter(
        ema_12__isnull=False,
        ema_26__isnull=False,
        rsi_14__isnull=False
    ).order_by('symbol', 'timestamp')
    
    signals_created = 0
    
    for record in ohlcv_records:
        # Create signals based on technical conditions
        if record.rsi_14 < 30:  # Oversold
            signal = Signal.objects.create(
                symbol=record.symbol,
                timeframe=record.timeframe,
                triggered_at=record.timestamp,
                signal_type='rsi_rebound_long',
                features={
                    'rsi_14': float(record.rsi_14),
                    'ema_12': float(record.ema_12),
                    'ema_26': float(record.ema_26),
                    'atr_14': float(record.atr_14) if record.atr_14 else 0,
                    'volume_surge': float(record.volume) / float(record.volume_sma_20) if record.volume_sma_20 else 1.0,
                },
                ml_score=0.75,
                thesis=f"RSI oversold at {record.rsi_14} with potential bounce",
                entry_price=record.close_price,
                stop_price=record.close_price * Decimal('0.95'),  # 5% stop
                target_price=record.close_price * Decimal('1.10'),  # 10% target
                is_active=True
            )
            signals_created += 1
            
        elif record.rsi_14 > 70:  # Overbought
            signal = Signal.objects.create(
                symbol=record.symbol,
                timeframe=record.timeframe,
                triggered_at=record.timestamp,
                signal_type='rsi_rebound_short',
                features={
                    'rsi_14': float(record.rsi_14),
                    'ema_12': float(record.ema_12),
                    'ema_26': float(record.ema_26),
                    'atr_14': float(record.atr_14) if record.atr_14 else 0,
                    'volume_surge': float(record.volume) / float(record.volume_sma_20) if record.volume_sma_20 else 1.0,
                },
                ml_score=0.65,
                thesis=f"RSI overbought at {record.rsi_14} with potential pullback",
                entry_price=record.close_price,
                stop_price=record.close_price * Decimal('1.05'),  # 5% stop
                target_price=record.close_price * Decimal('0.90'),  # 10% target
                is_active=True
            )
            signals_created += 1
    
    print(f"✅ Created {signals_created} sample trading signals!")

def create_sample_users_and_scores():
    """Create sample users and trader scores"""
    print("👥 Creating sample users and trader scores...")
    
    # Create sample users
    users_data = [
        {'username': 'trader1', 'email': 'trader1@example.com', 'first_name': 'John', 'last_name': 'Doe'},
        {'username': 'trader2', 'email': 'trader2@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
        {'username': 'trader3', 'email': 'trader3@example.com', 'first_name': 'Bob', 'last_name': 'Johnson'},
    ]
    
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
            }
        )
        
        if created:
            print(f"  ✅ Created user: {user.username}")
        
        # Create trader score
        TraderScore.objects.get_or_create(
            user=user,
            defaults={
                'accuracy': Decimal('75.5'),
                'total_signals': 100,
                'winning_signals': 75,
                'avg_return': Decimal('12.3'),
                'sharpe_ratio': Decimal('1.8'),
                'max_drawdown': Decimal('8.5'),
            }
        )
    
    print("✅ Sample users and trader scores created!")

def create_sample_backtest_data():
    """Create sample backtest strategies and results"""
    print("📈 Creating sample backtest data...")
    
    # Get a user for the backtest
    user = User.objects.first()
    if not user:
        print("❌ No users found. Please create users first.")
        return
    
    # Create sample backtest strategy
    strategy = BacktestStrategy.objects.create(
        name='EMA Crossover Strategy',
        description='Simple EMA 12/26 crossover strategy with RSI filter',
        strategy_type='ema_crossover',
        parameters={
            'ema_fast': 12,
            'ema_slow': 26,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
        },
        total_return=Decimal('15.5'),
        win_rate=Decimal('0.65'),
        max_drawdown=Decimal('8.2'),
        sharpe_ratio=Decimal('1.4'),
        total_trades=150,
        is_public=True,
        user=user
    )
    
    # Create sample backtest results
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    for symbol in symbols:
        BacktestResult.objects.create(
            strategy=strategy,
            symbol=symbol,
            timeframe='1d',
            start_date='2023-01-01',
            end_date='2023-12-31',
            initial_capital=Decimal('10000.00'),
            final_capital=Decimal('11550.00'),
            total_return=Decimal('15.5'),
            annualized_return=Decimal('15.5'),
            max_drawdown=Decimal('8.2'),
            sharpe_ratio=Decimal('1.4'),
            win_rate=Decimal('0.65'),
            profit_factor=Decimal('1.8'),
            total_trades=50,
            winning_trades=32,
            losing_trades=18,
            avg_win=Decimal('2.5'),
            avg_loss=Decimal('1.2'),
        )
    
    print("✅ Sample backtest data created!")

def create_sample_watchlists():
    """Create sample swing trading watchlists"""
    print("👀 Creating sample watchlists...")
    
    # Get users
    users = User.objects.all()[:3]
    
    watchlist_data = [
        {
            'name': 'Tech Giants',
            'description': 'Large cap technology stocks',
            'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN'],
            'is_public': True,
        },
        {
            'name': 'Growth Stocks',
            'description': 'High growth potential stocks',
            'symbols': ['TSLA', 'NVDA', 'AMD', 'NFLX'],
            'is_public': True,
        },
        {
            'name': 'My Picks',
            'description': 'Personal trading picks',
            'symbols': ['AAPL', 'TSLA', 'SPY'],
            'is_public': False,
        },
    ]
    
    for i, watchlist_info in enumerate(watchlist_data):
        if i < len(users):
            SwingWatchlist.objects.create(
                name=watchlist_info['name'],
                description=watchlist_info['description'],
                symbols=watchlist_info['symbols'],
                is_public=watchlist_info['is_public'],
                user=users[i]
            )
    
    print("✅ Sample watchlists created!")

def main():
    """Main function to create all sample data"""
    print("🎯 Creating Sample Data for Swing Trading Platform")
    print("=" * 60)
    
    try:
        # Create sample data
        create_sample_ohlcv_data()
        calculate_indicators()
        create_sample_signals()
        create_sample_users_and_scores()
        create_sample_backtest_data()
        create_sample_watchlists()
        
        print("\n" + "=" * 60)
        print("🎉 Sample data creation completed successfully!")
        print("\n📊 Data Summary:")
        print(f"  - OHLCV records: {OHLCV.objects.count()}")
        print(f"  - Trading signals: {Signal.objects.count()}")
        print(f"  - Users: {User.objects.count()}")
        print(f"  - Trader scores: {TraderScore.objects.count()}")
        print(f"  - Backtest strategies: {BacktestStrategy.objects.count()}")
        print(f"  - Backtest results: {BacktestResult.objects.count()}")
        print(f"  - Watchlists: {SwingWatchlist.objects.count()}")
        
        print("\n🚀 Your swing trading platform now has sample data for testing!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
