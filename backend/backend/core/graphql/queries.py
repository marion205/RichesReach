import graphene
from django.utils import timezone
from datetime import datetime, timedelta
import random
from .types import SignalType, UserType, MockSignal, MockUser, LeaderboardEntryType, TraderScoreType, MockTraderScore, MockLeaderboardEntry, BacktestStrategyType, MockBacktestStrategy, BacktestResultType, MockBacktestResult, BacktestConfigType, StrategyParamsType, BacktestResultOutputType, RunBacktestResultType, TargetPriceResultType, PositionSizeResultType, DynamicStopResultType, PortfolioMetricsType, PortfolioHoldingType, StockType, AdvancedStockScreeningResultType, WatchlistItemType, WatchlistStockType, RustStockAnalysisType, TechnicalIndicatorsType, FundamentalAnalysisType

# Mock data for signals - completely database-free
def get_mock_signals():
    # Create a mock user without database access
    mock_user = MockUser(
        id=1,
        username='ai_system',
        name='AI Trading System',
        email='ai@richesreach.com'
    )
    
    return [
        MockSignal(
            id=1,
            symbol='AAPL',
            timeframe='1D',
            triggered_at=timezone.now(),
            signal_type='BUY',
            entry_price=150.0,
            stop_price=145.0,
            target_price=160.0,
            ml_score=0.85,
            thesis='Strong technical breakout with volume confirmation',
            risk_reward_ratio=2.0,
            is_active=True,
            is_validated=False,
            validation_price=None,
            validation_timestamp=None,
            created_by=mock_user,
            features='RSI_OVERSOLD,EMA_CROSSOVER,VOLUME_SURGE',
            user_like_count=15
        ),
        MockSignal(
            id=2,
            symbol='TSLA',
            timeframe='1D',
            triggered_at=timezone.now(),
            signal_type='SELL',
            entry_price=250.0,
            stop_price=260.0,
            target_price=230.0,
            ml_score=0.75,
            thesis='Bearish divergence with resistance at key level',
            risk_reward_ratio=2.0,
            is_active=True,
            is_validated=False,
            validation_price=None,
            validation_timestamp=None,
            created_by=mock_user,
            features='RSI_OVERBOUGHT,MACD_DIVERGENCE,RESISTANCE_BREAK',
            user_like_count=8
        )
    ]

# Mock data for leaderboard - completely database-free
def get_mock_leaderboard():
    # Create mock users
    users = [
        MockUser(id=1, username='trader_pro', name='Trader Pro', email='pro@example.com'),
        MockUser(id=2, username='swing_master', name='Swing Master', email='swing@example.com'),
        MockUser(id=3, username='chart_king', name='Chart King', email='chart@example.com'),
        MockUser(id=4, username='signal_hunter', name='Signal Hunter', email='hunter@example.com'),
        MockUser(id=5, username='market_wizard', name='Market Wizard', email='wizard@example.com'),
    ]
    
    # Create mock trader scores
    scores = [
        MockTraderScore(
            overallScore=0.92,
            accuracyScore=0.88,
            consistencyScore=0.95,
            disciplineScore=0.91,
            totalSignals=156,
            validatedSignals=142,
            winRate=0.78
        ),
        MockTraderScore(
            overallScore=0.89,
            accuracyScore=0.85,
            consistencyScore=0.92,
            disciplineScore=0.88,
            totalSignals=134,
            validatedSignals=128,
            winRate=0.75
        ),
        MockTraderScore(
            overallScore=0.86,
            accuracyScore=0.82,
            consistencyScore=0.89,
            disciplineScore=0.85,
            totalSignals=98,
            validatedSignals=91,
            winRate=0.72
        ),
        MockTraderScore(
            overallScore=0.83,
            accuracyScore=0.79,
            consistencyScore=0.86,
            disciplineScore=0.82,
            totalSignals=87,
            validatedSignals=78,
            winRate=0.69
        ),
        MockTraderScore(
            overallScore=0.80,
            accuracyScore=0.76,
            consistencyScore=0.83,
            disciplineScore=0.79,
            totalSignals=76,
            validatedSignals=68,
            winRate=0.66
        ),
    ]
    
    # Create leaderboard entries
    leaderboard = []
    for i, (user, score) in enumerate(zip(users, scores)):
        leaderboard.append(MockLeaderboardEntry(
            rank=i + 1,
            category='overall',
            user=user,
            traderScore=score
        ))
    
    return leaderboard

