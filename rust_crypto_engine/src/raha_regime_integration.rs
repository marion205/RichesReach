use serde::{Serialize, Deserialize};
use crate::correlation_analysis::{GlobalRegime, LocalContext};

/// Strategy types that RAHA can execute
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum RahaStrategy {
    OrbMomentum,           // Opening Range Breakout momentum
    TrendSwing,            // Trend-following swing trades
    MeanReversionIntraday, // Mean-reversion intraday plays
    PullbackBuy,           // Pullback buys in strong names
    ShortWeakSectors,      // Short-side plays in weak sectors
    DefinedRiskOptions,    // Defined-risk options spreads
    BtcEthSwing,           // BTC/ETH swing trades
    AltTrendFollowing,     // Trend-following on strong alts
    RotationalTrade,      // Rotate from laggards to leaders
}

/// Position sizing multiplier based on regime
/// Base size is multiplied by this value
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PositionSizingMultiplier {
    pub strategy: RahaStrategy,
    pub equity_risk_on: f64,
    pub equity_risk_off: f64,
    pub crypto_alt_season: f64,
    pub crypto_btc_dominance: f64,
    pub neutral: f64,
    pub choppy_mean_revert: f64,
}

/// Risk controls that change based on regime
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegimeRiskControls {
    pub max_position_size_multiplier: f64,
    pub stop_loss_tightness: f64, // 1.0 = normal, <1.0 = tighter, >1.0 = wider
    pub take_profit_aggressiveness: f64, // 1.0 = normal, <1.0 = take profits earlier, >1.0 = let winners run
    pub max_trades_per_day_multiplier: f64,
    pub allow_aggressive_fades: bool,
}

/// UX narration text for each regime
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegimeNarration {
    pub regime: GlobalRegime,
    pub title: String,
    pub description: String,
    pub action_summary: String,
}

/// RAHA regime integration engine
/// Maps market regimes to RAHA behavior (position sizing, strategy selection, risk controls)
pub struct RahaRegimeIntegration {
    strategy_multipliers: Vec<PositionSizingMultiplier>,
}

impl RahaRegimeIntegration {
    pub fn new() -> Self {
        Self {
            strategy_multipliers: Self::default_strategy_matrix(),
        }
    }

    /// Get position sizing multiplier for a strategy in a given regime
    pub fn get_position_multiplier(
        &self,
        strategy: &RahaStrategy,
        global_regime: &GlobalRegime,
        local_context: &LocalContext,
    ) -> f64 {
        let base_multiplier = self
            .strategy_multipliers
            .iter()
            .find(|m| &m.strategy == strategy)
            .map(|m| match global_regime {
                GlobalRegime::EquityRiskOn => m.equity_risk_on,
                GlobalRegime::EquityRiskOff => m.equity_risk_off,
                GlobalRegime::CryptoAltSeason => m.crypto_alt_season,
                GlobalRegime::CryptoBtcDominance => m.crypto_btc_dominance,
                GlobalRegime::Neutral => m.neutral,
            })
            .unwrap_or(1.0);

        // Adjust for local context
        let context_multiplier = match local_context {
            LocalContext::IdiosyncraticBreakout => 1.1, // Slight bonus for decoupled moves
            LocalContext::ChoppyMeanRevert => 0.9,      // Reduce size in choppy markets
            LocalContext::Normal => 1.0,
        };

        base_multiplier * context_multiplier
    }

    /// Get risk controls for a given regime
    pub fn get_risk_controls(&self, global_regime: &GlobalRegime) -> RegimeRiskControls {
        match global_regime {
            GlobalRegime::EquityRiskOn => RegimeRiskControls {
                max_position_size_multiplier: 1.3,
                stop_loss_tightness: 0.8, // Wider stops (let winners breathe)
                take_profit_aggressiveness: 1.2, // Let winners run
                max_trades_per_day_multiplier: 1.1,
                allow_aggressive_fades: false,
            },
            GlobalRegime::EquityRiskOff => RegimeRiskControls {
                max_position_size_multiplier: 0.6,
                stop_loss_tightness: 1.3, // Tighter stops
                take_profit_aggressiveness: 0.7, // Take profits earlier (scalp mentality)
                max_trades_per_day_multiplier: 0.7,
                allow_aggressive_fades: false,
            },
            GlobalRegime::CryptoAltSeason => RegimeRiskControls {
                max_position_size_multiplier: 1.2,
                stop_loss_tightness: 0.9,
                take_profit_aggressiveness: 1.1,
                max_trades_per_day_multiplier: 1.0,
                allow_aggressive_fades: false,
            },
            GlobalRegime::CryptoBtcDominance => RegimeRiskControls {
                max_position_size_multiplier: 0.5, // Shrink alt exposure
                stop_loss_tightness: 1.2,
                take_profit_aggressiveness: 0.8,
                max_trades_per_day_multiplier: 0.8,
                allow_aggressive_fades: false,
            },
            GlobalRegime::Neutral => RegimeRiskControls {
                max_position_size_multiplier: 1.0,
                stop_loss_tightness: 1.0,
                take_profit_aggressiveness: 1.0,
                max_trades_per_day_multiplier: 1.0,
                allow_aggressive_fades: true,
            },
        }
    }

