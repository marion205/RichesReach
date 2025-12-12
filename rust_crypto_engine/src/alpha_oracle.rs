// src/alpha_oracle.rs
// THE RICHEST SIGNAL ON EARTH: macro regime + ML micro alpha

use std::collections::HashMap;
use std::sync::Arc;

use anyhow::Result;
use serde::{Serialize, Deserialize};
use tokio::try_join;

use crate::regime::{MarketRegimeEngine, SimpleMarketRegime};
use crate::ml_models::{CryptoMLPredictor, PredictionOutput};
use crate::market_data::provider::MarketDataProvider;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaSignal {
    pub symbol: String,

    // Regime context
    pub global_mood: String,      // "Greed", "Panic", "Euphoria", ...
    pub regime_headline: String,  // "Everything risk is ripping higher together"
    pub regime_action: String,    // "Go aggressive • Buy the dip"

    // ML prediction
    pub ml_label: String,         // "BULLISH" | "BEARISH" | "NEUTRAL"
    pub ml_confidence: f64,       // bullish probability 0.0–1.0
    pub explanation: String,      // ML explanation string

    // FINAL FUSION
    pub alpha_score: f64,         // 0.0 → 10.0 (higher = stronger edge)
    pub conviction: String,       // "STRONG BUY" | "BUY" | "WEAK BUY" | "NEUTRAL" | "DUMP"
    pub one_sentence: String,     // The Jobs-style screenshot line
}

pub struct AlphaOracle {
    regime_engine: MarketRegimeEngine,
    ml_predictor: CryptoMLPredictor,
}

impl AlphaOracle {
    pub fn new(provider: Arc<dyn MarketDataProvider>) -> Self {
        Self {
            regime_engine: MarketRegimeEngine::new(provider),
            ml_predictor: CryptoMLPredictor::new(),
        }
    }

    /// Generate a fused alpha signal for a given symbol + feature vector.
    /// `features` should contain keys like:
    /// - "price_usd"
    /// - "volatility"
    /// - "rsi"
    /// - "momentum_24h"
    /// - "market_cap_rank"
    /// - "risk_score"
    pub async fn generate_signal(
        &self,
        symbol: &str,
        features: &HashMap<String, f64>,
    ) -> Result<AlphaSignal> {
        // Run macro regime + micro ML in parallel
        let (regime, ml) = try_join!(
            self.regime_engine.analyze_simple(),
            self.ml_predictor.predict(symbol, features),
        )?;

        let alpha_score = self.fuse_scores(&regime, &ml);
        let (conviction, one_sentence) = self.to_conviction(symbol, alpha_score);

        Ok(AlphaSignal {
            symbol: symbol.to_string(),
            global_mood: regime.mood,
            regime_headline: regime.headline,
            regime_action: regime.action,
            ml_label: ml.label,
            ml_confidence: ml.bullish_probability,
            explanation: ml.explanation,
            alpha_score: alpha_score.min(10.0).max(0.0),
            conviction,
            one_sentence,
        })
    }

    fn fuse_scores(
        &self,
        regime: &SimpleMarketRegime,
        ml: &PredictionOutput,
    ) -> f64 {
        let mut score = 5.0; // neutral base: 0–10 scale

        // ───────────────── Regime contribution ─────────────────
        match regime.mood.as_str() {
            "Greed" | "Euphoria" => {
                // Tailwind: macro risk-on
                score += 2.0;
            }
            "Panic" => {
                // Contrarian alpha if ML agrees with fear or shows divergence
                score += 3.0;
            }
            "Fear" => {
                score += 1.5;
            }
            "Confusion" => {
                score -= 1.0;
            }
            "Boredom" => {
                score -= 0.5;
            }
            _ => {}
        }

        // ───────────────── ML alignment contribution ───────────
        let p_bull = ml.bullish_probability;

        // Regime tailwind + bullish ML
        if (regime.mood == "Greed" || regime.mood == "Euphoria") && p_bull > 0.65 {
            score += 2.5;
        }

        // Panic regime + bearish ML = crash continuation
        if regime.mood == "Panic" && p_bull < 0.4 {
            score += 3.0;
        }

        // Fear regime + bullish ML = potential bottom / squeeze
        if regime.mood == "Fear" && p_bull > 0.7 {
            score += 2.0;
        }

        // ───────────────── Risk / volatility penalties ─────────
        if ml.risk_score > 0.7 {
            score -= 1.5;
        }
        if ml.volatility_pred > 0.15 {
            score -= 1.0;
        }

        score
    }

    fn to_conviction(&self, symbol: &str, alpha_score: f64) -> (String, String) {
        if alpha_score >= 9.0 {
            (
                "STRONG BUY".to_string(),
                format!(
                    "This is once-in-a-cycle alignment — {} has a rare edge right now",
                    symbol
                ),
            )
        } else if alpha_score >= 7.5 {
            (
                "BUY".to_string(),
                format!(
                    "Strong edge on {} — macro regime and ML are pushing the same direction",
                    symbol
                ),
            )
        } else if alpha_score >= 6.0 {
            (
                "WEAK BUY".to_string(),
                format!(
                    "Mild edge on {} — worth watching closely but size carefully",
                    symbol
                ),
            )
        } else if alpha_score <= 3.0 {
            (
                "DUMP".to_string(),
                format!(
                    "Avoid {} — regime and ML are both flashing danger",
                    symbol
                ),
            )
        } else {
            (
                "NEUTRAL".to_string(),
                format!("No clear edge on {} right now", symbol),
            )
        }
    }
}