# Mock data for backtest strategies - completely database-free
def get_mock_backtest_strategies():
    # Create mock users
    users = [
        MockUser(id=1, username='strategy_master', name='Strategy Master', email='master@example.com'),
        MockUser(id=2, username='quant_trader', name='Quant Trader', email='quant@example.com'),
        MockUser(id=3, username='swing_expert', name='Swing Expert', email='swing@example.com'),
        MockUser(id=4, username='momentum_hunter', name='Momentum Hunter', email='momentum@example.com'),
    ]
    
    # Create mock backtest strategies
    strategies = [
        MockBacktestStrategy(
            id=1,
            name='RSI Mean Reversion Strategy',
            description='Buy oversold stocks (RSI < 30) and sell overbought (RSI > 70) with volume confirmation.',
            strategyType='MEAN_REVERSION',
            parameters={
                'rsi_period': 14,
                'oversold_threshold': 30,
                'overbought_threshold': 70,
                'volume_threshold': 1.5,
                'stop_loss': 0.05,
                'take_profit': 0.10
            },
            totalReturn=0.156,
            winRate=0.68,
            maxDrawdown=0.12,
            sharpeRatio=1.45,
            totalTrades=89,
            isPublic=True,
            likesCount=24,
            sharesCount=8,
            createdAt=timezone.now(),
            user=users[0]
        ),
        MockBacktestStrategy(
            id=2,
            name='EMA Crossover Momentum',
            description='Enter long when EMA 12 crosses above EMA 26 with strong volume. Exit when trend reverses.',
            strategyType='MOMENTUM',
            parameters={
                'ema_fast': 12,
                'ema_slow': 26,
                'volume_threshold': 1.2,
                'stop_loss': 0.08,
                'take_profit': 0.15
            },
            totalReturn=0.234,
            winRate=0.72,
            maxDrawdown=0.18,
            sharpeRatio=1.67,
            totalTrades=67,
            isPublic=True,
            likesCount=31,
            sharesCount=12,
            createdAt=timezone.now(),
            user=users[1]
        ),
        MockBacktestStrategy(
            id=3,
            name='Bollinger Band Squeeze',
            description='Trade the expansion after periods of low volatility (squeeze) with directional bias.',
            strategyType='VOLATILITY',
            parameters={
                'bb_period': 20,
                'bb_std': 2,
                'squeeze_threshold': 0.1,
                'stop_loss': 0.06,
                'take_profit': 0.12
            },
            totalReturn=0.189,
            winRate=0.65,
            maxDrawdown=0.14,
            sharpeRatio=1.52,
            totalTrades=45,
            isPublic=True,
            likesCount=18,
            sharesCount=6,
            createdAt=timezone.now(),
            user=users[2]
        ),
        MockBacktestStrategy(
            id=4,
            name='Breakout Trading System',
            description='Trade breakouts above resistance levels with volume confirmation and tight stops.',
            strategyType='BREAKOUT',
            parameters={
                'lookback_period': 20,
                'breakout_threshold': 0.02,
                'volume_threshold': 2.0,
                'stop_loss': 0.04,
                'take_profit': 0.08
            },
            totalReturn=0.278,
            winRate=0.58,
            maxDrawdown=0.22,
            sharpeRatio=1.89,
            totalTrades=34,
            isPublic=True,
            likesCount=42,
            sharesCount=15,
            createdAt=timezone.now(),
            user=users[3]
        ),
    ]
    
    return strategies

# Mock data for backtest results - completely database-free
def get_mock_backtest_results():
    # Create realistic backtest results for different symbols and timeframes
    symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'NFLX']
    timeframes = ['1D', '4H', '1H']
    
    results = []
    base_date = timezone.now() - timedelta(days=365)
    
    for i, symbol in enumerate(symbols):
        for j, timeframe in enumerate(timeframes):
            # Create realistic performance metrics
            initial_capital = 10000.0
            total_return = 0.12 + (i * 0.05) + (j * 0.02)  # Vary returns
            final_capital = initial_capital * (1 + total_return)
            
            # Calculate other metrics
            annualized_return = total_return * (365 / 252)  # Rough annualization
            max_drawdown = 0.08 + (i * 0.01)  # Vary drawdown
            sharpe_ratio = 1.2 + (i * 0.1) + (j * 0.05)
            sortino_ratio = sharpe_ratio * 1.1
            calmar_ratio = annualized_return / max_drawdown
            
            win_rate = 0.65 + (i * 0.02) + (j * 0.01)
            total_trades = 45 + (i * 5) + (j * 3)
            winning_trades = int(total_trades * win_rate)
            losing_trades = total_trades - winning_trades
            
            profit_factor = 1.8 + (i * 0.1) + (j * 0.05)
            avg_win = (total_return * initial_capital * 0.6) / winning_trades if winning_trades > 0 else 0
            avg_loss = (total_return * initial_capital * 0.4) / losing_trades if losing_trades > 0 else 0
            
            results.append(MockBacktestResult(
                id=f"{i * len(timeframes) + j + 1}",
                symbol=symbol,
                timeframe=timeframe,
                startDate=base_date + timedelta(days=i * 30),
                endDate=base_date + timedelta(days=(i + 1) * 30 + 365),
                initialCapital=initial_capital,
                finalCapital=final_capital,
                totalReturn=total_return,
                annualizedReturn=annualized_return,
                maxDrawdown=max_drawdown,
                sharpeRatio=sharpe_ratio,
                sortinoRatio=sortino_ratio,
                calmarRatio=calmar_ratio,
                winRate=win_rate,
                profitFactor=profit_factor,
                totalTrades=total_trades,
                winningTrades=winning_trades,
                losingTrades=losing_trades,
                avgWin=avg_win,
                avgLoss=avg_loss,
                createdAt=timezone.now() - timedelta(days=i * 7)
            ))
    
    return results

