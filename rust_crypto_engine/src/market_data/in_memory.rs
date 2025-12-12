// src/market_data/in_memory.rs
use super::provider::*;
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use dashmap::DashMap;
use std::sync::Arc;

#[derive(Default)]
pub struct InMemoryProvider {
    latest: DashMap<Arc<str>, Quote>,
    series: DashMap<Arc<str>, Vec<PricePoint>>,
    // Track insertions per symbol for batch pruning
    insert_counts: DashMap<Arc<str>, usize>,
}

impl InMemoryProvider {
    pub fn new() -> Self {
        Self {
            latest: DashMap::new(),
            series: DashMap::new(),
            insert_counts: DashMap::new(),
        }
    }

    /// Legacy compatibility: ingest price (creates a quote with bid=ask=price)
    pub async fn ingest_price(&self, symbol: &str, timestamp: DateTime<Utc>, price: rust_decimal::Decimal) {
        let quote = Quote {
            symbol: Arc::from(symbol),
            ts: timestamp,
            bid: price,
            ask: price,
        };
        let _ = self.ingest_quote(quote).await;
    }

    /// Legacy compatibility: ingest FX quote
    pub async fn ingest_fx_quote(
        &self,
        pair: &str,
        timestamp: DateTime<Utc>,
        bid: rust_decimal::Decimal,
        ask: rust_decimal::Decimal,
    ) {
        let quote = Quote {
            symbol: Arc::from(pair),
            ts: timestamp,
            bid,
            ask,
        };
        let _ = self.ingest_quote(quote).await;
    }
}

#[async_trait]
impl MarketDataProvider for InMemoryProvider {
    #[tracing::instrument(skip(self), fields(symbol = %symbol))]
    async fn latest_quote(&self, symbol: &str) -> Result<Quote, ProviderError> {
        self.latest
            .get(symbol)
            .map(|q| q.clone())
            .ok_or_else(|| ProviderError::NotFound(symbol.to_string()))
    }

    #[tracing::instrument(skip(self), fields(symbol = %symbol, start = %start, end = %end, limit = limit))]
    async fn mid_prices(
        &self,
        symbol: &str,
        start: DateTime<Utc>,
        end: DateTime<Utc>,
        limit: usize,
    ) -> Result<Vec<PricePoint>, ProviderError> {
        let Some(v) = self.series.get(symbol) else {
            return Ok(vec![]);
        };

        // Performance: Use binary search for time bounds (series is sorted ascending)
        // Find start position
        let start_pos = v.binary_search_by_key(&start, |p| p.ts)
            .unwrap_or_else(|pos| pos);
        
        // Find end position (inclusive)
        let end_pos = v.binary_search_by_key(&end, |p| p.ts)
            .map(|pos| pos + 1) // Make it exclusive
            .unwrap_or_else(|pos| pos);
        
        // Extract slice and apply limit
        let slice = &v[start_pos.min(v.len())..end_pos.min(v.len())];
        let capped_limit = limit.min(100_000); // Cap to prevent excessive memory
        let out: Vec<PricePoint> = if slice.len() > capped_limit {
            slice[slice.len() - capped_limit..].to_vec()
        } else {
            slice.to_vec()
        };

        Ok(out)
    }
}

#[async_trait]
impl MarketDataIngest for InMemoryProvider {
    #[tracing::instrument(skip(self), fields(symbol = %quote.symbol, ts = %quote.ts))]
    async fn ingest_quote(&self, quote: Quote) -> Result<(), ProviderError> {
        let sym = quote.symbol.clone();
        self.latest.insert(sym.clone(), quote.clone());

        // Dedupe by (symbol, ts): overwrite existing entry with same timestamp
        let mut entry = self.series
            .entry(sym.clone())
            .or_insert_with(Vec::new);
        
        // Remove any existing entry with same timestamp (overwrite behavior)
        entry.retain(|p| p.ts != quote.ts);
        
        // Insert in sorted order (ascending by timestamp)
        let insert_pos = entry.binary_search_by_key(&quote.ts, |p| p.ts)
            .unwrap_or_else(|pos| pos);
        entry.insert(insert_pos, PricePoint { ts: quote.ts, mid: quote.mid() });
        
        // Batch pruning: only prune every 1000 inserts per symbol to avoid heavy work on every insert
        let count = self.insert_counts
            .entry(sym.clone())
            .and_modify(|c| *c += 1)
            .or_insert(1);
        
        if *count % 1000 == 0 {
            // Prune old data (keep only last 90 days)
            let cutoff = Utc::now() - chrono::Duration::days(90);
            entry.retain(|p| p.ts >= cutoff);
        }

        Ok(())
    }
}
