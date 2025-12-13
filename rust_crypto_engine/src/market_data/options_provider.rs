// src/market_data/options_provider.rs
// Trait for pluggable options data providers (Alpaca, Tradier, Polygon, etc.)

use async_trait::async_trait;
use chrono::{DateTime, Utc};
use std::sync::Arc;
use crate::options_core::{OptionsChain, OptionContract};

#[async_trait]
pub trait OptionsDataProvider: Send + Sync + 'static {
    /// Get underlying last price + timestamp
    async fn get_underlying_price(&self, symbol: &str) -> anyhow::Result<(f64, DateTime<Utc>)>;

    /// Get full options chain (or filtered window) for a symbol
    async fn get_options_chain(&self, symbol: &str) -> anyhow::Result<OptionsChain>;
}

// Blanket impl for Arc<T> where T: OptionsDataProvider
#[async_trait]
impl<T: OptionsDataProvider> OptionsDataProvider for Arc<T> {
    async fn get_underlying_price(&self, symbol: &str) -> anyhow::Result<(f64, DateTime<Utc>)> {
        (**self).get_underlying_price(symbol).await
    }

    async fn get_options_chain(&self, symbol: &str) -> anyhow::Result<OptionsChain> {
        (**self).get_options_chain(symbol).await
    }
}

