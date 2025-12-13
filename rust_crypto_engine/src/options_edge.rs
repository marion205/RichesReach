// src/options_edge.rs
// OptionsEdgeForecaster: Edge prediction + OneTap trades, fused with AlphaOracle + RegimeEngine
// Deterministic, no randomness, production-grade

use std::sync::Arc;
use anyhow::{Result, Context};
use chrono::Utc;
use serde::{Serialize, Deserialize};

use crate::options_core::*;
use crate::alpha_oracle::{AlphaOracle, AlphaSignal};
use crate::regime::{MarketRegimeEngine, SimpleMarketRegime};
use crate::market_data::provider::MarketDataProvider;
use crate::market_data::options_provider::OptionsDataProvider;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EdgeForecastResponse {
    pub symbol: String,
    pub chain: OptionsChain,
    pub edge_predictions: Vec<EdgePrediction>,
    pub one_tap_trades: Vec<OneTapTrade>,
    pub timestamp: chrono::DateTime<Utc>,
}

pub struct OptionsEdgeForecaster {
    market_provider: Arc<dyn MarketDataProvider>,
    options_provider: Arc<dyn OptionsDataProvider>,
    alpha_oracle: AlphaOracle,
    regime_engine: MarketRegimeEngine,
}

impl OptionsEdgeForecaster {
    pub fn new(
        market_provider: Arc<dyn MarketDataProvider>,
        options_provider: Arc<dyn OptionsDataProvider>,
        alpha_oracle: AlphaOracle,
        regime_engine: MarketRegimeEngine,
    ) -> Self {
        Self {
            market_provider,
            options_provider,
            alpha_oracle,
            regime_engine,
        }
    }

    /// Forecast edges for a filtered set of contracts + generate OneTap trades.
    /// Reuses AlphaOracle for symbol-specific micro edge.
    /// Reuses RegimeEngine for macro tilt (e.g., risk-on favors calls).
    pub async fn forecast_edges(
        &self,
        symbol: &str,
    ) -> Result<EdgeForecastResponse> {
        let start = std::time::Instant::now();

        let chain = self
            .options_provider
            .get_options_chain(symbol)
            .await
            .with_context(|| format!("failed to get options chain for {symbol}"))?;

        let alpha_features = self.build_alpha_features(symbol, &chain)?;
        let alpha = self.alpha_oracle.generate_signal(symbol, &alpha_features).await?;
        let regime = self.regime_engine.analyze_simple().await?;

        let edge_predictions = self.predict_contract_edges(&chain, &alpha, &regime)?;
        let one_tap_trades = self.generate_one_tap_trades(&chain, &edge_predictions, &alpha, &regime)?;

        let resp = EdgeForecastResponse {
            symbol: symbol.to_string(),
            chain,
            edge_predictions,
            one_tap_trades,
            timestamp: Utc::now(),
        };

        tracing::info!(
            "OptionsEdgeForecaster::forecast_edges completed for {} in {:?}",
            symbol,
            start.elapsed()
        );

        Ok(resp)
    }

    fn build_alpha_features(
        &self,
        symbol: &str,
        chain: &OptionsChain,
    ) -> Result<std::collections::HashMap<String, f64>> {
        let mut features = std::collections::HashMap::new();

        features.insert("price_usd".into(), chain.underlying_price);

        let mut iv_sum = 0.0;
        let mut count = 0;
        for c in &chain.contracts {
            iv_sum += c.implied_volatility;
            count += 1;
        }
        let avg_iv = if count > 0 { iv_sum / count as f64 } else { 0.2 };
        features.insert("volatility".into(), avg_iv);

        // Add more: e.g., momentum from market_provider.get_price_history()
        features.insert("rsi".into(), 50.0); // Placeholder; pull real from provider
        features.insert("momentum_24h".into(), 0.0);
        features.insert("market_cap_rank".into(), 999.0);
        features.insert("risk_score".into(), 0.5);

        Ok(features)
    }

    fn predict_contract_edges(
        &self,
        chain: &OptionsChain,
        alpha: &AlphaSignal,
        regime: &SimpleMarketRegime,
    ) -> Result<Vec<EdgePrediction>> {
        let mut predictions = Vec::new();

        for contract in &chain.contracts {
            // Base edge from contract (e.g., bid/ask spread, IV vs realized)
            let current_edge = contract.edge; // Assume provider gives this; or calc as (bid + ask)/2 - intrinsic or something

            // Forecast IV change: deterministic based on regime + alpha
            let iv_change = self.predict_iv_change(regime, alpha, contract.implied_volatility);

            // Forecast price movement: tilt by alpha conviction
            let price_move = self.predict_price_movement(alpha, contract.days_to_expiration);

            // Edge change: simple BS-like sensitivity (delta * price_move + vega * iv_change)
            let edge_change = (contract.greeks.delta * price_move) + (contract.greeks.vega * iv_change);

            // Timesteps: scale by time (sqrt(t) for vol, linear for theta)
            let t_15min = 15.0 / (60.0 * 24.0 * 365.0); // fraction of year
            let t_1hr = 1.0 / (24.0 * 365.0);
            let t_1day = 1.0 / 365.0;

            let predicted_edge_15min = current_edge + edge_change * (t_15min as f64).sqrt();
            let predicted_edge_1hr = current_edge + edge_change * (t_1hr as f64).sqrt();
            let predicted_edge_1day = current_edge + edge_change * (t_1day as f64).sqrt();

            // Confidence: alpha confidence * regime confidence
            let confidence = alpha.ml_confidence * regime.confidence;

            // Explanation: human-readable, Jobs-style
            let explanation = format!(
                "Edge forecast tilted by {} regime (mood: {}) and ML conviction ({})",
                regime.headline,
                regime.mood,
                alpha.conviction
            );

            // Premium forecasts: edge_change in dollars (premium = mid_price)
            let mid_premium = (contract.bid + contract.ask) / 2.0;
            let edge_change_dollars = edge_change * mid_premium; // rough proxy
            let predicted_premium_15min = mid_premium + edge_change_dollars * t_15min;
            let predicted_premium_1hr = mid_premium + edge_change_dollars * t_1hr;
            // Note: 1day premium would also decay theta, but keep simple for now

            predictions.push(EdgePrediction {
                strike: contract.strike,
                expiration: contract.expiration.clone(),
                option_type: contract.option_type.clone(),
                current_edge,
                predicted_edge_15min,
                predicted_edge_1hr,
                predicted_edge_1day,
                confidence,
                explanation,
                edge_change_dollars,
                current_premium: mid_premium,
                predicted_premium_15min,
                predicted_premium_1hr,
            });
        }

        Ok(predictions)
    }