    /// Get UX narration for a regime
    pub fn get_narration(&self, global_regime: &GlobalRegime) -> RegimeNarration {
        match global_regime {
            GlobalRegime::EquityRiskOn => RegimeNarration {
                regime: GlobalRegime::EquityRiskOn,
                title: "📈 Equity RISK-ON".to_string(),
                description: "Markets are in a RISK-ON equity regime. Trends are being rewarded.".to_string(),
                action_summary: "We're slightly increasing size on high-conviction continuation setups and giving winners more room.".to_string(),
            },
            GlobalRegime::EquityRiskOff => RegimeNarration {
                regime: GlobalRegime::EquityRiskOff,
                title: "⚠️ Equity RISK-OFF".to_string(),
                description: "We're in a RISK-OFF equity regime. Volatility is elevated and correlations to the index are breaking down.".to_string(),
                action_summary: "I'm reducing your size, tightening stops, and favouring defined-risk or defensive setups.".to_string(),
            },
            GlobalRegime::CryptoAltSeason => RegimeNarration {
                regime: GlobalRegime::CryptoAltSeason,
                title: "🌕 Alt-Season".to_string(),
                description: "Crypto is in ALT-SEASON. BTC dominance is falling and high-quality alts are moving in sync with the broader risk trend.".to_string(),
                action_summary: "I'm slightly increasing size in your highest-ranked alts and rotating out of weaker names.".to_string(),
            },
            GlobalRegime::CryptoBtcDominance => RegimeNarration {
                regime: GlobalRegime::CryptoBtcDominance,
                title: "🟠 BTC-Dominance".to_string(),
                description: "We're in a BTC-DOMINANCE regime. Capital is hiding in BTC rather than chasing alts.".to_string(),
                action_summary: "I'm shrinking your alt exposure and focusing on higher-quality majors with defined risk.".to_string(),
            },
            GlobalRegime::Neutral => RegimeNarration {
                regime: GlobalRegime::Neutral,
                title: "⚪ Neutral".to_string(),
                description: "Market regime is neutral. No strong directional bias detected.".to_string(),
                action_summary: "Using standard position sizing and risk controls.".to_string(),
            },
        }
    }

    /// Get recommended strategies for a regime (prioritized list)
    pub fn get_recommended_strategies(&self, global_regime: &GlobalRegime) -> Vec<RahaStrategy> {
        match global_regime {
            GlobalRegime::EquityRiskOn => vec![
                RahaStrategy::OrbMomentum,
                RahaStrategy::TrendSwing,
                RahaStrategy::PullbackBuy,
            ],
            GlobalRegime::EquityRiskOff => vec![
                RahaStrategy::ShortWeakSectors,
                RahaStrategy::DefinedRiskOptions,
                RahaStrategy::MeanReversionIntraday,
            ],
            GlobalRegime::CryptoAltSeason => vec![
                RahaStrategy::AltTrendFollowing,
                RahaStrategy::RotationalTrade,
                RahaStrategy::TrendSwing,
            ],
            GlobalRegime::CryptoBtcDominance => vec![
                RahaStrategy::BtcEthSwing,
                RahaStrategy::DefinedRiskOptions,
            ],
            GlobalRegime::Neutral => vec![
                RahaStrategy::MeanReversionIntraday,
                RahaStrategy::OrbMomentum,
                RahaStrategy::TrendSwing,
            ],
        }
    }

