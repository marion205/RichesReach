# core/fss_data_pipeline.py
"""
FSS Data Pipeline
Fetches price, volume, and fundamental data for FSS calculation.

Integrates with:
- Polygon.io: Historical price/volume data
- Alpaca: Real-time and historical market data
- Alpha Vantage: Fundamental data (EPS, revenue, etc.)
- FinnHub: Alternative fundamental data source
"""
import os
import logging
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FSSDataRequest:
    """Request for FSS data"""
    tickers: List[str]
    lookback_days: int = 252  # ~1 year of trading days
    include_fundamentals: bool = True


@dataclass
class FSSDataResult:
    """Result from FSS data pipeline"""
    prices: pd.DataFrame  # date x tickers (adjusted close)
    volumes: pd.DataFrame  # date x tickers
    spy: pd.Series  # SPY benchmark
    vix: Optional[pd.Series] = None  # VIX (optional)
    fundamentals_daily: Optional[Dict[str, pd.DataFrame]] = None
    data_quality: Dict[str, Any] = None


class FSSDataPipeline:
    """
    Data pipeline for FSS calculation.
    
    Fetches and formats market data from multiple providers.
    """
    
    def __init__(self):
        """Initialize data pipeline"""
        # API keys from environment (no hardcoded defaults for security)
        self.polygon_key = os.getenv("POLYGON_API_KEY")
        self.alpaca_key = os.getenv("ALPACA_API_KEY")
        self.alpaca_secret = os.getenv("ALPACA_SECRET_KEY")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY")
        
        # Base URLs
        self.polygon_base = "https://api.polygon.io"
        self.alpaca_base = "https://data.alpaca.markets/v2"
        self.alpha_vantage_base = "https://www.alphavantage.co/query"
        self.finnhub_base = "https://finnhub.io/api/v1"
        
        # Session for async requests
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_fss_data(
        self,
        request: FSSDataRequest
    ) -> FSSDataResult:
        """
        Fetch all data needed for FSS calculation.
        
        Args:
            request: FSSDataRequest with tickers and options
            
        Returns:
            FSSDataResult with prices, volumes, fundamentals, etc.
        """
        tickers = request.tickers
        lookback_days = request.lookback_days
        
        logger.info(f"Fetching FSS data for {len(tickers)} tickers ({lookback_days} days lookback)")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + 30)  # Extra buffer
        
        # Fetch data in parallel
        tasks = [
            self._fetch_prices_volumes(tickers, start_date, end_date),
            self._fetch_spy(start_date, end_date),
            self._fetch_vix(start_date, end_date),
        ]
        
        if request.include_fundamentals:
            tasks.append(self._fetch_fundamentals(tickers))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Unpack results
        prices_volumes = results[0] if not isinstance(results[0], Exception) else None
        spy = results[1] if not isinstance(results[1], Exception) else None
        vix = results[2] if not isinstance(results[2], Exception) else None
        fundamentals = results[3] if len(results) > 3 and not isinstance(results[3], Exception) else None
        
        # Handle errors
        if prices_volumes is None:
            raise ValueError("Failed to fetch price/volume data")
        
        prices, volumes = prices_volumes
        
        if spy is None:
            logger.warning("Failed to fetch SPY, using synthetic benchmark")
            spy = self._create_synthetic_spy(prices.index)
        
        # Data quality metrics
        data_quality = {
            "prices_coverage": self._calculate_coverage(prices),
            "volumes_coverage": self._calculate_coverage(volumes),
            "fundamentals_available": fundamentals is not None,
            "tickers_with_data": list(prices.columns),
            "missing_tickers": [t for t in tickers if t not in prices.columns]
        }
        
        return FSSDataResult(
            prices=prices,
            volumes=volumes,
            spy=spy,
            vix=vix,
            fundamentals_daily=fundamentals,
            data_quality=data_quality
        )
    
    async def _fetch_prices_volumes(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch historical prices and volumes.
        
        Tries Polygon first, then Alpaca, then yfinance fallback.
        """
        # Try Polygon first (best for historical data)
        try:
            prices, volumes = await self._fetch_polygon_aggregates(tickers, start_date, end_date)
            if prices is not None and not prices.empty:
                logger.info(f"Fetched {len(prices)} days of data from Polygon")
                return prices, volumes
        except Exception as e:
            logger.warning(f"Polygon fetch failed: {e}")
        
        # Try Alpaca
        try:
            prices, volumes = await self._fetch_alpaca_bars(tickers, start_date, end_date)
            if prices is not None and not prices.empty:
                logger.info(f"Fetched {len(prices)} days of data from Alpaca")
                return prices, volumes
        except Exception as e:
            logger.warning(f"Alpaca fetch failed: {e}")
        
        # Fallback to yfinance
        try:
            prices, volumes = await self._fetch_yfinance_data(tickers, start_date, end_date)
            if prices is not None and not prices.empty:
                logger.info(f"Fetched {len(prices)} days of data from yfinance")
                return prices, volumes
        except Exception as e:
            logger.warning(f"yfinance fetch failed: {e}")
        
        raise ValueError("Failed to fetch price/volume data from all sources")
    
    async def _fetch_polygon_aggregates(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Fetch aggregates from Polygon.io"""
        if not self.polygon_key:
            return None, None
        
        prices_dict = {}
        volumes_dict = {}
        
        for ticker in tickers:
            try:
                # Polygon aggregates endpoint
                url = f"{self.polygon_base}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
                params = {"apikey": self.polygon_key, "adjusted": "true"}
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        
                        if results:
                            dates = []
                            closes = []
                            vols = []
                            
                            for bar in results:
                                timestamp_ms = bar.get("t", 0)
                                date = datetime.fromtimestamp(timestamp_ms / 1000)
                                dates.append(date)
                                closes.append(bar.get("c", 0))  # Close (adjusted)
                                vols.append(bar.get("v", 0))  # Volume
                            
                            if dates:
                                prices_dict[ticker] = pd.Series(closes, index=dates)
                                volumes_dict[ticker] = pd.Series(vols, index=dates)
                        
                        # Rate limiting: Polygon free tier is 5 req/min
                        await asyncio.sleep(12)  # ~5 req/min
                    else:
                        logger.warning(f"Polygon API error for {ticker}: {response.status}")
            except Exception as e:
                logger.warning(f"Error fetching {ticker} from Polygon: {e}")
                continue
        
        if not prices_dict:
            return None, None
        
        # Convert to DataFrames
        prices = pd.DataFrame(prices_dict)
        volumes = pd.DataFrame(volumes_dict)
        
        # Align dates and forward-fill
        prices = prices.sort_index().fillna(method='ffill')
        volumes = volumes.sort_index().fillna(0)
        
        return prices, volumes
    
    async def _fetch_alpaca_bars(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Fetch bars from Alpaca"""
        if not self.alpaca_key or not self.alpaca_secret:
            return None, None
        
        prices_dict = {}
        volumes_dict = {}
        
        headers = {
            "APCA-API-KEY-ID": self.alpaca_key,
            "APCA-API-SECRET-KEY": self.alpaca_secret
        }
        
        for ticker in tickers:
            try:
                url = f"{self.alpaca_base}/stocks/{ticker}/bars"
                params = {
                    "start": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                    "end": end_date.strftime("%Y-%m-%dT23:59:59Z"),
                    "timeframe": "1Day",
                    "adjustment": "all"  # Adjusted for splits/dividends
                }
                
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        bars = data.get("bars", [])
                        
                        if bars:
                            dates = []
                            closes = []
                            vols = []
                            
                            for bar in bars:
                                date_str = bar.get("t", "")
                                if date_str:
                                    date = pd.to_datetime(date_str)
                                    dates.append(date)
                                    closes.append(float(bar.get("c", 0)))
                                    vols.append(int(bar.get("v", 0)))
                            
                            if dates:
                                prices_dict[ticker] = pd.Series(closes, index=dates)
                                volumes_dict[ticker] = pd.Series(vols, index=dates)
                    else:
                        logger.warning(f"Alpaca API error for {ticker}: {response.status}")
            except Exception as e:
                logger.warning(f"Error fetching {ticker} from Alpaca: {e}")
                continue
        
        if not prices_dict:
            return None, None
        
        prices = pd.DataFrame(prices_dict)
        volumes = pd.DataFrame(volumes_dict)
        
        prices = prices.sort_index().fillna(method='ffill')
        volumes = volumes.sort_index().fillna(0)
        
        return prices, volumes
    
    async def _fetch_yfinance_data(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Fetch data using yfinance (fallback)"""
        try:
            import yfinance as yf
        except ImportError:
            logger.warning("yfinance not available")
            return None, None
        
        try:
            # Download data
            data = yf.download(
                tickers,
                start=start_date,
                end=end_date,
                progress=False,
                group_by='ticker'
            )
            
            if data.empty:
                return None, None
            
            # Extract adjusted close and volume
            if len(tickers) == 1:
                prices = pd.DataFrame({tickers[0]: data["Adj Close"]})
                volumes = pd.DataFrame({tickers[0]: data["Volume"]})
            else:
                prices = data["Adj Close"]
                volumes = data["Volume"]
            
            prices = prices.sort_index().fillna(method='ffill')
            volumes = volumes.sort_index().fillna(0)
            
            return prices, volumes
        except Exception as e:
            logger.warning(f"yfinance fetch error: {e}")
            return None, None
    
    async def _fetch_spy(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.Series]:
        """Fetch SPY benchmark"""
        try:
            prices, _ = await self._fetch_polygon_aggregates(["SPY"], start_date, end_date)
            if prices is not None and "SPY" in prices.columns:
                return prices["SPY"]
        except Exception as e:
            logger.warning(f"Failed to fetch SPY: {e}")
        
        # Fallback to yfinance
        try:
            import yfinance as yf
            spy = yf.download("SPY", start=start_date, end=end_date, progress=False)
            if not spy.empty and "Adj Close" in spy.columns:
                return spy["Adj Close"]
        except Exception as e:
            logger.warning(f"yfinance SPY fetch failed: {e}")
        
        return None
    
    async def _fetch_vix(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.Series]:
        """Fetch VIX (optional, for regime detection)"""
        try:
            import yfinance as yf
            vix = yf.download("^VIX", start=start_date, end=end_date, progress=False)
            if not vix.empty and "Adj Close" in vix.columns:
                return vix["Adj Close"]
        except Exception as e:
            logger.warning(f"VIX fetch failed: {e}")
        
        return None
    
    async def _fetch_fundamentals(
        self,
        tickers: List[str]
    ) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Fetch fundamental data and convert to daily-aligned format.
        
        Returns dict with:
        - eps_accel: EPS acceleration
        - rev_yoy: Revenue YoY growth
        - gm_trend: Gross margin trend
        - balance_strength: Balance sheet strength
        """
        fundamentals = {}
        
        # Fetch from Alpha Vantage (income statement, balance sheet)
        for ticker in tickers:
            try:
                # Get income statement
                income_data = await self._fetch_alpha_vantage_income(ticker)
                balance_data = await self._fetch_alpha_vantage_balance(ticker)
                
                if income_data and balance_data:
                    # Calculate fundamental metrics
                    eps_accel = self._calculate_eps_acceleration(income_data)
                    rev_yoy = self._calculate_revenue_yoy(income_data)
                    gm_trend = self._calculate_gm_trend(income_data)
                    balance_strength = self._calculate_balance_strength(balance_data)
                    
                    # Convert to daily-aligned (forward-fill quarterly data)
                    # This is a simplification - in production, you'd align by report date
                    fundamentals[ticker] = {
                        "eps_accel": eps_accel,
                        "rev_yoy": rev_yoy,
                        "gm_trend": gm_trend,
                        "balance_strength": balance_strength
                    }
                
                # Rate limiting: Alpha Vantage free tier is 5 req/min
                await asyncio.sleep(12)
            except Exception as e:
                logger.warning(f"Error fetching fundamentals for {ticker}: {e}")
                continue
        
        if not fundamentals:
            return None
        
        # Convert to daily-aligned DataFrames
        # Create a date range for the lookback period
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.Timedelta(days=lookback_days)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Build daily-aligned DataFrames for each fundamental metric
        fundamentals_daily = {}
        
        for metric in ['eps_accel', 'rev_yoy', 'gm_trend', 'balance_strength']:
            metric_df = pd.DataFrame(index=date_range, columns=tickers)
            
            for ticker in tickers:
                if ticker in fundamentals and metric in fundamentals[ticker]:
                    # Forward-fill the quarterly value across all dates
                    # In production, this would align by actual report dates
                    value = fundamentals[ticker][metric]
                    metric_df[ticker] = value
            
            fundamentals_daily[metric] = metric_df.fillna(method='ffill').fillna(0)
        
        return fundamentals_daily
    
    async def _fetch_alpha_vantage_income(
        self,
        ticker: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch income statement from Alpha Vantage"""
        if not self.alpha_vantage_key:
            return None
        
        url = self.alpha_vantage_base
        params = {
            "function": "INCOME_STATEMENT",
            "symbol": ticker,
            "apikey": self.alpha_vantage_key
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("annualReports", [])
        except Exception as e:
            logger.warning(f"Alpha Vantage income fetch failed for {ticker}: {e}")
        
        return None
    
    async def _fetch_alpha_vantage_balance(
        self,
        ticker: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch balance sheet from Alpha Vantage"""
        if not self.alpha_vantage_key:
            return None
        
        url = self.alpha_vantage_base
        params = {
            "function": "BALANCE_SHEET",
            "symbol": ticker,
            "apikey": self.alpha_vantage_key
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("annualReports", [])
        except Exception as e:
            logger.warning(f"Alpha Vantage balance fetch failed for {ticker}: {e}")
        
        return None
    
    def _calculate_eps_acceleration(self, income_data: List[Dict]) -> float:
        """Calculate EPS acceleration (simplified)"""
        if len(income_data) < 2:
            return 0.0
        
        # Get EPS growth rates
        eps_growths = []
        for i in range(len(income_data) - 1):
            curr_eps = float(income_data[i].get("netIncome", 0))
            prev_eps = float(income_data[i + 1].get("netIncome", 0))
            if prev_eps > 0:
                growth = (curr_eps - prev_eps) / prev_eps
                eps_growths.append(growth)
        
        if len(eps_growths) < 2:
            return 0.0
        
        # Acceleration = current growth - previous growth
        return eps_growths[0] - eps_growths[1]
    
    def _calculate_revenue_yoy(self, income_data: List[Dict]) -> float:
        """Calculate revenue YoY growth"""
        if len(income_data) < 2:
            return 0.0
        
        curr_rev = float(income_data[0].get("totalRevenue", 0))
        prev_rev = float(income_data[1].get("totalRevenue", 0))
        
        if prev_rev > 0:
            return (curr_rev - prev_rev) / prev_rev
        
        return 0.0
    
    def _calculate_gm_trend(self, income_data: List[Dict]) -> float:
        """Calculate gross margin trend (slope of last 4 quarters)"""
        if len(income_data) < 2:
            return 0.0
        
        margins = []
        for report in income_data[:4]:  # Last 4 reports
            rev = float(report.get("totalRevenue", 0))
            cogs = float(report.get("costOfRevenue", 0))
            if rev > 0:
                margin = (rev - cogs) / rev
                margins.append(margin)
        
        if len(margins) < 2:
            return 0.0
        
        # Linear trend (slope)
        x = np.arange(len(margins))
        slope = np.polyfit(x, margins, 1)[0]
        return slope
    
    def _calculate_balance_strength(self, balance_data: List[Dict]) -> float:
        """Calculate balance sheet strength score"""
        if not balance_data:
            return 0.0
        
        latest = balance_data[0]
        total_assets = float(latest.get("totalAssets", 0))
        total_liabilities = float(latest.get("totalLiabilities", 0))
        total_equity = float(latest.get("totalShareholderEquity", 0))
        
        if total_assets == 0:
            return 0.0
        
        # Debt-to-equity ratio (lower is better)
        if total_equity > 0:
            debt_equity = total_liabilities / total_equity
        else:
            debt_equity = 999
        
        # Current ratio (higher is better)
        current_assets = float(latest.get("totalCurrentAssets", 0))
        current_liabilities = float(latest.get("totalCurrentLiabilities", 0))
        if current_liabilities > 0:
            current_ratio = current_assets / current_liabilities
        else:
            current_ratio = 999
        
        # Combined score (normalize to 0-100, higher is better)
        # Lower debt/equity and higher current ratio = better
        score = 100 - min(100, debt_equity * 10) + min(50, current_ratio * 10)
        return max(0, min(100, score))
    
    def _create_synthetic_spy(self, dates: pd.DatetimeIndex) -> pd.Series:
        """Create synthetic SPY if real data unavailable"""
        # Use average market return as proxy
        return pd.Series(
            np.random.normal(0.0003, 0.012, len(dates)).cumsum(),
            index=dates
        ) * 400 + 400  # Start around SPY level
    
    def _calculate_coverage(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate data coverage metrics"""
        if df.empty:
            return {"overall": 0.0}
        
        coverage = {}
        for col in df.columns:
            non_null = df[col].notna().sum()
            total = len(df)
            coverage[col] = non_null / total if total > 0 else 0.0
        
        coverage["overall"] = np.mean(list(coverage.values()))
        return coverage


# Singleton instance
_fss_data_pipeline = None


def get_fss_data_pipeline() -> FSSDataPipeline:
    """Get singleton FSS data pipeline instance"""
    global _fss_data_pipeline
    if _fss_data_pipeline is None:
        _fss_data_pipeline = FSSDataPipeline()
    return _fss_data_pipeline