    fn predict_iv_change(
        &self,
        regime: &SimpleMarketRegime,
        alpha: &AlphaSignal,
        current_iv: f64,
    ) -> f64 {
        // Deterministic: regime mood tilts IV (fear → higher IV, greed → lower)
        let regime_tilt = match regime.mood.as_str() {
            "Panic" | "Fear" => 0.15,  // IV spike
            "Greed" | "Euphoria" => -0.05,  // IV crush
            _ => 0.0,
        };

        // Alpha tilt: high conviction bullish → slight IV drop
        let alpha_tilt = if alpha.ml_confidence > 0.7 && alpha.ml_label == "BULLISH" {
            -0.03
        } else if alpha.ml_confidence > 0.7 && alpha.ml_label == "BEARISH" {
            0.10
        } else {
            0.0
        };

        (regime_tilt + alpha_tilt) * current_iv  // proportional change
    }

    fn predict_price_movement(
        &self,
        alpha: &AlphaSignal,
        dte: i32,
    ) -> f64 {
        // Deterministic: alpha bullish prob → expected move
        let base_move = (alpha.ml_confidence - 0.5) * 2.0;  // -1.0 to +1.0
        let time_scale = (dte as f64 / 30.0).min(1.0);  // cap at 30d
        base_move * time_scale * 0.05  // e.g., +5% expected for strong bullish in 30d
    }

    fn generate_one_tap_trades(
        &self,
        chain: &OptionsChain,
        edges: &[EdgePrediction],
        alpha: &AlphaSignal,
        regime: &SimpleMarketRegime,
    ) -> Result<Vec<OneTapTrade>> {
        // Strategy synthesis: generate 2-3 one-taps based on best edges + regime/alpha
        let mut trades = Vec::new();

        // Filter best edges: top 3 by predicted_edge_1day * confidence
        let mut sorted_edges = edges.to_vec();
        sorted_edges.sort_by(|a, b| {
            let a_score = a.predicted_edge_1day * a.confidence;
            let b_score = b.predicted_edge_1day * b.confidence;
            b_score.partial_cmp(&a_score).unwrap_or(std::cmp::Ordering::Equal)
        });
        let best_edges = &sorted_edges[0..3.min(sorted_edges.len())];

        // For each best edge, build a simple debit/credit strategy
        for edge in best_edges {
            // Example: long call/put debit if bullish/bearish
            let strategy_type = if edge.option_type == "call" { "Long Call" } else { "Long Put" };
            let action = if alpha.conviction.contains("BUY") { "buy" } else { "sell" };

            let legs = vec![
                OneTapLeg {
                    action: action.to_string(),
                    option_type: edge.option_type.clone(),
                    strike: edge.strike,
                    expiration: edge.expiration.clone(),
                    quantity: 1,
                    premium: edge.current_premium,
                },
            ];

            // Brackets: take_profit at +50% edge, stop at -20% or regime-based
            let expected_edge = edge.predicted_edge_1day;
            let take_profit = edge.current_premium * (1.0 + expected_edge * 1.5);
            let stop_loss = edge.current_premium * (1.0 - 0.20);

            // POP: confidence tilted by regime
            let pop = edge.confidence * if regime.mood == "Greed" { 1.1 } else { 0.9 };

            // Max P/L: debit strategies
            let total_cost = edge.current_premium;
            let max_loss = -total_cost;
            let max_profit = f64::INFINITY;  // uncapped for longs

            let reasoning = format!(
                "One-tap {} based on edge forecast ({:.2} predicted) in {} regime",
                strategy_type,
                expected_edge,
                regime.mood
            );

            trades.push(OneTapTrade {
                strategy: strategy_type.to_string(),
                entry_price: edge.current_premium,
                expected_edge,
                confidence: edge.confidence,
                take_profit,
                stop_loss,
                reasoning,
                max_loss,
                max_profit,
                probability_of_profit: pop,
                symbol: chain.symbol.clone(),
                legs,
                strategy_type: strategy_type.to_string(),
                days_to_expiration: 30,  // placeholder; pull from contract
                total_cost,
                total_credit: 0.0,
            });
        }

        Ok(trades)
    }
}

