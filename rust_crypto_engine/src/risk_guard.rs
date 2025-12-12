// src/risk_guard.rs
// Portfolio-level risk cap

use serde::{Serialize, Deserialize};
use crate::position_sizing::PositionSizingDecision;

/// What the portfolio currently has open.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpenRiskPosition {
    pub symbol: String,
    /// Dollar risk on this position (usually: equity * risk_fraction_at_entry)
    pub dollar_risk: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskGuardConfig {
    /// Max total risk as a fraction of equity, e.g. 0.12 = 12% of account
    pub max_total_risk_fraction: f64,
    /// Optional max number of concurrent Oracle positions
    pub max_positions: usize,
}

impl Default for RiskGuardConfig {
    fn default() -> Self {
        Self {
            max_total_risk_fraction: 0.12, // 12% of equity across all trades
            max_positions: 8,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskGuardDecision {
    pub allow: bool,
    pub adjusted: Option<PositionSizingDecision>,
    pub reason: String,
}

pub struct RiskGuard {
    config: RiskGuardConfig,
}

impl RiskGuard {
    pub fn new(config: RiskGuardConfig) -> Self {
        Self { config }
    }

    /// Decide if we can take a new sized position, given existing portfolio risk.
    ///
    /// - `equity`: current account equity in USD
    /// - `open_positions`: active positions with their current dollar risk
    /// - `proposed`: what PositionSizingEngine wants to do
    pub fn evaluate(
        &self,
        equity: f64,
        open_positions: &[OpenRiskPosition],
        proposed: &PositionSizingDecision,
    ) -> RiskGuardDecision {
        // If proposed is flat already, nothing to do.
        if proposed.dollar_risk <= 0.0 {
            return RiskGuardDecision {
                allow: false,
                adjusted: None,
                reason: format!(
                    "No trade on {} — proposed risk is zero",
                    proposed.symbol
                ),
            };
        }

        // Hard cap on number of Oracle positions
        if open_positions.len() >= self.config.max_positions {
            return RiskGuardDecision {
                allow: false,
                adjusted: None,
                reason: format!(
                    "Max Oracle positions ({}) reached — not opening {}",
                    self.config.max_positions,
                    proposed.symbol
                ),
            };
        }

        let max_total_risk = equity * self.config.max_total_risk_fraction;
        let current_risk: f64 = open_positions.iter().map(|p| p.dollar_risk).sum();

        let remaining_risk_capacity = (max_total_risk - current_risk).max(0.0);

        if remaining_risk_capacity <= 0.0 {
            return RiskGuardDecision {
                allow: false,
                adjusted: None,
                reason: format!(
                    "Total risk cap reached ({:.2}% of equity) — cannot add {}",
                    self.config.max_total_risk_fraction * 100.0,
                    proposed.symbol
                ),
            };
        }

        // If proposed fits fully, allow as-is
        if proposed.dollar_risk <= remaining_risk_capacity {
            RiskGuardDecision {
                allow: true,
                adjusted: Some(proposed.clone()),
                reason: format!(
                    "Approved full size on {} (risk ${:.2}, remaining capacity ${:.2})",
                    proposed.symbol,
                    proposed.dollar_risk,
                    remaining_risk_capacity - proposed.dollar_risk
                ),
            }
        } else {
            // Scale down proportionally to remaining risk capacity
            let scale = remaining_risk_capacity / proposed.dollar_risk;

            let mut adjusted = proposed.clone();
            adjusted.dollar_risk *= scale;
            adjusted.target_notional *= scale;
            adjusted.quantity *= scale;
            adjusted.risk_fraction *= scale;

            RiskGuardDecision {
                allow: true,
                adjusted: Some(adjusted),
                reason: format!(
                    "Scaled down {} to fit portfolio risk cap (used {:.1}% of intended size)",
                    proposed.symbol,
                    scale * 100.0
                ),
            }
        }
    }
}

