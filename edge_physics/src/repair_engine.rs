// edge_physics/src/repair_engine.rs
// Real-time position monitoring and repair plan generation

use crate::black_scholes::{BlackScholesCalculator, Greeks};
use rayon::prelude::*;

/// Represents an open position
#[derive(Debug, Clone)]
pub struct Position {
    pub id: String,
    pub ticker: String,
    pub strategy_type: String,
    pub current_delta: f64,
    pub current_gamma: f64,
    pub current_theta: f64,
    pub current_vega: f64,
    pub current_price: f64,
    pub max_loss: f64,
    pub unrealized_pnl: f64,
    pub days_to_expiration: i32,
}

/// Repair plan for a leaking position
#[derive(Debug, Clone)]
pub struct RepairPlan {
    pub position_id: String,
    pub ticker: String,
    pub repair_type: String,
    pub delta_drift_pct: f64,
    pub repair_credit: f64,
    pub new_max_loss: f64,
    pub priority: String,
    pub confidence_boost: f64,
}

/// The repair engine
pub struct RepairEngine {
    delta_repair_threshold: f64,
    max_loss_ratio_threshold: f64,
}

impl RepairEngine {
    /// Create a new repair engine
    pub fn new() -> Self {
        RepairEngine {
            delta_repair_threshold: 0.25,
            max_loss_ratio_threshold: 0.15,
        }
    }

    /// Analyze a single position for repair needs
    pub fn analyze_position(
        &self,
        position: &Position,
        account_equity: f64,
    ) -> Option<RepairPlan> {
        // Check delta drift
        let delta_drift = position.current_delta.abs();
        if delta_drift < self.delta_repair_threshold {
            return None;
        }

        // Check loss ratio
        let loss_ratio = position.unrealized_pnl.abs() / account_equity.max(1.0);
        if loss_ratio < 0.10 {
            return None;
        }

        // Position needs repair
        let repair_credit = (position.unrealized_pnl.abs() * 0.3).max(50.0).min(500.0);
        let new_max_loss = position.max_loss - repair_credit;
        let priority = self.calculate_priority(delta_drift, loss_ratio);
        let confidence_boost = (delta_drift * 0.3).min(0.15);

        Some(RepairPlan {
            position_id: position.id.clone(),
            ticker: position.ticker.clone(),
            repair_type: if position.current_delta > 0.0 {
                "BEAR_CALL_SPREAD".to_string()
            } else {
                "BULL_PUT_SPREAD".to_string()
            },
            delta_drift_pct: delta_drift,
            repair_credit,
            new_max_loss,
            priority,
            confidence_boost,
        })
    }

    /// Batch analyze many positions (uses parallel processing)
    pub fn batch_analyze(
        &self,
        positions: &[Position],
        account_equity: f64,
    ) -> Vec<RepairPlan> {
        positions
            .par_iter()
            .filter_map(|pos| self.analyze_position(pos, account_equity))
            .collect::<Vec<_>>()
            .into_iter()
            .collect()
    }

    /// Calculate priority based on risk score
    fn calculate_priority(&self, delta_drift: f64, loss_ratio: f64) -> String {
        let risk_score = delta_drift * 0.6 + loss_ratio * 0.4;

        if risk_score > 0.40 {
            "CRITICAL".to_string()
        } else if risk_score > 0.30 {
            "HIGH".to_string()
        } else if risk_score > 0.20 {
            "MEDIUM".to_string()
        } else {
            "LOW".to_string()
        }
    }

    /// Find optimal hedge strikes for delta neutralization
    pub fn find_hedge_strikes(
        &self,
        position: &Position,
        underlying_price: f64,
        iv: f64,
    ) -> (f64, f64) {
        let calc = BlackScholesCalculator::new(underlying_price, 0.045);

        // If position is long delta, we sell call spreads
        // If position is short delta, we sell put spreads
        if position.current_delta > 0.0 {
            // Find strikes that create -delta hedge
            let short_strike = underlying_price.round();
            let long_strike = (underlying_price + 5.0).round();
            (short_strike, long_strike)
        } else {
            let short_strike = (underlying_price - 5.0).round();
            let long_strike = (underlying_price - 10.0).round();
            (short_strike, long_strike)
        }
    }
}

impl Default for RepairEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_position_analysis() {
        let engine = RepairEngine::new();
        let position = Position {
            id: "pos_001".to_string(),
            ticker: "AAPL".to_string(),
            strategy_type: "BULL_PUT_SPREAD".to_string(),
            current_delta: 0.35,
            current_gamma: 0.02,
            current_theta: 1.5,
            current_vega: 0.8,
            current_price: 95.0,
            max_loss: 500.0,
            unrealized_pnl: -150.0,
            days_to_expiration: 21,
        };

        let plan = engine.analyze_position(&position, 10000.0);
        assert!(plan.is_some());

        let plan = plan.unwrap();
        assert_eq!(plan.priority, "MEDIUM");
        assert!(plan.repair_credit > 0.0);
    }

    #[test]
    fn test_batch_analysis() {
        let engine = RepairEngine::new();
        let positions = vec![
            Position {
                id: "pos_001".to_string(),
                ticker: "AAPL".to_string(),
                strategy_type: "BULL_PUT_SPREAD".to_string(),
                current_delta: 0.35,
                current_gamma: 0.02,
                current_theta: 1.5,
                current_vega: 0.8,
                current_price: 95.0,
                max_loss: 500.0,
                unrealized_pnl: -150.0,
                days_to_expiration: 21,
            },
            Position {
                id: "pos_002".to_string(),
                ticker: "MSFT".to_string(),
                strategy_type: "CALL_SPREAD".to_string(),
                current_delta: -0.40,
                current_gamma: 0.01,
                current_theta: 2.0,
                current_vega: 0.9,
                current_price: 350.0,
                max_loss: 1000.0,
                unrealized_pnl: -200.0,
                days_to_expiration: 14,
            },
        ];

        let repairs = engine.batch_analyze(&positions, 15000.0);
        assert!(repairs.len() >= 1);
    }
}
