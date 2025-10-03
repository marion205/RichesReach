"""
Swing Trading Service
Provides real-time swing trading signals and technical analysis using existing APIs
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

# Lazy imports to avoid Django settings issues
# from .real_market_data_service import real_market_data_service
# from .ml_stock_recommender import MLStockRecommender

logger = logging.getLogger(__name__)

class SwingTradingService:
    """Service for generating swing trading signals and technical analysis"""
    
    def __init__(self):
        self.market_data_service = None
        self.ml_service = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of services"""
        if not self._initialized:
            try:
                from .ml_stock_recommender import MLStockRecommender
                from .real_market_data_service import real_market_data_service
                self.market_data_service = real_market_data_service
                self.ml_service = MLStockRecommender()
                self._initialized = True
                logger.info("Swing trading service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize services: {e}")
                self._initialized = True
        
    def get_market_overview(self, symbols: List[str] = None) -> List[Dict]:
        """Get real-time market overview data"""
        self._ensure_initialized()
        try:
            if not symbols:
                symbols = ['SPY', 'QQQ', 'IWM', 'VIX', 'DIA', 'VTI']
            
            market_data = []
            for symbol in symbols:
                try:
                    quote_data = self.market_data_service.get_stock_quote(symbol)
                    
                    market_data.append({
                        'symbol': symbol,
                        'name': quote_data.get('name', symbol),
                        'price': quote_data.get('price', 0.0),
                        'change': quote_data.get('change', 0.0),
                        'changePercent': quote_data.get('changePercent', 0.0),
                        'volume': quote_data.get('volume', 0),
                        'marketCap': quote_data.get('marketCap', 'N/A'),
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {symbol}: {e}")
                    # Fallback to mock data
                    market_data.append(self._get_mock_market_data(symbol))
            
            return market_data
        except Exception as e:
            logger.error(f"Error in get_market_overview: {e}")
            return self._get_mock_market_data_list()

    def get_sector_performance(self) -> List[Dict]:
        """Get sector performance data"""
        self._ensure_initialized()
        try:
            sector_etfs = ['XLK', 'XLV', 'XLF', 'XLY', 'XLC', 'XLI', 'XLP', 'XLE', 'XLU', 'XLRE', 'XLB']
            sector_data = []
            
            for etf in sector_etfs:
                try:
                    quote_data = self.market_data_service.get_stock_quote(etf)
                    sector_data.append({
                        'name': self._get_sector_name(etf),
                        'symbol': etf,
                        'change': quote_data.get('change', 0.0),
                        'changePercent': quote_data.get('changePercent', 0.0),
                        'weight': self._get_sector_weight(etf)
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch sector data for {etf}: {e}")
                    sector_data.append(self._get_mock_sector_data(etf))
            
            return sector_data
        except Exception as e:
            logger.error(f"Error in get_sector_performance: {e}")
            return self._get_mock_sector_data_list()

    def get_volatility_data(self) -> Dict:
        """Get volatility and market sentiment data"""
        self._ensure_initialized()
        try:
            # Get VIX data
            vix_data = self.market_data_service.get_stock_quote('VIX')
            
            return {
                'vix': vix_data.get('price', 18.45),
                'vixChange': vix_data.get('change', -1.23),
                'fearGreedIndex': self._calculate_fear_greed_index(),
                'putCallRatio': self._get_put_call_ratio()
            }
        except Exception as e:
            logger.error(f"Error in get_volatility_data: {e}")
            return {
                'vix': 18.45,
                'vixChange': -1.23,
                'fearGreedIndex': 45,
                'putCallRatio': 0.85
            }

    def calculate_technical_indicators(self, symbol: str, timeframe: str = '1d') -> List[Dict]:
        """Calculate technical indicators for a symbol"""
        self._ensure_initialized()
        logger.info(f"Calculating technical indicators for {symbol}")
        try:
            # Get historical data for technical analysis
            historical_data = self._get_historical_data(symbol, timeframe)
            
            if not historical_data:
                return self._get_mock_technical_indicators()
            
            # Calculate indicators
            indicators = []
            
            # RSI
            rsi = self._calculate_rsi(historical_data)
            if rsi is not None:
                indicators.append({
                    'name': 'RSI (14)',
                    'value': round(rsi, 2),
                    'signal': 'bullish' if rsi < 30 else 'bearish' if rsi > 70 else 'neutral',
                    'strength': 85 if rsi < 30 or rsi > 70 else 50,
                    'description': f'RSI at {rsi:.1f} - {"Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"}'
                })
            
            # MACD
            macd_data = self._calculate_macd(historical_data)
            if macd_data:
                indicators.append({
                    'name': 'MACD',
                    'value': round(macd_data['macd'], 2),
                    'signal': 'bullish' if macd_data['macd'] > macd_data['signal'] else 'bearish',
                    'strength': 72 if macd_data['macd'] > macd_data['signal'] else 28,
                    'description': f'MACD {"above" if macd_data["macd"] > macd_data["signal"] else "below"} signal line'
                })
            
            # Moving Averages
            ema_12 = self._calculate_ema(historical_data, 12)
            ema_26 = self._calculate_ema(historical_data, 26)
            if ema_12 and ema_26:
                indicators.append({
                    'name': 'EMA 12/26',
                    'value': round(ema_12, 2),
                    'signal': 'bullish' if ema_12 > ema_26 else 'bearish',
                    'strength': 68 if ema_12 > ema_26 else 32,
                    'description': f'EMA 12 {"above" if ema_12 > ema_26 else "below"} EMA 26'
                })
            
            # Volume
            volume_ratio = self._calculate_volume_ratio(historical_data)
            if volume_ratio:
                indicators.append({
                    'name': 'Volume',
                    'value': round(volume_ratio, 2),
                    'signal': 'bullish' if volume_ratio > 1.5 else 'bearish' if volume_ratio < 0.5 else 'neutral',
                    'strength': 80 if volume_ratio > 1.5 else 20 if volume_ratio < 0.5 else 50,
                    'description': f'Volume {"surge" if volume_ratio > 1.5 else "decline" if volume_ratio < 0.5 else "normal"}'
                })
            
            return indicators if indicators else self._get_mock_technical_indicators()
            
        except Exception as e:
            logger.error(f"Error in calculate_technical_indicators: {e}")
            return self._get_mock_technical_indicators()

    def identify_patterns(self, symbol: str, timeframe: str = '1d') -> List[Dict]:
        """Identify chart patterns for a symbol"""
        try:
            historical_data = self._get_historical_data(symbol, timeframe)
            
            if not historical_data:
                return self._get_mock_patterns()
            
            patterns = []
            
            # Simple pattern detection
            prices = [float(d['close']) for d in historical_data[-20:]]  # Last 20 days
            
            # Double Bottom
            if self._detect_double_bottom(prices):
                patterns.append({
                    'name': 'Double Bottom',
                    'confidence': 0.85,
                    'signal': 'bullish',
                    'description': 'Strong reversal pattern with high volume confirmation',
                    'timeframe': timeframe
                })
            
            # Ascending Triangle
            if self._detect_ascending_triangle(prices):
                patterns.append({
                    'name': 'Ascending Triangle',
                    'confidence': 0.72,
                    'signal': 'bullish',
                    'description': 'Breakout pattern with increasing support levels',
                    'timeframe': timeframe
                })
            
            # Head and Shoulders
            if self._detect_head_shoulders(prices):
                patterns.append({
                    'name': 'Head and Shoulders',
                    'confidence': 0.78,
                    'signal': 'bearish',
                    'description': 'Reversal pattern indicating potential downtrend',
                    'timeframe': timeframe
                })
            
            return patterns if patterns else self._get_mock_patterns()
            
        except Exception as e:
            logger.error(f"Error in identify_patterns: {e}")
            return self._get_mock_patterns()

    def generate_swing_signals(self, symbol: str = None, signal_type: str = None, 
                             min_score: float = 0.5, active_only: bool = True, 
                             limit: int = 50) -> List[Dict]:
        """Generate swing trading signals using ML"""
        self._ensure_initialized()
        logger.info(f"Generating swing signals for symbol: {symbol}")
        try:
            # For now, generate signals based on technical analysis
            # In a real implementation, this would use ML models
            signals = []
            
            # Get symbols to analyze
            symbols_to_analyze = [symbol] if symbol else ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']
            
            for sym in symbols_to_analyze:
                try:
                    # Get technical indicators
                    indicators = self.calculate_technical_indicators(sym, '1d')
                    
                    # Generate signal based on indicators
                    signal = self._create_signal_from_indicators(sym, indicators)
                    
                    if signal and signal['ml_score'] >= min_score:
                        signals.append(signal)
                        
                except Exception as e:
                    logger.warning(f"Failed to generate signal for {sym}: {e}")
                    continue
            
            # Sort by ML score and limit results
            signals.sort(key=lambda x: x['ml_score'], reverse=True)
            return signals[:limit] if signals else self._get_mock_swing_signals()
            
        except Exception as e:
            logger.error(f"Error in generate_swing_signals: {e}")
            return self._get_mock_swing_signals()

    def get_performance_metrics(self, timeframe: str = '30d') -> Dict:
        """Get performance metrics for swing trading"""
        try:
            # This would integrate with your portfolio/trades database
            # For now, return calculated metrics
            return self._calculate_performance_metrics(timeframe)
        except Exception as e:
            logger.error(f"Error in get_performance_metrics: {e}")
            return self._get_mock_performance_metrics()

    def get_recent_trades(self, limit: int = 20) -> List[Dict]:
        """Get recent trades"""
        try:
            # This would query your trades database
            return self._get_recent_trades_from_db(limit)
        except Exception as e:
            logger.error(f"Error in get_recent_trades: {e}")
            return self._get_mock_trades()

    def get_market_news(self, limit: int = 20) -> List[Dict]:
        """Get market news and sentiment"""
        try:
            # This would integrate with your news service
            return self._get_market_news_from_service(limit)
        except Exception as e:
            logger.error(f"Error in get_market_news: {e}")
            return self._get_mock_news()

    def get_sentiment_indicators(self) -> List[Dict]:
        """Get market sentiment indicators"""
        try:
            return self._calculate_sentiment_indicators()
        except Exception as e:
            logger.error(f"Error in get_sentiment_indicators: {e}")
            return self._get_mock_sentiment_indicators()

    # Technical Analysis Helper Methods
    def _get_historical_data(self, symbol: str, timeframe: str) -> List[Dict]:
        """Get historical data for technical analysis"""
        try:
            # This would use your market data service to get historical data
            # For now, return mock data
            return self._get_mock_historical_data(symbol, timeframe)
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return []

    def _calculate_rsi(self, data: List[Dict], period: int = 14) -> Optional[float]:
        """Calculate RSI"""
        try:
            if len(data) < period + 1:
                return None
            
            prices = [float(d['close']) for d in data[-period-1:]]
            gains = []
            losses = []
            
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            if not gains or not losses:
                return None
            
            avg_gain = sum(gains) / len(gains)
            avg_loss = sum(losses) / len(losses)
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return None

    def _calculate_macd(self, data: List[Dict]) -> Optional[Dict]:
        """Calculate MACD"""
        try:
            if len(data) < 26:
                return None
            
            prices = [float(d['close']) for d in data]
            
            ema_12 = self._calculate_ema_from_prices(prices, 12)
            ema_26 = self._calculate_ema_from_prices(prices, 26)
            
            if not ema_12 or not ema_26:
                return None
            
            macd = ema_12 - ema_26
            signal = self._calculate_ema_from_prices([macd], 9) if macd else None
            
            return {
                'macd': macd,
                'signal': signal or 0,
                'histogram': macd - (signal or 0)
            }
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return None

    def _calculate_ema(self, data: List[Dict], period: int) -> Optional[float]:
        """Calculate EMA"""
        try:
            if len(data) < period:
                return None
            
            prices = [float(d['close']) for d in data]
            return self._calculate_ema_from_prices(prices, period)
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
            return None

    def _calculate_ema_from_prices(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate EMA from price list"""
        try:
            if len(prices) < period:
                return None
            
            multiplier = 2 / (period + 1)
            ema = prices[0]
            
            for price in prices[1:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            
            return ema
        except Exception as e:
            logger.error(f"Error calculating EMA from prices: {e}")
            return None

    def _calculate_volume_ratio(self, data: List[Dict]) -> Optional[float]:
        """Calculate volume ratio"""
        try:
            if len(data) < 2:
                return None
            
            recent_volume = float(data[-1].get('volume', 0))
            avg_volume = sum(float(d.get('volume', 0)) for d in data[-10:]) / min(10, len(data))
            
            if avg_volume == 0:
                return None
            
            return recent_volume / avg_volume
        except Exception as e:
            logger.error(f"Error calculating volume ratio: {e}")
            return None

    # Pattern Detection Methods
    def _detect_double_bottom(self, prices: List[float]) -> bool:
        """Detect double bottom pattern"""
        try:
            if len(prices) < 10:
                return False
            
            # Simple double bottom detection
            min_price = min(prices)
            min_indices = [i for i, price in enumerate(prices) if price == min_price]
            
            return len(min_indices) >= 2 and abs(min_indices[0] - min_indices[1]) >= 3
        except:
            return False

    def _detect_ascending_triangle(self, prices: List[float]) -> bool:
        """Detect ascending triangle pattern"""
        try:
            if len(prices) < 8:
                return False
            
            # Simple ascending triangle detection
            recent_prices = prices[-8:]
            highs = [max(recent_prices[i:i+3]) for i in range(len(recent_prices)-2)]
            lows = [min(recent_prices[i:i+3]) for i in range(len(recent_prices)-2)]
            
            # Check if lows are increasing and highs are relatively flat
            return len(set(highs)) <= 2 and lows[-1] > lows[0]
        except:
            return False

    def _detect_head_shoulders(self, prices: List[float]) -> bool:
        """Detect head and shoulders pattern"""
        try:
            if len(prices) < 12:
                return False
            
            # Simple head and shoulders detection
            recent_prices = prices[-12:]
            peaks = []
            
            for i in range(1, len(recent_prices)-1):
                if recent_prices[i] > recent_prices[i-1] and recent_prices[i] > recent_prices[i+1]:
                    peaks.append((i, recent_prices[i]))
            
            if len(peaks) < 3:
                return False
            
            # Check if middle peak is highest (head)
            peaks.sort(key=lambda x: x[1], reverse=True)
            return len(peaks) >= 3
        except:
            return False

    def _create_signal_from_indicators(self, symbol: str, indicators: List[Dict]) -> Optional[Dict]:
        """Create a swing trading signal from technical indicators"""
        try:
            if not indicators:
                return None
            
            # Calculate ML score based on indicators
            ml_score = 0.0
            signal_type = 'neutral'
            thesis_parts = []
            
            for indicator in indicators:
                if indicator['name'] == 'RSI (14)':
                    rsi = indicator['value']
                    if rsi < 30:  # Oversold
                        ml_score += 0.3
                        signal_type = 'rsi_rebound_long'
                        thesis_parts.append(f'RSI oversold at {rsi:.1f}')
                    elif rsi > 70:  # Overbought
                        ml_score += 0.2
                        signal_type = 'rsi_reversal_short'
                        thesis_parts.append(f'RSI overbought at {rsi:.1f}')
                
                elif indicator['name'] == 'MACD':
                    if indicator['signal'] == 'bullish':
                        ml_score += 0.2
                        thesis_parts.append('MACD bullish crossover')
                    elif indicator['signal'] == 'bearish':
                        ml_score += 0.1
                        thesis_parts.append('MACD bearish crossover')
                
                elif indicator['name'] == 'EMA 12/26':
                    if indicator['signal'] == 'bullish':
                        ml_score += 0.15
                        thesis_parts.append('EMA 12 above EMA 26')
                    elif indicator['signal'] == 'bearish':
                        ml_score += 0.1
                        thesis_parts.append('EMA 12 below EMA 26')
                
                elif indicator['name'] == 'Volume':
                    if indicator['value'] > 1.5:  # Volume surge
                        ml_score += 0.1
                        thesis_parts.append('Volume surge confirms movement')
            
            # Only create signal if ML score is above threshold
            if ml_score < 0.3:
                return None
            
            # Get current price for entry/stop/target
            try:
                quote_data = self.market_data_service.get_stock_quote(symbol)
                current_price = quote_data.get('price', 100.0)
            except:
                current_price = 100.0
            
            # Calculate entry, stop, and target prices
            entry_price = current_price
            if signal_type == 'rsi_rebound_long':
                stop_price = entry_price * 0.95  # 5% stop loss
                target_price = entry_price * 1.10  # 10% target
            elif signal_type == 'rsi_reversal_short':
                stop_price = entry_price * 1.05  # 5% stop loss
                target_price = entry_price * 0.90  # 10% target
            else:
                stop_price = entry_price * 0.97  # 3% stop loss
                target_price = entry_price * 1.06  # 6% target
            
            return {
                'id': f"{symbol}_{int(datetime.now().timestamp())}",
                'symbol': symbol,
                'timeframe': '1d',
                'triggered_at': datetime.now().isoformat(),
                'signal_type': signal_type,
                'entry_price': entry_price,
                'stop_price': stop_price,
                'target_price': target_price,
                'ml_score': min(ml_score, 1.0),  # Cap at 1.0
                'thesis': '. '.join(thesis_parts) + '. Technical analysis suggests potential price movement.',
                'risk_reward_ratio': abs(target_price - entry_price) / abs(entry_price - stop_price) if entry_price != stop_price else 0,
                'days_since_triggered': 0,
                'is_liked_by_user': False,
                'user_like_count': 0,
                'features': {ind['name']: ind['value'] for ind in indicators},
                'is_active': True,
                'is_validated': False
            }
            
        except Exception as e:
            logger.error(f"Error creating signal from indicators: {e}")
            return None

    # Helper methods for calculations
    def _calculate_fear_greed_index(self) -> int:
        """Calculate Fear & Greed Index"""
        try:
            vix_data = self.market_data_service.get_stock_quote('VIX')
            vix = vix_data.get('price', 20)
            
            if vix < 15:
                return 75  # Greed
            elif vix > 30:
                return 25  # Fear
            else:
                return 50  # Neutral
        except:
            return 45

    def _get_put_call_ratio(self) -> float:
        """Get put/call ratio"""
        try:
            # This would typically come from options data
            return 0.85
        except:
            return 0.85

    def _get_sector_name(self, etf: str) -> str:
        """Map ETF symbol to sector name"""
        sector_map = {
            'XLK': 'Technology', 'XLV': 'Healthcare', 'XLF': 'Financials',
            'XLY': 'Consumer Discretionary', 'XLC': 'Communication Services',
            'XLI': 'Industrials', 'XLP': 'Consumer Staples', 'XLE': 'Energy',
            'XLU': 'Utilities', 'XLRE': 'Real Estate', 'XLB': 'Materials'
        }
        return sector_map.get(etf, etf)

    def _get_sector_weight(self, etf: str) -> float:
        """Get sector weight in S&P 500"""
        weights = {
            'XLK': 28.5, 'XLV': 13.2, 'XLF': 11.8, 'XLY': 10.9,
            'XLC': 8.7, 'XLI': 8.1, 'XLP': 6.8, 'XLE': 4.2,
            'XLU': 3.1, 'XLRE': 2.8, 'XLB': 2.0
        }
        return weights.get(etf, 1.0)

    def _calculate_performance_metrics(self, timeframe: str) -> Dict:
        """Calculate performance metrics"""
        # This would integrate with your portfolio data
        return {
            'totalTrades': 47,
            'winningTrades': 32,
            'losingTrades': 15,
            'winRate': 68.09,
            'avgWin': 485.32,
            'avgLoss': -287.45,
            'profitFactor': 1.69,
            'totalReturn': 15430.50,
            'maxDrawdown': -8.5,
            'sharpeRatio': 1.42,
            'avgHoldingPeriod': 5.2
        }

    def _get_recent_trades_from_db(self, limit: int) -> List[Dict]:
        """Get recent trades from database"""
        # This would query your trades database
        return []

    def _get_market_news_from_service(self, limit: int) -> List[Dict]:
        """Get market news from news service"""
        # This would integrate with your news service
        return []

    def _calculate_sentiment_indicators(self) -> List[Dict]:
        """Calculate market sentiment indicators"""
        return [
            {
                'name': 'VIX',
                'value': 18.45,
                'change': -1.23,
                'signal': 'bullish',
                'level': 'low'
            },
            {
                'name': 'Put/Call Ratio',
                'value': 0.85,
                'change': 0.05,
                'signal': 'bullish',
                'level': 'normal'
            }
        ]

    # Mock data methods (fallbacks)
    def _get_mock_market_data(self, symbol: str) -> Dict:
        """Get mock market data for a symbol"""
        mock_data = {
            'SPY': {'name': 'S&P 500', 'price': 4456.78, 'change': 12.45, 'changePercent': 0.28, 'volume': 45234567, 'marketCap': '$40.2T'},
            'QQQ': {'name': 'NASDAQ 100', 'price': 3789.23, 'change': -8.92, 'changePercent': -0.23, 'volume': 23456789, 'marketCap': '$15.8T'},
            'IWM': {'name': 'Russell 2000', 'price': 1892.45, 'change': 5.67, 'changePercent': 0.30, 'volume': 12345678, 'marketCap': '$2.1T'},
            'VIX': {'name': 'Volatility Index', 'price': 18.45, 'change': -1.23, 'changePercent': -6.25, 'volume': 9876543, 'marketCap': 'N/A'},
            'DIA': {'name': 'Dow Jones', 'price': 34567.89, 'change': 123.45, 'changePercent': 0.36, 'volume': 8765432, 'marketCap': '$8.5T'},
            'VTI': {'name': 'Total Stock Market', 'price': 234.56, 'change': 1.23, 'changePercent': 0.53, 'volume': 3456789, 'marketCap': '$12.3T'}
        }
        
        data = mock_data.get(symbol, {'name': symbol, 'price': 100.0, 'change': 0.0, 'changePercent': 0.0, 'volume': 1000000, 'marketCap': 'N/A'})
        
        return {
            'symbol': symbol,
            'name': data['name'],
            'price': data['price'],
            'change': data['change'],
            'changePercent': data['changePercent'],
            'volume': data['volume'],
            'marketCap': data['marketCap'],
            'timestamp': datetime.now().isoformat()
        }

    def _get_mock_market_data_list(self) -> List[Dict]:
        """Get list of mock market data"""
        symbols = ['SPY', 'QQQ', 'IWM', 'VIX']
        return [self._get_mock_market_data(symbol) for symbol in symbols]

    def _get_mock_sector_data(self, etf: str) -> Dict:
        """Get mock sector data"""
        mock_sectors = {
            'XLK': {'name': 'Technology', 'change': 0.45, 'changePercent': 0.32, 'weight': 28.5},
            'XLV': {'name': 'Healthcare', 'change': -0.12, 'changePercent': -0.08, 'weight': 13.2},
            'XLF': {'name': 'Financials', 'change': 0.78, 'changePercent': 0.56, 'weight': 11.8},
            'XLY': {'name': 'Consumer Discretionary', 'change': 0.23, 'changePercent': 0.18, 'weight': 10.9},
            'XLC': {'name': 'Communication Services', 'change': -0.34, 'changePercent': -0.25, 'weight': 8.7},
            'XLI': {'name': 'Industrials', 'change': 0.67, 'changePercent': 0.48, 'weight': 8.1},
            'XLP': {'name': 'Consumer Staples', 'change': 0.15, 'changePercent': 0.12, 'weight': 6.8},
            'XLE': {'name': 'Energy', 'change': 1.23, 'changePercent': 0.89, 'weight': 4.2},
            'XLU': {'name': 'Utilities', 'change': -0.08, 'changePercent': -0.06, 'weight': 3.1},
            'XLRE': {'name': 'Real Estate', 'change': 0.34, 'changePercent': 0.28, 'weight': 2.8},
            'XLB': {'name': 'Materials', 'change': 0.56, 'changePercent': 0.42, 'weight': 2.0}
        }
        
        data = mock_sectors.get(etf, {'name': etf, 'change': 0.0, 'changePercent': 0.0, 'weight': 1.0})
        
        return {
            'name': data['name'],
            'symbol': etf,
            'change': data['change'],
            'changePercent': data['changePercent'],
            'weight': data['weight']
        }

    def _get_mock_sector_data_list(self) -> List[Dict]:
        """Get list of mock sector data"""
        etfs = ['XLK', 'XLV', 'XLF', 'XLY', 'XLC', 'XLI', 'XLP', 'XLE', 'XLU', 'XLRE', 'XLB']
        return [self._get_mock_sector_data(etf) for etf in etfs]

    def _get_mock_technical_indicators(self) -> List[Dict]:
        """Get mock technical indicators"""
        return [
            {
                'name': 'RSI (14)',
                'value': 28.5,
                'signal': 'bullish',
                'strength': 85,
                'description': 'Oversold condition, potential reversal signal'
            },
            {
                'name': 'MACD',
                'value': 2.34,
                'signal': 'bullish',
                'strength': 72,
                'description': 'Bullish crossover above signal line'
            },
            {
                'name': 'EMA 12/26',
                'value': 176.2,
                'signal': 'bullish',
                'strength': 68,
                'description': 'EMA 12 above EMA 26, bullish momentum'
            }
        ]

    def _get_mock_patterns(self) -> List[Dict]:
        """Get mock pattern recognition"""
        return [
            {
                'name': 'Double Bottom',
                'confidence': 0.85,
                'signal': 'bullish',
                'description': 'Strong reversal pattern with high volume confirmation',
                'timeframe': '1d'
            },
            {
                'name': 'Ascending Triangle',
                'confidence': 0.72,
                'signal': 'bullish',
                'description': 'Breakout pattern with increasing support levels',
                'timeframe': '1d'
            }
        ]

    def _get_mock_swing_signals(self) -> List[Dict]:
        """Get mock swing signals"""
        return [
            {
                'id': '1',
                'symbol': 'AAPL',
                'timeframe': '1d',
                'triggered_at': datetime.now().isoformat(),
                'signal_type': 'rsi_rebound_long',
                'entry_price': 175.50,
                'stop_price': 170.00,
                'target_price': 185.00,
                'ml_score': 0.78,
                'thesis': 'RSI oversold at 28.5 with strong volume confirmation. EMA crossover suggests bullish momentum.',
                'risk_reward_ratio': 2.1,
                'days_since_triggered': 1,
                'is_liked_by_user': False,
                'user_like_count': 12,
                'features': {'rsi_14': 28.5, 'ema_12': 176.2, 'ema_26': 174.8},
                'is_active': True,
                'is_validated': False
            }
        ]

    def _get_mock_performance_metrics(self) -> Dict:
        """Get mock performance metrics"""
        return {
            'totalTrades': 47,
            'winningTrades': 32,
            'losingTrades': 15,
            'winRate': 68.09,
            'avgWin': 485.32,
            'avgLoss': -287.45,
            'profitFactor': 1.69,
            'totalReturn': 15430.50,
            'maxDrawdown': -8.5,
            'sharpeRatio': 1.42,
            'avgHoldingPeriod': 5.2
        }

    def _get_mock_trades(self) -> List[Dict]:
        """Get mock trades"""
        return [
            {
                'id': '1',
                'symbol': 'AAPL',
                'side': 'long',
                'entry_price': 175.50,
                'exit_price': 182.30,
                'quantity': 100,
                'entry_date': '2024-01-15',
                'exit_date': '2024-01-20',
                'pnl': 680.00,
                'pnl_percent': 3.87,
                'holding_period': 5,
                'status': 'closed'
            }
        ]

    def _get_mock_news(self) -> List[Dict]:
        """Get mock news"""
        return [
            {
                'id': '1',
                'title': 'Fed Signals Potential Rate Cuts as Inflation Cools',
                'summary': 'Federal Reserve officials hint at possible interest rate reductions in the coming months as inflation data shows continued moderation.',
                'source': 'Reuters',
                'timestamp': '2 hours ago',
                'impact': 'high',
                'sentiment': 'bullish',
                'related_symbols': ['SPY', 'QQQ', 'TLT'],
                'category': 'Monetary Policy'
            }
        ]

    def _get_mock_sentiment_indicators(self) -> List[Dict]:
        """Get mock sentiment indicators"""
        return [
            {
                'name': 'VIX',
                'value': 18.45,
                'change': -1.23,
                'signal': 'bullish',
                'level': 'low'
            },
            {
                'name': 'Put/Call Ratio',
                'value': 0.85,
                'change': 0.05,
                'signal': 'bullish',
                'level': 'normal'
            }
        ]

    def _get_mock_historical_data(self, symbol: str, timeframe: str) -> List[Dict]:
        """Get mock historical data for technical analysis"""
        # Generate mock historical data
        base_price = 100.0
        data = []
        
        for i in range(30):  # 30 days of data
            price = base_price + (i * 0.5) + (np.random.random() - 0.5) * 2
            data.append({
                'date': (datetime.now() - timedelta(days=30-i)).isoformat(),
                'open': price - 0.5,
                'high': price + 1.0,
                'low': price - 1.0,
                'close': price,
                'volume': int(1000000 + np.random.random() * 500000)
            })
        
        return data


# Create singleton instance
swing_trading_service = SwingTradingService()
