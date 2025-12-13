// src/backtesting.rs
// Backtesting + Live Scoring Engine
// Historical validation and performance metrics for all strategies

use std::collections::HashMap;
use chrono::{DateTime, Utc, NaiveDate};
use serde::{Serialize, Deserialize};
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestConfig {
    pub start_date: NaiveDate,
    pub end_date: NaiveDate,
    pub initial_capital: f64,
    pub commission_per_trade: f64,
    pub slippage_pct: f64, // e.g., 0.001 = 0.1%
}

impl Default for BacktestConfig {
    fn default() -> Self {
        Self {
            start_date: NaiveDate::from_ymd_opt(2018, 1, 1).unwrap(),
            end_date: Utc::now().date_naive(),
            initial_capital: 10_000.0,
            commission_per_trade: 0.65,
            slippage_pct: 0.001,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestResult {
    pub strategy_name: String,
    pub symbol: String,
    pub start_date: NaiveDate,
    pub end_date: NaiveDate,
    pub total_trades: usize,
    pub winning_trades: usize,
    pub losing_trades: usize,
    pub win_rate: f64,
    pub total_return: f64,
    pub total_return_pct: f64,
    pub max_drawdown: f64,
    pub max_drawdown_pct: f64,
    pub sharpe_ratio: f64,
    pub profit_factor: f64,
    pub avg_win: f64,
    pub avg_loss: f64,
    pub largest_win: f64,
    pub largest_loss: f64,
    pub equity_curve: Vec<EquityPoint>,
    pub monthly_returns: HashMap<String, f64>, // "YYYY-MM" -> return %
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EquityPoint {
    pub date: NaiveDate,
    pub equity: f64,
    pub drawdown: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeSignal {
    pub date: NaiveDate,
    pub symbol: String,
    pub strategy_type: String,
    pub entry_price: f64,
    pub exit_price: Option<f64>,
    pub exit_date: Option<NaiveDate>,
    pub quantity: i32,
    pub direction: String, // "long" | "short"
    pub pnl: Option<f64>,
    pub pnl_pct: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyScore {
    pub strategy_name: String,
    pub symbol: String,
    pub overall_score: f64, // 0-100
    pub sharpe_score: f64,
    pub win_rate_score: f64,
    pub profit_factor_score: f64,
    pub drawdown_score: f64,
    pub recent_performance_score: f64, // Last 30 days
    pub edge_decay_detected: bool,
    pub recommendation: String, // "STRONG BUY" | "BUY" | "NEUTRAL" | "AVOID"
    pub backtest_result: Option<BacktestResult>,
    pub timestamp: DateTime<Utc>,
}

pub struct BacktestingEngine {
    // In production, this would connect to historical data provider
    // For now, we'll use in-memory storage
    signals: Arc<RwLock<Vec<TradeSignal>>>,
    results: Arc<RwLock<HashMap<String, BacktestResult>>>, // strategy_symbol -> result
}

impl BacktestingEngine {
    pub fn new() -> Self {
        Self {
            signals: Arc::new(RwLock::new(Vec::new())),
            results: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Run backtest on a strategy
    pub async fn run_backtest(
        &self,
        strategy_name: &str,
        symbol: &str,
        signals: Vec<TradeSignal>,
        config: BacktestConfig,
    ) -> anyhow::Result<BacktestResult> {
        let mut equity = config.initial_capital;
        let mut max_equity = equity;
        let mut max_drawdown: f64 = 0.0;
        let mut equity_curve = Vec::new();
        let mut monthly_returns: HashMap<String, f64> = HashMap::new();
        
        let mut winning_trades = 0;
        let mut losing_trades = 0;
        let mut total_win = 0.0;
        let mut total_loss = 0.0;
        let mut largest_win: f64 = 0.0;
        let mut largest_loss: f64 = 0.0;
        let mut returns = Vec::new();

        let mut current_month: Option<String> = None;
        let mut month_start_equity = equity;

        for signal in &signals {
            // Calculate PnL if exit exists
            if let (Some(exit_price), Some(exit_date)) = (signal.exit_price, signal.exit_date) {
                let pnl = match signal.direction.as_str() {
                    "long" => (exit_price - signal.entry_price) * signal.quantity as f64,
                    "short" => (signal.entry_price - exit_price) * signal.quantity as f64,
                    _ => 0.0,
                };

                // Apply commission and slippage
                let commission = config.commission_per_trade * 2.0; // entry + exit
                let slippage = (signal.entry_price + exit_price) * signal.quantity as f64 * config.slippage_pct;
                let net_pnl = pnl - commission - slippage;

                equity += net_pnl;
                let return_pct = net_pnl / equity;

                // Track monthly returns
                let month_key = format!("{}", exit_date.format("%Y-%m"));
                if current_month.as_ref() != Some(&month_key) {
                    if let Some(prev_month) = &current_month {
                        let month_return = (equity - month_start_equity) / month_start_equity;
                        monthly_returns.insert(prev_month.clone(), month_return);
                    }
                    current_month = Some(month_key.clone());
                    month_start_equity = equity;
                }

                // Track win/loss
                if net_pnl > 0.0 {
                    winning_trades += 1;
                    total_win += net_pnl;
                    largest_win = largest_win.max(net_pnl);
                } else {
                    losing_trades += 1;
                    total_loss += net_pnl.abs();
                    largest_loss = largest_loss.max(net_pnl.abs());
                }

                returns.push(return_pct);

                // Update drawdown
                if equity > max_equity {
                    max_equity = equity;
                }
                let drawdown = (max_equity - equity) / max_equity;
                max_drawdown = max_drawdown.max(drawdown);

                equity_curve.push(EquityPoint {
                    date: exit_date,
                    equity,
                    drawdown,
                });
            }
        }

        // Final month return
        if let Some(month) = &current_month {
            let month_return = (equity - month_start_equity) / month_start_equity;
            monthly_returns.insert(month.clone(), month_return);
        }

        // Calculate metrics
        let total_trades = winning_trades + losing_trades;
        let win_rate = if total_trades > 0 {
            winning_trades as f64 / total_trades as f64
        } else {
            0.0
        };

        let total_return = equity - config.initial_capital;
        let total_return_pct = (total_return / config.initial_capital) * 100.0;

        let avg_win = if winning_trades > 0 {
            total_win / winning_trades as f64
        } else {
            0.0
        };

        let avg_loss = if losing_trades > 0 {
            total_loss / losing_trades as f64
        } else {
            1.0
        };

        let profit_factor = if avg_loss > 0.0 {
            avg_win / avg_loss
        } else {
            0.0
        };

        // Calculate Sharpe ratio (simplified)
        let sharpe_ratio = if returns.len() > 1 {
            let mean_return: f64 = returns.iter().sum::<f64>() / returns.len() as f64;
            let variance: f64 = returns
                .iter()
                .map(|r| (r - mean_return).powi(2))
                .sum::<f64>()
                / returns.len() as f64;
            let std_dev = variance.sqrt();
            if std_dev > 0.0 {
                (mean_return / std_dev) * (252.0_f64).sqrt() // Annualized
            } else {
                0.0
            }
        } else {
            0.0
        };

        let result = BacktestResult {
            strategy_name: strategy_name.to_string(),
            symbol: symbol.to_string(),
            start_date: config.start_date,
            end_date: config.end_date,
            total_trades,
            winning_trades,
            losing_trades,
            win_rate,
            total_return,
            total_return_pct,
            max_drawdown,
            max_drawdown_pct: max_drawdown * 100.0,
            sharpe_ratio,
            profit_factor,
            avg_win,
            avg_loss,
            largest_win,
            largest_loss,
            equity_curve,
            monthly_returns,
            timestamp: Utc::now(),
        };

        // Store result
        let key = format!("{}::{}", strategy_name, symbol);
        let mut results = self.results.write().await;
        results.insert(key, result.clone());

        Ok(result)
    }

    /// Score a strategy based on backtest results
    pub async fn score_strategy(
        &self,
        strategy_name: &str,
        symbol: &str,
        backtest_result: &BacktestResult,
    ) -> anyhow::Result<StrategyScore> {
        // Score components (0-100 each)
        let sharpe_score = (backtest_result.sharpe_ratio * 10.0).min(100.0).max(0.0);
        let win_rate_score = backtest_result.win_rate * 100.0;
        let profit_factor_score = (backtest_result.profit_factor * 20.0).min(100.0).max(0.0);
        let drawdown_score = (100.0 - (backtest_result.max_drawdown_pct * 2.0)).max(0.0).min(100.0);

        // Recent performance (last 30 days or last 10% of trades)
        let recent_trades = (backtest_result.total_trades as f64 * 0.1).max(1.0) as usize;
        let recent_win_rate = if recent_trades > 0 {
            // Simplified: assume recent trades match overall win rate
            // In production, track actual recent performance
            backtest_result.win_rate
        } else {
            0.5
        };
        let recent_performance_score = recent_win_rate * 100.0;

        // Overall score (weighted average)
        let overall_score = (
            sharpe_score * 0.3 +
            win_rate_score * 0.25 +
            profit_factor_score * 0.25 +
            drawdown_score * 0.1 +
            recent_performance_score * 0.1
        );

        // Detect edge decay (simplified: if recent performance < 70% of historical)
        let edge_decay_detected = recent_performance_score < (win_rate_score * 0.7);

        // Recommendation
        let recommendation = if overall_score >= 80.0 && !edge_decay_detected {
            "STRONG BUY"
        } else if overall_score >= 65.0 && !edge_decay_detected {
            "BUY"
        } else if overall_score >= 50.0 {
            "NEUTRAL"
        } else {
            "AVOID"
        };

        Ok(StrategyScore {
            strategy_name: strategy_name.to_string(),
            symbol: symbol.to_string(),
            overall_score,
            sharpe_score,
            win_rate_score,
            profit_factor_score,
            drawdown_score,
            recent_performance_score,
            edge_decay_detected,
            recommendation: recommendation.to_string(),
            backtest_result: Some(backtest_result.clone()),
            timestamp: Utc::now(),
        })
    }

    /// Get strategy score (cached or compute)
    pub async fn get_strategy_score(
        &self,
        strategy_name: &str,
        symbol: &str,
    ) -> anyhow::Result<Option<StrategyScore>> {
        let key = format!("{}::{}", strategy_name, symbol);
        let results = self.results.read().await;
        
        if let Some(result) = results.get(&key) {
            let score = self.score_strategy(strategy_name, symbol, result).await?;
            Ok(Some(score))
        } else {
            Ok(None)
        }
    }

    /// Check if edge decay is detected for a strategy
    pub async fn check_edge_decay(
        &self,
        strategy_name: &str,
        symbol: &str,
    ) -> anyhow::Result<bool> {
        if let Some(score) = self.get_strategy_score(strategy_name, symbol).await? {
            Ok(score.edge_decay_detected)
        } else {
            Ok(false) // No data = no decay detected
        }
    }
}

