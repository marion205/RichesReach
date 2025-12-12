// Adapter to make CorrelationAnalysisEngine's internal storage work as a provider
use super::provider::MarketDataProvider;
use crate::correlation_analysis::CorrelationAnalysisEngine;
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use anyhow::{Result, anyhow};
use std::sync::Arc;

pub struct CorrelationEngineAdapter {
    engine: Arc<CorrelationAnalysisEngine>,
}

impl CorrelationEngineAdapter {
    pub fn new(engine: Arc<CorrelationAnalysisEngine>) -> Self {
        Self { engine }
    }
}

#[async_trait]
impl MarketDataProvider for CorrelationEngineAdapter {
    async fn get_price_history(
        &self,
        symbol: &str,
        start: DateTime<Utc>,
        end: DateTime<Utc>,
    ) -> Result<Vec<(DateTime<Utc>, Decimal)>> {
        // Access internal storage via a public method or use reflection
        // For now, we'll need to add a method to CorrelationAnalysisEngine
        // Or we can use the existing ingest_price pattern
        // This is a temporary adapter - in production, CorrelationAnalysisEngine should use provider directly
        Err(anyhow!("CorrelationEngineAdapter: use CorrelationAnalysisEngine directly for now"))
    }

    async fn get_fx_history(
        &self,
        _pair: &str,
        _start: DateTime<Utc>,
        _end: DateTime<Utc>,
    ) -> Result<Vec<(DateTime<Utc>, Decimal, Decimal)>> {
        Err(anyhow!("CorrelationEngineAdapter: FX not supported"))
    }

    async fn get_latest(&self, _symbol: &str) -> Result<(DateTime<Utc>, Decimal)> {
        Err(anyhow!("CorrelationEngineAdapter: use CorrelationAnalysisEngine directly"))
    }

    async fn get_latest_fx(&self, _pair: &str) -> Result<(DateTime<Utc>, Decimal, Decimal)> {
        Err(anyhow!("CorrelationEngineAdapter: FX not supported"))
    }
}

