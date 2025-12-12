// src/position_sizing.rs
// Position sizing engine driven by AlphaSignal

use serde::{Serialize, Deserialize};
use crate::alpha_oracle::AlphaSignal;

/// Static configuration for position sizing.
/// All values are *fractions of account equity*, not leverage.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PositionSizingConfig {
    /// Baseline risk per trade as fraction of equity (e.g. 0.01 = 1%)
    pub base_risk_per_trade: f64,

    /// Hard cap per-trade risk (e.g. 0.04 = 4% of equity)
    pub max_risk_per_trade: f64,

    /// Maximum notional exposure as a multiple of equity (e.g. 3.0 = 3x)
    pub max_notional_leverage: f64,

    /// Minimum notional size to bother taking (e.g. $50)
    pub min_notional: f64,

    /// Default stop distance as % from entry (e.g. 0.05 = 5%)
    pub default_stop_pct: f64,
}

impl Default for PositionSizingConfig {
    fn default() -> Self {
        Self {
            base_risk_per_trade: 0.01,     // 1% per trade
            max_risk_per_trade: 0.04,      // 4% absolute max
            max_notional_leverage: 3.0,    // 3x exposure cap
            min_notional: 50.0,            // don't bother < $50
            default_stop_pct: 0.05,        // 5% stop by default
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PositionSizingDecision {
    pub symbol: String,

    /// Fraction of account equity at risk (0.0–1.0)
    pub risk_fraction: f64,

    /// Dollar risk (equity * risk_fraction)
    pub dollar_risk: f64,

    /// Target notional exposure in dollars (position size)
    pub target_notional: f64,

    /// Position quantity (e.g. coins/shares/contracts)
    pub quantity: f64,

    /// Suggested stop distance as fraction from entry (e.g. 0.05 = 5%)
    pub stop_loss_pct: f64,

    /// Conviction label mirrored from AlphaSignal
    pub conviction: String,

    /// Human-readable summary for the UI
    pub summary: String,
}

pub struct PositionSizingEngine {
    config: PositionSizingConfig,
}

impl PositionSizingEngine {
    pub fn new(config: PositionSizingConfig) -> Self {
        Self { config }
    }

    /// Core sizing function.
    ///
    /// - `equity`: total account equity in USD
    /// - `entry_price`: intended entry price for the symbol in USD
    pub fn size_position(
        &self,
        alpha: &AlphaSignal,
        equity: f64,
        entry_price: f64,
    ) -> PositionSizingDecision {
        let PositionSizingConfig {
            base_risk_per_trade,
            max_risk_per_trade,
            max_notional_leverage,
            min_notional,
            default_stop_pct,
        } = self.config;

        let score = alpha.alpha_score; // 0–10

        // Map alpha_score to risk multiplier
        let risk_multiplier = if score >= 9.0 {
            4.0
        } else if score >= 7.5 {
            2.5
        } else if score >= 6.0 {
            1.5
        } else if score <= 3.0 {
            0.0
        } else {
            0.75
        };

        let mut risk_fraction = base_risk_per_trade * risk_multiplier;

        // Clamp to max allowed risk per trade
        if risk_fraction > max_risk_per_trade {
            risk_fraction = max_risk_per_trade;
        }

        // If we're in "DUMP" territory or zero risk, force flat
        if alpha.conviction == "DUMP" || risk_fraction <= 0.0 {
            return PositionSizingDecision {
                symbol: alpha.symbol.clone(),
                risk_fraction: 0.0,
                dollar_risk: 0.0,
                target_notional: 0.0,
                quantity: 0.0,
                stop_loss_pct: default_stop_pct,
                conviction: alpha.conviction.clone(),
                summary: format!(
                    "No position in {} — alpha_score {:.2} with conviction {}",
                    alpha.symbol, alpha.alpha_score, alpha.conviction
                ),
            };
        }

        // Risk in dollars
        let dollar_risk = equity * risk_fraction;

        // Position notional based on stop distance:
        // Notional = dollar_risk / stop_pct
        let stop_loss_pct = default_stop_pct;
        let mut target_notional = dollar_risk / stop_loss_pct;

        // Cap notional by leverage limit
        let max_notional = equity * max_notional_leverage;
        if target_notional > max_notional {
            target_notional = max_notional;
        }

        // If too small, just don't trade
        if target_notional < min_notional {
            return PositionSizingDecision {
                symbol: alpha.symbol.clone(),
                risk_fraction: 0.0,
                dollar_risk: 0.0,
                target_notional: 0.0,
                quantity: 0.0,
                stop_loss_pct,
                conviction: alpha.conviction.clone(),
                summary: format!(
                    "Position in {} would be too small to matter (notional {:.2}) — skipping",
                    alpha.symbol, target_notional
                ),
            };
        }

        // Quantity in units (coins/shares)
        let quantity = if entry_price > 0.0 {
            target_notional / entry_price
        } else {
            0.0
        };

        let summary = format!(
            "{} on {} → risk {:.2}% of equity (${:.2}), target size ${:.2}, qty {:.6}, stop at {:.1}% below entry",
            alpha.conviction,
            alpha.symbol,
            risk_fraction * 100.0,
            dollar_risk,
            target_notional,
            quantity,
            stop_loss_pct * 100.0,
        );

        PositionSizingDecision {
            symbol: alpha.symbol.clone(),
            risk_fraction,
            dollar_risk,
            target_notional,
            quantity,
            stop_loss_pct,
            conviction: alpha.conviction.clone(),
            summary,
        }
    }
}

