// src/quant_terminal.rs
// Phase 3: RichesReach Quant Terminal
// Vol surface heatmaps, edge decay curves, regime timeline, portfolio DNA

use std::collections::HashMap;
use chrono::{DateTime, Utc, NaiveDate};
use serde::{Serialize, Deserialize};
use std::sync::Arc;
use tokio::sync::RwLock;

use crate::backtesting::BacktestingEngine;
use crate::regime::MarketRegimeEngine;
use crate::portfolio_memory::PortfolioMemoryEngine;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VolSurfaceHeatmap {
    pub symbol: String,
    pub strikes: Vec<f64>,
    pub expirations: Vec<String>, // ISO date strings
    pub iv_matrix: Vec<Vec<f64>>, // [strike][expiration] -> IV
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EdgeDecayCurve {
    pub strategy_name: String,
    pub symbol: String,
    pub time_points: Vec<DateTime<Utc>>,
    pub edge_values: Vec<f64>, // Edge at each time point
    pub confidence_values: Vec<f64>, // Confidence at each time point
    pub decay_rate: f64, // % per day
    pub half_life_days: f64, // Days until edge drops to 50%
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegimeTimeline {
    pub start_date: NaiveDate,
    pub end_date: NaiveDate,
    pub events: Vec<RegimeEvent>,
    pub transitions: Vec<RegimeTransition>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegimeEvent {
    pub date: NaiveDate,
    pub regime: String, // "RiskOn", "RiskOff", etc.
    pub headline: String,
    pub confidence: f64,
    pub market_impact: f64, // 0-1 scale
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegimeTransition {
    pub from: String,
    pub to: String,
    pub date: NaiveDate,
    pub duration_days: i64,
    pub volatility_spike: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PortfolioDNA {
    pub user_id: String,
    pub fingerprint: PortfolioFingerprint,
    pub archetype: String, // "Renaissance", "Jim Simons", "Warren Buffett", etc.
    pub archetype_breakdown: HashMap<String, f64>, // archetype -> percentage
    pub strengths: Vec<String>,
    pub weaknesses: Vec<String>,
    pub recommendations: Vec<String>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PortfolioFingerprint {
    pub win_rate: f64,
    pub profit_factor: f64,
    pub avg_holding_period_days: f64,
    pub preferred_iv_regime: String, // "Low", "Medium", "High"
    pub preferred_dte_range: String, // "0-7", "8-30", etc.
    pub risk_tolerance: f64, // 0-1
    pub strategy_preferences: HashMap<String, f64>, // strategy -> weight
    pub sharpe_ratio: f64,
    pub max_drawdown: f64,
    pub total_trades: usize,
    pub best_performing_strategy: String,
    pub worst_performing_strategy: String,
}

pub struct QuantTerminal {
    backtesting_engine: Arc<BacktestingEngine>,
    regime_engine: MarketRegimeEngine,
    portfolio_memory: Arc<PortfolioMemoryEngine>,
}

impl QuantTerminal {
    pub fn new(
        backtesting_engine: Arc<BacktestingEngine>,
        regime_engine: MarketRegimeEngine,
        portfolio_memory: Arc<PortfolioMemoryEngine>,
    ) -> Self {
        Self {
            backtesting_engine,
            regime_engine,
            portfolio_memory,
        }
    }

    /// Generate volatility surface heatmap for options
    pub async fn generate_vol_surface_heatmap(
        &self,
        symbol: &str,
    ) -> anyhow::Result<VolSurfaceHeatmap> {
        // In production, this would fetch real options chain data
        // For now, generate a realistic mock surface
        
        let strikes = vec![
            90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0,
        ];
        
        let expirations = vec![
            "2024-02-16".to_string(),
            "2024-03-15".to_string(),
            "2024-04-19".to_string(),
            "2024-06-21".to_string(),
        ];

        // Generate IV matrix: higher IV for OTM and near-term
        let mut iv_matrix = Vec::new();
        for strike in &strikes {
            let mut row = Vec::new();
            for (exp_idx, _) in expirations.iter().enumerate() {
                // ATM has lower IV, OTM has higher (volatility smile)
                let diff: f64 = strike - 100.0; // Assuming spot = 100
                let moneyness: f64 = (diff / 100.0).abs();
                let time_to_exp = (exp_idx + 1) as f64 * 0.25; // Fraction of year
                
                let base_iv = 0.20; // 20% base
                let smile_adjustment = (moneyness * 0.10).min(0.15); // Volatility smile
                let term_structure = 0.05 * (1.0 - time_to_exp.min(1.0)); // Higher IV for near-term
                
                let iv = base_iv + smile_adjustment + term_structure;
                row.push(iv);
            }
            iv_matrix.push(row);
        }

        Ok(VolSurfaceHeatmap {
            symbol: symbol.to_string(),
            strikes,
            expirations,
            iv_matrix,
            timestamp: Utc::now(),
        })
    }

    /// Calculate edge decay curve for a strategy
    pub async fn calculate_edge_decay(
        &self,
        strategy_name: &str,
        symbol: &str,
    ) -> anyhow::Result<EdgeDecayCurve> {
        // Get strategy score to determine current edge
        let score = self.backtesting_engine
            .get_strategy_score(strategy_name, symbol)
            .await?;

        let current_edge = score
            .as_ref()
            .and_then(|s| Some(s.overall_score / 100.0))
            .unwrap_or(0.5);

        // Generate time series (last 30 days)
        let mut time_points = Vec::new();
        let mut edge_values = Vec::new();
        let mut confidence_values = Vec::new();

        for days_ago in (0..30).rev() {
            let date = Utc::now() - chrono::Duration::days(days_ago);
            time_points.push(date);

            // Simulate exponential decay
            let decay_factor = (-0.05 * days_ago as f64).exp(); // 5% decay per day
            let edge = current_edge * decay_factor;
            edge_values.push(edge);

            // Confidence also decays
            let confidence = (0.8 * decay_factor).min(1.0);
            confidence_values.push(confidence);
        }

        // Calculate decay metrics
        let decay_rate = 0.05; // 5% per day
        let half_life_days = (0.5_f64.ln() / -decay_rate).max(1.0);

        Ok(EdgeDecayCurve {
            strategy_name: strategy_name.to_string(),
            symbol: symbol.to_string(),
            time_points,
            edge_values,
            confidence_values,
            decay_rate,
            half_life_days,
            timestamp: Utc::now(),
        })
    }

    /// Generate regime timeline
    pub async fn generate_regime_timeline(
        &self,
        start_date: NaiveDate,
        end_date: NaiveDate,
    ) -> anyhow::Result<RegimeTimeline> {
        // Get current regime
        let current_regime = self.regime_engine.analyze_simple().await?;

        // Generate historical events (in production, this would query historical data)
        let mut events = Vec::new();
        let mut transitions = Vec::new();

        // Sample events (in production, derive from actual historical data)
        let sample_dates = vec![
            (start_date, "RiskOff", "Market correction begins", 0.9, 0.8),
            (start_date + chrono::Duration::days(7), "ExtremeFear", "Panic selling", 0.95, 0.9),
            (start_date + chrono::Duration::days(14), "RiskOff", "Recovery attempt", 0.7, 0.6),
            (start_date + chrono::Duration::days(21), "Neutral", "Stabilization", 0.6, 0.4),
            (end_date, current_regime.headline.as_str(), "Current regime", current_regime.confidence, 0.5),
        ];

        for (date, regime, headline, confidence, impact) in sample_dates {
            events.push(RegimeEvent {
                date,
                regime: regime.to_string(),
                headline: headline.to_string(),
                confidence,
                market_impact: impact,
            });
        }

        // Generate transitions
        for i in 0..events.len() - 1 {
            let from_event = &events[i];
            let to_event = &events[i + 1];
            
            if from_event.regime != to_event.regime {
                transitions.push(RegimeTransition {
                    from: from_event.regime.clone(),
                    to: to_event.regime.clone(),
                    date: to_event.date,
                    duration_days: (to_event.date - from_event.date).num_days(),
                    volatility_spike: (to_event.market_impact - from_event.market_impact).abs(),
                });
            }
        }

        Ok(RegimeTimeline {
            start_date,
            end_date,
            events,
            transitions,
            timestamp: Utc::now(),
        })
    }

    /// Generate portfolio DNA fingerprint
    pub async fn generate_portfolio_dna(
        &self,
        user_id: &str,
    ) -> anyhow::Result<PortfolioDNA> {
        // Get user profile
        let profile = self.portfolio_memory.get_profile(user_id).await?;

        // Compute derived metrics from profile
        let avg_holding_period_days = profile.dte_preferences
            .iter()
            .map(|(range, _)| {
                // Parse range like "0-7", "8-30", etc. to get average
                if range.contains("-") {
                    let parts: Vec<&str> = range.split("-").collect();
                    if parts.len() == 2 {
                        let start: f64 = parts[0].parse().unwrap_or(0.0);
                        let end: f64 = parts[1].parse().unwrap_or(0.0);
                        (start + end) / 2.0
                    } else {
                        30.0 // default
                    }
                } else if range == "60+" {
                    90.0
                } else {
                    30.0
                }
            })
            .sum::<f64>() / profile.dte_preferences.len().max(1) as f64;

        // Find preferred IV regime (highest avg PnL)
        let preferred_iv_regime = profile.iv_regime_preferences
            .iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
            .map(|(k, _)| k.clone())
            .unwrap_or_else(|| "Medium".to_string());

        // Find preferred DTE range (highest win rate)
        let preferred_dte_range = profile.dte_preferences
            .iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
            .map(|(k, _)| k.clone())
            .unwrap_or_else(|| "8-30".to_string());

        // Find best/worst performing strategies
        let best_performing_strategy = profile.preferred_strategies
            .iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
            .map(|(k, _)| k.clone())
            .unwrap_or_else(|| "Unknown".to_string());

        let worst_performing_strategy = profile.preferred_strategies
            .iter()
            .min_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
            .map(|(k, _)| k.clone())
            .unwrap_or_else(|| "Unknown".to_string());

        // Estimate risk tolerance from sizing patterns
        let risk_tolerance = if profile.sizing_patterns.tends_to_oversize {
            0.8
        } else if profile.sizing_patterns.tends_to_undersize {
            0.3
        } else {
            0.5
        };

        // Estimate Sharpe and max drawdown (would need trade history for real values)
        let sharpe_ratio = if profile.profit_factor > 1.5 && profile.win_rate > 0.55 {
            1.5
        } else if profile.profit_factor > 1.0 && profile.win_rate > 0.5 {
            0.8
        } else {
            0.3
        };

        let max_drawdown = if profile.win_rate < 0.4 {
            0.5
        } else if profile.win_rate < 0.5 {
            0.3
        } else {
            0.2
        };

        // Build fingerprint
        let fingerprint = PortfolioFingerprint {
            win_rate: profile.win_rate,
            profit_factor: profile.profit_factor,
            avg_holding_period_days,
            preferred_iv_regime,
            preferred_dte_range,
            risk_tolerance,
            strategy_preferences: profile.preferred_strategies.clone(),
            sharpe_ratio,
            max_drawdown,
            total_trades: profile.total_trades,
            best_performing_strategy,
            worst_performing_strategy,
        };

        // Determine archetype
        let mut archetype_scores: HashMap<String, f64> = HashMap::new();

        // Renaissance-style: High Sharpe, systematic, many trades
        let renaissance_score = (
            (fingerprint.sharpe_ratio / 2.0).min(1.0) * 0.4 +
            (fingerprint.total_trades as f64 / 1000.0).min(1.0) * 0.3 +
            (1.0 - fingerprint.max_drawdown).min(1.0) * 0.3
        );
        archetype_scores.insert("Renaissance".to_string(), renaissance_score);

        // Jim Simons-style: Very high Sharpe, quantitative, short holding periods
        let simons_score = (
            (fingerprint.sharpe_ratio / 3.0).min(1.0) * 0.5 +
            (1.0 / (fingerprint.avg_holding_period_days + 1.0)).min(1.0) * 0.5
        );
        archetype_scores.insert("Jim Simons".to_string(), simons_score);

        // Warren Buffett-style: High win rate, long holding, value-focused
        let buffett_score = (
            fingerprint.win_rate * 0.4 +
            (fingerprint.avg_holding_period_days / 365.0).min(1.0) * 0.4 +
            (1.0 - fingerprint.max_drawdown).min(1.0) * 0.2
        );
        archetype_scores.insert("Warren Buffett".to_string(), buffett_score);

        // Normalize archetype breakdown first
        let total: f64 = archetype_scores.values().sum();
        let archetype_breakdown: HashMap<String, f64> = archetype_scores
            .iter()
            .map(|(k, v)| (k.clone(), if total > 0.0 { v / total } else { 0.0 }))
            .collect();
        
        // Find dominant archetype
        let archetype = archetype_breakdown
            .iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
            .map(|(k, _)| k.clone())
            .unwrap_or_else(|| "Balanced".to_string());

        // Generate strengths and weaknesses
        let mut strengths = Vec::new();
        let mut weaknesses = Vec::new();

        if fingerprint.win_rate > 0.6 {
            strengths.push("High win rate".to_string());
        } else if fingerprint.win_rate < 0.4 {
            weaknesses.push("Low win rate".to_string());
        }

        if fingerprint.profit_factor > 1.5 {
            strengths.push("Strong profit factor".to_string());
        } else if fingerprint.profit_factor < 1.0 {
            weaknesses.push("Profit factor below 1.0".to_string());
        }

        if fingerprint.sharpe_ratio > 1.5 {
            strengths.push("Excellent risk-adjusted returns".to_string());
        } else if fingerprint.sharpe_ratio < 0.5 {
            weaknesses.push("Low risk-adjusted returns".to_string());
        }

        if fingerprint.max_drawdown < 0.2 {
            strengths.push("Low drawdowns".to_string());
        } else if fingerprint.max_drawdown > 0.5 {
            weaknesses.push("High drawdowns".to_string());
        }

        // Generate recommendations
        let mut recommendations = Vec::new();
        
        if fingerprint.win_rate < 0.5 {
            recommendations.push("Focus on improving win rate through better entry timing".to_string());
        }
        
        if fingerprint.max_drawdown > 0.3 {
            recommendations.push("Consider reducing position sizes to limit drawdowns".to_string());
        }
        
        if fingerprint.avg_holding_period_days < 7.0 {
            recommendations.push("Consider longer holding periods for better risk/reward".to_string());
        }

        Ok(PortfolioDNA {
            user_id: user_id.to_string(),
            fingerprint,
            archetype: archetype.clone(),
            archetype_breakdown,
            strengths,
            weaknesses,
            recommendations,
            timestamp: Utc::now(),
        })
    }
}

