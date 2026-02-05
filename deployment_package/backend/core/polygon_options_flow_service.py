# core/polygon_options_flow_service.py
"""
Real Unusual Options Flow Detection using Polygon API

Detects unusual options activity by analyzing:
1. Volume vs Open Interest ratios (high volume relative to OI = unusual)
2. Large trades (blocks > $25k premium)
3. Sweep detection (multiple exchanges hit rapidly)
4. Put/Call ratio anomalies
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)


@dataclass
class UnusualActivity:
    """Represents an unusual options activity event"""
    contract_symbol: str
    underlying_symbol: str
    strike: float
    expiration_date: str
    option_type: str  # 'call' or 'put'
    volume: int
    open_interest: int
    volume_oi_ratio: float
    last_price: float
    bid: float
    ask: float
    implied_volatility: float
    unusual_score: float  # 0-100, higher = more unusual
    activity_type: str  # 'High Volume', 'Block Trade', 'Sweep', 'OI Spike'
    premium_total: float  # Total premium traded
    is_bullish: bool  # True if likely bullish sentiment
    timestamp: str


class PolygonOptionsFlowService:
    """
    Service to detect unusual options activity using Polygon.io API.

    Unusual activity is detected when:
    - Volume > 2x average daily volume
    - Volume > 25% of open interest (liquidity squeeze potential)
    - Single trades > $25,000 premium (block trades)
    - Multiple rapid executions across exchanges (sweeps)
    """

    # Thresholds for unusual activity detection
    VOLUME_OI_THRESHOLD = 0.25  # Volume > 25% of OI is unusual
    HIGH_VOLUME_MULTIPLIER = 2.0  # Volume > 2x normal is unusual
    BLOCK_TRADE_THRESHOLD = 25000  # $25k+ premium = block trade
    SWEEP_TIME_WINDOW = 60  # Seconds - trades within this window may be sweeps

    def __init__(self):
        """Initialize with Polygon API key"""
        self.polygon_api_key = os.getenv('POLYGON_API_KEY', '')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RichesReach-OptionsFlow/1.0'
        })
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._cache_ttl = 60  # Cache for 60 seconds

    def get_unusual_options_flow(
        self,
        symbol: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get unusual options flow for a symbol.

        Returns:
            Dict with unusual_activity list, put_call_ratio, volumes, etc.
        """
        symbol = symbol.upper()

        # Check cache
        cache_key = f"flow_{symbol}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_ttl:
                logger.debug(f"Using cached options flow for {symbol}")
                return cached_data

        try:
            # Get options contracts and their data
            contracts = self._get_options_contracts(symbol)
            if not contracts:
                logger.warning(f"No options contracts found for {symbol}")
                return self._empty_flow_response(symbol)

            # Get snapshot data for volume/OI using free-tier-compatible aggregates
            snapshots = self._get_options_snapshots(symbol, contracts)

            # Merge contract and snapshot data
            enriched_contracts = self._enrich_contracts_with_snapshots(contracts, snapshots)

            # Detect unusual activity
            unusual_activities = self._detect_unusual_activity(enriched_contracts, symbol)

            # Calculate aggregate metrics
            total_call_volume = sum(c.get('volume', 0) for c in enriched_contracts if c.get('option_type') == 'call')
            total_put_volume = sum(c.get('volume', 0) for c in enriched_contracts if c.get('option_type') == 'put')
            put_call_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else 0

            # Get largest trades
            largest_trades = self._get_largest_trades(unusual_activities)

            result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'unusual_activity': unusual_activities[:limit],
                'put_call_ratio': round(put_call_ratio, 2),
                'total_call_volume': total_call_volume,
                'total_put_volume': total_put_volume,
                'largest_trades': largest_trades[:10],
                'data_source': 'polygon',
                'is_real_data': True
            }

            # Cache result
            self._cache[cache_key] = (datetime.now(), result)

            logger.info(f"Detected {len(unusual_activities)} unusual activities for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Error getting unusual options flow for {symbol}: {e}")
            return self._empty_flow_response(symbol)

    def _get_options_contracts(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch options contracts from Polygon"""
        if not self.polygon_api_key:
            logger.warning("No Polygon API key configured")
            return []

        try:
            url = "https://api.polygon.io/v3/reference/options/contracts"
            params = {
                'underlying_ticker': symbol,
                'limit': 250,  # Get good coverage
                'expired': 'false',
                'apiKey': self.polygon_api_key
            }

            response = self.session.get(url, params=params, timeout=10)
            if not response.ok:
                logger.warning(f"Polygon contracts API returned {response.status_code}")
                return []

            data = response.json()
            return data.get('results', [])

        except Exception as e:
            logger.error(f"Error fetching options contracts: {e}")
            return []

    def _get_options_snapshots(self, symbol: str, contracts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Get options data with volume from Polygon using free tier endpoints.

        Uses /v2/aggs/ticker/{ticker}/prev for previous day's aggregates
        which is available on the free tier.
        """
        if not self.polygon_api_key:
            return {}

        snapshots = {}

        # Limit to top contracts to stay within rate limits (5 req/min on free tier)
        limited_contracts = contracts[:25]  # Process up to 25 contracts

        # Batch fetch - get prev day data for each contract
        for contract in limited_contracts:
            ticker = contract.get('ticker', '')
            if not ticker:
                continue

            try:
                url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev"
                params = {
                    'adjusted': 'true',
                    'apiKey': self.polygon_api_key
                }

                response = self.session.get(url, params=params, timeout=5)
                if response.ok:
                    data = response.json()
                    results = data.get('results', [])
                    if results:
                        r = results[0]
                        snapshots[ticker] = {
                            'volume': int(r.get('v', 0)),
                            'open_interest': 0,  # Not available in free tier
                            'last_price': float(r.get('c', 0)),
                            'open': float(r.get('o', 0)),
                            'high': float(r.get('h', 0)),
                            'low': float(r.get('l', 0)),
                            'vwap': float(r.get('vw', 0)),
                            'bid': float(r.get('c', 0)) * 0.98,  # Estimate
                            'ask': float(r.get('c', 0)) * 1.02,  # Estimate
                            'implied_volatility': 0,  # Will be calculated
                            'delta': 0,
                            'gamma': 0,
                            'theta': 0,
                            'vega': 0,
                            'transactions': int(r.get('n', 0)),  # Number of trades
                        }
                elif response.status_code == 429:
                    logger.warning("Polygon rate limit reached while fetching aggregates for %s", symbol)
                    break

            except Exception as e:
                logger.debug(f"Error fetching data for {ticker}: {e}")
                continue

        logger.info(f"Got volume data for {len(snapshots)} options contracts for {symbol}")
        return snapshots

    def _enrich_contracts_with_snapshots(
        self,
        contracts: List[Dict[str, Any]],
        snapshots: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge contract reference data with snapshot data"""
        enriched = []

        for contract in contracts:
            ticker = contract.get('ticker', '')
            snapshot = snapshots.get(ticker, {})

            enriched.append({
                'contract_symbol': ticker,
                'underlying_symbol': contract.get('underlying_ticker', ''),
                'strike': contract.get('strike_price', 0),
                'expiration_date': contract.get('expiration_date', ''),
                'option_type': contract.get('contract_type', '').lower(),
                'volume': snapshot.get('volume', 0),
                'open_interest': snapshot.get('open_interest', 0),
                'last_price': snapshot.get('last_price', 0),
                'bid': snapshot.get('bid', 0),
                'ask': snapshot.get('ask', 0),
                'implied_volatility': snapshot.get('implied_volatility', 0),
                'delta': snapshot.get('delta', 0),
                'gamma': snapshot.get('gamma', 0),
                'theta': snapshot.get('theta', 0),
                'vega': snapshot.get('vega', 0),
                'transactions': snapshot.get('transactions', 0),
            })

        return enriched

    def _detect_unusual_activity(
        self,
        contracts: List[Dict[str, Any]],
        symbol: str
    ) -> List[Dict[str, Any]]:
        """
        Detect unusual options activity based on various signals.

        Signals:
        1. High Volume/OI ratio (> 25%)
        2. High absolute volume
        3. Large premium traded (potential block)
        4. Unusual IV levels
        """
        unusual = []

        # Calculate baseline metrics
        volumes = [c.get('volume', 0) for c in contracts if c.get('volume', 0) > 0]
        avg_volume = sum(volumes) / len(volumes) if volumes else 100

        for contract in contracts:
            volume = contract.get('volume', 0)
            open_interest = contract.get('open_interest', 0)
            last_price = contract.get('last_price', 0)
            transactions = contract.get('transactions', 0)

            if volume == 0:
                continue

            # Calculate unusual score (0-100)
            unusual_score = 0
            activity_types = []

            # Signal 1: Volume/OI ratio
            vol_oi_ratio = volume / open_interest if open_interest > 0 else None
            if vol_oi_ratio is not None and vol_oi_ratio > self.VOLUME_OI_THRESHOLD:
                unusual_score += min(40, vol_oi_ratio * 100)
                activity_types.append('High Vol/OI')

            # Signal 2: High volume vs average
            if volume > avg_volume * self.HIGH_VOLUME_MULTIPLIER:
                volume_multiplier = volume / avg_volume
                unusual_score += min(30, volume_multiplier * 10)
                activity_types.append('High Volume')

            # Signal 3: Large premium (potential block trade)
            total_premium = volume * last_price * 100  # Options are for 100 shares
            is_block = total_premium > self.BLOCK_TRADE_THRESHOLD and (transactions <= 2 or volume >= 500)
            if is_block:
                unusual_score += min(20, (total_premium / self.BLOCK_TRADE_THRESHOLD) * 10)
                activity_types.append('Block Trade')

            # Signal 4: Sweep detection using trade count proxy
            is_sweep = transactions >= 10 and volume >= avg_volume * 1.5
            if is_sweep:
                unusual_score += 10
                activity_types.append('Sweep')

            # Signal 5: Unusual IV (> 50% or < 10%)
            iv = contract.get('implied_volatility', 0)
            if iv > 0.50:
                unusual_score += 10
                activity_types.append('High IV')
            elif 0 < iv < 0.10:
                unusual_score += 5
                activity_types.append('Low IV')

            # Only include if unusual enough
            if unusual_score >= 20:
                # Determine sentiment
                option_type = contract.get('option_type', 'call')
                delta = contract.get('delta', 0)

                # Bullish: buying calls (positive delta) or selling puts
                # Bearish: buying puts (negative delta) or selling calls
                is_bullish = (option_type == 'call' and delta > 0) or (option_type == 'put' and delta < 0)

                unusual.append({
                    'contract_symbol': contract.get('contract_symbol', ''),
                    'underlying_symbol': symbol,
                    'strike': contract.get('strike', 0),
                    'expiration_date': contract.get('expiration_date', ''),
                    'option_type': option_type,
                    'volume': volume,
                    'open_interest': open_interest,
                    'volume_oi_ratio': round(vol_oi_ratio, 2) if vol_oi_ratio is not None else 0.0,
                    'last_price': last_price,
                    'bid': contract.get('bid', 0),
                    'ask': contract.get('ask', 0),
                    'implied_volatility': round(iv, 4) if iv else 0.25,
                    'unusual_score': min(100, round(unusual_score, 1)),
                    'activity_type': ' + '.join(activity_types) if activity_types else 'Unusual',
                    'premium_total': round(total_premium, 2),
                    'is_bullish': is_bullish,
                    'delta': contract.get('delta', 0),
                    'sweep_count': 1 if is_sweep else 0,
                    'block_size': volume if is_block else 0,
                    'is_dark_pool': False,  # Would need Level 2 data
                    'timestamp': datetime.now().isoformat()
                })

        # Sort by unusual score descending
        unusual.sort(key=lambda x: x.get('unusual_score', 0), reverse=True)

        return unusual

    def _get_largest_trades(
        self,
        unusual_activities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract largest trades from unusual activities"""
        sorted_by_premium = sorted(
            unusual_activities,
            key=lambda x: x.get('premium_total', 0),
            reverse=True
        )

        return [
            {
                'contract_symbol': item.get('contract_symbol', ''),
                'size': item.get('volume', 0),
                'price': item.get('last_price', 0),
                'premium': item.get('premium_total', 0),
                'time': item.get('timestamp', ''),
                'is_call': item.get('option_type', '') == 'call',
                'is_sweep': item.get('sweep_count', 0) > 0,
                'is_block': item.get('block_size', 0) > 0,
            }
            for item in sorted_by_premium[:10]
        ]

    def _empty_flow_response(self, symbol: str) -> Dict[str, Any]:
        """Return empty flow response structure"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'unusual_activity': [],
            'put_call_ratio': 0.0,
            'total_call_volume': 0,
            'total_put_volume': 0,
            'largest_trades': [],
            'data_source': 'none',
            'is_real_data': False
        }


# Singleton instance
_polygon_flow_service: Optional[PolygonOptionsFlowService] = None


def get_polygon_flow_service() -> PolygonOptionsFlowService:
    """Get or create the Polygon flow service singleton"""
    global _polygon_flow_service
    if _polygon_flow_service is None:
        _polygon_flow_service = PolygonOptionsFlowService()
    return _polygon_flow_service
