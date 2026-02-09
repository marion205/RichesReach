"""
Pre-Market Scanner Service
Scans pre-market movers (4AM-9:30AM ET) and flags quality setups before market open
"""
import os
import aiohttp
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from django.core.cache import cache
from django.utils import timezone as django_timezone
import logging

logger = logging.getLogger(__name__)

# Import ML learner (optional - graceful degradation if not available)
try:
    from .pre_market_ml_learner import get_ml_learner
    ML_LEARNING_AVAILABLE = True
except ImportError:
    ML_LEARNING_AVAILABLE = False
    logger.warning("ML learning not available")

# Import alert service (optional)
try:
    from .pre_market_alerts import get_alert_service
    ALERTS_AVAILABLE = True
except ImportError:
    ALERTS_AVAILABLE = False
    def get_alert_service():
        raise ImportError("Alert service not available")


class PreMarketScanner:
    """
    Pre-market scanner that identifies quality setups before market open.
    
    Strategy:
    - Scans pre-market movers (4AM-9:30AM ET)
    - Applies looser filters (pre-market moves are often bigger)
    - Flags quality setups with room to run
    - Alerts before market open (9:30AM ET)
    """
    
    def __init__(self):
        self.polygon_key = os.getenv('POLYGON_API_KEY', '').strip()
        self.base_url = "https://api.polygon.io"
        
    def _get_et_hour(self) -> int:
        """Get current hour in Eastern Time"""
        now = datetime.now(timezone.utc)
        # Convert UTC to ET (UTC-5, or UTC-4 during DST - simplified)
        et_hour = (now.hour - 5) % 24
        return et_hour
    
    def is_pre_market_hours(self) -> bool:
        """Check if we're in pre-market hours (4AM-9:30AM ET)"""
        et_hour = self._get_et_hour()
        return 4 <= et_hour < 9 or (et_hour == 9 and datetime.now(timezone.utc).minute < 30)
    
    async def fetch_pre_market_movers(self, limit: int = 50) -> List[Dict]:
        """
        Fetch pre-market movers from Polygon.
        Returns list of ticker objects with pre-market data.
        """
        if not self.polygon_key:
            logger.warning("No POLYGON_API_KEY for pre-market scanner")
            return []
        
        try:
            # Polygon snapshot endpoint includes pre-market data
            url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/gainers"
            params = {'apikey': self.polygon_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tickers = data.get('tickers', [])
                        
                        # Filter for pre-market activity
                        pre_market_tickers = []
                        for ticker in tickers[:limit]:
                            # Check if has pre-market data
                            prev_day = ticker.get('prevDay', {})
                            last_trade = ticker.get('lastTrade', {})
                            
                            # Get pre-market change
                            if prev_day and last_trade:
                                prev_close = prev_day.get('c', 0)
                                current_price = last_trade.get('p', 0)
                                
                                if prev_close > 0 and current_price > 0:
                                    change_pct = (current_price - prev_close) / prev_close
                                    
                                    # Only include if moved in pre-market
                                    if abs(change_pct) > 0.01:  # At least 1% move
                                        ticker['pre_market_change_pct'] = change_pct
                                        pre_market_tickers.append(ticker)
                        
                        logger.info(f"✅ Found {len(pre_market_tickers)} pre-market movers")
                        return pre_market_tickers
                    else:
                        logger.warning(f"Polygon API error: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching pre-market movers: {e}", exc_info=True)
            return []
    
    def apply_pre_market_filters(self, ticker: Dict, mode: str = "AGGRESSIVE") -> Tuple[bool, List[str]]:
        """
        Apply pre-market specific filters.
        Returns: (passed, reasons_if_failed)
        """
        reasons = []
        
        # Pre-market filters (looser than regular trading hours)
        if mode == "SAFE":
            min_price = 5.0
            min_volume = 2_000_000  # Lower for pre-market (2M vs 5M)
            min_market_cap = 10_000_000_000  # Lower for pre-market ($10B vs $50B)
            max_change_pct = 0.25  # 25% for pre-market (vs 15% regular)
        else:  # AGGRESSIVE
            min_price = 2.0
            min_volume = 500_000  # Lower for pre-market (500K vs 1M)
            min_market_cap = 500_000_000  # Lower for pre-market ($500M vs $1B)
            max_change_pct = 0.50  # 50% for pre-market (vs 30% regular)
        
        # Extract ticker data
        ticker_str = ticker.get('ticker', '')
        last_trade = ticker.get('lastTrade', {})
        price = float(last_trade.get('p', 0)) if last_trade else 0
        volume = int(ticker.get('day', {}).get('v', 0))
        market_cap = float(ticker.get('market_cap', 0) or 0)
        change_pct = abs(ticker.get('pre_market_change_pct', 0))
        
        # Basic symbol filters
        if not ticker_str or len(ticker_str) > 5:
            reasons.append(f"Symbol format invalid: {ticker_str}")
            return False, reasons
        if '.' in ticker_str or ticker_str.endswith('X'):
            reasons.append(f"Symbol type filtered: {ticker_str}")
            return False, reasons
        
        # Price filter
        if price < min_price or price > 500.0:
            reasons.append(f"Price out of range: ${price:.2f}")
            return False, reasons
        
        # Volume filter (pre-market volume is lower, so we're more lenient)
        if volume < min_volume:
            reasons.append(f"Volume too low: {volume:,} shares")
            return False, reasons
        
        # Market cap filter
        if market_cap > 0 and market_cap < min_market_cap:
            reasons.append(f"Market cap too low: ${market_cap:,.0f}")
            return False, reasons
        
        # Change percentage filter (pre-market allows bigger moves)
        if change_pct > max_change_pct:
            reasons.append(f"Change too high: {change_pct:.1%} > {max_change_pct:.1%}")
            return False, reasons
        
        return True, []
    
    async def scan_pre_market(self, mode: str = "AGGRESSIVE", limit: int = 20) -> List[Dict]:
        """
        Main pre-market scanning function.
        Returns list of quality setups ready for market open.
        """
        if not self.is_pre_market_hours():
            logger.warning(f"Not in pre-market hours (current ET hour: {self._get_et_hour()})")
            return []
        
        logger.info(f"🔍 Starting pre-market scan (mode: {mode})")
        
        # Fetch pre-market movers
        movers = await self.fetch_pre_market_movers(limit=100)
        
        if not movers:
            logger.warning("No pre-market movers found")
            return []
        
        # Apply filters
        quality_setups = []
        for ticker in movers:
            passed, reasons = self.apply_pre_market_filters(ticker, mode)
            
            if passed:
                symbol = ticker.get('ticker', '')
                last_trade = ticker.get('lastTrade', {})
                price = float(last_trade.get('p', 0)) if last_trade else 0
                change_pct = ticker.get('pre_market_change_pct', 0)
                volume = int(ticker.get('day', {}).get('v', 0))
                
                # Calculate side (LONG if positive change, SHORT if negative)
                side = 'LONG' if change_pct > 0 else 'SHORT'
                
                # Estimate quality score (simplified - would use full feature extraction in production)
                score = abs(change_pct) * 10  # Scale change % to score
                if volume > 1_000_000:
                    score += 2  # Bonus for high volume
                
                setup = {
                    'symbol': symbol,
                    'side': side,
                    'score': min(score, 10.0),  # Cap at 10
                    'pre_market_price': price,
                    'pre_market_change_pct': change_pct,
                    'volume': volume,
                    'market_cap': float(ticker.get('market_cap', 0) or 0),
                    'prev_close': ticker.get('prevDay', {}).get('c', 0),
                    'notes': f"Pre-market {side}: {change_pct:.1%} move, {volume:,} shares",
                    'scanned_at': django_timezone.now().isoformat(),
                }
                
                quality_setups.append(setup)
        
        # Sort by score (highest first)
        quality_setups.sort(key=lambda x: x['score'], reverse=True)
        
        # Enhance with ML predictions if available
        if ML_LEARNING_AVAILABLE:
            try:
                ml_learner = get_ml_learner()
                quality_setups = ml_learner.enhance_picks_with_ml(quality_setups)
                logger.info("✅ Enhanced picks with ML predictions")
            except Exception as e:
                logger.warning(f"ML enhancement failed: {e}, using base scores")
        
        # Return top N
        result = quality_setups[:limit]
        logger.info(f"✅ Pre-market scan complete: {len(result)} quality setups found")
        
        return result
    
    def generate_alert(self, setups: List[Dict]) -> str:
        """
        Generate alert message for pre-market setups.
        """
        if not setups:
            return "No quality pre-market setups found today."
        
        alert = f"🔔 PRE-MARKET ALERT - {len(setups)} Quality Setups Found\n"
        alert += "=" * 80 + "\n\n"
        alert += f"Scanned at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        alert += f"Market opens in: ~{self._minutes_until_open()} minutes\n\n"
        
        alert += "TOP SETUPS:\n"
        alert += "-" * 80 + "\n"
        
        for i, setup in enumerate(setups[:10], 1):
            symbol = setup['symbol']
            side = setup['side']
            change = setup['pre_market_change_pct']
            price = setup['pre_market_price']
            score = setup.get('ml_enhanced_score', setup.get('score', 0))
            ml_prob = setup.get('ml_success_probability')
            
            alert += f"{i}. {symbol} - {side}\n"
            alert += f"   Pre-market: {change:+.2%} | Price: ${price:.2f} | Score: {score:.2f}"
            
            if ml_prob is not None:
                alert += f" | ML Success Prob: {ml_prob:.1%}"
            
            alert += f"\n   {setup['notes']}\n\n"
        
        alert += "=" * 80 + "\n"
        alert += "⚠️  Remember: Pre-market moves can reverse at open. Use proper risk management.\n"
        
        return alert
    
    def send_alerts(self, setups: List[Dict]) -> Dict:
        """
        Send alerts via email, push notifications, Discord, and Slack webhooks.
        Returns dict with success status for each channel.
        """
        results = {
            'email_sent': False,
            'push_sent': False,
            'discord_sent': False,
            'slack_sent': False,
        }
        
        if not setups:
            logger.info("No setups to alert")
            return results
        
        # Send all alerts
        if ALERTS_AVAILABLE:
            try:
                alert_service = get_alert_service()
                results['email_sent'] = alert_service.send_email_alert(setups)
                results['push_sent'] = alert_service.send_push_notification(setups)
                results['discord_sent'] = alert_service.send_discord_webhook(setups)
                results['slack_sent'] = alert_service.send_slack_webhook(setups)
            except Exception as e:
                logger.error(f"Error sending alerts: {e}", exc_info=True)
        else:
            logger.warning("Alert service not available")
        
        return results
    
    def _minutes_until_open(self) -> int:
        """Calculate minutes until market open (9:30 AM ET)"""
        now = datetime.now(timezone.utc)
        et_hour = (now.hour - 5) % 24
        
        if et_hour < 9:
            # Market opens at 9:30 AM ET
            minutes_until = (9 - et_hour) * 60 - now.minute + 30
        elif et_hour == 9 and now.minute < 30:
            minutes_until = 30 - now.minute
        else:
            minutes_until = 0  # Market already open
        
        return max(0, minutes_until)


async def scan_pre_market_async(mode: str = "AGGRESSIVE", limit: int = 20) -> List[Dict]:
    """Async wrapper for pre-market scanning"""
    scanner = PreMarketScanner()
    return await scanner.scan_pre_market(mode=mode, limit=limit)


def scan_pre_market_sync(mode: str = "AGGRESSIVE", limit: int = 20) -> List[Dict]:
    """Synchronous wrapper for pre-market scanning"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(scan_pre_market_async(mode, limit))
    finally:
        loop.close()

