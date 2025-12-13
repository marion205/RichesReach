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
        let provider = Self {
            latest: DashMap::new(),
            series: DashMap::new(),
            insert_counts: DashMap::new(),
        };
        // Initialize with mock forex data for development
        provider.initialize_mock_forex_data();
        // Initialize with SPY data for regime engine
        provider.initialize_spy_data();
        provider
    }

    fn initialize_mock_forex_data(&self) {
        use chrono::Utc;
        use rust_decimal::Decimal;
        
        // Major forex pairs with realistic mock data (expanded from 7 to 20+ pairs)
        let pairs = vec![
            // Major pairs
            ("EURUSD", 1.0850, 1.0852),
            ("GBPUSD", 1.2650, 1.2653),
            ("USDJPY", 149.50, 149.53),
            ("AUDUSD", 0.6580, 0.6583),
            ("USDCAD", 1.3520, 1.3523),
            ("USDCHF", 0.8750, 0.8753),
            ("NZDUSD", 0.6120, 0.6123),
            // Cross pairs
            ("EURGBP", 0.8575, 0.8578),
            ("EURJPY", 162.25, 162.28),
            ("GBPJPY", 189.15, 189.18),
            ("AUDJPY", 98.45, 98.48),
            ("EURCHF", 0.9495, 0.9498),
            ("GBPCHF", 1.1065, 1.1068),
            // Commodity pairs
            ("USDCNH", 7.2450, 7.2453),
            ("USDMXN", 17.1250, 17.1253),
            ("USDZAR", 18.850, 18.853),
            ("USDBRL", 4.9850, 4.9853),
            // Exotic pairs
            ("USDTRY", 32.150, 32.153),
            ("USDINR", 83.125, 83.128),
            ("USDSGD", 1.3425, 1.3428),
            ("USDHKD", 7.8125, 7.8128),
            ("USDNOK", 10.625, 10.628),
            ("USDSEK", 10.325, 10.328),
        ];

        let pair_count = pairs.len();
        let now = Utc::now();
        
        for (pair, bid, ask) in pairs {
            let quote = Quote {
                symbol: Arc::from(pair),
                ts: now,
                bid: rust_decimal::Decimal::from_f64_retain(bid).unwrap_or_default(),
                ask: rust_decimal::Decimal::from_f64_retain(ask).unwrap_or_default(),
            };
            
            // Store latest quote
            self.latest.insert(Arc::from(pair), quote.clone());
            
            // Generate 30 days of historical data
            let mut history = Vec::new();
            for i in 0..30 {
                let timestamp = now - chrono::Duration::days(30 - i);
                // Add some variation to make it realistic
                let variation = (i as f64 * 0.0001).sin() * 0.01;
                let mid_price = (bid + ask) / 2.0 + variation;
                let spread = ask - bid;
                
                history.push(PricePoint {
                    ts: timestamp,
                    mid: rust_decimal::Decimal::from_f64_retain(mid_price).unwrap_or_default(),
                });
            }
            
            self.series.insert(Arc::from(pair), history);
        }
        
        tracing::info!("Initialized mock forex data for {} pairs", pair_count);
    }

    fn initialize_spy_data(&self) {
        use chrono::Utc;
        use rust_decimal::Decimal;
        
        // SPY is required for regime engine volatility calculations
        // Initialize with realistic SPY price (~450) and 30 days of history
        let spy_price = 450.0;
        let now = Utc::now();
        
        let quote = Quote {
            symbol: Arc::from("SPY"),
            ts: now,
            bid: Decimal::from_f64_retain(spy_price - 0.01).unwrap_or_default(),
            ask: Decimal::from_f64_retain(spy_price + 0.01).unwrap_or_default(),
        };
        
        // Store latest quote
        self.latest.insert(Arc::from("SPY"), quote.clone());
        
        // Generate 30 days of historical data (regime engine needs at least 20 days)
        let mut history = Vec::new();
        for i in 0..30 {
            let timestamp = now - chrono::Duration::days(30 - i);
            // Add realistic price variation (SPY typically moves 0.5-2% daily)
            let daily_return = (i as f64 * 0.1).sin() * 0.015; // ±1.5% variation
            let price = spy_price * (1.0 + daily_return);
            
            history.push(PricePoint {
                ts: timestamp,
                mid: Decimal::from_f64_retain(price).unwrap_or_default(),
            });
        }
        
        self.series.insert(Arc::from("SPY"), history);
        tracing::info!("Initialized SPY data for regime engine");
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
