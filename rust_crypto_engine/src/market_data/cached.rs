// src/market_data/cached.rs
// Cache wrapper (Redis or in-proc) without changing engines

use super::provider::*;
use async_trait::async_trait;
use chrono::{DateTime, Duration, Utc};
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Clone)]
struct CachedLatest {
    quote: Quote,
    expires_at: DateTime<Utc>,
}

pub struct CachedProvider<P> {
    inner: P,
    ttl: Duration,
    latest_cache: dashmap::DashMap<Arc<str>, Arc<RwLock<Option<CachedLatest>>>>,
}

impl<P> CachedProvider<P> {
    pub fn new(inner: P, ttl: Duration) -> Self {
        Self {
            inner,
            ttl,
            latest_cache: dashmap::DashMap::new(),
        }
    }
}

#[async_trait]
impl<P: MarketDataProvider> MarketDataProvider for CachedProvider<P> {
    #[tracing::instrument(skip(self))]
    async fn latest_quote(&self, symbol: &str) -> Result<Quote, ProviderError> {
        let key: Arc<str> = Arc::from(symbol);
        let cell = self
            .latest_cache
            .entry(key.clone())
            .or_insert_with(|| Arc::new(RwLock::new(None)))
            .clone();

        {
            let guard = cell.read().await;
            if let Some(c) = &*guard {
                if Utc::now() <= c.expires_at {
                    return Ok(c.quote.clone());
                }
            }
        }

        let fresh = self.inner.latest_quote(symbol).await?;
        let mut guard = cell.write().await;
        *guard = Some(CachedLatest {
            quote: fresh.clone(),
            expires_at: Utc::now() + self.ttl,
        });
        Ok(fresh)
    }

    #[tracing::instrument(skip(self))]
    async fn mid_prices(
        &self,
        symbol: &str,
        start: DateTime<Utc>,
        end: DateTime<Utc>,
        limit: usize,
    ) -> Result<Vec<PricePoint>, ProviderError> {
        // usually don't cache long series unless you have Redis/materialized candles
        self.inner.mid_prices(symbol, start, end, limit).await
    }
}