class Query(graphene.ObjectType):
    signals = graphene.List(
        SignalType,
        symbol=graphene.String(),
        signal_type=graphene.String(),
        min_ml_score=graphene.Float(),
        is_active=graphene.Boolean(),
        limit=graphene.Int(default_value=50),
    )
    
    me = graphene.Field(UserType)
    
    leaderboard = graphene.List(
        LeaderboardEntryType,
        category=graphene.String(),
        limit=graphene.Int(default_value=50),
    )
    
    backtestStrategies = graphene.List(
        BacktestStrategyType,
        isPublic=graphene.Boolean(),
        limit=graphene.Int(default_value=50),
    )
    
    backtestResults = graphene.List(
        BacktestResultType,
        strategyId=graphene.ID(),
        limit=graphene.Int(default_value=50),
    )
    
    calculateTargetPrice = graphene.Field(
        TargetPriceResultType,
        entryPrice=graphene.Float(required=True),
        stopPrice=graphene.Float(required=True),
        riskRewardRatio=graphene.Float(),
        atr=graphene.Float(),
        resistanceLevel=graphene.Float(),
        supportLevel=graphene.Float(),
        signalType=graphene.String(),
    )
    
    calculatePositionSize = graphene.Field(
        PositionSizeResultType,
        accountBalance=graphene.Float(),
        accountEquity=graphene.Float(),
        entryPrice=graphene.Float(required=True),
        stopPrice=graphene.Float(required=True),
        riskPercentage=graphene.Float(),
        riskPerTrade=graphene.Float(),
        riskAmount=graphene.Float(),
        maxPositionSize=graphene.Float(),
        maxPositionPct=graphene.Float(),
        confidence=graphene.Float(),
        method=graphene.String(),
    )
    
    calculateDynamicStop = graphene.Field(
        DynamicStopResultType,
        entryPrice=graphene.Float(required=True),
        atr=graphene.Float(required=True),
        atrMultiplier=graphene.Float(),
        supportLevel=graphene.Float(),
        resistanceLevel=graphene.Float(),
        signalType=graphene.String(),
    )
    
    

    def resolve_signals(self, info, symbol=None, signal_type=None,
                        min_ml_score=None, is_active=None, limit=50):
        # Get mock signals
        signals = get_mock_signals()
        
        # Apply filters
        filtered_signals = []
        for signal in signals:
            if symbol and signal.symbol.lower() != symbol.lower():
                continue
            if signal_type and signal.signal_type != signal_type:
                continue
            if min_ml_score is not None and signal.ml_score < min_ml_score:
                continue
            if is_active is not None and signal.is_active != is_active:
                continue
            filtered_signals.append(signal)
        
        # Apply limit
        return filtered_signals[:min(limit or 50, 200)]
    
    def resolve_me(self, info):
        # Return mock user data (database-free)
        return MockUser(
            id=1,
            name='Test User',
            email='test@example.com',
            username='testuser',
            hasPremiumAccess=True,
            subscriptionTier='PREMIUM'
        )
    
    def resolve_leaderboard(self, info, category=None, limit=50):
        # Get mock leaderboard data
        leaderboard = get_mock_leaderboard()
        
        # Apply category filter if provided
        if category:
            leaderboard = [entry for entry in leaderboard if entry.category == category]
        
        # Apply limit
        return leaderboard[:min(limit or 50, 200)]
    
    def resolve_backtestStrategies(self, info, isPublic=None, limit=50):
        # Get mock backtest strategies data
        strategies = get_mock_backtest_strategies()
        
        # Apply isPublic filter if provided
        if isPublic is not None:
            strategies = [strategy for strategy in strategies if strategy.isPublic == isPublic]
        
        # Apply limit
        return strategies[:min(limit or 50, 200)]
    
    def resolve_backtestResults(self, info, strategyId=None, limit=50):
        # Get mock backtest results data
        results = get_mock_backtest_results()
        
        # Apply strategyId filter if provided
        if strategyId:
            # For now, return all results regardless of strategyId
            # In a real implementation, you'd filter by strategyId
            pass
        
        # Apply limit
        return results[:min(limit or 50, 200)]

# Mock data for portfolio metrics - completely database-free
def _mock_portfolio_metrics():
    holdings = [
        dict(symbol="AAPL", company_name="Apple Inc.", shares=20,
             current_price=175.50, total_value=3510.00, cost_basis=3000.00,
             return_amount=510.00, return_percent=0.17, sector="Technology"),
        dict(symbol="TSLA", company_name="Tesla, Inc.", shares=10,
             current_price=260.00, total_value=2600.00, cost_basis=2200.00,
             return_amount=400.00, return_percent=0.1818, sector="Automotive"),
        dict(symbol="MSFT", company_name="Microsoft Corp.", shares=12,
             current_price=410.00, total_value=4920.00, cost_basis=4200.00,
             return_amount=720.00, return_percent=0.1714, sector="Technology"),
        dict(symbol="GOOGL", company_name="Alphabet Class A", shares=8,
             current_price=155.00, total_value=1240.00, cost_basis=1000.00,
             return_amount=240.00, return_percent=0.24, sector="Communication Services"),
        dict(symbol="AMZN", company_name="Amazon.com, Inc.", shares=6,
             current_price=135.00, total_value=810.00, cost_basis=720.00,
             return_amount=90.00, return_percent=0.125, sector="Consumer Discretionary"),
    ]
    total_value = sum(h["total_value"] for h in holdings)
    total_cost  = sum(h["cost_basis"] for h in holdings)
    total_return = total_value - total_cost
    total_return_percent = (total_return / total_cost) if total_cost else 0.0
    return dict(
        total_value=total_value,
        total_cost=total_cost,
        total_return=total_return,
        total_return_percent=total_return_percent,
        holdings=holdings,
    )

