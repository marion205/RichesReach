// src/market_data/provider.rs
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use std::sync::Arc;
use thiserror::Error;

#[derive(Clone, Debug)]
pub struct Quote {
    pub symbol: Arc<str>,
    pub ts: DateTime<Utc>,
    pub bid: Decimal,
    pub ask: Decimal,
}

impl Quote {
    pub fn mid(&self) -> Decimal {
        (self.bid + self.ask) / Decimal::from(2)
    }
}

#[derive(Clone, Debug)]
pub struct PricePoint {
    pub ts: DateTime<Utc>,
    pub mid: Decimal,
}

#[derive(Error, Debug)]
pub enum ProviderError {
    #[error("not found: {0}")]
    NotFound(String),

    #[error("invalid request: {0}")]
    Invalid(String),

    #[error("backend error: {0}")]
    Backend(String),

    #[error(transparent)]
    Other(#[from] anyhow::Error),
}

/// Read path for engines (compute-only).
#[async_trait]
pub trait MarketDataProvider: Send + Sync {
    async fn latest_quote(&self, symbol: &str) -> Result<Quote, ProviderError>;

    /// Returns mid price series in ascending time order.
    async fn mid_prices(
        &self,
        symbol: &str,
        start: DateTime<Utc>,
        end: DateTime<Utc>,
        limit: usize,
    ) -> Result<Vec<PricePoint>, ProviderError>;

    /// Legacy compatibility: get price history as (timestamp, price) tuples
    async fn get_price_history(
        &self,
        symbol: &str,
        start: DateTime<Utc>,
        end: DateTime<Utc>,
    ) -> Result<Vec<(DateTime<Utc>, Decimal)>, ProviderError> {
        let points = self.mid_prices(symbol, start, end, 10_000).await?;
        Ok(points.into_iter().map(|p| (p.ts, p.mid)).collect())
    }

    /// Legacy compatibility: get FX history as (timestamp, bid, ask) tuples
    async fn get_fx_history(
        &self,
        pair: &str,
        start: DateTime<Utc>,
        end: DateTime<Utc>,
    ) -> Result<Vec<(DateTime<Utc>, Decimal, Decimal)>, ProviderError> {
        // For FX, we need bid/ask. If provider doesn't support it, use mid for both
        let quote = self.latest_quote(pair).await?;
        let points = self.mid_prices(pair, start, end, 10_000).await?;
        Ok(points.into_iter().map(|p| {
            // Use latest quote's spread to estimate bid/ask
            let spread = quote.ask - quote.bid;
            let half_spread = spread / Decimal::from(2);
            (p.ts, p.mid - half_spread, p.mid + half_spread)
        }).collect())
    }

    /// Legacy compatibility: latest price
    async fn get_latest(&self, symbol: &str) -> Result<(DateTime<Utc>, Decimal), ProviderError> {
        let quote = self.latest_quote(symbol).await?;
        Ok((quote.ts, quote.mid()))
    }

    /// Legacy compatibility: latest FX quote
    async fn get_latest_fx(&self, pair: &str) -> Result<(DateTime<Utc>, Decimal, Decimal), ProviderError> {
        let quote = self.latest_quote(pair).await?;
        Ok((quote.ts, quote.bid, quote.ask))
    }
}

/// Optional write path (ingestion). Keep separate so engines never require it.
#[async_trait]
pub trait MarketDataIngest: Send + Sync {
    async fn ingest_quote(&self, quote: Quote) -> Result<(), ProviderError>;
}

// Blanket impls for Arc<T> to make Arc<dyn Trait> seamless
#[async_trait]
impl<T: MarketDataProvider + ?Sized> MarketDataProvider for Arc<T> {
    async fn latest_quote(&self, symbol: &str) -> Result<Quote, ProviderError> {
        (**self).latest_quote(symbol).await
    }

    async fn mid_prices(
        &self,
        symbol: &str,
        start: DateTime<Utc>,
        end: DateTime<Utc>,
        limit: usize,
    ) -> Result<Vec<PricePoint>, ProviderError> {
        (**self).mid_prices(symbol, start, end, limit).await
    }
}

#[async_trait]
impl<T: MarketDataIngest + ?Sized> MarketDataIngest for Arc<T> {
    async fn ingest_quote(&self, quote: Quote) -> Result<(), ProviderError> {
        (**self).ingest_quote(quote).await
    }
}
