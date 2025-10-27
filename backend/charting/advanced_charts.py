"""
Advanced Charting and Visualization System for RichesReach
Provides comprehensive charting capabilities with technical indicators,
real-time data, and multiple chart types.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import random
import math

class TechnicalIndicators:
    """Technical analysis indicators for charting"""
    
    @staticmethod
    def sma(data: List[float], period: int) -> List[float]:
        """Simple Moving Average"""
        if len(data) < period:
            return [0.0] * len(data)
        
        result = []
        for i in range(len(data)):
            if i < period - 1:
                result.append(0.0)
            else:
                avg = sum(data[i-period+1:i+1]) / period
                result.append(avg)
        return result
    
    @staticmethod
    def ema(data: List[float], period: int) -> List[float]:
        """Exponential Moving Average"""
        if len(data) < period:
            return [0.0] * len(data)
        
        multiplier = 2 / (period + 1)
        result = [0.0] * len(data)
        result[period-1] = sum(data[:period]) / period
        
        for i in range(period, len(data)):
            result[i] = (data[i] * multiplier) + (result[i-1] * (1 - multiplier))
        
        return result
    
    @staticmethod
    def rsi(data: List[float], period: int = 14) -> List[float]:
        """Relative Strength Index"""
        if len(data) < period + 1:
            return [50.0] * len(data)
        
        deltas = [data[i] - data[i-1] for i in range(1, len(data))]
        gains = [max(0, delta) for delta in deltas]
        losses = [max(0, -delta) for delta in deltas]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        result = [50.0] * period
        
        for i in range(period, len(data)):
            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                result.append(rsi)
            
            # Update averages
            avg_gain = (avg_gain * (period - 1) + gains[i-1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i-1]) / period
        
        return result
    
    @staticmethod
    def macd(data: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        
        macd_line = [fast_val - slow_val for fast_val, slow_val in zip(ema_fast, ema_slow)]
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = [macd_val - sig_val for macd_val, sig_val in zip(macd_line, signal_line)]
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    @staticmethod
    def bollinger_bands(data: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, List[float]]:
        """Bollinger Bands"""
        sma = TechnicalIndicators.sma(data, period)
        
        upper_band = []
        lower_band = []
        
        for i in range(len(data)):
            if i < period - 1:
                upper_band.append(0.0)
                lower_band.append(0.0)
            else:
                # Calculate standard deviation
                period_data = data[i-period+1:i+1]
                mean = sma[i]
                variance = sum((x - mean) ** 2 for x in period_data) / period
                std = math.sqrt(variance)
                
                upper_band.append(mean + (std_dev * std))
                lower_band.append(mean - (std_dev * std))
        
        return {
            "upper": upper_band,
            "middle": sma,
            "lower": lower_band
        }
    
    @staticmethod
    def atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
        """Average True Range"""
        if len(high) < 2:
            return [0.0] * len(high)
        
        true_ranges = []
        for i in range(1, len(high)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        if len(true_ranges) < period:
            return [0.0] * len(high)
        
        result = [0.0] * (len(high) - len(true_ranges))
        result.append(sum(true_ranges[:period]) / period)
        
        for i in range(period, len(true_ranges)):
            atr_val = (result[-1] * (period - 1) + true_ranges[i]) / period
            result.append(atr_val)
        
        return result

class ChartDataGenerator:
    """Generates mock chart data for testing and development"""
    
    @staticmethod
    def generate_ohlcv_data(symbol: str, timeframe: str, periods: int = 100) -> List[Dict[str, Any]]:
        """Generate mock OHLCV data"""
        base_price = random.uniform(100, 500)
        data = []
        
        for i in range(periods):
            # Generate realistic price movement
            volatility = random.uniform(0.01, 0.05)
            change = random.uniform(-volatility, volatility)
            price = base_price * (1 + change)
            
            # Generate OHLC
            open_price = base_price
            high_price = max(open_price, price) * random.uniform(1.0, 1.02)
            low_price = min(open_price, price) * random.uniform(0.98, 1.0)
            close_price = price
            
            # Generate volume
            volume = random.randint(1000000, 10000000)
            
            # Generate timestamp
            timestamp = datetime.now() - timedelta(minutes=periods-i)
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume
            })
            
            base_price = close_price
        
        return data
    
    @staticmethod
    def generate_volume_profile(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate volume profile data"""
        prices = []
        volumes = []
        
        for candle in data:
            # Distribute volume across price range
            price_range = candle["high"] - candle["low"]
            if price_range > 0:
                steps = max(1, int(price_range * 10))  # 10 price levels per dollar
                step_size = price_range / steps
                
                for i in range(steps):
                    price = candle["low"] + (i * step_size)
                    volume_portion = candle["volume"] / steps
                    prices.append(price)
                    volumes.append(volume_portion)
        
        # Group by price levels
        price_levels = {}
        for price, volume in zip(prices, volumes):
            rounded_price = round(price, 2)
            if rounded_price not in price_levels:
                price_levels[rounded_price] = 0
            price_levels[rounded_price] += volume
        
        # Convert to sorted lists
        sorted_prices = sorted(price_levels.keys())
        sorted_volumes = [price_levels[price] for price in sorted_prices]
        
        return {
            "prices": sorted_prices,
            "volumes": sorted_volumes,
            "max_volume": max(sorted_volumes) if sorted_volumes else 0,
            "poc": sorted_prices[sorted_volumes.index(max(sorted_volumes))] if sorted_volumes else 0
        }

