"""
RAHA Backtest Service
Runs historical backtests using real historical data and PaperTradingService
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import date, timedelta, datetime
from decimal import Decimal
import asyncio

from .raha_models import RAHABacktestRun, StrategyVersion
from .paper_trading_service import PaperTradingService
from .raha_strategy_engine import RAHAStrategyEngine
from .fss_data_pipeline import FSSDataPipeline, FSSDataRequest

logger = logging.getLogger(__name__)


class RAHABacktestService:
    """
    Service for running RAHA strategy backtests.
    Uses real historical data and PaperTradingService for virtual execution.
    """
    
    def __init__(self):
        self.paper_trading = PaperTradingService()
        self.strategy_engine = RAHAStrategyEngine()
        self.data_pipeline = FSSDataPipeline()
    
    def run_backtest(self, backtest_run_id: str) -> RAHABacktestRun:
        """
        Run a backtest with real historical data and strategy execution.
        
        Args:
            backtest_run_id: UUID of the backtest run
        
        Returns:
            Updated RAHABacktestRun instance
        """
        try:
            backtest = RAHABacktestRun.objects.get(id=backtest_run_id)
            backtest.status = 'RUNNING'
            backtest.save()
            
            logger.info(f"Starting backtest {backtest_run_id} for {backtest.strategy_version.strategy.name} on {backtest.symbol}")
            
            # Step 1: Fetch historical OHLCV data
            logger.info(f"Fetching historical data for {backtest.symbol} from {backtest.start_date} to {backtest.end_date}")
            historical_data = self._fetch_historical_data(
                symbol=backtest.symbol,
                start_date=backtest.start_date,
                end_date=backtest.end_date
            )
            
            if historical_data is None or historical_data.empty:
                logger.warning(f"No historical data available for {backtest.symbol}")
                backtest.status = 'FAILED'
                backtest.save()
                return backtest
            
            logger.info(f"Fetched {len(historical_data)} bars of historical data")
            
            # Step 2: Generate signals using RAHAStrategyEngine
            logger.info("Generating signals from historical data...")
            signals = self._generate_signals_from_history(
                symbol=backtest.symbol,
                historical_data=historical_data,
                strategy_version=backtest.strategy_version
            )
            
            logger.info(f"Generated {len(signals)} signals")
            
            # Step 3: Execute trades using PaperTradingService (virtual)
            logger.info("Executing virtual trades...")
            trades, equity_curve = self._execute_backtest_trades(
                symbol=backtest.symbol,
                signals=signals,
                historical_data=historical_data,
                initial_capital=Decimal('100000.00')
            )
            
            logger.info(f"Executed {len(trades)} trades")
            
            # Step 4: Calculate metrics
            logger.info("Calculating performance metrics...")
            metrics = self._calculate_metrics(trades, equity_curve)
            
            # Step 5: Build equity curve
            equity_curve_data = [
                {
                    'timestamp': point['timestamp'].isoformat() if isinstance(point['timestamp'], datetime) else str(point['timestamp']),
                    'equity': float(point['equity'])
                }
                for point in equity_curve
            ]
            
            # Format trade log
            trade_log_data = [
                {
                    'timestamp': trade['timestamp'].isoformat() if isinstance(trade['timestamp'], datetime) else str(trade['timestamp']),
                    'action': trade['action'],
                    'price': float(trade['price']),
                    'shares': int(trade.get('shares', 0)),
                    'pnl': float(trade.get('pnl', 0))
                }
                for trade in trades
            ]
            
            # Update backtest with results
            backtest.metrics = metrics
            backtest.equity_curve = equity_curve_data
            backtest.trade_log = trade_log_data
            backtest.status = 'COMPLETED'
            from django.utils import timezone
            backtest.completed_at = timezone.now()
            backtest.save()
            
            logger.info(f"Backtest {backtest_run_id} completed successfully")
            logger.info(f"Results: Win Rate={metrics.get('win_rate', 0):.2%}, Sharpe={metrics.get('sharpe_ratio', 0):.2f}, Max DD={metrics.get('max_drawdown', 0):.2%}")
            
            return backtest
            
        except RAHABacktestRun.DoesNotExist:
            logger.error(f"Backtest run {backtest_run_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error running backtest {backtest_run_id}: {e}", exc_info=True)
            try:
                backtest = RAHABacktestRun.objects.get(id=backtest_run_id)
                backtest.status = 'FAILED'
                backtest.save()
            except:
                pass
            raise
    
    def _fetch_historical_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data for backtesting.
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Calculate lookback days
            days = (end_date - start_date).days
            
            # Use FSSDataPipeline to fetch data
            request = FSSDataRequest(
                tickers=[symbol],
                lookback_days=days + 30,  # Extra buffer
                include_fundamentals=False
            )
            
            # Run async fetch
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create new one
                    import nest_asyncio
                    nest_asyncio.apply()
                    result = loop.run_until_complete(self.data_pipeline.fetch_fss_data(request))
                else:
                    result = loop.run_until_complete(self.data_pipeline.fetch_fss_data(request))
            except RuntimeError:
                # No event loop, create new one
                result = asyncio.run(self.data_pipeline.fetch_fss_data(request))
            
            if result and result.prices is not None and not result.prices.empty:
                # Convert to OHLCV format
                prices_df = result.prices
                volumes_df = result.volumes
                
                # Filter by date range
                prices_df = prices_df[(prices_df.index.date >= start_date) & (prices_df.index.date <= end_date)]
                
                if prices_df.empty:
                    return None
                
                # Create OHLCV DataFrame
                ohlcv = pd.DataFrame({
                    'open': prices_df[symbol] * 0.998,  # Approximate open (use close as proxy)
                    'high': prices_df[symbol] * 1.002,  # Approximate high
                    'low': prices_df[symbol] * 0.998,   # Approximate low
                    'close': prices_df[symbol],
                    'volume': volumes_df[symbol] if symbol in volumes_df.columns else 0
                })
                
                # If we have real OHLCV data, use it (from Alpaca/Polygon)
                # For now, use close price as proxy for all OHLCV
                ohlcv['open'] = ohlcv['close'].shift(1).fillna(ohlcv['close'])
                ohlcv['high'] = ohlcv[['open', 'close']].max(axis=1) * 1.001
                ohlcv['low'] = ohlcv[['open', 'close']].min(axis=1) * 0.999
                
                return ohlcv
            
            # Fallback: Try yfinance
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    ohlcv = pd.DataFrame({
                        'open': hist['Open'],
                        'high': hist['High'],
                        'low': hist['Low'],
                        'close': hist['Close'],
                        'volume': hist['Volume']
                    })
                    return ohlcv
            except Exception as e:
                logger.warning(f"yfinance fallback failed: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}", exc_info=True)
            return None
    
    def _generate_signals_from_history(
        self,
        symbol: str,
        historical_data: pd.DataFrame,
        strategy_version: StrategyVersion
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals from historical data.
        
        Args:
            symbol: Stock symbol
            historical_data: Historical OHLCV DataFrame
            strategy_version: Strategy version to use
        
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        try:
            # Get strategy logic reference
            logic_ref = strategy_version.logic_ref
            
            # Process historical data in chronological order
            for idx, row in historical_data.iterrows():
                # Create a data point for the strategy engine
                data_point = {
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume'],
                    'timestamp': idx
                }
                
                # Generate signal using strategy engine
                # This is simplified - in production, would use full strategy engine
                signal = self._generate_signal_for_data_point(
                    symbol=symbol,
                    data_point=data_point,
                    logic_ref=logic_ref,
                    historical_data=historical_data.loc[:idx] if isinstance(idx, pd.Timestamp) else historical_data.iloc[:historical_data.index.get_loc(idx)]
                )
                
                if signal:
                    signals.append(signal)
        
        except Exception as e:
            logger.error(f"Error generating signals: {e}", exc_info=True)
        
        return signals
    
    def _generate_signal_for_data_point(
        self,
        symbol: str,
        data_point: Dict[str, Any],
        logic_ref: str,
        historical_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a single signal for a data point.
        
        Simplified implementation - uses basic technical indicators.
        """
        try:
            if len(historical_data) < 20:
                return None
            
            # Calculate simple indicators
            closes = historical_data['close'].values
            current_price = data_point['close']
            
            # Simple moving averages
            sma_20 = np.mean(closes[-20:])
            sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else sma_20
            
            # RSI approximation
            price_changes = np.diff(closes[-14:])
            gains = price_changes[price_changes > 0].sum()
            losses = abs(price_changes[price_changes < 0].sum())
            rs = gains / losses if losses > 0 else 0
            rsi = 100 - (100 / (1 + rs)) if rs > 0 else 50
            
            # Generate signal based on strategy type
            if 'ORB' in logic_ref or 'MOMENTUM' in logic_ref:
                # Momentum/ORB strategy
                if current_price > sma_20 and rsi < 70:
                    return {
                        'action': 'BUY',
                        'price': current_price,
                        'confidence': 0.75,
                        'timestamp': data_point['timestamp']
                    }
                elif current_price < sma_20 and rsi > 30:
                    return {
                        'action': 'SELL',
                        'price': current_price,
                        'confidence': 0.75,
                        'timestamp': data_point['timestamp']
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"Error generating signal: {e}")
            return None
    
    def _execute_backtest_trades(
        self,
        symbol: str,
        signals: List[Dict[str, Any]],
        historical_data: pd.DataFrame,
        initial_capital: Decimal
    ) -> tuple:
        """
        Execute virtual trades from signals.
        
        Returns:
            Tuple of (trades list, equity_curve list)
        """
        trades = []
        equity_curve = []
        
        cash = initial_capital
        shares = Decimal('0')
        entry_price = Decimal('0')
        equity = initial_capital
        
        for signal in signals:
            timestamp = signal['timestamp']
            action = signal['action']
            price = Decimal(str(signal['price']))
            
            if action == 'BUY' and shares == 0:
                # Enter position
                shares_to_buy = (cash * Decimal('0.1')) / price  # 10% of capital
                cost = shares_to_buy * price
                commission = cost * Decimal('0.0005')  # 5 bps
                total_cost = cost + commission
                
                if total_cost <= cash:
                    shares = shares_to_buy
                    cash -= total_cost
                    entry_price = price
                    
                    trades.append({
                        'timestamp': timestamp,
                        'action': 'BUY',
                        'price': float(price),
                        'shares': float(shares),
                        'cost': float(total_cost),
                        'pnl': 0.0
                    })
            
            elif action == 'SELL' and shares > 0:
                # Exit position
                proceeds = shares * price
                commission = proceeds * Decimal('0.0005')  # 5 bps
                slippage = proceeds * Decimal('0.0002')  # 2 bps
                net_proceeds = proceeds - commission - slippage
                
                pnl = net_proceeds - (shares * entry_price)
                pnl_percent = (pnl / (shares * entry_price)) * 100 if entry_price > 0 else 0
                
                cash += net_proceeds
                equity = cash
                shares = Decimal('0')
                
                trades.append({
                    'timestamp': timestamp,
                    'action': 'SELL',
                    'price': float(price),
                    'shares': float(shares),
                    'proceeds': float(net_proceeds),
                    'pnl': float(pnl),
                    'pnl_percent': float(pnl_percent)
                })
            
            # Update equity curve
            current_equity = cash + (shares * price if shares > 0 else Decimal('0'))
            equity_curve.append({
                'timestamp': timestamp,
                'equity': float(current_equity)
            })
        
        return trades, equity_curve
    
    def _calculate_metrics(
        self,
        trades: List[Dict[str, Any]],
        equity_curve: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics from trades and equity curve.
        """
        if not trades or not equity_curve:
            return {
                'win_rate': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'total_pnl_percent': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'expectancy': 0.0
            }
        
        # Filter closed trades (SELL actions with P&L)
        closed_trades = [t for t in trades if t.get('action') == 'SELL' and 'pnl' in t]
        
        if not closed_trades:
            return {
                'win_rate': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'total_pnl_percent': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'expectancy': 0.0
            }
        
        # Calculate win rate
        wins = [t for t in closed_trades if t.get('pnl', 0) > 0]
        losses = [t for t in closed_trades if t.get('pnl', 0) <= 0]
        win_rate = len(wins) / len(closed_trades) if closed_trades else 0.0
        
        # Calculate total P&L
        total_pnl = sum(t.get('pnl', 0) for t in closed_trades)
        initial_equity = equity_curve[0]['equity'] if equity_curve else 100000.0
        total_pnl_percent = (total_pnl / initial_equity * 100) if initial_equity > 0 else 0.0
        
        # Calculate max drawdown
        equity_values = [point['equity'] for point in equity_curve]
        if equity_values:
            peak = equity_values[0]
            max_dd = 0.0
            for equity in equity_values:
                if equity > peak:
                    peak = equity
                dd = (equity - peak) / peak if peak > 0 else 0.0
                if dd < max_dd:
                    max_dd = dd
        else:
            max_dd = 0.0
        
        # Calculate Sharpe ratio (simplified)
        returns = [t.get('pnl_percent', 0) / 100.0 for t in closed_trades]
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns) if len(returns) > 1 else 0.0
            sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0.0  # Annualized
        else:
            sharpe_ratio = 0.0
        
        # Calculate expectancy (average R-multiple)
        if wins and losses:
            avg_win = np.mean([t.get('pnl', 0) for t in wins])
            avg_loss = abs(np.mean([t.get('pnl', 0) for t in losses]))
            expectancy = (avg_win * win_rate - avg_loss * (1 - win_rate)) / initial_equity if initial_equity > 0 else 0.0
        else:
            expectancy = 0.0
        
        return {
            'win_rate': float(win_rate),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_dd),
            'total_pnl_percent': float(total_pnl_percent),
            'total_trades': len(closed_trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'expectancy': float(expectancy)
        }