# Mock data for stocks - completely database-free
def get_mock_stocks():
    stocks = [
        {
            'id': '1',
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'sector': 'Technology',
            'market_cap': 2800000000000,  # $2.8T
            'pe_ratio': 28.5,
            'dividend_yield': 0.0044,  # 0.44%
            'beginner_friendly_score': 85,  # 85% (was 0.85)
            'dividend_score': 65  # Good dividend growth history
        },
        {
            'id': '2',
            'symbol': 'MSFT',
            'company_name': 'Microsoft Corporation',
            'sector': 'Technology',
            'market_cap': 2600000000000,  # $2.6T
            'pe_ratio': 32.1,
            'dividend_yield': 0.0071,  # 0.71%
            'beginner_friendly_score': 82,  # 82% (was 0.82)
            'dividend_score': 78  # Strong dividend growth
        },
        {
            'id': '3',
            'symbol': 'GOOGL',
            'company_name': 'Alphabet Inc.',
            'sector': 'Communication Services',
            'market_cap': 1800000000000,  # $1.8T
            'pe_ratio': 24.8,
            'dividend_yield': 0.0,  # No dividend
            'beginner_friendly_score': 78,  # 78% (was 0.78)
            'dividend_score': 0  # No dividend
        },
        {
            'id': '4',
            'symbol': 'TSLA',
            'company_name': 'Tesla, Inc.',
            'sector': 'Automotive',
            'market_cap': 800000000000,  # $800B
            'pe_ratio': 65.2,
            'dividend_yield': 0.0,  # No dividend
            'beginner_friendly_score': 65,  # 65% (was 0.65)
            'dividend_score': 0  # No dividend
        },
        {
            'id': '5',
            'symbol': 'AMZN',
            'company_name': 'Amazon.com, Inc.',
            'sector': 'Consumer Discretionary',
            'market_cap': 1500000000000,  # $1.5T
            'pe_ratio': 45.3,
            'dividend_yield': 0.0,  # No dividend
            'beginner_friendly_score': 72,  # 72% (was 0.72)
            'dividend_score': 0  # No dividend
        },
        {
            'id': '6',
            'symbol': 'META',
            'company_name': 'Meta Platforms, Inc.',
            'sector': 'Communication Services',
            'market_cap': 900000000000,  # $900B
            'pe_ratio': 22.1,
            'dividend_yield': 0.0,  # No dividend
            'beginner_friendly_score': 68,  # 68% (was 0.68)
            'dividend_score': 0  # No dividend
        },
        {
            'id': '7',
            'symbol': 'NVDA',
            'company_name': 'NVIDIA Corporation',
            'sector': 'Technology',
            'market_cap': 1200000000000,  # $1.2T
            'pe_ratio': 55.8,
            'dividend_yield': 0.0003,  # 0.03%
            'beginner_friendly_score': 58,  # 58% (was 0.58)
            'dividend_score': 25  # Minimal dividend
        },
        {
            'id': '8',
            'symbol': 'JPM',
            'company_name': 'JPMorgan Chase & Co.',
            'sector': 'Financial Services',
            'market_cap': 450000000000,  # $450B
            'pe_ratio': 12.3,
            'dividend_yield': 0.0234,  # 2.34%
            'beginner_friendly_score': 88,  # 88% (was 0.88)
            'dividend_score': 85  # Excellent dividend history
        },
        {
            'id': '9',
            'symbol': 'JNJ',
            'company_name': 'Johnson & Johnson',
            'sector': 'Healthcare',
            'market_cap': 420000000000,  # $420B
            'pe_ratio': 15.7,
            'dividend_yield': 0.0298,  # 2.98%
            'beginner_friendly_score': 92,  # 92% (was 0.92)
            'dividend_score': 95  # Dividend aristocrat
        },
        {
            'id': '10',
            'symbol': 'PG',
            'company_name': 'Procter & Gamble Co.',
            'sector': 'Consumer Staples',
            'market_cap': 380000000000,  # $380B
            'pe_ratio': 25.4,
            'dividend_yield': 0.0245,  # 2.45%
            'beginner_friendly_score': 90,  # 90% (was 0.90)
            'dividend_score': 92  # Dividend aristocrat
        }
    ]
    return stocks

# Mock data for advanced stock screening - completely database-free
def get_mock_advanced_screening_results():
    results = [
        {
            'id': '1',
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'sector': 'Technology',
            'market_cap': 2800000000000,
            'pe_ratio': 28.5,
            'dividend_yield': 0.0044,
            'beginner_friendly_score': 0.85,
            'technical_score': 0.78,
            'fundamental_score': 0.82,
            'growth_score': 0.75,
            'value_score': 0.68,
            'current_price': 175.50,
            'volatility': 0.25,
            'debt_ratio': 0.15,
            'reasoning': 'Strong fundamentals with consistent revenue growth and solid balance sheet. High brand loyalty and ecosystem lock-in.',
            'score': 0.82,
            'ml_score': 0.87
        },
        {
            'id': '2',
            'symbol': 'MSFT',
            'company_name': 'Microsoft Corporation',
            'sector': 'Technology',
            'market_cap': 2600000000000,
            'pe_ratio': 32.1,
            'dividend_yield': 0.0071,
            'beginner_friendly_score': 0.82,
            'technical_score': 0.85,
            'fundamental_score': 0.88,
            'growth_score': 0.82,
            'value_score': 0.72,
            'current_price': 380.25,
            'volatility': 0.22,
            'debt_ratio': 0.18,
            'reasoning': 'Cloud leadership with Azure growth, strong enterprise relationships, and diversified revenue streams.',
            'score': 0.88,
            'ml_score': 0.91
        },
        {
            'id': '3',
            'symbol': 'GOOGL',
            'company_name': 'Alphabet Inc.',
            'sector': 'Communication Services',
            'market_cap': 1800000000000,
            'pe_ratio': 24.8,
            'dividend_yield': 0.0,
            'beginner_friendly_score': 0.78,
            'technical_score': 0.72,
            'fundamental_score': 0.85,
            'growth_score': 0.88,
            'value_score': 0.75,
            'current_price': 142.30,
            'volatility': 0.28,
            'debt_ratio': 0.12,
            'reasoning': 'Search dominance with strong AI capabilities, YouTube growth, and cloud expansion potential.',
            'score': 0.85,
            'ml_score': 0.89
        },
        {
            'id': '4',
            'symbol': 'TSLA',
            'company_name': 'Tesla, Inc.',
            'sector': 'Automotive',
            'market_cap': 800000000000,
            'pe_ratio': 65.2,
            'dividend_yield': 0.0,
            'beginner_friendly_score': 0.65,
            'technical_score': 0.68,
            'fundamental_score': 0.72,
            'growth_score': 0.85,
            'value_score': 0.45,
            'current_price': 245.80,
            'volatility': 0.45,
            'debt_ratio': 0.08,
            'reasoning': 'EV market leader with strong brand, expanding production capacity, and energy business growth.',
            'score': 0.72,
            'ml_score': 0.78
        },
        {
            'id': '5',
            'symbol': 'AMZN',
            'company_name': 'Amazon.com, Inc.',
            'sector': 'Consumer Discretionary',
            'market_cap': 1500000000000,
            'pe_ratio': 45.3,
            'dividend_yield': 0.0,
            'beginner_friendly_score': 0.72,
            'technical_score': 0.75,
            'fundamental_score': 0.78,
            'growth_score': 0.82,
            'value_score': 0.65,
            'current_price': 155.75,
            'volatility': 0.32,
            'debt_ratio': 0.22,
            'reasoning': 'E-commerce dominance with AWS cloud leadership, expanding logistics network, and advertising growth.',
            'score': 0.78,
            'ml_score': 0.83
        }
    ]
    return results

