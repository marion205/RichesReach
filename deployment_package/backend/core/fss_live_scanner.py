# core/fss_live_scanner.py
"""
FSS Live Scanner
Daily scanner that calculates FSS scores and alerts on new high-conviction stocks.

Production-ready script for:
- Daily FSS calculation
- New high-FSS stock alerts
- Regime detection
- Top stock ranking
"""
import os
import pickle
import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

from .fss_engine import get_fss_engine
from .fss_data_pipeline import get_fss_data_pipeline, FSSDataRequest
from .fss_universe import get_universe_manager
from .fss_engine import get_safety_filter

logger = logging.getLogger(__name__)


class FSSLiveScanner:
    """
    Live scanner for FSS scores.
    
    Runs daily to:
    1. Fetch latest market data
    2. Calculate FSS scores
    3. Detect regime
    4. Filter and rank stocks
    5. Alert on new high-conviction stocks
    """
    
    def __init__(
        self,
        prior_top_file: str = "fss_prior_top.pkl",
        alert_threshold: float = 80.0,
        top_n: int = 30,
        email_config: Optional[Dict[str, str]] = None
    ):
        """
        Initialize live scanner.
        
        Args:
            prior_top_file: Path to file storing previous top stocks
            alert_threshold: FSS score threshold for alerts (default: 80)
            top_n: Number of top stocks to track (default: 30)
            email_config: Email configuration for alerts (optional)
        """
        self.prior_top_file = prior_top_file
        self.alert_threshold = alert_threshold
        self.top_n = top_n
        self.email_config = email_config or {}
        
        self.fss_engine = get_fss_engine()
        self.data_pipeline = get_fss_data_pipeline()
        self.universe_manager = get_universe_manager()
        self.safety_filter = get_safety_filter()
    
    async def scan(
        self,
        tickers: List[str],
        lookback_days: int = 252
    ) -> Dict[str, Any]:
        """
        Run daily FSS scan.
        
        Args:
            tickers: List of stock symbols to scan
            lookback_days: Days of historical data to fetch
            
        Returns:
            Dictionary with scan results
        """
        logger.info(f"Starting FSS scan for {len(tickers)} tickers")
        
        # 1. Fetch latest data
        async with self.data_pipeline:
            data_request = FSSDataRequest(
                tickers=tickers,
                lookback_days=lookback_days,
                include_fundamentals=True
            )
            data_result = await self.data_pipeline.fetch_fss_data(data_request)
        
        # 2. Detect regime
        regime_result = self.fss_engine.detect_market_regime(
            data_result.spy,
            data_result.vix
        )
        regime = regime_result.regime
        
        logger.info(f"Market regime: {regime} (confidence: {regime_result.confidence:.2f})")
        
        # 3. Calculate FSS scores
        fss_data = self.fss_engine.compute_fss_v3(
            prices=data_result.prices,
            volumes=data_result.volumes,
            spy=data_result.spy,
            vix=data_result.vix,
            fundamentals_daily=data_result.fundamentals_daily
        )
        
        # 4. Get latest scores
        latest_date = fss_data.index[-1]
        fss_today = fss_data["FSS"].loc[latest_date].dropna()
        
        # 5. Apply safety filters
        qualified = {}
        for ticker in fss_today.index:
            if ticker in data_result.volumes.columns:
                safety_passed, safety_reason = self.safety_filter.check_safety(
                    ticker=ticker,
                    volumes=data_result.volumes
                )
                if safety_passed:
                    qualified[ticker] = {
                        "fss_score": float(fss_today[ticker]),
                        "safety_reason": safety_reason
                    }
        
        if not qualified:
            logger.warning("No stocks passed safety filters")
            return {
                "regime": regime,
                "top_stocks": [],
                "new_high_conviction": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # 6. Rank and filter
        qualified_df = pd.DataFrame(qualified).T.sort_values("fss_score", ascending=False)
        top_stocks = qualified_df.head(self.top_n)
        high_conviction = qualified_df[qualified_df["fss_score"] >= self.alert_threshold]
        
        # 7. Check for new entrants
        prior_top = self._load_prior_top()
        new_high = high_conviction[~high_conviction.index.isin(prior_top.index)]
        
        # 8. Save current top for next run
        self._save_prior_top(top_stocks)
        
        # 9. Alert if new high-conviction stocks
        if not new_high.empty:
            logger.info(f"Found {len(new_high)} new high-conviction stocks")
            await self._send_alert(new_high, top_stocks, regime)
        
        # 10. Prepare results
        result = {
            "regime": regime,
            "regime_confidence": regime_result.confidence,
            "top_stocks": top_stocks.to_dict(orient="index"),
            "high_conviction": high_conviction.to_dict(orient="index"),
            "new_high_conviction": new_high.to_dict(orient="index"),
            "total_scanned": len(tickers),
            "qualified": len(qualified),
            "timestamp": datetime.now().isoformat(),
            "data_quality": data_result.data_quality
        }
        
        logger.info(f"Scan complete: {len(top_stocks)} top stocks, {len(new_high)} new alerts")
        
        return result
    
    def _load_prior_top(self) -> pd.DataFrame:
        """Load previous top stocks from file"""
        if os.path.exists(self.prior_top_file):
            try:
                return pd.read_pickle(self.prior_top_file)
            except Exception as e:
                logger.warning(f"Failed to load prior top: {e}")
        return pd.DataFrame()
    
    def _save_prior_top(self, top_stocks: pd.DataFrame):
        """Save current top stocks to file"""
        try:
            top_stocks.to_pickle(self.prior_top_file)
        except Exception as e:
            logger.error(f"Failed to save prior top: {e}")
    
    async def _send_alert(
        self,
        new_stocks: pd.DataFrame,
        top_stocks: pd.DataFrame,
        regime: str
    ):
        """
        Send email alert for new high-conviction stocks.
        
        Args:
            new_stocks: DataFrame of new high-conviction stocks
            top_stocks: DataFrame of top stocks
            regime: Current market regime
        """
        if not self.email_config:
            logger.info("Email not configured, skipping alert")
            return
        
        try:
            subject = f"FSS Alert: {len(new_stocks)} New High-Conviction Stocks ({regime})"
            
            body = f"""
FSS Live Scanner Alert
=====================

Market Regime: {regime}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

New High-Conviction Stocks (FSS >= {self.alert_threshold}):
{'-' * 60}
"""
            for ticker, row in new_stocks.iterrows():
                body += f"{ticker}: {row['fss_score']:.1f} ({row.get('safety_reason', 'Clear')})\n"
            
            body += f"""

Top {self.top_n} Stocks:
{'-' * 60}
"""
            for ticker, row in top_stocks.head(10).iterrows():
                body += f"{ticker}: {row['fss_score']:.1f}\n"
            
            # Send email
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.email_config.get('from', 'scanner@richesreach.ai')
            msg['To'] = self.email_config.get('to', 'alerts@richesreach.ai')
            
            # SMTP configuration
            smtp_server = self.email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = self.email_config.get('smtp_port', 587)
            smtp_user = self.email_config.get('smtp_user')
            smtp_password = self.email_config.get('smtp_password')
            
            if smtp_user and smtp_password:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                logger.info("Alert email sent")
            else:
                logger.warning("SMTP credentials not configured")
        
        except Exception as e:
            logger.error(f"Failed to send alert: {e}", exc_info=True)


async def run_daily_scan(
    tickers: Optional[List[str]] = None,
    universe_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run daily FSS scan (main entry point).
    
    Args:
        tickers: Optional list of tickers (if None, uses universe manager)
        universe_config: Optional universe configuration
        
    Returns:
        Scan results
    """
    scanner = FSSLiveScanner()
    
    # Get tickers from universe if not provided
    if tickers is None:
        universe_manager = get_universe_manager()
        universe_df = universe_manager.build_universe(
            include_sp500=True,
            include_russell1000=False
        )
        tickers = universe_df['ticker'].tolist()
    
    # Run scan
    results = await scanner.scan(tickers)
    
    return results


# CLI entry point
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Run scan for specific tickers
    tickers = sys.argv[1:] if len(sys.argv) > 1 else None
    
    results = asyncio.run(run_daily_scan(tickers))
    
    print(f"\nScan Results:")
    print(f"Regime: {results['regime']}")
    print(f"Top Stocks: {len(results['top_stocks'])}")
    print(f"New Alerts: {len(results['new_high_conviction'])}")

