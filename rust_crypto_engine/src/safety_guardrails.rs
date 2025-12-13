// src/safety_guardrails.rs
// Safety & Guardrails Engine - Risk limits and user protection
// Keeps the system responsible and regulator-friendly

use std::sync::Arc;
use chrono::Utc;
use serde::{Serialize, Deserialize};

use crate::options_core::OneTapTrade;
use crate::portfolio_memory::PortfolioMemoryEngine;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafetyCheck {
    pub passed: bool,
    pub warnings: Vec<String>,
    pub blocks: Vec<String>,
    pub adjustments: Vec<TradeAdjustment>,
    pub confidence: f64, // 0.0-1.0, how safe this trade is
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeAdjustment {
    pub field: String, // "position_size", "stop_loss", "take_profit"
    pub original_value: f64,
    pub adjusted_value: f64,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafetyConfig {
    pub max_loss_per_trade_pct: f64, // e.g., 0.03 = 3% of portfolio
    pub max_total_risk_pct: f64, // e.g., 0.12 = 12% across all positions
    pub max_position_size_pct: f64, // e.g., 0.10 = 10% of portfolio
    pub high_iv_threshold: f64, // e.g., 0.50 = 50% IV
    pub require_confirmation_0dte: bool,
    pub require_confirmation_high_iv: bool,
    pub require_confirmation_large_size: bool,
    pub min_experience_for_0dte: usize, // min trades before allowing 0DTE
    pub max_spread_width_pct: f64, // max bid/ask spread as % of mid
}

impl Default for SafetyConfig {
    fn default() -> Self {
        Self {
            max_loss_per_trade_pct: 0.03, // 3%
            max_total_risk_pct: 0.12, // 12%
            max_position_size_pct: 0.10, // 10%
            high_iv_threshold: 0.50, // 50%
            require_confirmation_0dte: true,
            require_confirmation_high_iv: true,
            require_confirmation_large_size: true,
            min_experience_for_0dte: 20,
            max_spread_width_pct: 0.10, // 10% spread
        }
    }
}

pub struct SafetyGuardrailsEngine {
    config: SafetyConfig,
    pme: Arc<PortfolioMemoryEngine>,
}

impl SafetyGuardrailsEngine {
    pub fn new(config: SafetyConfig, pme: Arc<PortfolioMemoryEngine>) -> Self {
        Self { config, pme }
    }

    /// Run all safety checks on a proposed trade
    pub async fn check_trade(
        &self,
        user_id: &str,
        trade: &OneTapTrade,
        account_equity: f64,
        current_iv: f64,
        open_positions_risk: f64, // Total risk from existing positions
    ) -> anyhow::Result<SafetyCheck> {
        let mut warnings = Vec::new();
        let mut blocks = Vec::new();
        let mut adjustments = Vec::new();
        let mut confidence: f64 = 1.0;

        // ───────────────────── Position Size Check ─────────────────────
        let position_size_pct = (trade.total_cost / account_equity) * 100.0;
        if position_size_pct > self.config.max_position_size_pct {
            blocks.push(format!(
                "Position size ({:.1}%) exceeds maximum allowed ({:.1}%)",
                position_size_pct,
                self.config.max_position_size_pct * 100.0
            ));
            confidence = 0.0;
        } else if position_size_pct > self.config.max_position_size_pct * 0.8 {
            warnings.push(format!(
                "Large position size ({:.1}%) - ensure you can handle the risk",
                position_size_pct
            ));
            confidence -= 0.2;
        }

        // ───────────────────── Max Loss Check ─────────────────────
        let max_loss_pct = (trade.max_loss.abs() / account_equity) * 100.0;
        if max_loss_pct > self.config.max_loss_per_trade_pct * 100.0 {
            blocks.push(format!(
                "Maximum loss ({:.1}%) exceeds per-trade limit ({:.1}%)",
                max_loss_pct,
                self.config.max_loss_per_trade_pct * 100.0
            ));
            confidence = 0.0;
        } else if max_loss_pct > self.config.max_loss_per_trade_pct * 100.0 * 0.8 {
            warnings.push(format!(
                "High potential loss ({:.1}%) - consider reducing position size",
                max_loss_pct
            ));
            confidence -= 0.15;
        }

        // ───────────────────── Total Risk Check ─────────────────────
        let trade_risk = trade.max_loss.abs();
        let total_risk_pct = ((open_positions_risk + trade_risk) / account_equity) * 100.0;
        if total_risk_pct > self.config.max_total_risk_pct * 100.0 {
            blocks.push(format!(
                "Total portfolio risk ({:.1}%) would exceed limit ({:.1}%)",
                total_risk_pct,
                self.config.max_total_risk_pct * 100.0
            ));
            confidence = 0.0;
        } else if total_risk_pct > self.config.max_total_risk_pct * 100.0 * 0.8 {
            warnings.push(format!(
                "Approaching total risk limit ({:.1}% / {:.1}%)",
                total_risk_pct,
                self.config.max_total_risk_pct * 100.0
            ));
            confidence -= 0.1;
        }

        // ───────────────────── IV Check ─────────────────────
        if current_iv > self.config.high_iv_threshold {
            if self.config.require_confirmation_high_iv {
                warnings.push(format!(
                    "Extremely high IV ({:.1}%) - requires confirmation",
                    current_iv * 100.0
                ));
                confidence -= 0.3;
            } else {
                warnings.push(format!(
                    "High IV ({:.1}%) - options are expensive",
                    current_iv * 100.0
                ));
                confidence -= 0.1;
            }
        }

        // ───────────────────── 0DTE Check ─────────────────────
        if trade.days_to_expiration == 0 {
            let profile = self.pme.get_profile(user_id).await?;
            if profile.total_trades < self.config.min_experience_for_0dte {
                if self.config.require_confirmation_0dte {
                    blocks.push(format!(
                        "0DTE options require {}+ trades of experience (you have {})",
                        self.config.min_experience_for_0dte,
                        profile.total_trades
                    ));
                    confidence = 0.0;
                } else {
                    warnings.push(format!(
                        "0DTE options are extremely risky - you have limited experience ({} trades)",
                        profile.total_trades
                    ));
                    confidence -= 0.4;
                }
            } else {
                warnings.push("0DTE options are high risk - time decay is extreme".to_string());
                confidence -= 0.2;
            }
        }

        // ───────────────────── Spread Width Check ─────────────────────
        // For multi-leg strategies, check if spread width is reasonable
        if trade.legs.len() > 1 {
            // Calculate spread width (simplified)
            let total_premium: f64 = trade.legs.iter().map(|l| l.premium).sum();
            let mid_price = total_premium / trade.legs.len() as f64;
            // Assume 2% spread per leg (in production, get real bid/ask)
            let estimated_spread = mid_price * 0.02 * trade.legs.len() as f64;
            let spread_pct = (estimated_spread / mid_price) * 100.0;

            if spread_pct > self.config.max_spread_width_pct * 100.0 {
                warnings.push(format!(
                    "Wide bid/ask spread ({:.1}%) - execution may be poor",
                    spread_pct
                ));
                confidence -= 0.15;
            }
        }

        // ───────────────────── User-Specific Checks ─────────────────────
        let profile = self.pme.get_profile(user_id).await?;
        
        // Check if user tends to oversize
        if profile.sizing_patterns.tends_to_oversize && position_size_pct > profile.sizing_patterns.avg_position_size_pct {
            warnings.push(format!(
                "You tend to oversize positions - consider reducing to {:.1}%",
                profile.sizing_patterns.avg_position_size_pct
            ));
            confidence -= 0.1;
        }

        // Check strategy performance
        let strategy_win_rate = profile
            .preferred_strategies
            .get(&trade.strategy_type)
            .copied()
            .unwrap_or(0.5);
        if strategy_win_rate < 0.4 {
            warnings.push(format!(
                "Your win rate with {} strategies is only {:.1}%",
                trade.strategy_type,
                strategy_win_rate * 100.0
            ));
            confidence -= 0.2;
        }

        // ───────────────────── Auto-Adjustments ─────────────────────
        // If position is too large, suggest reduction
        if position_size_pct > self.config.max_position_size_pct * 0.9 && blocks.is_empty() {
            let suggested_size = account_equity * self.config.max_position_size_pct * 0.8;
            adjustments.push(TradeAdjustment {
                field: "position_size".to_string(),
                original_value: trade.total_cost,
                adjusted_value: suggested_size,
                reason: "Reduce to stay within safety limits".to_string(),
            });
            confidence -= 0.1;
        }

        // If max loss is too high, suggest tighter stop
        if max_loss_pct > self.config.max_loss_per_trade_pct * 100.0 * 0.9 && blocks.is_empty() {
            let suggested_stop = trade.entry_price * (1.0 - self.config.max_loss_per_trade_pct * 0.8);
            adjustments.push(TradeAdjustment {
                field: "stop_loss".to_string(),
                original_value: trade.stop_loss,
                adjusted_value: suggested_stop,
                reason: "Tighten stop to limit risk".to_string(),
            });
            confidence -= 0.1;
        }

        confidence = confidence.max(0.0).min(1.0);

        Ok(SafetyCheck {
            passed: blocks.is_empty(),
            warnings,
            blocks,
            adjustments,
            confidence,
        })
    }

    /// Check if trade requires user confirmation
    pub async fn requires_confirmation(
        &self,
        user_id: &str,
        trade: &OneTapTrade,
        current_iv: f64,
    ) -> bool {
        // 0DTE check
        if trade.days_to_expiration == 0 && self.config.require_confirmation_0dte {
            let profile = self.pme.get_profile(user_id).await.ok();
            if let Some(p) = profile {
                if p.total_trades < self.config.min_experience_for_0dte {
                    return true;
                }
            }
        }

        // High IV check
        if current_iv > self.config.high_iv_threshold && self.config.require_confirmation_high_iv {
            return true;
        }

        // Large size check
        if self.config.require_confirmation_large_size {
            // This would need account_equity, but for now just check if it's a large absolute value
            if trade.total_cost > 10_000.0 {
                return true;
            }
        }

        false
    }
}

