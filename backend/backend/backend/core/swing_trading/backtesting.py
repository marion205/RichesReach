"""
Backtesting Engine for Swing Trading Strategies
Professional backtesting with realistic execution, slippage, and commission modeling
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Callable
from decimal import Decimal
import logging
from datetime import datetime, timedelta
import math
from dataclasses import dataclass

from .indicators import TechnicalIndicators, calculate_all_indicators
from .risk_management import RiskManager, calculate_max_drawdown

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Individual trade record"""
    entry_date: datetime
    exit_date: Optional[datetime]
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    stop_loss: float
    take_profit: float
    commission: float
    slippage: float
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    duration_days: Optional[int] = None
    exit_reason: Optional[str] = None


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    initial_capital: float = 10000.0
    commission_per_trade: float = 1.0  # $1 per trade
    slippage_pct: float = 0.001  # 0.1% slippage
    max_position_size: float = 0.1  # 10% max position
    risk_per_trade: float = 0.01  # 1% risk per trade
    max_trades_per_day: int = 5
    max_open_positions: int = 10
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BacktestEngine:
    """
    Professional backtesting engine for swing trading strategies
    """
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.risk_manager = RiskManager()
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.daily_returns: List[float] = []
        self.open_positions: Dict[str, Trade] = {}
        self.current_capital = self.config.initial_capital
        self.peak_capital = self.config.initial_capital
        self.trade_count = 0
        self.daily_trade_count = 0
        self.current_date = None
        
    def run_backtest(self, 
                    df: pd.DataFrame, 
                    strategy_func: Callable,
                    strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run backtesting on historical data
        
        Args:
            df: DataFrame with OHLCV data
            strategy_func: Strategy function that generates signals
            strategy_params: Parameters for the strategy
            
        Returns:
            Dictionary with backtest results
        """
        try:
            logger.info(f"Starting backtest with {len(df)} data points")
            
            # Reset state
            self._reset_backtest_state()
            
            # Calculate technical indicators
            df_with_indicators = calculate_all_indicators(df)
            
            # Filter data by date range if specified
            if self.config.start_date:
                df_with_indicators = df_with_indicators[df_with_indicators.index >= self.config.start_date]
            if self.config.end_date:
                df_with_indicators = df_with_indicators[df_with_indicators.index <= self.config.end_date]
            
            # Run strategy on each day
            for i, (date, row) in enumerate(df_with_indicators.iterrows()):
                self.current_date = date
                self.daily_trade_count = 0
                
                # Check for exit signals on open positions
                self._check_exit_signals(row, df_with_indicators, i)
                
                # Check for new entry signals
                if self.daily_trade_count < self.config.max_trades_per_day:
                    signals = strategy_func(row, df_with_indicators, i, strategy_params or {})
                    self._process_entry_signals(signals, row, date)
                
                # Update equity curve
                self._update_equity_curve(row)
            
            # Close any remaining open positions
            self._close_all_positions(df_with_indicators.iloc[-1])
            
            # Calculate performance metrics
            results = self._calculate_performance_metrics()
            
            logger.info(f"Backtest completed: {len(self.trades)} trades, {results['total_return']:.2%} return")
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {
                'error': str(e),
                'total_return': 0.0,
                'trades': [],
                'equity_curve': []
            }
    
    def _reset_backtest_state(self):
        """Reset backtest state for new run"""
        self.trades = []
        self.equity_curve = []
        self.daily_returns = []
        self.open_positions = {}
        self.current_capital = self.config.initial_capital
        self.peak_capital = self.config.initial_capital
        self.trade_count = 0
        self.daily_trade_count = 0
        self.current_date = None
    
    def _check_exit_signals(self, row: pd.Series, df: pd.DataFrame, index: int):
        """Check for exit signals on open positions"""
        try:
            positions_to_close = []
            
            for symbol, trade in self.open_positions.items():
                exit_signal = False
                exit_reason = None
                
                # Check stop loss
                if trade.side == 'long' and row['low'] <= trade.stop_loss:
                    exit_signal = True
                    exit_reason = 'stop_loss'
                    trade.exit_price = trade.stop_loss
                elif trade.side == 'short' and row['high'] >= trade.stop_loss:
                    exit_signal = True
                    exit_reason = 'stop_loss'
                    trade.exit_price = trade.stop_loss
                
                # Check take profit
                if not exit_signal:
                    if trade.side == 'long' and row['high'] >= trade.take_profit:
                        exit_signal = True
                        exit_reason = 'take_profit'
                        trade.exit_price = trade.take_profit
                    elif trade.side == 'short' and row['low'] <= trade.take_profit:
                        exit_signal = True
                        exit_reason = 'take_profit'
                        trade.exit_price = trade.take_profit
                
                # Check time-based exit (e.g., 30 days max hold)
                if not exit_signal:
                    days_held = (self.current_date - trade.entry_date).days
                    if days_held >= 30:  # Max 30 days hold
                        exit_signal = True
                        exit_reason = 'time_exit'
                        trade.exit_price = row['close']
                
                if exit_signal:
                    positions_to_close.append(symbol)
                    self._close_trade(trade, exit_reason)
            
            # Remove closed positions
            for symbol in positions_to_close:
                del self.open_positions[symbol]
                
        except Exception as e:
            logger.error(f"Error checking exit signals: {e}")
    
    def _process_entry_signals(self, signals: List[Dict[str, Any]], row: pd.Series, date: datetime):
        """Process entry signals and open new positions"""
        try:
            for signal in signals:
                if len(self.open_positions) >= self.config.max_open_positions:
                    break
                
                if self.daily_trade_count >= self.config.max_trades_per_day:
                    break
                
                symbol = signal.get('symbol', 'UNKNOWN')
                side = signal.get('side', 'long')
                entry_price = signal.get('entry_price', row['close'])
                stop_loss = signal.get('stop_loss')
                take_profit = signal.get('take_profit')
                confidence = signal.get('confidence', 0.5)
                
                # Skip if already have position in this symbol
                if symbol in self.open_positions:
                    continue
                
                # Calculate position size
                position_size = self._calculate_position_size(entry_price, stop_loss, confidence)
                
                if position_size['shares'] <= 0:
                    continue
                
                # Create trade
                trade = Trade(
                    entry_date=date,
                    exit_date=None,
                    symbol=symbol,
                    side=side,
                    entry_price=entry_price,
                    exit_price=None,
                    quantity=position_size['shares'],
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    commission=self.config.commission_per_trade,
                    slippage=entry_price * self.config.slippage_pct
                )
                
                # Adjust entry price for slippage
                if side == 'long':
                    trade.entry_price += trade.slippage
                else:
                    trade.entry_price -= trade.slippage
                
                # Add to open positions
                self.open_positions[symbol] = trade
                self.trades.append(trade)
                self.trade_count += 1
                self.daily_trade_count += 1
                
                # Update capital
                position_value = trade.quantity * trade.entry_price
                self.current_capital -= position_value + trade.commission
                
        except Exception as e:
            logger.error(f"Error processing entry signals: {e}")
    
    def _calculate_position_size(self, entry_price: float, stop_loss: float, confidence: float) -> Dict[str, Any]:
        """Calculate position size based on risk management rules"""
        try:
            # Adjust risk based on signal confidence
            adjusted_risk = self.config.risk_per_trade * confidence
            
            return self.risk_manager.calculate_position_size(
                account_equity=self.current_capital,
                entry_price=entry_price,
                stop_price=stop_loss,
                risk_per_trade=adjusted_risk,
                max_position_pct=self.config.max_position_size
            )
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {'shares': 0}
    
    def _close_trade(self, trade: Trade, exit_reason: str):
        """Close a trade and calculate P&L"""
        try:
            trade.exit_date = self.current_date
            trade.exit_reason = exit_reason
            
            # Calculate P&L
            if trade.side == 'long':
                trade.pnl = (trade.exit_price - trade.entry_price) * trade.quantity - trade.commission
            else:
                trade.pnl = (trade.entry_price - trade.exit_price) * trade.quantity - trade.commission
            
            trade.pnl_pct = trade.pnl / (trade.entry_price * trade.quantity) * 100
            trade.duration_days = (trade.exit_date - trade.entry_date).days
            
            # Update capital
            position_value = trade.quantity * trade.exit_price
            self.current_capital += position_value - trade.commission
            
            # Update peak capital
            if self.current_capital > self.peak_capital:
                self.peak_capital = self.current_capital
                
        except Exception as e:
            logger.error(f"Error closing trade: {e}")
    
    def _close_all_positions(self, last_row: pd.Series):
        """Close all remaining open positions at the end of backtest"""
        try:
            for symbol, trade in self.open_positions.items():
                trade.exit_price = last_row['close']
                self._close_trade(trade, 'end_of_data')
            
            self.open_positions.clear()
            
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
    
    def _update_equity_curve(self, row: pd.Series):
        """Update equity curve with current portfolio value"""
        try:
            # Calculate current portfolio value
            portfolio_value = self.current_capital
            
            # Add value of open positions
            for trade in self.open_positions.values():
                position_value = trade.quantity * row['close']
                portfolio_value += position_value
            
            self.equity_curve.append(portfolio_value)
            
            # Calculate daily return
            if len(self.equity_curve) > 1:
                daily_return = (portfolio_value - self.equity_curve[-2]) / self.equity_curve[-2]
                self.daily_returns.append(daily_return)
            else:
                self.daily_returns.append(0.0)
                
        except Exception as e:
            logger.error(f"Error updating equity curve: {e}")
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            if not self.trades or not self.equity_curve:
                return {
                    'total_return': 0.0,
                    'annualized_return': 0.0,
                    'max_drawdown': 0.0,
                    'sharpe_ratio': 0.0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'total_trades': 0,
                    'trades': [],
                    'equity_curve': []
                }
            
            # Basic metrics
            initial_capital = self.config.initial_capital
            final_capital = self.equity_curve[-1]
            total_return = (final_capital - initial_capital) / initial_capital
            
            # Calculate time period
            if len(self.equity_curve) > 1:
                days = len(self.equity_curve)
                years = days / 365.25
                annualized_return = (final_capital / initial_capital) ** (1 / years) - 1 if years > 0 else 0
            else:
                annualized_return = 0
            
            # Drawdown metrics
            drawdown_metrics = calculate_max_drawdown(self.equity_curve)
            
            # Trade statistics
            completed_trades = [t for t in self.trades if t.exit_date is not None]
            winning_trades = [t for t in completed_trades if t.pnl and t.pnl > 0]
            losing_trades = [t for t in completed_trades if t.pnl and t.pnl < 0]
            
            total_trades = len(completed_trades)
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            
            # Profit factor
            total_wins = sum(t.pnl for t in winning_trades) if winning_trades else 0
            total_losses = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Average win/loss
            avg_win = total_wins / len(winning_trades) if winning_trades else 0
            avg_loss = total_losses / len(losing_trades) if losing_trades else 0
            
            # Sharpe ratio
            if len(self.daily_returns) > 1:
                mean_return = np.mean(self.daily_returns)
                std_return = np.std(self.daily_returns)
                sharpe_ratio = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Sortino ratio
            if len(self.daily_returns) > 1:
                negative_returns = [r for r in self.daily_returns if r < 0]
                downside_std = np.std(negative_returns) if negative_returns else 0
                sortino_ratio = (np.mean(self.daily_returns) / downside_std) * np.sqrt(252) if downside_std > 0 else 0
            else:
                sortino_ratio = 0
            
            # Calmar ratio
            calmar_ratio = annualized_return / (drawdown_metrics['max_drawdown_pct'] / 100) if drawdown_metrics['max_drawdown_pct'] > 0 else 0
            
            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'max_drawdown': drawdown_metrics['max_drawdown_pct'],
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'total_wins': total_wins,
                'total_losses': total_losses,
                'initial_capital': initial_capital,
                'final_capital': final_capital,
                'trades': [
                    {
                        'entry_date': t.entry_date.isoformat(),
                        'exit_date': t.exit_date.isoformat() if t.exit_date else None,
                        'symbol': t.symbol,
                        'side': t.side,
                        'entry_price': t.entry_price,
                        'exit_price': t.exit_price,
                        'quantity': t.quantity,
                        'pnl': t.pnl,
                        'pnl_pct': t.pnl_pct,
                        'duration_days': t.duration_days,
                        'exit_reason': t.exit_reason
                    }
                    for t in completed_trades
                ],
                'equity_curve': self.equity_curve,
                'daily_returns': self.daily_returns
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {
                'error': str(e),
                'total_return': 0.0,
                'trades': [],
                'equity_curve': []
            }


# Pre-built strategy functions

def ema_crossover_strategy(row: pd.Series, df: pd.DataFrame, index: int, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    EMA Crossover Strategy
    
    Args:
        row: Current row data
        df: Full DataFrame
        index: Current index
        
    Returns:
        List of signals
    """
    signals = []
    
    try:
        if index < 1:
            return signals
        
        # Get current and previous values
        current_ema_fast = row.get('ema_12', 0)
        current_ema_slow = row.get('ema_26', 0)
        prev_ema_fast = df.iloc[index-1].get('ema_12', 0)
        prev_ema_slow = df.iloc[index-1].get('ema_26', 0)
        
        if current_ema_fast == 0 or current_ema_slow == 0:
            return signals
        
        # Bullish crossover
        if (current_ema_fast > current_ema_slow and 
            prev_ema_fast <= prev_ema_slow and
            row.get('volume_surge', 1) > 1.2):
            
            entry_price = row['close']
            atr = row.get('atr_14', entry_price * 0.02)
            stop_loss = entry_price - (atr * 1.5)
            take_profit = entry_price + (atr * 3.0)
            
            signals.append({
                'symbol': row.get('symbol', 'UNKNOWN'),
                'side': 'long',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': min(0.8, row.get('volume_surge', 1) / 2),
                'strategy': 'ema_crossover'
            })
        
        # Bearish crossover
        elif (current_ema_fast < current_ema_slow and 
              prev_ema_fast >= prev_ema_slow and
              row.get('volume_surge', 1) > 1.2):
            
            entry_price = row['close']
            atr = row.get('atr_14', entry_price * 0.02)
            stop_loss = entry_price + (atr * 1.5)
            take_profit = entry_price - (atr * 3.0)
            
            signals.append({
                'symbol': row.get('symbol', 'UNKNOWN'),
                'side': 'short',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': min(0.8, row.get('volume_surge', 1) / 2),
                'strategy': 'ema_crossover'
            })
    
    except Exception as e:
        logger.error(f"Error in EMA crossover strategy: {e}")
    
    return signals


def rsi_mean_reversion_strategy(row: pd.Series, df: pd.DataFrame, index: int, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    RSI Mean Reversion Strategy
    
    Args:
        row: Current row data
        df: Full DataFrame
        index: Current index
        
    Returns:
        List of signals
    """
    signals = []
    
    try:
        rsi = row.get('rsi_14', 50)
        volume_surge = row.get('volume_surge', 1)
        
        # RSI oversold bounce
        if rsi < 30 and volume_surge > 1.5:
            entry_price = row['close']
            atr = row.get('atr_14', entry_price * 0.02)
            stop_loss = entry_price - (atr * 1.2)
            take_profit = entry_price + (atr * 2.5)
            
            signals.append({
                'symbol': row.get('symbol', 'UNKNOWN'),
                'side': 'long',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': min(0.9, (30 - rsi) / 30 + 0.3),
                'strategy': 'rsi_mean_reversion'
            })
        
        # RSI overbought rejection
        elif rsi > 70 and volume_surge > 1.5:
            entry_price = row['close']
            atr = row.get('atr_14', entry_price * 0.02)
            stop_loss = entry_price + (atr * 1.2)
            take_profit = entry_price - (atr * 2.5)
            
            signals.append({
                'symbol': row.get('symbol', 'UNKNOWN'),
                'side': 'short',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': min(0.9, (rsi - 70) / 30 + 0.3),
                'strategy': 'rsi_mean_reversion'
            })
    
    except Exception as e:
        logger.error(f"Error in RSI mean reversion strategy: {e}")
    
    return signals


def breakout_strategy(row: pd.Series, df: pd.DataFrame, index: int, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Breakout Strategy
    
    Args:
        row: Current row data
        df: Full DataFrame
        index: Current index
        
    Returns:
        List of signals
    """
    signals = []
    
    try:
        close = row['close']
        high = row['high']
        low = row['low']
        volume_surge = row.get('volume_surge', 1)
        bb_upper = row.get('bb_upper', close * 1.02)
        bb_lower = row.get('bb_lower', close * 0.98)
        
        # Bullish breakout
        if high > bb_upper and volume_surge > 2.0:
            entry_price = bb_upper
            atr = row.get('atr_14', close * 0.02)
            stop_loss = close - (atr * 1.0)
            take_profit = close + (atr * 3.0)
            
            signals.append({
                'symbol': row.get('symbol', 'UNKNOWN'),
                'side': 'long',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': min(0.9, volume_surge / 3),
                'strategy': 'breakout'
            })
        
        # Bearish breakdown
        elif low < bb_lower and volume_surge > 2.0:
            entry_price = bb_lower
            atr = row.get('atr_14', close * 0.02)
            stop_loss = close + (atr * 1.0)
            take_profit = close - (atr * 3.0)
            
            signals.append({
                'symbol': row.get('symbol', 'UNKNOWN'),
                'side': 'short',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': min(0.9, volume_surge / 3),
                'strategy': 'breakout'
            })
    
    except Exception as e:
        logger.error(f"Error in breakout strategy: {e}")
    
    return signals


def run_strategy_backtest(df: pd.DataFrame, 
                         strategy_name: str, 
                         config: BacktestConfig = None,
                         strategy_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run backtest for a specific strategy
    
    Args:
        df: Historical data
        strategy_name: Name of strategy to run
        config: Backtest configuration
        strategy_params: Strategy parameters
        
    Returns:
        Backtest results
    """
    try:
        # Select strategy function
        strategy_functions = {
            'ema_crossover': ema_crossover_strategy,
            'rsi_mean_reversion': rsi_mean_reversion_strategy,
            'breakout': breakout_strategy
        }
        
        if strategy_name not in strategy_functions:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        # Run backtest
        engine = BacktestEngine(config)
        results = engine.run_backtest(df, strategy_functions[strategy_name], strategy_params)
        
        # Add strategy info
        results['strategy_name'] = strategy_name
        results['strategy_params'] = strategy_params or {}
        
        return results
        
    except Exception as e:
        logger.error(f"Error running strategy backtest: {e}")
        return {
            'error': str(e),
            'strategy_name': strategy_name,
            'total_return': 0.0
        }
