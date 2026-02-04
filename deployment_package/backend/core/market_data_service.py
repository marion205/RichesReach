"""
Market Data Service for ML Models
Fetches real-time and historical market data for enhanced AI recommendations
"""
import asyncio

import logging

import random

from datetime import datetime

from typing import Dict, Any, Optional



from .market_data_manager import get_market_data_service

from .enhanced_api_service import enhanced_api_service  # kept for future use



logger = logging.getLogger(__name__)





class MarketDataService:

    """

    Service for fetching market data from various sources

    (real when possible, synthetic fallback otherwise).

    """



    def __init__(self):

        # API keys (in production, use environment variables / settings)

        self.alpha_vantage_key: Optional[str] = None

        self.finnhub_key: Optional[str] = None

        self.yahoo_finance_base = "https://query1.finance.yahoo.com"



        # Simple in-memory cache (not heavily used yet)

        self.cache: Dict[str, Any] = {}

        self.cache_expiry: Dict[str, float] = {}

        self.cache_duration: int = 300  # 5 minutes



        # Fallback data when APIs are not available

        self.fallback_data = self._initialize_fallback_data()



    # ------------------------------------------------------------------

    # Public API

    # ------------------------------------------------------------------

    def get_market_overview(self) -> Dict[str, Any]:

        """

        Get comprehensive market overview for ML models.



        Returns:

            dict with fields like:

            - sp500_return (decimal)

            - volatility

            - current_price

            - change

            - change_percent

            - last_updated

        """

        try:

            market_data = self._fetch_real_market_data()

            if market_data:

                return market_data

            return self._generate_synthetic_market_data()

        except Exception as e:

            logger.error(f"Error getting market overview: {e}", exc_info=True)

            return self._generate_synthetic_market_data()



    def get_sector_performance(self) -> Dict[str, str]:

        """

        Get current sector performance.



        Returns:

            dict mapping sector -> performance flag

            e.g. {"technology": "outperforming", ...}

        """

        try:

            sector_data = self._fetch_sector_data()

            if sector_data:

                return sector_data

            return self._generate_synthetic_sector_data()

        except Exception as e:

            logger.error(f"Error getting sector performance: {e}", exc_info=True)

            return self._generate_synthetic_sector_data()



    def get_economic_indicators(self) -> Dict[str, float]:

        """

        Get key economic indicators.



        Returns:

            dict with fields like:

            - interest_rate

            - gdp_growth

            - unemployment_rate

            - inflation_rate

        """

        try:

            economic_data = self._fetch_economic_data()

            if economic_data:

                return economic_data

            return self._generate_synthetic_economic_data()

        except Exception as e:

            logger.error(f"Error getting economic indicators: {e}", exc_info=True)

            return self._generate_synthetic_economic_data()



    def get_market_regime_indicators(self) -> Dict[str, Any]:

        """

        Get indicators for market regime classification.



        Returns:

            dict containing regime-related fields, e.g.:

            - sp500_return

            - volatility

            - interest_rate

            - gdp_growth

            - unemployment_rate

            - sector_performance

            - market_regime

            - volatility_regime

            - interest_rate_environment

            - economic_cycle

        """

        try:

            market_data = self.get_market_overview()

            economic_data = self.get_economic_indicators()

            sector_data = self.get_sector_performance()



            regime_indicators = {

                "sp500_return": market_data.get("sp500_return", 0.0),

                "volatility": market_data.get("volatility", 0.15),

                "interest_rate": economic_data.get("interest_rate", 0.05),

                "gdp_growth": economic_data.get("gdp_growth", 0.02),

                "unemployment_rate": economic_data.get("unemployment_rate", 0.05),

                "sector_performance": sector_data,

                "market_regime": self._classify_market_regime(

                    market_data, economic_data

                ),

                "volatility_regime": self._classify_volatility_regime(market_data),

                "interest_rate_environment": self._classify_interest_rate_environment(

                    economic_data

                ),

                "economic_cycle": self._classify_economic_cycle(economic_data),

            }

            return regime_indicators

        except Exception as e:

            logger.error(

                f"Error getting market regime indicators: {e}", exc_info=True

            )

            return self._generate_synthetic_regime_indicators()



    # ------------------------------------------------------------------

    # Real data fetch helpers

    # ------------------------------------------------------------------

    def _fetch_real_market_data(self) -> Optional[Dict[str, Any]]:

        """

        Fetch real market data from APIs.



        Uses shared market data service (facade) to fetch SPY data as a proxy for S&P 500.

        """

        try:

            async def get_market_data():

                service = get_market_data_service()

                spy_data = await service.get_stock_quote("SPY")

                if not spy_data:

                    return None



                current_price = spy_data.get("price", 0)

                change = spy_data.get("change", 0)

                change_percent = spy_data.get("change_percent", 0)



                high = spy_data.get("high", current_price)

                low = spy_data.get("low", current_price)

                if current_price > 0:

                    daily_range = (high - low) / current_price

                else:

                    daily_range = 0.0



                return {

                    "sp500_return": change_percent / 100.0,  # Convert to decimal

                    "volatility": min(daily_range * 2, 0.5),  # crude estimate

                    "current_price": current_price,

                    "change": change,

                    "change_percent": change_percent,

                    "last_updated": datetime.now().isoformat(),

                }



            # Run async helper in a fresh event loop

            return asyncio.run(get_market_data())

        except Exception as e:

            logger.error(f"Failed to fetch real market data: {e}", exc_info=True)

            return None



    def _fetch_sector_data(self) -> Optional[Dict[str, str]]:

        """

        Fetch real sector performance data.



        Placeholder: return None so we fall back to synthetic data.

        """
        return None



    def _fetch_economic_data(self) -> Optional[Dict[str, float]]:

        """

        Fetch real economic indicators.



        Placeholder: return None so we fall back to synthetic data.

        """
        return None



    # ------------------------------------------------------------------

    # Classification helpers

    # ------------------------------------------------------------------

    def _classify_market_regime(

        self, market_data: Dict[str, Any], economic_data: Dict[str, Any]

    ) -> str:

        """Classify current market regime based on simple thresholds."""

        sp500_return = market_data.get("sp500_return", 0.0)

        gdp_growth = economic_data.get("gdp_growth", 0.02)

        unemployment = economic_data.get("unemployment_rate", 0.05)



        if sp500_return > 0.10 and gdp_growth > 0.02 and unemployment < 0.06:

            return "bull_market"

        elif sp500_return < -0.10 or gdp_growth < 0.0 or unemployment > 0.08:

            return "bear_market"

        elif abs(sp500_return) < 0.05:

            return "sideways"

        else:

            return "volatile"



    def _classify_volatility_regime(self, market_data: Dict[str, Any]) -> str:

        """Classify volatility regime."""

        volatility = market_data.get("volatility", 0.15)

        if volatility < 0.10:

            return "low"

        elif volatility < 0.20:

            return "moderate"

        else:

            return "high"



    def _classify_interest_rate_environment(

        self, economic_data: Dict[str, Any]

    ) -> str:

        """Classify interest rate environment with simple thresholds."""

        interest_rate = economic_data.get("interest_rate", 0.05)



        if interest_rate > 0.06:

            return "rising"

        elif interest_rate < 0.04:

            return "falling"

        else:

            return "stable"



    def _classify_economic_cycle(self, economic_data: Dict[str, Any]) -> str:

        """Classify economic cycle phase."""

        gdp_growth = economic_data.get("gdp_growth", 0.02)

        unemployment = economic_data.get("unemployment_rate", 0.05)



        if gdp_growth > 0.03 and unemployment < 0.05:

            return "expansion"

        elif gdp_growth > 0.02 and unemployment < 0.06:

            return "peak"

        elif gdp_growth < 0.01 or unemployment > 0.07:

            return "contraction"

        else:

            return "trough"



    # ------------------------------------------------------------------

    # Synthetic / fallback generators

    # ------------------------------------------------------------------

    def _generate_synthetic_market_data(self) -> Dict[str, Any]:

        """Generate synthetic market data for development/testing."""

        base_return = random.uniform(-0.05, 0.08)  # -5% to +8%

        base_volatility = random.uniform(0.10, 0.25)  # 10% to 25%

        return {

            "sp500_return": round(base_return, 4),

            "volatility": round(base_volatility, 4),

            "last_updated": datetime.now().isoformat(),

            "method": "synthetic",

        }



    def _generate_synthetic_sector_data(self) -> Dict[str, str]:

        """Generate synthetic sector performance data."""

        sectors = [

            "technology",

            "healthcare",

            "financials",

            "consumer_discretionary",

            "utilities",

            "energy",

        ]

        performances = ["outperforming", "neutral", "underperforming"]

        weights = [0.3, 0.5, 0.2]  # 30% outperforming, 50% neutral, 20% underperforming



        sector_data: Dict[str, str] = {}

        for sector in sectors:

            sector_data[sector] = random.choices(performances, weights=weights)[0]



        return sector_data



    def _generate_synthetic_economic_data(self) -> Dict[str, float]:

        """Generate synthetic economic indicators."""

        return {

            "interest_rate": round(random.uniform(0.03, 0.08), 4),

            "gdp_growth": round(random.uniform(-0.01, 0.04), 4),

            "unemployment_rate": round(random.uniform(0.03, 0.08), 4),

            "inflation_rate": round(random.uniform(0.01, 0.06), 4),

            "method": "synthetic",

        }



    def _generate_synthetic_regime_indicators(self) -> Dict[str, Any]:

        """Generate synthetic regime indicators."""

        return {

            "sp500_return": round(random.uniform(-0.08, 0.12), 4),

            "volatility": round(random.uniform(0.08, 0.30), 4),

            "interest_rate": round(random.uniform(0.02, 0.10), 4),

            "gdp_growth": round(random.uniform(-0.02, 0.05), 4),

            "unemployment_rate": round(random.uniform(0.03, 0.09), 4),

            "sector_performance": self._generate_synthetic_sector_data(),

            "market_regime": random.choice(

                ["bull_market", "bear_market", "sideways", "volatile"]

            ),

            "volatility_regime": random.choice(["low", "moderate", "high"]),

            "interest_rate_environment": random.choice(

                ["rising", "falling", "stable"]

            ),

            "economic_cycle": random.choice(

                ["expansion", "peak", "contraction", "trough"]

            ),

            "method": "synthetic",

        }



    def _initialize_fallback_data(self) -> Dict[str, Any]:

        """Initialize fallback data structure."""

        return {

            "market_overview": self._generate_synthetic_market_data(),

            "sector_performance": self._generate_synthetic_sector_data(),

            "economic_indicators": self._generate_synthetic_economic_data(),

            "regime_indicators": self._generate_synthetic_regime_indicators(),

        }



    # ------------------------------------------------------------------

    # Utility / config

    # ------------------------------------------------------------------

    def set_api_keys(

        self,

        alpha_vantage_key: Optional[str] = None,

        finnhub_key: Optional[str] = None,

    ):

        """Set API keys for real data sources."""

        if alpha_vantage_key:

            self.alpha_vantage_key = alpha_vantage_key

        if finnhub_key:

            self.finnhub_key = finnhub_key

        logger.info("API keys updated")



    def clear_cache(self):

        """Clear the market data cache."""

        self.cache.clear()

        self.cache_expiry.clear()

        logger.info("Market data cache cleared")



    def get_cache_status(self) -> Dict[str, Any]:

        """Get cache status information."""

        return {

            "cache_size": len(self.cache),

            "cache_keys": list(self.cache.keys()),

            "cache_expiry": self.cache_expiry,

            "cache_duration": self.cache_duration,

        }
