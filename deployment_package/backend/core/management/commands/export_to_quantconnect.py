"""
Export Hybrid LSTM + XGBoost Strategy to QuantConnect
Generates QuantConnect algorithm code for independent backtesting.
"""
from django.core.management.base import BaseCommand
from core.quantconnect_bridge import get_quantconnect_bridge
import os
import json
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Export hybrid LSTM + XGBoost strategy to QuantConnect format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strategy',
            type=str,
            default='hybrid_lstm_xgboost',
            help='Strategy name (default: hybrid_lstm_xgboost)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='quantconnect_strategy.py',
            help='Output file path (default: quantconnect_strategy.py)'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            default='2020-01-01',
            help='Backtest start date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            default=None,
            help='Backtest end date (YYYY-MM-DD, default: today)'
        )
        parser.add_argument(
            '--initial-capital',
            type=int,
            default=100000,
            help='Initial capital (default: 100000)'
        )
        parser.add_argument(
            '--symbols',
            type=str,
            nargs='+',
            default=['SPY'],
            help='Symbols to trade (default: SPY)'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔄 Exporting Strategy to QuantConnect")
        self.stdout.write("=" * 60)
        
        strategy_name = options['strategy']
        output_path = options['output']
        
        # Get strategy parameters
        start_date = options['start_date']
        end_date = options['end_date'] or datetime.now().strftime('%Y-%m-%d')
        initial_capital = options['initial_capital']
        symbols = options['symbols']
        
        # Get bridge
        bridge = get_quantconnect_bridge()
        
        # Prepare strategy logic
        strategy_logic = {
            'type': 'hybrid_lstm_xgboost',
            'description': 'Hybrid LSTM + XGBoost model for day trading signals',
            'features': [
                'LSTM temporal momentum score',
                'XGBoost classification with abstention',
                'Net-of-costs labeling',
                'Confidence threshold: 0.78'
            ]
        }
        
        # Prepare parameters
        parameters = {
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital,
            'symbols': symbols,
            'confidence_threshold': 0.78,
            'position_size': 0.1,  # 10% of capital per position
            'fee_bps': 5.0,  # 5 basis points commission
            'slippage_bps': 2.0,  # 2 basis points slippage
        }
        
        # Export strategy
        self.stdout.write(f"\n📊 Strategy: {strategy_name}")
        self.stdout.write(f"   Symbols: {', '.join(symbols)}")
        self.stdout.write(f"   Period: {start_date} to {end_date}")
        self.stdout.write(f"   Initial Capital: ${initial_capital:,}")
        
        result = bridge.export_strategy(
            strategy_name=strategy_name,
            strategy_logic=strategy_logic,
            parameters=parameters
        )
        
        if result.get('success'):
            # Save to file
            algorithm_code = result['algorithm_code']
            
            # Enhance with actual model logic
            enhanced_code = self._enhance_algorithm_code(algorithm_code, parameters)
            
            with open(output_path, 'w') as f:
                f.write(enhanced_code)
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Strategy exported to: {output_path}"))
            self.stdout.write(f"\n📝 Next Steps:")
            self.stdout.write(f"   1. Upload {output_path} to QuantConnect")
            self.stdout.write(f"   2. Run backtest on QuantConnect")
            self.stdout.write(f"   3. Compare results with RichesReach backtest")
            self.stdout.write(f"\n💡 Note: This is a simplified version.")
            self.stdout.write(f"   Full model requires LSTM + XGBoost inference which")
            self.stdout.write(f"   can be added via QuantConnect's ML libraries.")
        else:
            self.stdout.write(self.style.ERROR(f"\n❌ Export failed: {result.get('error')}"))

    def _enhance_algorithm_code(self, base_code: str, parameters: dict) -> str:
        """Enhance algorithm code with hybrid model logic"""
        
        enhanced = f'''"""
QuantConnect Algorithm: Hybrid LSTM + XGBoost Strategy
Exported from RichesReach AI Trading Platform
Generated: {datetime.now().isoformat()}

This algorithm implements a simplified version of the RichesReach hybrid model.
For full LSTM + XGBoost inference, use QuantConnect's ML libraries.
"""

from AlgorithmImports import *

class RichesReachHybridStrategy(QCAlgorithm):
    """
    Hybrid LSTM + XGBoost Strategy
    Exported from RichesReach ML System
    
    Strategy Logic:
    - Uses technical indicators as proxy for LSTM temporal features
    - Applies XGBoost-like decision tree logic
    - Implements net-of-costs entry/exit
    - Confidence-based position sizing
    """
    
    def Initialize(self):
        # Set backtest period
        self.SetStartDate({parameters['start_date'].replace('-', ', ')})
        self.SetEndDate({parameters['end_date'].replace('-', ', ')})
        self.SetCash({parameters['initial_capital']})
        
        # Add symbols
        symbols = {parameters['symbols']}
        for symbol in symbols:
            self.AddEquity(symbol, Resolution.Minute)
        
        # Strategy parameters
        self.confidence_threshold = {parameters['confidence_threshold']}
        self.position_size = {parameters['position_size']}
        self.fee_bps = {parameters['fee_bps']} / 10000.0
        self.slippage_bps = {parameters['slippage_bps']} / 10000.0
        self.total_friction = self.fee_bps + self.slippage_bps
        
        # Technical indicators (proxy for LSTM features)
        self.rsi = {{}}
        self.sma_fast = {{}}
        self.sma_slow = {{}}
        self.atr = {{}}
        
        for symbol in symbols:
            equity = self.Securities[symbol]
            self.rsi[symbol] = self.RSI(symbol, 14, Resolution.Minute)
            self.sma_fast[symbol] = self.SMA(symbol, 20, Resolution.Minute)
            self.sma_slow[symbol] = self.SMA(symbol, 50, Resolution.Minute)
            self.atr[symbol] = self.ATR(symbol, 14, Resolution.Minute)
        
        # Performance tracking
        self.trades = []
        self.equity_curve = []
        
    def OnData(self, data):
        """Main strategy logic"""
        for symbol in {parameters['symbols']}:
            if symbol not in data or not data[symbol]:
                continue
            
            if not self.rsi[symbol].IsReady or not self.sma_fast[symbol].IsReady:
                continue
            
            # Calculate "temporal momentum" (proxy for LSTM feature)
            price = data[symbol].Close
            sma_fast_val = self.sma_fast[symbol].Current.Value
            sma_slow_val = self.sma_slow[symbol].Current.Value if self.sma_slow[symbol].IsReady else sma_fast_val
            
            # Temporal momentum score (simplified LSTM feature)
            momentum_score = (price - sma_fast_val) / sma_fast_val if sma_fast_val > 0 else 0.0
            
            # RSI-based confidence (proxy for XGBoost confidence)
            rsi_val = self.rsi[symbol].Current.Value
            rsi_confidence = abs(rsi_val - 50) / 50.0  # Normalize to 0-1
            
            # Combined confidence (simplified hybrid model)
            confidence = (rsi_confidence + abs(momentum_score) * 2) / 2.0
            confidence = min(1.0, max(0.0, confidence))
            
            # Entry logic (BUY signal)
            if not self.Portfolio[symbol].Invested:
                if self._should_enter(symbol, price, momentum_score, confidence, data):
                    # Calculate position size based on confidence
                    position_pct = self.position_size * confidence
                    self.SetHoldings(symbol, position_pct)
                    
                    self.trades.append({{
                        'symbol': symbol,
                        'action': 'BUY',
                        'price': price,
                        'confidence': confidence,
                        'timestamp': self.Time
                    }})
            
            # Exit logic (SELL signal)
            else:
                if self._should_exit(symbol, price, momentum_score, confidence, data):
                    self.Liquidate(symbol)
                    
                    # Calculate P&L
                    entry_price = self.Portfolio[symbol].AveragePrice
                    raw_return = (price - entry_price) / entry_price
                    net_return = raw_return - self.total_friction
                    
                    self.trades.append({{
                        'symbol': symbol,
                        'action': 'SELL',
                        'price': price,
                        'entry_price': entry_price,
                        'raw_return': raw_return,
                        'net_return': net_return,
                        'timestamp': self.Time
                    }})
            
            # Track equity curve
            self.equity_curve.append({{
                'timestamp': self.Time,
                'equity': self.Portfolio.TotalPortfolioValue
            }})
    
    def _should_enter(self, symbol, price, momentum_score, confidence, data) -> bool:
        """Entry conditions (simplified hybrid model logic)"""
        rsi_val = self.rsi[symbol].Current.Value
        sma_fast_val = self.sma_fast[symbol].Current.Value
        
        # Entry conditions:
        # 1. Confidence above threshold
        # 2. Positive momentum (price above fast SMA)
        # 3. RSI not overbought (< 70)
        return (
            confidence >= self.confidence_threshold and
            momentum_score > 0.001 and  # 0.1% momentum threshold
            rsi_val < 70 and
            price > sma_fast_val
        )
    
    def _should_exit(self, symbol, price, momentum_score, confidence, data) -> bool:
        """Exit conditions (net-of-costs aware)"""
        entry_price = self.Portfolio[symbol].AveragePrice
        raw_return = (price - entry_price) / entry_price
        
        # Exit if:
        # 1. Net return (after costs) is positive and momentum reverses
        # 2. Stop loss: net return < -2%
        # 3. Take profit: net return > 3%
        # 4. Confidence drops below threshold
        net_return = raw_return - self.total_friction
        
        return (
            (net_return > 0 and momentum_score < -0.001) or  # Profit + momentum reversal
            net_return < -0.02 or  # Stop loss: -2%
            net_return > 0.03 or  # Take profit: +3%
            confidence < self.confidence_threshold * 0.7  # Confidence drop
        )
    
    def OnEndOfAlgorithm(self):
        """Calculate final metrics"""
        self.Debug(f"Total Trades: {{len(self.trades)}}")
        self.Debug(f"Final Equity: ${{self.Portfolio.TotalPortfolioValue:.2f}}")
        
        # Calculate win rate
        closed_trades = [t for t in self.trades if t.get('action') == 'SELL']
        if closed_trades:
            wins = [t for t in closed_trades if t.get('net_return', 0) > 0]
            win_rate = len(wins) / len(closed_trades) if closed_trades else 0.0
            self.Debug(f"Win Rate: {{win_rate:.2%}}")
'''
        
        return enhanced

