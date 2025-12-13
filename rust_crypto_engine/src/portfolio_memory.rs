// src/portfolio_memory.rs
// Portfolio Memory Engine (PME) - User-specific adaptive quant coach
// Tracks patterns, learns preferences, provides personalized guidance

use std::collections::HashMap;
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeRecord {
    pub user_id: String,
    pub symbol: String,
    pub strategy_type: String, // "Long Call", "Bull Call Spread", "Straddle", etc.
    pub entry_price: f64,
    pub exit_price: Option<f64>,
    pub pnl: Option<f64>,
    pub pnl_pct: Option<f64>,
    pub entry_iv: f64,
    pub days_to_expiration: i32,
    pub position_size: f64, // dollar notional
    pub risk_fraction: f64, // % of portfolio at risk
    pub timestamp: DateTime<Utc>,
    pub exit_timestamp: Option<DateTime<Utc>>,
    pub outcome: Option<TradeOutcome>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TradeOutcome {
    Win,
    Loss,
    Breakeven,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserProfile {
    pub user_id: String,
    pub total_trades: usize,
    pub win_rate: f64,
    pub avg_win: f64,
    pub avg_loss: f64,
    pub profit_factor: f64, // avg_win / avg_loss
    pub preferred_strategies: HashMap<String, f64>, // strategy -> win rate
    pub iv_regime_preferences: HashMap<String, f64>, // "Low" | "Medium" | "High" -> avg PnL
    pub dte_preferences: HashMap<String, f64>, // "0-7" | "8-30" | "31-60" | "60+" -> win rate
    pub sizing_patterns: SizingPatterns,
    pub risk_warnings: Vec<String>,
    pub strengths: Vec<String>,
    pub weaknesses: Vec<String>,
    pub last_updated: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SizingPatterns {
    pub avg_position_size_pct: f64, // average % of portfolio per trade
    pub max_position_size_pct: f64,
    pub tends_to_oversize: bool,
    pub tends_to_undersize: bool,
    pub iv_aware_sizing: bool, // adjusts size based on IV
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersonalizedRecommendation {
    pub user_id: String,
    pub symbol: String,
    pub strategy_suggestion: String,
    pub sizing_advice: String,
    pub risk_warning: Option<String>,
    pub confidence: f64,
    pub reasoning: String,
    pub timestamp: DateTime<Utc>,
}

pub struct PortfolioMemoryEngine {
    // In-memory store (in production, use Postgres/Redis)
    trades: Arc<RwLock<HashMap<String, Vec<TradeRecord>>>>, // user_id -> trades
    profiles: Arc<RwLock<HashMap<String, UserProfile>>>, // user_id -> profile
}

impl PortfolioMemoryEngine {
    pub fn new() -> Self {
        Self {
            trades: Arc::new(RwLock::new(HashMap::new())),
            profiles: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Record a new trade (entry)
    pub async fn record_trade(&self, trade: TradeRecord) -> anyhow::Result<()> {
        let mut trades = self.trades.write().await;
        trades
            .entry(trade.user_id.clone())
            .or_insert_with(Vec::new)
            .push(trade.clone());

        // Update profile asynchronously
        self.update_profile(&trade.user_id).await?;

        Ok(())
    }

    /// Record trade exit (update PnL)
    pub async fn record_exit(
        &self,
        user_id: &str,
        trade_id: Option<String>, // If None, use most recent open trade
        exit_price: f64,
        outcome: TradeOutcome,
    ) -> anyhow::Result<()> {
        let mut trades = self.trades.write().await;
        if let Some(user_trades) = trades.get_mut(user_id) {
            // Find the trade to update
            let trade = if let Some(id) = trade_id {
                user_trades.iter_mut().find(|t| {
                    // Simple matching - in production, use proper trade IDs
                    t.symbol == id || t.timestamp.to_rfc3339() == id
                })
            } else {
                // Find most recent open trade
                user_trades
                    .iter_mut()
                    .filter(|t| t.exit_price.is_none())
                    .max_by_key(|t| t.timestamp)
            };

            if let Some(trade) = trade {
                trade.exit_price = Some(exit_price);
                trade.exit_timestamp = Some(Utc::now());
                trade.outcome = Some(outcome.clone());

                // Calculate PnL
                let pnl = exit_price - trade.entry_price;
                let pnl_pct = (pnl / trade.entry_price) * 100.0;
                trade.pnl = Some(pnl);
                trade.pnl_pct = Some(pnl_pct);
            }
        }

        // Update profile
        self.update_profile(user_id).await?;

        Ok(())
    }

    /// Get personalized recommendation for a user
    pub async fn get_recommendation(
        &self,
        user_id: &str,
        symbol: &str,
        proposed_strategy: &str,
        proposed_size: f64,
        account_equity: f64,
        current_iv: f64,
        dte: i32,
    ) -> anyhow::Result<PersonalizedRecommendation> {
        let profile = self.get_profile(user_id).await?;

        // Analyze user's history with this strategy
        let strategy_win_rate = profile
            .preferred_strategies
            .get(proposed_strategy)
            .copied()
            .unwrap_or(0.5);

        // Check IV regime preference
        let iv_regime = if current_iv < 0.20 {
            "Low"
        } else if current_iv < 0.40 {
            "Medium"
        } else {
            "High"
        };
        let iv_performance = profile
            .iv_regime_preferences
            .get(iv_regime)
            .copied()
            .unwrap_or(0.0);

        // Check DTE preference
        let dte_bucket = if dte <= 7 {
            "0-7"
        } else if dte <= 30 {
            "8-30"
        } else if dte <= 60 {
            "31-60"
        } else {
            "60+"
        };
        let dte_win_rate = profile
            .dte_preferences
            .get(dte_bucket)
            .copied()
            .unwrap_or(0.5);

        // Build recommendation
        let mut reasoning = Vec::new();
        let mut confidence: f64 = 0.7; // base confidence

        // Strategy match
        if strategy_win_rate > 0.6 {
            reasoning.push(format!(
                "You have a {:.1}% win rate with {} strategies",
                strategy_win_rate * 100.0,
                proposed_strategy
            ));
            confidence += 0.1;
        } else if strategy_win_rate < 0.4 {
            reasoning.push(format!(
                "Warning: Your win rate with {} strategies is only {:.1}%",
                proposed_strategy,
                strategy_win_rate * 100.0
            ));
            confidence -= 0.2;
        }

        // IV regime
        if iv_performance > 0.0 {
            reasoning.push(format!(
                "You perform well in {} IV regimes (avg +{:.1}%)",
                iv_regime,
                iv_performance * 100.0
            ));
        } else if iv_performance < -0.1 {
            reasoning.push(format!(
                "Caution: You tend to lose money in {} IV regimes",
                iv_regime
            ));
            confidence -= 0.1;
        }

        // DTE preference
        if dte_win_rate > 0.6 {
            reasoning.push(format!(
                "You excel with {}-day options ({}% win rate)",
                dte_bucket,
                dte_win_rate * 100.0
            ));
            confidence += 0.05;
        }

        // Sizing check
        let size_pct = (proposed_size / account_equity) * 100.0;
        let sizing_advice = if size_pct > profile.sizing_patterns.max_position_size_pct {
            format!(
                "This position ({:.1}%) exceeds your typical max ({:.1}%)",
                size_pct,
                profile.sizing_patterns.max_position_size_pct
            )
        } else if profile.sizing_patterns.tends_to_oversize && size_pct > profile.sizing_patterns.avg_position_size_pct * 1.5 {
            format!(
                "You tend to oversize positions. Consider reducing to {:.1}%",
                profile.sizing_patterns.avg_position_size_pct
            )
        } else {
            format!("Position size ({:.1}%) looks appropriate", size_pct)
        };

        // Risk warning
        let risk_warning = if dte <= 7 && profile.total_trades < 20 {
            Some("0DTE options are high risk. Consider waiting until you have more experience.".to_string())
        } else if current_iv > 0.50 && iv_performance < -0.15 {
            Some("Extremely high IV detected. You've struggled in this regime before.".to_string())
        } else if size_pct > 0.10 {
            Some(format!("Large position size ({:.1}%) - ensure you can handle the risk", size_pct))
        } else {
            None
        };

        confidence = confidence.max(0.0).min(1.0);

        Ok(PersonalizedRecommendation {
            user_id: user_id.to_string(),
            symbol: symbol.to_string(),
            strategy_suggestion: proposed_strategy.to_string(),
            sizing_advice,
            risk_warning,
            confidence,
            reasoning: reasoning.join(" • "),
            timestamp: Utc::now(),
        })
    }

    /// Get user profile
    pub async fn get_profile(&self, user_id: &str) -> anyhow::Result<UserProfile> {
        let profiles = self.profiles.read().await;
        if let Some(profile) = profiles.get(user_id) {
            Ok(profile.clone())
        } else {
            // Return default profile for new users
            Ok(UserProfile {
                user_id: user_id.to_string(),
                total_trades: 0,
                win_rate: 0.5,
                avg_win: 0.0,
                avg_loss: 0.0,
                profit_factor: 1.0,
                preferred_strategies: HashMap::new(),
                iv_regime_preferences: HashMap::new(),
                dte_preferences: HashMap::new(),
                sizing_patterns: SizingPatterns {
                    avg_position_size_pct: 2.0,
                    max_position_size_pct: 5.0,
                    tends_to_oversize: false,
                    tends_to_undersize: false,
                    iv_aware_sizing: false,
                },
                risk_warnings: Vec::new(),
                strengths: Vec::new(),
                weaknesses: Vec::new(),
                last_updated: Utc::now(),
            })
        }
    }

    /// Update user profile from trade history
    async fn update_profile(&self, user_id: &str) -> anyhow::Result<()> {
        let trades = self.trades.read().await;
        let user_trades = trades.get(user_id).cloned().unwrap_or_default();
        drop(trades);

        if user_trades.is_empty() {
            return Ok(());
        }

        // Calculate metrics
        let closed_trades: Vec<_> = user_trades
            .iter()
            .filter(|t| t.outcome.is_some())
            .collect();

        let total_trades = closed_trades.len();
        if total_trades == 0 {
            return Ok(());
        }

        let wins = closed_trades
            .iter()
            .filter(|t| t.outcome == Some(TradeOutcome::Win))
            .count();
        let win_rate = wins as f64 / total_trades as f64;

        let winning_trades: Vec<f64> = closed_trades
            .iter()
            .filter_map(|t| {
                if t.outcome == Some(TradeOutcome::Win) {
                    t.pnl_pct
                } else {
                    None
                }
            })
            .collect();
        let avg_win = if !winning_trades.is_empty() {
            winning_trades.iter().sum::<f64>() / winning_trades.len() as f64
        } else {
            0.0
        };

        let losing_trades: Vec<f64> = closed_trades
            .iter()
            .filter_map(|t| {
                if t.outcome == Some(TradeOutcome::Loss) {
                    t.pnl_pct.map(|p| p.abs())
                } else {
                    None
                }
            })
            .collect();
        let avg_loss = if !losing_trades.is_empty() {
            losing_trades.iter().sum::<f64>() / losing_trades.len() as f64
        } else {
            1.0
        };

        let profit_factor = if avg_loss > 0.0 { avg_win / avg_loss } else { 0.0 };

        // Strategy preferences
        let mut strategy_wins: HashMap<String, (usize, usize)> = HashMap::new();
        for trade in &closed_trades {
            let entry = strategy_wins
                .entry(trade.strategy_type.clone())
                .or_insert((0, 0));
            entry.1 += 1;
            if trade.outcome == Some(TradeOutcome::Win) {
                entry.0 += 1;
            }
        }
        let preferred_strategies: HashMap<String, f64> = strategy_wins
            .into_iter()
            .map(|(k, (wins, total))| (k, wins as f64 / total as f64))
            .collect();

        // IV regime preferences
        let mut iv_performance: HashMap<String, Vec<f64>> = HashMap::new();
        for trade in &closed_trades {
            let regime = if trade.entry_iv < 0.20 {
                "Low"
            } else if trade.entry_iv < 0.40 {
                "Medium"
            } else {
                "High"
            };
            if let Some(pnl) = trade.pnl_pct {
                iv_performance
                    .entry(regime.to_string())
                    .or_insert_with(Vec::new)
                    .push(pnl);
            }
        }
        let iv_regime_preferences: HashMap<String, f64> = iv_performance
            .into_iter()
            .map(|(k, v)| (k, v.iter().sum::<f64>() / v.len() as f64))
            .collect();

        // DTE preferences
        let mut dte_wins: HashMap<String, (usize, usize)> = HashMap::new();
        for trade in &closed_trades {
            let bucket = if trade.days_to_expiration <= 7 {
                "0-7"
            } else if trade.days_to_expiration <= 30 {
                "8-30"
            } else if trade.days_to_expiration <= 60 {
                "31-60"
            } else {
                "60+"
            };
            let entry = dte_wins.entry(bucket.to_string()).or_insert((0, 0));
            entry.1 += 1;
            if trade.outcome == Some(TradeOutcome::Win) {
                entry.0 += 1;
            }
        }
        let dte_preferences: HashMap<String, f64> = dte_wins
            .into_iter()
            .map(|(k, (wins, total))| (k, wins as f64 / total as f64))
            .collect();

        // Sizing patterns
        let position_sizes: Vec<f64> = user_trades
            .iter()
            .map(|t| (t.position_size / 10000.0) * 100.0) // Assume $10k base, convert to %
            .collect();
        let avg_position_size_pct = if !position_sizes.is_empty() {
            position_sizes.iter().sum::<f64>() / position_sizes.len() as f64
        } else {
            2.0
        };
        let max_position_size_pct = position_sizes
            .iter()
            .copied()
            .fold(0.0, f64::max)
            .max(5.0);

        // Identify strengths and weaknesses
        let mut strengths = Vec::new();
        let mut weaknesses = Vec::new();

        if win_rate > 0.6 {
            strengths.push("Strong win rate".to_string());
        }
        if profit_factor > 2.0 {
            strengths.push("Excellent profit factor".to_string());
        }
        if let Some((best_strategy, rate)) = preferred_strategies
            .iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
        {
            if *rate > 0.65 {
                strengths.push(format!("Excel at {} strategies", best_strategy));
            }
        }

        if win_rate < 0.4 {
            weaknesses.push("Low win rate - consider adjusting strategy".to_string());
        }
        if profit_factor < 1.0 {
            weaknesses.push("Losing money on average - review risk management".to_string());
        }
        if avg_position_size_pct > 8.0 {
            weaknesses.push("Tendency to oversize positions".to_string());
        }

        let profile = UserProfile {
            user_id: user_id.to_string(),
            total_trades,
            win_rate,
            avg_win,
            avg_loss,
            profit_factor,
            preferred_strategies,
            iv_regime_preferences,
            dte_preferences,
            sizing_patterns: SizingPatterns {
                avg_position_size_pct,
                max_position_size_pct,
                tends_to_oversize: avg_position_size_pct > 5.0,
                tends_to_undersize: avg_position_size_pct < 1.0,
                iv_aware_sizing: false, // TODO: detect from IV vs size correlation
            },
            risk_warnings: Vec::new(),
            strengths,
            weaknesses,
            last_updated: Utc::now(),
        };

        let mut profiles = self.profiles.write().await;
        profiles.insert(user_id.to_string(), profile);

        Ok(())
    }
}