# Mock data for watchlist - completely database-free
def get_mock_watchlist():
    watchlist = [
        {
            'id': '1',
            'stock': {
                'id': '1',
                'symbol': 'AAPL',
                'company_name': 'Apple Inc.',
                'sector': 'Technology',
                'beginner_friendly_score': 0.85,
                'current_price': 175.50
            },
            'added_at': datetime.now() - timedelta(days=5),
            'notes': 'Strong fundamentals, good for long-term hold',
            'target_price': 200.0
        },
        {
            'id': '2',
            'stock': {
                'id': '2',
                'symbol': 'TSLA',
                'company_name': 'Tesla, Inc.',
                'sector': 'Automotive',
                'beginner_friendly_score': 0.65,
                'current_price': 245.80
            },
            'added_at': datetime.now() - timedelta(days=3),
            'notes': 'High volatility, watch for entry point',
            'target_price': 300.0
        },
        {
            'id': '3',
            'stock': {
                'id': '3',
                'symbol': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'sector': 'Technology',
                'beginner_friendly_score': 0.82,
                'current_price': 380.25
            },
            'added_at': datetime.now() - timedelta(days=7),
            'notes': 'Cloud growth story, solid dividend',
            'target_price': 450.0
        },
        {
            'id': '4',
            'stock': {
                'id': '4',
                'symbol': 'GOOGL',
                'company_name': 'Alphabet Inc.',
                'sector': 'Communication Services',
                'beginner_friendly_score': 0.78,
                'current_price': 142.30
            },
            'added_at': datetime.now() - timedelta(days=2),
            'notes': 'AI leadership and search dominance',
            'target_price': 180.0
        },
        {
            'id': '5',
            'stock': {
                'id': '5',
                'symbol': 'NVDA',
                'company_name': 'NVIDIA Corporation',
                'sector': 'Technology',
                'beginner_friendly_score': 0.58,
                'current_price': 485.20
            },
            'added_at': datetime.now() - timedelta(days=1),
            'notes': 'AI chip leader, high growth potential',
            'target_price': 600.0
        }
    ]
    return watchlist