class AdvancedChartEngine:
    """Main charting engine with multiple chart types and indicators"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.data_generator = ChartDataGenerator()
    
    def get_candlestick_chart(self, symbol: str, timeframe: str, periods: int = 100) -> Dict[str, Any]:
        """Generate candlestick chart with technical indicators"""
        ohlcv_data = self.data_generator.generate_ohlcv_data(symbol, timeframe, periods)
        
        # Extract price data for indicators
        closes = [candle["close"] for candle in ohlcv_data]
        highs = [candle["high"] for candle in ohlcv_data]
        lows = [candle["low"] for candle in ohlcv_data]
        
        # Calculate technical indicators
        sma_20 = self.indicators.sma(closes, 20)
        sma_50 = self.indicators.sma(closes, 50)
        ema_12 = self.indicators.ema(closes, 12)
        rsi = self.indicators.rsi(closes, 14)
        macd = self.indicators.macd(closes)
        bollinger = self.indicators.bollinger_bands(closes, 20, 2.0)
        atr = self.indicators.atr(highs, lows, closes, 14)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": ohlcv_data,
            "indicators": {
                "sma_20": sma_20,
                "sma_50": sma_50,
                "ema_12": ema_12,
                "rsi": rsi,
                "macd": macd,
                "bollinger_bands": bollinger,
                "atr": atr
            },
            "metadata": {
                "total_periods": len(ohlcv_data),
                "price_range": {
                    "min": min(closes),
                    "max": max(closes)
                },
                "volume_range": {
                    "min": min(candle["volume"] for candle in ohlcv_data),
                    "max": max(candle["volume"] for candle in ohlcv_data)
                },
                "generated_at": datetime.now().isoformat()
            }
        }
    
    def get_volume_chart(self, symbol: str, timeframe: str, periods: int = 100) -> Dict[str, Any]:
        """Generate volume chart with volume profile"""
        ohlcv_data = self.data_generator.generate_ohlcv_data(symbol, timeframe, periods)
        volume_profile = self.data_generator.generate_volume_profile(ohlcv_data)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "volume_data": [
                {
                    "timestamp": candle["timestamp"],
                    "volume": candle["volume"],
                    "price": candle["close"]
                }
                for candle in ohlcv_data
            ],
            "volume_profile": volume_profile,
            "metadata": {
                "total_volume": sum(candle["volume"] for candle in ohlcv_data),
                "average_volume": sum(candle["volume"] for candle in ohlcv_data) / len(ohlcv_data),
                "generated_at": datetime.now().isoformat()
            }
        }
    
    def get_line_chart(self, symbol: str, timeframe: str, periods: int = 100) -> Dict[str, Any]:
        """Generate simple line chart"""
        ohlcv_data = self.data_generator.generate_ohlcv_data(symbol, timeframe, periods)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "line_data": [
                {
                    "timestamp": candle["timestamp"],
                    "price": candle["close"]
                }
                for candle in ohlcv_data
            ],
            "metadata": {
                "price_range": {
                    "min": min(candle["close"] for candle in ohlcv_data),
                    "max": max(candle["close"] for candle in ohlcv_data)
                },
                "generated_at": datetime.now().isoformat()
            }
        }
    
    def get_heatmap_chart(self, symbols: List[str], timeframe: str = "1D") -> Dict[str, Any]:
        """Generate sector/stock heatmap"""
        heatmap_data = []
        
        for symbol in symbols:
            ohlcv_data = self.data_generator.generate_ohlcv_data(symbol, timeframe, 1)
            if ohlcv_data:
                candle = ohlcv_data[0]
                change_percent = random.uniform(-5, 5)  # Mock change percentage
                
                heatmap_data.append({
                    "symbol": symbol,
                    "price": candle["close"],
                    "change_percent": round(change_percent, 2),
                    "volume": candle["volume"],
                    "sector": random.choice(["Technology", "Healthcare", "Finance", "Energy", "Consumer"]),
                    "market_cap": random.randint(1000000000, 1000000000000)
                })
        
        return {
            "timeframe": timeframe,
            "heatmap_data": heatmap_data,
            "metadata": {
                "total_symbols": len(symbols),
                "sectors": list(set(item["sector"] for item in heatmap_data)),
                "generated_at": datetime.now().isoformat()
            }
        }
    
    def get_correlation_matrix(self, symbols: List[str], timeframe: str = "1D", periods: int = 30) -> Dict[str, Any]:
        """Generate correlation matrix for multiple symbols"""
        price_data = {}
        
        # Generate price data for each symbol
        for symbol in symbols:
            ohlcv_data = self.data_generator.generate_ohlcv_data(symbol, timeframe, periods)
            price_data[symbol] = [candle["close"] for candle in ohlcv_data]
        
        # Calculate correlations
        correlations = {}
        for symbol1 in symbols:
            correlations[symbol1] = {}
            for symbol2 in symbols:
                if symbol1 == symbol2:
                    correlations[symbol1][symbol2] = 1.0
                else:
                    # Calculate correlation coefficient
                    corr = random.uniform(-0.8, 0.8)  # Mock correlation
                    correlations[symbol1][symbol2] = round(corr, 3)
        
        return {
            "symbols": symbols,
            "timeframe": timeframe,
            "correlations": correlations,
            "metadata": {
                "periods": periods,
                "generated_at": datetime.now().isoformat()
            }
        }
    
    def get_market_depth_chart(self, symbol: str) -> Dict[str, Any]:
        """Generate market depth (order book) chart"""
        base_price = random.uniform(100, 500)
        
        # Generate bid orders
        bids = []
        for i in range(20):
            price = base_price - (i * random.uniform(0.01, 0.05))
            size = random.randint(100, 10000)
            bids.append({
                "price": round(price, 2),
                "size": size,
                "orders": random.randint(1, 50)
            })
        
        # Generate ask orders
        asks = []
        for i in range(20):
            price = base_price + (i * random.uniform(0.01, 0.05))
            size = random.randint(100, 10000)
            asks.append({
                "price": round(price, 2),
                "size": size,
                "orders": random.randint(1, 50)
            })
        
        return {
            "symbol": symbol,
            "bids": sorted(bids, key=lambda x: x["price"], reverse=True),
            "asks": sorted(asks, key=lambda x: x["price"]),
            "metadata": {
                "spread": round(asks[0]["price"] - bids[0]["price"], 2),
                "mid_price": round((bids[0]["price"] + asks[0]["price"]) / 2, 2),
                "total_bid_size": sum(bid["size"] for bid in bids),
                "total_ask_size": sum(ask["size"] for ask in asks),
                "generated_at": datetime.now().isoformat()
            }
        }
