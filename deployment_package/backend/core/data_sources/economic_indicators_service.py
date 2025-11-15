"""
Economic Indicators Service
Tracks macroeconomic indicators that affect stock prices.
"""

import os
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EconomicIndicator:
    """Economic indicator data point"""
    name: str
    value: float
    timestamp: datetime
    change: float  # Change from previous period
    impact: str  # "positive", "negative", "neutral"
    description: str
    source: str


class EconomicIndicatorsService:
    """Service for tracking economic indicators"""

    def __init__(self):
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.fred_api_key = os.getenv("FRED_API_KEY", "")  # Federal Reserve Economic Data
        self.enabled = bool(self.alpha_vantage_api_key or self.fred_api_key)

    async def get_relevant_indicators(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[EconomicIndicator]:
        """
        Get economic indicators that were released in the time period.
        """
        if not self.enabled:
            logger.warning("Economic indicators service not configured")
            return []

        indicators = []

        # Get Federal Reserve interest rate data (free)
        try:
            fed_data = await self._get_fed_interest_rates(start_date, end_date)
            indicators.extend(fed_data)
        except Exception as e:
            logger.error(f"Error fetching Fed data: {e}")

        # Get CPI data (if FRED API key available)
        if self.fred_api_key:
            try:
                cpi_data = await self._get_cpi_data(start_date, end_date)
                indicators.extend(cpi_data)
            except Exception as e:
                logger.error(f"Error fetching CPI data: {e}")

        return sorted(indicators, key=lambda x: x.timestamp)

    async def _get_fed_interest_rates(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[EconomicIndicator]:
        """Get Federal Reserve interest rate data"""
        # Federal Reserve API (free, no key required for basic data)
        url = "https://api.fiscaldata.treasury.gov/services/api/v1/accounting/od/avg_interest_rates"
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "filter": f"record_date:gte:{start_date.strftime('%Y-%m-%d')},record_date:lte:{end_date.strftime('%Y-%m-%d')}",
                    "page[size]": 100,
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()
                    records = data.get("data", [])

                    indicators = []
                    for record in records:
                        rate = float(record.get("avg_interest_rate_amt", 0))
                        record_date = datetime.fromisoformat(
                            record.get("record_date", "")
                        )

                        indicators.append(
                            EconomicIndicator(
                                name="Federal Funds Rate",
                                value=rate,
                                timestamp=record_date,
                                change=0.0,  # Would need previous value to calculate
                                impact="neutral",  # Would analyze based on change
                                description=f"Federal Reserve interest rate: {rate}%",
                                source="federal_reserve",
                            )
                        )

                    return indicators
        except Exception as e:
            logger.error(f"Error fetching Fed interest rates: {e}")
            return []

    async def _get_cpi_data(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[EconomicIndicator]:
        """Get Consumer Price Index data from FRED"""
        if not self.fred_api_key:
            return []

        # FRED API endpoint
        url = "https://api.stlouisfed.org/fred/series/observations"
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "series_id": "CPIAUCSL",  # CPI for All Urban Consumers
                    "api_key": self.fred_api_key,
                    "file_type": "json",
                    "observation_start": start_date.strftime("%Y-%m-%d"),
                    "observation_end": end_date.strftime("%Y-%m-%d"),
                }

                async with session.get(url, params=params, timeout=10) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()
                    observations = data.get("observations", [])

                    indicators = []
                    prev_value = None
                    for obs in observations:
                        value = float(obs.get("value", 0))
                        obs_date = datetime.fromisoformat(obs.get("date", ""))

                        change = 0.0
                        if prev_value:
                            change = ((value - prev_value) / prev_value) * 100

                        indicators.append(
                            EconomicIndicator(
                                name="Consumer Price Index (CPI)",
                                value=value,
                                timestamp=obs_date,
                                change=change,
                                impact="positive" if change < 0 else "negative",  # Lower inflation is positive
                                description=f"CPI: {value:.2f} ({change:+.2f}% change)",
                                source="fred",
                            )
                        )

                        prev_value = value

                    return indicators
        except Exception as e:
            logger.error(f"Error fetching CPI data: {e}")
            return []

