"""
Custom Strategy Engine
Executes user-created custom trading strategies
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from decimal import Decimal

from .raha_models import StrategyVersion
from .day_trading_feature_service import DayTradingFeatureService

logger = logging.getLogger(__name__)


class CustomStrategyEngine:
    """
    Engine for executing custom user-created strategies.
    Interprets strategy logic defined in JSON format.
    """
    
    def __init__(self):
        self.feature_service = DayTradingFeatureService()
    
    def execute_custom_strategy(
        self,
        strategy_version: StrategyVersion,
        symbol: str,
        timeframe: str = "5m",
        lookback_candles: int = 500,
        parameters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a custom strategy defined in custom_logic JSON.
        
        Args:
            strategy_version: StrategyVersion with custom_logic
            symbol: Stock symbol
            timeframe: Candle timeframe
            lookback_candles: Number of historical candles
            parameters: Strategy parameters
        
        Returns:
            List of signal dictionaries
        """
        if not strategy_version.custom_logic:
            logger.warning(f"Strategy {strategy_version.id} has no custom_logic")
            return []
        
        try:
            # Fetch OHLCV data
            ohlcv_data = self._fetch_ohlcv_data(symbol, timeframe, lookback_candles)
            if ohlcv_data is None or ohlcv_data.empty:
                logger.warning(f"No OHLCV data for {symbol}")
                return []
            
            # Execute strategy logic
            signals = self._execute_logic(
                strategy_version.custom_logic,
                ohlcv_data,
                parameters or {}
            )
            
            return signals
            
        except Exception as e:
            logger.error(f"Error executing custom strategy: {e}", exc_info=True)
            return []
    
    def _fetch_ohlcv_data(
        self,
        symbol: str,
        timeframe: str,
        lookback_candles: int
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data using existing infrastructure"""
        try:
            from .raha_strategy_engine import RAHAStrategyEngine
            engine = RAHAStrategyEngine()
            return engine._fetch_ohlcv_data(symbol, timeframe, lookback_candles)
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}", exc_info=True)
            return None
    
    def _execute_logic(
        self,
        logic: Dict[str, Any],
        ohlcv_data: pd.DataFrame,
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute custom strategy logic.
        
        Logic structure:
        {
            "conditions": [
                {
                    "type": "indicator",
                    "indicator": "rsi",
                    "operator": ">",
                    "value": 70
                },
                {
                    "type": "price",
                    "field": "close",
                    "operator": ">",
                    "value": "sma_20"
                }
            ],
            "entry": {
                "type": "long",  # or "short"
                "conditions": ["all", "any"]  # all conditions must be true, or any
            },
            "exit": {
                "stop_loss": 0.02,  # 2% stop loss
                "take_profit": 0.04,  # 4% take profit
                "time_stop": 240  # 4 hours (in minutes)
            }
        }
        """
        signals = []
        
        try:
            # Calculate indicators
            indicators = self._calculate_indicators(ohlcv_data, logic.get('indicators', []))
            
            # Evaluate entry conditions
            entry_conditions = logic.get('entry', {}).get('conditions', [])
            entry_type = logic.get('entry', {}).get('type', 'long')
            require_all = logic.get('entry', {}).get('require_all', True)
            
            # Check each candle for entry signals
            for i in range(len(ohlcv_data) - 1, max(0, len(ohlcv_data) - 50), -1):  # Check last 50 candles
                candle = ohlcv_data.iloc[i]
                
                # Evaluate conditions
                condition_results = []
                for condition in entry_conditions:
                    result = self._evaluate_condition(condition, candle, indicators, i, ohlcv_data)
                    condition_results.append(result)
                
                # Check if entry conditions are met
                if require_all:
                    entry_signal = all(condition_results)
                else:
                    entry_signal = any(condition_results)
                
                if entry_signal:
                    # Calculate stop loss and take profit
                    exit_config = logic.get('exit', {})
                    entry_price = float(candle['close'])
                    
                    if entry_type == 'long':
                        stop_loss_pct = exit_config.get('stop_loss', 0.02)
                        take_profit_pct = exit_config.get('take_profit', 0.04)
                        stop_loss = entry_price * (1 - stop_loss_pct)
                        take_profit = entry_price * (1 + take_profit_pct)
                    else:  # short
                        stop_loss_pct = exit_config.get('stop_loss', 0.02)
                        take_profit_pct = exit_config.get('take_profit', 0.04)
                        stop_loss = entry_price * (1 + stop_loss_pct)
                        take_profit = entry_price * (1 - take_profit_pct)
                    
                    # Create signal
                    signal = {
                        'signal_type': 'ENTRY_LONG' if entry_type == 'long' else 'ENTRY_SHORT',
                        'price': Decimal(str(entry_price)),
                        'stop_loss': Decimal(str(stop_loss)),
                        'take_profit': Decimal(str(take_profit)),
                        'confidence_score': Decimal('0.7'),  # Default confidence
                        'meta': {
                            'custom_strategy': True,
                            'timestamp': candle.name if hasattr(candle, 'name') else datetime.now(),
                            'conditions_met': len([r for r in condition_results if r])
                        }
                    }
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error executing logic: {e}", exc_info=True)
            return []
    
    def _calculate_indicators(
        self,
        ohlcv_data: pd.DataFrame,
        indicator_configs: List[Dict[str, Any]]
    ) -> Dict[str, pd.Series]:
        """Calculate technical indicators"""
        indicators = {}
        
        try:
            # Calculate common indicators
            if len(ohlcv_data) >= 20:
                indicators['sma_20'] = ohlcv_data['close'].rolling(window=20).mean()
                indicators['sma_50'] = ohlcv_data['close'].rolling(window=50).mean()
            
            if len(ohlcv_data) >= 14:
                # RSI
                delta = ohlcv_data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                indicators['rsi'] = 100 - (100 / (1 + rs))
                
                # MACD
                ema_12 = ohlcv_data['close'].ewm(span=12, adjust=False).mean()
                ema_26 = ohlcv_data['close'].ewm(span=26, adjust=False).mean()
                indicators['macd'] = ema_12 - ema_26
                indicators['macd_signal'] = indicators['macd'].ewm(span=9, adjust=False).mean()
            
            # ATR
            if len(ohlcv_data) >= 14:
                high_low = ohlcv_data['high'] - ohlcv_data['low']
                high_close = np.abs(ohlcv_data['high'] - ohlcv_data['close'].shift())
                low_close = np.abs(ohlcv_data['low'] - ohlcv_data['close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = ranges.max(axis=1)
                indicators['atr'] = true_range.rolling(window=14).mean()
            
            # Calculate custom indicators from config
            for config in indicator_configs:
                ind_type = config.get('type')
                if ind_type == 'sma':
                    window = config.get('window', 20)
                    if len(ohlcv_data) >= window:
                        indicators[f"sma_{window}"] = ohlcv_data['close'].rolling(window=window).mean()
                elif ind_type == 'ema':
                    window = config.get('window', 12)
                    if len(ohlcv_data) >= window:
                        indicators[f"ema_{window}"] = ohlcv_data['close'].ewm(span=window, adjust=False).mean()
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}", exc_info=True)
            return {}
    
    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        candle: pd.Series,
        indicators: Dict[str, pd.Series],
        index: int,
        ohlcv_data: pd.DataFrame
    ) -> bool:
        """Evaluate a single condition"""
        try:
            cond_type = condition.get('type')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if cond_type == 'indicator':
                indicator_name = condition.get('indicator')
                if indicator_name not in indicators:
                    return False
                
                indicator_value = indicators[indicator_name].iloc[index] if index < len(indicators[indicator_name]) else None
                if indicator_value is None or pd.isna(indicator_value):
                    return False
                
                return self._compare_values(indicator_value, operator, value)
            
            elif cond_type == 'price':
                field = condition.get('field', 'close')
                if field not in candle:
                    return False
                
                price_value = float(candle[field])
                
                # If value is a string reference to another indicator
                if isinstance(value, str) and value in indicators:
                    compare_value = indicators[value].iloc[index] if index < len(indicators[value]) else None
                    if compare_value is None or pd.isna(compare_value):
                        return False
                    return self._compare_values(price_value, operator, float(compare_value))
                else:
                    return self._compare_values(price_value, operator, value)
            
            elif cond_type == 'volume':
                volume_value = float(candle.get('volume', 0))
                return self._compare_values(volume_value, operator, value)
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}", exc_info=True)
            return False
    
    def _compare_values(self, left: float, operator: str, right: Any) -> bool:
        """Compare two values with an operator"""
        try:
            right_value = float(right) if not isinstance(right, str) else right
            
            if operator == '>':
                return left > right_value
            elif operator == '>=':
                return left >= right_value
            elif operator == '<':
                return left < right_value
            elif operator == '<=':
                return left <= right_value
            elif operator == '==':
                return abs(left - right_value) < 0.0001  # Float comparison
            elif operator == '!=':
                return abs(left - right_value) >= 0.0001
            else:
                return False
        except Exception as e:
            logger.error(f"Error comparing values: {e}", exc_info=True)
            return False