# Mock data for rust stock analysis - completely database-free
def get_mock_rust_stock_analysis(symbol):
    # Generate realistic analysis data based on symbol
    analysis_data = {
        'AAPL': {
            'symbol': 'AAPL',
            'beginner_friendly_score': 0.85,
            'risk_level': 'Medium',
            'recommendation': 'BUY',
            'technical_indicators': {
                'rsi': 58.5,
                'macd': 2.3,
                'macd_signal': 1.8,
                'macd_histogram': 0.5,
                'sma20': 172.4,
                'sma50': 168.9,
                'ema12': 174.2,
                'ema26': 171.1,
                'bollinger_upper': 182.1,
                'bollinger_lower': 162.7,
                'bollinger_middle': 172.4
            },
            'fundamental_analysis': {
                'valuation_score': 0.75,
                'growth_score': 0.82,
                'stability_score': 0.88,
                'dividend_score': 0.65,
                'debt_score': 0.92
            },
            'reasoning': 'Apple shows strong technical momentum with RSI in neutral territory and MACD indicating bullish trend. Fundamentally, the company maintains excellent financial health with strong cash position and consistent revenue growth. The ecosystem lock-in provides competitive moat. Current valuation is reasonable given growth prospects.'
        },
        'MSFT': {
            'symbol': 'MSFT',
            'beginner_friendly_score': 0.82,
            'risk_level': 'Low',
            'recommendation': 'STRONG BUY',
            'technical_indicators': {
                'rsi': 62.1,
                'macd': 3.2,
                'macd_signal': 2.1,
                'macd_histogram': 1.1,
                'sma20': 375.8,
                'sma50': 368.2,
                'ema12': 378.5,
                'ema26': 371.3,
                'bollinger_upper': 392.1,
                'bollinger_lower': 359.5,
                'bollinger_middle': 375.8
            },
            'fundamental_analysis': {
                'valuation_score': 0.78,
                'growth_score': 0.85,
                'stability_score': 0.91,
                'dividend_score': 0.72,
                'debt_score': 0.89
            },
            'reasoning': 'Microsoft demonstrates exceptional technical strength with all indicators pointing to continued upward momentum. Azure cloud growth and AI integration provide strong fundamental tailwinds. The company\'s diversified revenue streams and strong balance sheet make it a low-risk investment with high growth potential.'
        },
        'TSLA': {
            'symbol': 'TSLA',
            'beginner_friendly_score': 0.65,
            'risk_level': 'High',
            'recommendation': 'HOLD',
            'technical_indicators': {
                'rsi': 45.2,
                'macd': -1.8,
                'macd_signal': -0.9,
                'macd_histogram': -0.9,
                'sma20': 248.3,
                'sma50': 252.1,
                'ema12': 243.7,
                'ema26': 249.8,
                'bollinger_upper': 268.9,
                'bollinger_lower': 227.7,
                'bollinger_middle': 248.3
            },
            'fundamental_analysis': {
                'valuation_score': 0.45,
                'growth_score': 0.88,
                'stability_score': 0.52,
                'dividend_score': 0.0,
                'debt_score': 0.78
            },
            'reasoning': 'Tesla shows mixed technical signals with RSI indicating oversold conditions but MACD showing bearish momentum. High volatility and premium valuation create significant risk. While growth prospects remain strong in EV and energy sectors, current price levels may not justify the risk for conservative investors.'
        },
        'GOOGL': {
            'symbol': 'GOOGL',
            'beginner_friendly_score': 0.78,
            'risk_level': 'Medium',
            'recommendation': 'BUY',
            'technical_indicators': {
                'rsi': 55.8,
                'macd': 1.2,
                'macd_signal': 0.8,
                'macd_histogram': 0.4,
                'sma20': 140.5,
                'sma50': 138.2,
                'ema12': 142.1,
                'ema26': 139.7,
                'bollinger_upper': 148.9,
                'bollinger_lower': 132.1,
                'bollinger_middle': 140.5
            },
            'fundamental_analysis': {
                'valuation_score': 0.82,
                'growth_score': 0.75,
                'stability_score': 0.85,
                'dividend_score': 0.0,
                'debt_score': 0.88
            },
            'reasoning': 'Alphabet presents attractive technical setup with improving momentum indicators. Search dominance and AI capabilities provide strong fundamental foundation. YouTube and cloud growth offer additional revenue streams. Current valuation appears reasonable given growth prospects and market position.'
        },
        'NVDA': {
            'symbol': 'NVDA',
            'beginner_friendly_score': 0.58,
            'risk_level': 'High',
            'recommendation': 'BUY',
            'technical_indicators': {
                'rsi': 68.3,
                'macd': 8.5,
                'macd_signal': 5.2,
                'macd_histogram': 3.3,
                'sma20': 472.8,
                'sma50': 445.1,
                'ema12': 485.2,
                'ema26': 461.7,
                'bollinger_upper': 512.4,
                'bollinger_lower': 433.2,
                'bollinger_middle': 472.8
            },
            'fundamental_analysis': {
                'valuation_score': 0.35,
                'growth_score': 0.95,
                'stability_score': 0.68,
                'dividend_score': 0.15,
                'debt_score': 0.82
            },
            'reasoning': 'NVIDIA shows extremely strong technical momentum with RSI approaching overbought levels and MACD indicating strong bullish trend. AI chip leadership provides exceptional growth potential, but high valuation creates significant risk. Suitable for growth-oriented investors with high risk tolerance.'
        }
    }
    
    # Return analysis for the requested symbol, or default to AAPL
    return analysis_data.get(symbol.upper(), analysis_data['AAPL'])

    def resolve_calculateTargetPrice(self, info, entryPrice, stopPrice, riskRewardRatio=None, atr=None, resistanceLevel=None, supportLevel=None, signalType=None):
        # Calculate risk distance
        risk_distance = abs(entryPrice - stopPrice)
        
        # Default risk-reward ratio if not provided
        if riskRewardRatio is None:
            riskRewardRatio = 2.0
        
        # Calculate different target price methods
        rr_target = None
        atr_target = None
        sr_target = None
        method = "risk_reward"
        
        # Risk-Reward Ratio method
        if signalType == "BUY":
            rr_target = entryPrice + (risk_distance * riskRewardRatio)
        else:  # SELL
            rr_target = entryPrice - (risk_distance * riskRewardRatio)
        
        # ATR-based method
        if atr is not None:
            if signalType == "BUY":
                atr_target = entryPrice + (atr * riskRewardRatio)
            else:  # SELL
                atr_target = entryPrice - (atr * riskRewardRatio)
        
        # Support/Resistance method
        if signalType == "BUY" and resistanceLevel is not None:
            sr_target = resistanceLevel
            method = "resistance"
        elif signalType == "SELL" and supportLevel is not None:
            sr_target = supportLevel
            method = "support"
        
        # Choose the best target price
        target_price = rr_target  # Default to risk-reward
        
        if sr_target is not None:
            # Prefer support/resistance if it's closer to entry (more conservative)
            if signalType == "BUY":
                if sr_target < rr_target:
                    target_price = sr_target
                    method = "resistance"
            else:  # SELL
                if sr_target > rr_target:
                    target_price = sr_target
                    method = "support"
        
        if atr_target is not None:
            # Use ATR if it's more conservative than current target
            if signalType == "BUY":
                if atr_target < target_price:
                    target_price = atr_target
                    method = "atr"
            else:  # SELL
                if atr_target > target_price:
                    target_price = atr_target
                    method = "atr"
        
        # Calculate reward distance
        reward_distance = abs(target_price - entryPrice)
        
        # Recalculate actual risk-reward ratio
        actual_risk_reward_ratio = reward_distance / risk_distance if risk_distance > 0 else 0
        
        return TargetPriceResultType(
            targetPrice=round(target_price, 2),
            rewardDistance=round(reward_distance, 2),
            riskRewardRatio=round(actual_risk_reward_ratio, 2),
            method=method,
            rrTarget=round(rr_target, 2) if rr_target else None,
            atrTarget=round(atr_target, 2) if atr_target else None,
            srTarget=round(sr_target, 2) if sr_target else None
        )
    
    def resolve_calculatePositionSize(self, info, accountBalance=None, accountEquity=None, entryPrice=None, stopPrice=None, riskPercentage=None, riskPerTrade=None, riskAmount=None, maxPositionSize=None, maxPositionPct=None, confidence=None, method=None):
        # Use accountEquity if provided, otherwise accountBalance, otherwise default
        if accountEquity is not None:
            accountBalance = accountEquity
        elif accountBalance is None:
            accountBalance = 10000.0
        
        # Use riskPerTrade if provided, otherwise riskPercentage
        if riskPerTrade is not None:
            # riskPerTrade is typically passed as decimal (0.01 = 1%), convert to percentage
            riskPercentage = riskPerTrade * 100
        
        # Calculate risk per share
        risk_per_share = abs(entryPrice - stopPrice)
        
        if risk_per_share <= 0:
            # Invalid stop price
            return PositionSizeResultType(
                positionSize=0,
                shares=0,
                dollarAmount=0,
                riskAmount=0,
                riskPercentage=0,
                method="invalid",
                maxPositionSize=maxPositionSize or 0,
                recommendedSize=0,
                dollarRisk=0,
                positionValue=0,
                positionPct=0,
                riskPerTradePct=0,
                riskPerShare=0,
                maxSharesFixedRisk=0,
                maxSharesPosition=0
            )
        
        # Determine calculation method
        if method is None:
            if riskAmount is not None:
                method = "fixed_risk"
            elif riskPercentage is not None:
                method = "percentage_risk"
            else:
                method = "percentage_risk"
                riskPercentage = 1.0  # Default to 1% risk
        
        # Calculate position size based on method
        if method == "fixed_risk" and riskAmount is not None:
            # Fixed dollar risk amount
            shares = int(riskAmount / risk_per_share)
            dollar_amount = shares * entryPrice
            actual_risk_amount = shares * risk_per_share
            actual_risk_percentage = (actual_risk_amount / accountBalance) * 100
            
        elif method == "percentage_risk" and riskPercentage is not None:
            # Percentage of account balance risk
            risk_amount = (riskPercentage / 100) * accountBalance
            shares = int(risk_amount / risk_per_share)
            dollar_amount = shares * entryPrice
            actual_risk_amount = shares * risk_per_share
            actual_risk_percentage = (actual_risk_amount / accountBalance) * 100
            
        else:
            # Default to 1% risk
            risk_amount = 0.01 * accountBalance
            shares = int(risk_amount / risk_per_share)
            dollar_amount = shares * entryPrice
            actual_risk_amount = shares * risk_per_share
            actual_risk_percentage = (actual_risk_amount / accountBalance) * 100
        
        # Apply maximum position size constraints
        if maxPositionSize is not None and dollar_amount > maxPositionSize:
            shares = int(maxPositionSize / entryPrice)
            dollar_amount = shares * entryPrice
            actual_risk_amount = shares * risk_per_share
            actual_risk_percentage = (actual_risk_amount / accountBalance) * 100
            method = "max_position_constraint"
        
        if maxPositionPct is not None:
            # maxPositionPct is passed as decimal (0.1 = 10%), not percentage
            max_position_dollar = maxPositionPct * accountBalance
            if dollar_amount > max_position_dollar:
                shares = int(max_position_dollar / entryPrice)
                dollar_amount = shares * entryPrice
                actual_risk_amount = shares * risk_per_share
                actual_risk_percentage = (actual_risk_amount / accountBalance) * 100
                method = "max_position_pct_constraint"
        
        # Calculate position size as percentage of account
        position_size_percentage = (dollar_amount / accountBalance) * 100
        
        # Calculate recommended size (conservative approach)
        recommended_risk_percentage = min(actual_risk_percentage, 2.0)  # Cap at 2%
        recommended_risk_amount = (recommended_risk_percentage / 100) * accountBalance
        recommended_shares = int(recommended_risk_amount / risk_per_share)
        recommended_size = recommended_shares * entryPrice
        
        # Calculate additional fields expected by mobile app
        max_shares_fixed_risk = int(riskAmount / risk_per_share) if riskAmount else 0
        max_shares_position = int(maxPositionSize / entryPrice) if maxPositionSize else 0
        
        return PositionSizeResultType(
            positionSize=round(position_size_percentage, 2),
            shares=shares,
            dollarAmount=round(dollar_amount, 2),
            riskAmount=round(actual_risk_amount, 2),
            riskPercentage=round(actual_risk_percentage, 2),
            method=method,
            maxPositionSize=maxPositionSize or 0,
            recommendedSize=round(recommended_size, 2),
            dollarRisk=round(actual_risk_amount, 2),
            positionValue=round(dollar_amount, 2),
            positionPct=round(position_size_percentage, 2),
            riskPerTradePct=round(actual_risk_percentage, 2),
            riskPerShare=round(risk_per_share, 2),
            maxSharesFixedRisk=max_shares_fixed_risk,
            maxSharesPosition=max_shares_position
        )
    
    def resolve_calculateDynamicStop(self, info, entryPrice, atr, atrMultiplier=None, supportLevel=None, resistanceLevel=None, signalType=None):
        # Default ATR multiplier if not provided
        if atrMultiplier is None:
            atrMultiplier = 2.0
        
        # Calculate different stop loss methods
        atr_stop = None
        sr_stop = None
        pct_stop = None
        method = "atr"
        
        # ATR-based stop loss
        if signalType == "BUY":
            atr_stop = entryPrice - (atr * atrMultiplier)
        else:  # SELL
            atr_stop = entryPrice + (atr * atrMultiplier)
        
        # Support/Resistance based stop loss
        if signalType == "BUY" and supportLevel is not None:
            sr_stop = supportLevel
            method = "support_resistance"
        elif signalType == "SELL" and resistanceLevel is not None:
            sr_stop = resistanceLevel
            method = "support_resistance"
        
        # Percentage-based stop loss (default 2%)
        pct_stop_distance = entryPrice * 0.02  # 2% stop
        if signalType == "BUY":
            pct_stop = entryPrice - pct_stop_distance
        else:  # SELL
            pct_stop = entryPrice + pct_stop_distance
        
        # Choose the best stop loss
        stop_price = atr_stop  # Default to ATR
        
        if sr_stop is not None:
            # Prefer support/resistance if it's more conservative (closer to entry)
            if signalType == "BUY":
                if sr_stop > atr_stop:  # Support is higher (more conservative)
                    stop_price = sr_stop
                    method = "support_resistance"
            else:  # SELL
                if sr_stop < atr_stop:  # Resistance is lower (more conservative)
                    stop_price = sr_stop
                    method = "support_resistance"
        
        # Use percentage stop if it's more conservative than current choice
        if signalType == "BUY":
            if pct_stop > stop_price:  # Percentage stop is higher (more conservative)
                stop_price = pct_stop
                method = "percentage"
        else:  # SELL
            if pct_stop < stop_price:  # Percentage stop is lower (more conservative)
                stop_price = pct_stop
                method = "percentage"
        
        # Calculate stop distance and risk percentage
        stop_distance = abs(entryPrice - stop_price)
        risk_percentage = (stop_distance / entryPrice) * 100
        
        return DynamicStopResultType(
            stopPrice=round(stop_price, 2),
            stopDistance=round(stop_distance, 2),
            riskPercentage=round(risk_percentage, 2),
            method=method,
            atrStop=round(atr_stop, 2) if atr_stop else None,
            srStop=round(sr_stop, 2) if sr_stop else None,
            pctStop=round(pct_stop, 2) if pct_stop else None
        )
    