    /// Default strategy × regime matrix
    fn default_strategy_matrix() -> Vec<PositionSizingMultiplier> {
        vec![
            PositionSizingMultiplier {
                strategy: RahaStrategy::OrbMomentum,
                equity_risk_on: 1.3,
                equity_risk_off: 0.7,
                crypto_alt_season: 1.1,
                crypto_btc_dominance: 0.8,
                neutral: 1.0,
                choppy_mean_revert: 0.9,
            },
            PositionSizingMultiplier {
                strategy: RahaStrategy::TrendSwing,
                equity_risk_on: 1.4,
                equity_risk_off: 0.6,
                crypto_alt_season: 1.2,
                crypto_btc_dominance: 0.7,
                neutral: 1.0,
                choppy_mean_revert: 0.9,
            },
            PositionSizingMultiplier {
                strategy: RahaStrategy::MeanReversionIntraday,
                equity_risk_on: 0.9,
                equity_risk_off: 0.8,
                crypto_alt_season: 0.9,
                crypto_btc_dominance: 0.9,
                neutral: 1.0,
                choppy_mean_revert: 1.2,
            },
            PositionSizingMultiplier {
                strategy: RahaStrategy::PullbackBuy,
                equity_risk_on: 1.3,
                equity_risk_off: 0.5,
                crypto_alt_season: 1.1,
                crypto_btc_dominance: 0.7,
                neutral: 1.0,
                choppy_mean_revert: 0.8,
            },
            PositionSizingMultiplier {
                strategy: RahaStrategy::ShortWeakSectors,
                equity_risk_on: 0.3,
                equity_risk_off: 1.2,
                crypto_alt_season: 0.5,
                crypto_btc_dominance: 0.5,
                neutral: 0.8,
                choppy_mean_revert: 0.9,
            },
            PositionSizingMultiplier {
                strategy: RahaStrategy::DefinedRiskOptions,
                equity_risk_on: 0.8,
                equity_risk_off: 1.1,
                crypto_alt_season: 0.9,
                crypto_btc_dominance: 1.0,
                neutral: 1.0,
                choppy_mean_revert: 1.0,
            },
            PositionSizingMultiplier {
                strategy: RahaStrategy::BtcEthSwing,
                equity_risk_on: 1.0,
                equity_risk_off: 0.8,
                crypto_alt_season: 0.7,
                crypto_btc_dominance: 1.1,
                neutral: 1.0,
                choppy_mean_revert: 0.9,
            },
            PositionSizingMultiplier {
                strategy: RahaStrategy::AltTrendFollowing,
                equity_risk_on: 1.0,
                equity_risk_off: 0.6,
                crypto_alt_season: 1.3,
                crypto_btc_dominance: 0.5,
                neutral: 1.0,
                choppy_mean_revert: 0.8,
            },
            PositionSizingMultiplier {
                strategy: RahaStrategy::RotationalTrade,
                equity_risk_on: 1.1,
                equity_risk_off: 0.7,
                crypto_alt_season: 1.2,
                crypto_btc_dominance: 0.6,
                neutral: 1.0,
                choppy_mean_revert: 0.9,
            },
        ]
    }
}

impl Default for RahaRegimeIntegration {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_position_multipliers() {
        let integration = RahaRegimeIntegration::new();
        
        // ORB momentum should be larger in risk-on
        let mult = integration.get_position_multiplier(
            &RahaStrategy::OrbMomentum,
            &GlobalRegime::EquityRiskOn,
            &LocalContext::Normal,
        );
        assert_eq!(mult, 1.3);
        
        // ORB momentum should be smaller in risk-off
        let mult = integration.get_position_multiplier(
            &RahaStrategy::OrbMomentum,
            &GlobalRegime::EquityRiskOff,
            &LocalContext::Normal,
        );
        assert_eq!(mult, 0.7);
        
        // Mean reversion should be larger in choppy markets
        let mult = integration.get_position_multiplier(
            &RahaStrategy::MeanReversionIntraday,
            &GlobalRegime::Neutral,
            &LocalContext::ChoppyMeanRevert,
        );
        assert_eq!(mult, 1.2);
    }

    #[test]
    fn test_risk_controls() {
        let integration = RahaRegimeIntegration::new();
        
        let controls = integration.get_risk_controls(&GlobalRegime::EquityRiskOn);
        assert_eq!(controls.max_position_size_multiplier, 1.3);
        assert_eq!(controls.stop_loss_tightness, 0.8); // Wider stops
        
        let controls = integration.get_risk_controls(&GlobalRegime::EquityRiskOff);
        assert_eq!(controls.max_position_size_multiplier, 0.6);
        assert_eq!(controls.stop_loss_tightness, 1.3); // Tighter stops
    }
}

