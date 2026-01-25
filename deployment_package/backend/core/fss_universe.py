# core/fss_universe.py
"""
FSS Universe Management
Handles stock universe expansion, sector filtering, and liquidity checks.

Supports:
- S&P 500 + Russell 1000 mid-caps
- Sector filtering (e.g., cap tech exposure in Parabolic regimes)
- Liquidity filters (minimum daily dollar volume)
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UniverseConfig:
    """Configuration for universe filtering"""
    min_dollar_volume: float = 10_000_000  # $10M daily average
    max_tech_weight: float = 0.40  # 40% max tech exposure in Parabolic/Expansion
    include_sp500: bool = True
    include_russell1000: bool = True
    exclude_sectors: List[str] = None  # Sectors to exclude


class FSSUniverseManager:
    """
    Manages stock universe for FSS calculation.
    
    Handles:
    - Universe expansion (S&P 500, Russell 1000)
    - Sector filtering
    - Liquidity checks
    """
    
    def __init__(self, config: Optional[UniverseConfig] = None):
        """
        Initialize universe manager.
        
        Args:
            config: Universe configuration (default: standard config)
        """
        self.config = config or UniverseConfig()
    
    def filter_universe(
        self,
        universe_df: pd.DataFrame,
        regime: str,
        prices: Optional[pd.DataFrame] = None,
        volumes: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Filter universe based on regime and liquidity.
        
        Args:
            universe_df: DataFrame with columns: ticker, sector, market_cap, etc.
            regime: Market regime ("Expansion", "Parabolic", "Deflation", "Crisis")
            prices: Optional price DataFrame for liquidity calculation
            volumes: Optional volume DataFrame for liquidity calculation
            
        Returns:
            Filtered universe DataFrame
        """
        filtered = universe_df.copy()
        
        # 1. Liquidity filter
        if prices is not None and volumes is not None:
            filtered = self._apply_liquidity_filter(filtered, prices, volumes)
        
        # 2. Sector filter (cap tech exposure in Parabolic/Expansion)
        if regime in ["Parabolic", "Expansion"]:
            filtered = self._apply_sector_cap(filtered, regime)
        
        # 3. Exclude sectors if configured
        if self.config.exclude_sectors:
            filtered = filtered[~filtered['sector'].isin(self.config.exclude_sectors)]
        
        return filtered
    
    def _apply_liquidity_filter(
        self,
        universe_df: pd.DataFrame,
        prices: pd.DataFrame,
        volumes: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Filter by minimum dollar volume.
        
        Args:
            universe_df: Universe DataFrame
            prices: Price DataFrame
            volumes: Volume DataFrame
            
        Returns:
            Filtered universe
        """
        tickers = universe_df['ticker'].tolist()
        available_tickers = [t for t in tickers if t in prices.columns and t in volumes.columns]
        
        if not available_tickers:
            return universe_df
        
        # Calculate average dollar volume (last 30 days)
        prices_subset = prices[available_tickers].iloc[-30:]
        volumes_subset = volumes[available_tickers].iloc[-30:]
        
        dollar_volumes = (prices_subset * volumes_subset).mean()
        
        # Filter by minimum
        liquid_tickers = dollar_volumes[dollar_volumes >= self.config.min_dollar_volume].index.tolist()
        
        return universe_df[universe_df['ticker'].isin(liquid_tickers)]
    
    def _apply_sector_cap(
        self,
        universe_df: pd.DataFrame,
        regime: str
    ) -> pd.DataFrame:
        """
        Cap technology sector exposure in Parabolic/Expansion regimes.
        
        Args:
            universe_df: Universe DataFrame
            regime: Market regime
            
        Returns:
            Filtered universe with tech exposure capped
        """
        if 'sector' not in universe_df.columns:
            logger.warning("No sector column in universe_df, skipping sector filter")
            return universe_df
        
        tech_tickers = universe_df[universe_df['sector'] == 'Technology']['ticker']
        non_tech = universe_df[~universe_df['ticker'].isin(tech_tickers)]
        
        if len(tech_tickers) == 0:
            return universe_df
        
        # Calculate how many tech stocks to keep
        total_stocks = len(universe_df)
        max_tech_count = int(total_stocks * self.config.max_tech_weight)
        
        # Sample tech stocks (could use market cap weighting, FSS scores, etc.)
        if len(tech_tickers) > max_tech_count:
            tech_sample = tech_tickers.sample(n=max_tech_count, random_state=42)
        else:
            tech_sample = tech_tickers
        
        # Combine
        filtered = pd.concat([
            non_tech,
            universe_df[universe_df['ticker'].isin(tech_sample)]
        ])
        
        logger.info(f"Sector filter: {len(tech_sample)}/{len(tech_tickers)} tech stocks kept ({regime} regime)")
        
        return filtered
    
    def get_sp500_tickers(self) -> List[str]:
        """
        Get S&P 500 ticker list.
        
        In production, this would fetch from:
        - Polygon API
        - Wikipedia scraping
        - Static file
        
        Returns:
            List of S&P 500 tickers
        """
        # Placeholder: In production, fetch from API or file
        # For now, return common large caps
        common_sp500 = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
            "V", "JNJ", "WMT", "PG", "JPM", "MA", "UNH", "HD", "DIS", "BAC",
            "ADBE", "NFLX", "PYPL", "CMCSA", "XOM", "VZ", "AVGO", "COST", "CVX",
            "MRK", "PFE", "ABT", "TMO", "ACN", "CSCO", "NKE", "MCD", "LIN",
            "PM", "NEE", "TXN", "HON", "QCOM", "AMGN", "RTX", "LOW", "INTU"
        ]
        
        logger.warning("Using placeholder S&P 500 list. In production, fetch from API.")
        return common_sp500
    
    def get_russell1000_tickers(self) -> List[str]:
        """
        Get Russell 1000 ticker list.
        
        In production, fetch from:
        - FTSE Russell API
        - Static file
        
        Returns:
            List of Russell 1000 tickers
        """
        # Placeholder: In production, fetch from API or file
        logger.warning("Using placeholder Russell 1000 list. In production, fetch from API.")
        return []  # Would be populated from API
    
    def build_universe(
        self,
        include_sp500: bool = True,
        include_russell1000: bool = False
    ) -> pd.DataFrame:
        """
        Build universe DataFrame with tickers and sectors.
        
        Args:
            include_sp500: Include S&P 500 tickers
            include_russell1000: Include Russell 1000 tickers
            
        Returns:
            DataFrame with columns: ticker, sector, market_cap, etc.
        """
        tickers = []
        
        if include_sp500:
            tickers.extend(self.get_sp500_tickers())
        
        if include_russell1000:
            tickers.extend(self.get_russell1000_tickers())
        
        # Remove duplicates
        tickers = list(set(tickers))
        
        # Build DataFrame (in production, fetch sectors from API)
        universe_df = pd.DataFrame({
            'ticker': tickers,
            'sector': 'Unknown',  # Would be fetched from Polygon/GICS
            'market_cap': 0.0  # Would be fetched from API
        })
        
        logger.info(f"Built universe with {len(tickers)} tickers")
        
        return universe_df


# Singleton instance
_universe_manager = None


def get_universe_manager() -> FSSUniverseManager:
    """Get singleton universe manager instance"""
    global _universe_manager
    if _universe_manager is None:
        _universe_manager = FSSUniverseManager()
    return _universe_manager