# RunBacktest mutation
class RunBacktestMutation(graphene.Mutation):
    class Arguments:
        config = BacktestConfigType(required=True)

    Output = RunBacktestResultType

    def mutate(self, info, config):
        try:
            # Extract values from config
            strategy_id = getattr(config, 'strategyId', '1')
            start_date = getattr(config, 'startDate', timezone.now() - timedelta(days=365))
            end_date = getattr(config, 'endDate', timezone.now())
            initial_capital = getattr(config, 'initialCapital', 10000.0)
            commission_per_trade = getattr(config, 'commissionPerTrade', 1.0)
            slippage_pct = getattr(config, 'slippagePct', 0.001)
            max_position_size = getattr(config, 'maxPositionSize', 0.1)
            risk_per_trade = getattr(config, 'riskPerTrade', 0.02)
            max_trades_per_day = getattr(config, 'maxTradesPerDay', 5)
            max_open_positions = getattr(config, 'maxOpenPositions', 3)
            parameters = getattr(config, 'parameters', {})
            
            # Set default params based on strategy
            if not parameters:
                if strategy_id == '1':
                    parameters = {
                        'ema_fast': 12,
                        'ema_slow': 26,
                        'stop_loss': 0.05,
                        'take_profit': 0.10
                    }
                elif strategy_id == '2':
                    parameters = {
                        'rsi_period': 14,
                        'oversold_threshold': 30,
                        'overbought_threshold': 70,
                        'stop_loss': 0.03,
                        'take_profit': 0.08
                    }
                else:
                    parameters = {
                        'stop_loss': 0.05,
                        'take_profit': 0.10
                    }
            
            # Simulate backtest execution with realistic results
            
            # Generate realistic performance based on strategy and symbol
            base_return = 0.15 + random.uniform(-0.05, 0.1)  # 10-25% base return
            symbol_multiplier = {
                'AAPL': 1.0, 'TSLA': 1.2, 'MSFT': 0.9, 'GOOGL': 1.1,
                'AMZN': 1.15, 'NVDA': 1.3, 'META': 1.05, 'NFLX': 0.95
            }.get(symbol, 1.0)
            
            total_return = base_return * symbol_multiplier
            final_capital = initial_capital * (1 + total_return)
            
            # Calculate other metrics
            days = (endDate - startDate).days
            annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else total_return
            
            max_drawdown = 0.05 + random.uniform(0, 0.1)  # 5-15% drawdown
            sharpe_ratio = 1.2 + random.uniform(-0.3, 0.8)  # 0.9-2.0 Sharpe
            sortino_ratio = sharpe_ratio * 1.1
            calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
            
            win_rate = 0.6 + random.uniform(-0.1, 0.2)  # 50-80% win rate
            total_trades = 30 + random.randint(0, 50)  # 30-80 trades
            winning_trades = int(total_trades * win_rate)
            losing_trades = total_trades - winning_trades
            
            profit_factor = 1.5 + random.uniform(-0.3, 0.8)  # 1.2-2.3 profit factor
            avg_win = (total_return * initial_capital * 0.6) / winning_trades if winning_trades > 0 else 0
            avg_loss = (total_return * initial_capital * 0.4) / losing_trades if losing_trades > 0 else 0
            
            # Generate mock equity curve (daily values)
            equity_curve = []
            daily_returns = []
            current_equity = initial_capital
            
            for i in range(min(days, 252)):  # Max 1 year of daily data
                daily_return = random.uniform(-0.05, 0.05)  # ±5% daily volatility
                current_equity *= (1 + daily_return)
                equity_curve.append(round(current_equity, 2))
                daily_returns.append(round(daily_return, 4))
            
            # Create result
            result = BacktestResultOutputType(
                totalReturn=round(total_return, 4),
                annualizedReturn=round(annualized_return, 4),
                maxDrawdown=round(max_drawdown, 4),
                sharpeRatio=round(sharpe_ratio, 3),
                sortinoRatio=round(sortino_ratio, 3),
                calmarRatio=round(calmar_ratio, 3),
                winRate=round(win_rate, 3),
                profitFactor=round(profit_factor, 3),
                totalTrades=total_trades,
                winningTrades=winning_trades,
                losingTrades=losing_trades,
                avgWin=round(avg_win, 2),
                avgLoss=round(avg_loss, 2),
                initialCapital=initial_capital,
                finalCapital=round(final_capital, 2),
                equityCurve=equity_curve,
                dailyReturns=daily_returns
            )
            
            return RunBacktestResultType(
                success=True,
                result=result,
                errors=[]
            )
            
        except Exception as e:
            return RunBacktestResultType(
                success=False,
                result=None,
                errors=[str(e)]
            )
