use crate::feature_sources::{AssetClass, FeatureSource};
use crate::options_edge::OptionsEdgeForecaster;
use std::collections::HashMap;
use anyhow::Result;
use async_trait::async_trait;
use std::sync::Arc;

/// Wrapper to make OptionsEdgeForecaster a FeatureSource
pub struct OptionsFeatureSource {
    forecaster: Arc<OptionsEdgeForecaster>,
}

impl OptionsFeatureSource {
    pub fn new(forecaster: Arc<OptionsEdgeForecaster>) -> Self {
        Self { forecaster }
    }
}

#[async_trait]
impl FeatureSource for OptionsFeatureSource {
    fn asset_class(&self) -> AssetClass {
        AssetClass::Options
    }

    async fn build_features(&self, symbol: &str) -> Result<HashMap<String, f64>> {
        let forecast = self.forecaster.forecast_edges(symbol).await?;
        let mut features = HashMap::new();
        
        // Extract features from options chain and predictions
        features.insert("underlying_price".to_string(), forecast.chain.underlying_price);
        
        // Calculate average IV from chain
        let mut iv_sum = 0.0;
        let mut count = 0;
        for contract in &forecast.chain.contracts {
            iv_sum += contract.implied_volatility;
            count += 1;
        }
        let avg_iv = if count > 0 { iv_sum / count as f64 } else { 0.2 };
        features.insert("avg_iv".to_string(), avg_iv);
        
        // Best edge from predictions
        if let Some(best) = forecast.edge_predictions.iter().max_by(|a, b| a.current_edge.partial_cmp(&b.current_edge).unwrap_or(std::cmp::Ordering::Equal)) {
            features.insert("best_edge".to_string(), best.current_edge);
        }
        
        // One-tap trade features
        if let Some(best) = forecast.one_tap_trades.first() {
            features.insert("one_tap_edge".to_string(), best.expected_edge);
            features.insert("one_tap_confidence".to_string(), best.confidence);
            features.insert("one_tap_dte".to_string(), best.days_to_expiration as f64);
        }
        
        Ok(features)
    }
}

