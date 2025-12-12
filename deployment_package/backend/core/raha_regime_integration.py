"""
RAHA Market Regime Integration
Applies market regime analysis to RAHA strategy execution and position sizing
"""
import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from .rust_stock_service import rust_stock_service
from .raha_models import RAHASignal, StrategyVersion

logger = logging.getLogger(__name__)


class RAHARegimeIntegration:
    """
    Integrates market regime oracle with RAHA strategy execution.
    Provides regime-aware position sizing and risk controls.
    """
    
    # Strategy type mapping from RAHA strategy names to regime strategy types
    STRATEGY_MAPPING = {
        'ORB': 'ORB_MOMENTUM',
        'MOMENTUM': 'TREND_SWING',
        'BREAKOUT': 'ORB_MOMENTUM',
        'PULLBACK': 'PULLBACK_BUY',
        'MEAN_REVERSION': 'MEAN_REVERSION_INTRADAY',
        'SWING': 'TREND_SWING',
    }
    
    def __init__(self):
        self.rust_service = rust_stock_service
    
    def get_regime_analysis(
        self,
        symbol: str,
        secondary: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get market regime analysis for a symbol.
        
        Args:
            symbol: Primary symbol to analyze
            secondary: Secondary symbol for correlation (defaults to SPY)
        
        Returns:
            Dict with regime analysis or None if unavailable
        """
        try:
            response = self.rust_service.analyze_correlation(symbol, secondary)
            
            if not response:
                logger.warning(f"No regime analysis available for {symbol}")
                return None
            
            return {
                'global_regime': response.get('global_regime', 'NEUTRAL'),
                'local_context': response.get('local_context', 'NORMAL'),
                'correlation_1d': response.get('correlation_1d', 0.0),
                'correlation_7d': response.get('correlation_7d', 0.0),
                'correlation_30d': response.get('correlation_30d', 0.0),
                'btc_dominance': response.get('btc_dominance'),
                'spy_correlation': response.get('spy_correlation'),
            }
        except Exception as e:
            logger.warning(f"Error getting regime analysis for {symbol}: {e}")
            return None
    
    def get_position_multiplier(
        self,
        signal: RAHASignal,
        regime_analysis: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """
        Calculate position size multiplier based on regime.
        
        Args:
            signal: RAHA signal
            regime_analysis: Pre-fetched regime analysis (optional)
        
        Returns:
            Multiplier to apply to base position size (1.0 = no change)
        """
        if not regime_analysis:
            regime_analysis = self.get_regime_analysis(signal.symbol)
        
        if not regime_analysis:
            # No regime data available, use neutral multiplier
            return Decimal('1.0')
        
        global_regime = regime_analysis.get('global_regime', 'NEUTRAL')
        local_context = regime_analysis.get('local_context', 'NORMAL')
        
        # Map RAHA strategy to regime strategy type
        strategy_name = signal.strategy_version.strategy.name.upper() if signal.strategy_version else 'UNKNOWN'
        strategy_type = self.STRATEGY_MAPPING.get(strategy_name, 'TREND_SWING')
        
        # Get multiplier from Rust service (or use hardcoded defaults)
        # For now, we'll use hardcoded multipliers based on the regime matrix
        multiplier = self._get_regime_multiplier(strategy_type, global_regime, local_context)
        
        logger.info(
            f"Regime multiplier for {signal.symbol} ({strategy_type}): {multiplier}x "
            f"(regime: {global_regime}, context: {local_context})"
        )
        
        return Decimal(str(multiplier))
    
    def _get_regime_multiplier(
        self,
        strategy_type: str,
        global_regime: str,
        local_context: str
    ) -> float:
        """
        Get position size multiplier based on strategy type and regime.
        This matches the Rust raha_regime_integration.rs matrix.
        """
        # Base multipliers by regime
        base_multipliers = {
            'EQUITY_RISK_ON': {
                'ORB_MOMENTUM': 1.3,
                'TREND_SWING': 1.4,
                'MEAN_REVERSION_INTRADAY': 0.9,
                'PULLBACK_BUY': 1.3,
            },
            'EQUITY_RISK_OFF': {
                'ORB_MOMENTUM': 0.7,
                'TREND_SWING': 0.6,
                'MEAN_REVERSION_INTRADAY': 0.8,
                'PULLBACK_BUY': 0.5,
            },
            'CRYPTO_ALT_SEASON': {
                'ORB_MOMENTUM': 1.1,
                'TREND_SWING': 1.2,
                'MEAN_REVERSION_INTRADAY': 0.9,
                'PULLBACK_BUY': 1.1,
            },
            'CRYPTO_BTC_DOMINANCE': {
                'ORB_MOMENTUM': 0.8,
                'TREND_SWING': 0.7,
                'MEAN_REVERSION_INTRADAY': 0.9,
                'PULLBACK_BUY': 0.7,
            },
            'NEUTRAL': {
                'ORB_MOMENTUM': 1.0,
                'TREND_SWING': 1.0,
                'MEAN_REVERSION_INTRADAY': 1.0,
                'PULLBACK_BUY': 1.0,
            },
        }
        
        # Get base multiplier
        base = base_multipliers.get(global_regime, {}).get(strategy_type, 1.0)
        
        # Adjust for local context
        if local_context == 'IDIOSYNCRATIC_BREAKOUT':
            base *= 1.1  # Slight bonus for decoupled moves
        elif local_context == 'CHOPPY_MEAN_REVERT':
            base *= 0.9  # Reduce size in choppy markets
        
        return base
    
    def get_risk_controls(
        self,
        symbol: str,
        regime_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get risk control adjustments based on regime.
        
        Returns:
            Dict with risk control parameters:
            - stop_loss_tightness: Multiplier for stop loss (1.0 = normal, <1.0 = tighter, >1.0 = wider)
            - take_profit_aggressiveness: Multiplier for take profit (1.0 = normal, <1.0 = take earlier, >1.0 = let run)
            - max_trades_multiplier: Multiplier for max trades per day
        """
        if not regime_analysis:
            regime_analysis = self.get_regime_analysis(symbol)
        
        if not regime_analysis:
            return {
                'stop_loss_tightness': 1.0,
                'take_profit_aggressiveness': 1.0,
                'max_trades_multiplier': 1.0,
            }
        
        global_regime = regime_analysis.get('global_regime', 'NEUTRAL')
        
        # Risk controls by regime (matching Rust implementation)
        controls = {
            'EQUITY_RISK_ON': {
                'stop_loss_tightness': 0.8,  # Wider stops (let winners breathe)
                'take_profit_aggressiveness': 1.2,  # Let winners run
                'max_trades_multiplier': 1.1,
            },
            'EQUITY_RISK_OFF': {
                'stop_loss_tightness': 1.3,  # Tighter stops
                'take_profit_aggressiveness': 0.7,  # Take profits earlier (scalp)
                'max_trades_multiplier': 0.7,
            },
            'CRYPTO_ALT_SEASON': {
                'stop_loss_tightness': 0.9,
                'take_profit_aggressiveness': 1.1,
                'max_trades_multiplier': 1.0,
            },
            'CRYPTO_BTC_DOMINANCE': {
                'stop_loss_tightness': 1.2,
                'take_profit_aggressiveness': 0.8,
                'max_trades_multiplier': 0.8,
            },
            'NEUTRAL': {
                'stop_loss_tightness': 1.0,
                'take_profit_aggressiveness': 1.0,
                'max_trades_multiplier': 1.0,
            },
        }
        
        return controls.get(global_regime, controls['NEUTRAL'])
    
    def get_regime_narration(
        self,
        symbol: str,
        regime_analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, str]]:
        """
        Get human-readable narration for the current regime.
        
        Returns:
            Dict with title, description, and action_summary
        """
        if not regime_analysis:
            regime_analysis = self.get_regime_analysis(symbol)
        
        if not regime_analysis:
            return None
        
        global_regime = regime_analysis.get('global_regime', 'NEUTRAL')
        
        narrations = {
            'EQUITY_RISK_ON': {
                'title': '📈 Equity RISK-ON',
                'description': 'Markets are in a RISK-ON equity regime. Trends are being rewarded.',
                'action_summary': "We're slightly increasing size on high-conviction continuation setups and giving winners more room.",
            },
            'EQUITY_RISK_OFF': {
                'title': '⚠️ Equity RISK-OFF',
                'description': "We're in a RISK-OFF equity regime. Volatility is elevated and correlations to the index are breaking down.",
                'action_summary': "I'm reducing your size, tightening stops, and favouring defined-risk or defensive setups.",
            },
            'CRYPTO_ALT_SEASON': {
                'title': '🌕 Alt-Season',
                'description': 'Crypto is in ALT-SEASON. BTC dominance is falling and high-quality alts are moving in sync with the broader risk trend.',
                'action_summary': "I'm slightly increasing size in your highest-ranked alts and rotating out of weaker names.",
            },
            'CRYPTO_BTC_DOMINANCE': {
                'title': '🟠 BTC-Dominance',
                'description': "We're in a BTC-DOMINANCE regime. Capital is hiding in BTC rather than chasing alts.",
                'action_summary': "I'm shrinking your alt exposure and focusing on higher-quality majors with defined risk.",
            },
            'NEUTRAL': {
                'title': '⚪ Neutral',
                'description': 'Market regime is neutral. No strong directional bias detected.',
                'action_summary': 'Using standard position sizing and risk controls.',
            },
        }
        
        return narrations.get(global_regime, narrations['NEUTRAL'])


# Global instance
raha_regime_integration = RAHARegimeIntegration()

