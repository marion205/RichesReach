// src/metrics.rs
// Prometheus metrics for production observability
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

#[derive(Clone)]
pub struct Metrics {
    // Provider latency histograms (in milliseconds)
    pub provider_latest_quote_ms: Arc<AtomicU64>,
    pub provider_mid_prices_ms: Arc<AtomicU64>,
    
    // Ingest counters
    pub ingest_quotes_total: Arc<AtomicU64>,
    pub ingest_errors_total: Arc<AtomicU64>,
    
    // Error counters by type
    pub errors_not_found: Arc<AtomicU64>,
    pub errors_backend: Arc<AtomicU64>,
    pub errors_invalid: Arc<AtomicU64>,
    
    // Cache metrics (if using CachedProvider)
    pub cache_hits: Arc<AtomicU64>,
    pub cache_misses: Arc<AtomicU64>,
}

impl Metrics {
    pub fn new() -> Self {
        Self {
            provider_latest_quote_ms: Arc::new(AtomicU64::new(0)),
            provider_mid_prices_ms: Arc::new(AtomicU64::new(0)),
            ingest_quotes_total: Arc::new(AtomicU64::new(0)),
            ingest_errors_total: Arc::new(AtomicU64::new(0)),
            errors_not_found: Arc::new(AtomicU64::new(0)),
            errors_backend: Arc::new(AtomicU64::new(0)),
            errors_invalid: Arc::new(AtomicU64::new(0)),
            cache_hits: Arc::new(AtomicU64::new(0)),
            cache_misses: Arc::new(AtomicU64::new(0)),
        }
    }
    
    pub fn record_provider_latency(&self, operation: &str, ms: u64) {
        match operation {
            "latest_quote" => self.provider_latest_quote_ms.store(ms, Ordering::Relaxed),
            "mid_prices" => self.provider_mid_prices_ms.store(ms, Ordering::Relaxed),
            _ => {}
        }
    }
    
    pub fn record_ingest(&self) {
        self.ingest_quotes_total.fetch_add(1, Ordering::Relaxed);
    }
    
    pub fn record_ingest_error(&self) {
        self.ingest_errors_total.fetch_add(1, Ordering::Relaxed);
    }
    
    pub fn record_error(&self, error_type: &str) {
        match error_type {
            "NotFound" => { self.errors_not_found.fetch_add(1, Ordering::Relaxed); }
            "Backend" => { self.errors_backend.fetch_add(1, Ordering::Relaxed); }
            "Invalid" => { self.errors_invalid.fetch_add(1, Ordering::Relaxed); }
            _ => {}
        }
    }
    
    pub fn record_cache_hit(&self) {
        self.cache_hits.fetch_add(1, Ordering::Relaxed);
    }
    
    pub fn record_cache_miss(&self) {
        self.cache_misses.fetch_add(1, Ordering::Relaxed);
    }
    
    /// Format metrics in Prometheus text format
    pub fn format_prometheus(&self) -> String {
        let mut out = String::new();
        
        // Provider latency (last observed value - in production, use histogram)
        out.push_str(&format!("# HELP provider_latest_quote_ms_ms Latency of latest_quote operation in milliseconds\n"));
        out.push_str(&format!("# TYPE provider_latest_quote_ms_ms gauge\n"));
        out.push_str(&format!("provider_latest_quote_ms_ms {}\n", self.provider_latest_quote_ms.load(Ordering::Relaxed)));
        
        out.push_str(&format!("# HELP provider_mid_prices_ms Latency of mid_prices operation in milliseconds\n"));
        out.push_str(&format!("# TYPE provider_mid_prices_ms gauge\n"));
        out.push_str(&format!("provider_mid_prices_ms {}\n", self.provider_mid_prices_ms.load(Ordering::Relaxed)));
        
        // Ingest counters
        out.push_str(&format!("# HELP ingest_quotes_total Total number of quotes ingested\n"));
        out.push_str(&format!("# TYPE ingest_quotes_total counter\n"));
        out.push_str(&format!("ingest_quotes_total {}\n", self.ingest_quotes_total.load(Ordering::Relaxed)));
        
        out.push_str(&format!("# HELP ingest_errors_total Total number of ingest errors\n"));
        out.push_str(&format!("# TYPE ingest_errors_total counter\n"));
        out.push_str(&format!("ingest_errors_total {}\n", self.ingest_errors_total.load(Ordering::Relaxed)));
        
        // Error counters
        out.push_str(&format!("# HELP errors_not_found Total NotFound errors\n"));
        out.push_str(&format!("# TYPE errors_not_found counter\n"));
        out.push_str(&format!("errors_not_found {}\n", self.errors_not_found.load(Ordering::Relaxed)));
        
        out.push_str(&format!("# HELP errors_backend Total Backend errors\n"));
        out.push_str(&format!("# TYPE errors_backend counter\n"));
        out.push_str(&format!("errors_backend {}\n", self.errors_backend.load(Ordering::Relaxed)));
        
        out.push_str(&format!("# HELP errors_invalid Total Invalid errors\n"));
        out.push_str(&format!("# TYPE errors_invalid counter\n"));
        out.push_str(&format!("errors_invalid {}\n", self.errors_invalid.load(Ordering::Relaxed)));
        
        // Cache metrics
        let hits = self.cache_hits.load(Ordering::Relaxed);
        let misses = self.cache_misses.load(Ordering::Relaxed);
        let total = hits + misses;
        let hit_rate = if total > 0 { (hits as f64 / total as f64) * 100.0 } else { 0.0 };
        
        out.push_str(&format!("# HELP cache_hits Total cache hits\n"));
        out.push_str(&format!("# TYPE cache_hits counter\n"));
        out.push_str(&format!("cache_hits {}\n", hits));
        
        out.push_str(&format!("# HELP cache_misses Total cache misses\n"));
        out.push_str(&format!("# TYPE cache_misses counter\n"));
        out.push_str(&format!("cache_misses {}\n", misses));
        
        out.push_str(&format!("# HELP cache_hit_rate Cache hit rate percentage\n"));
        out.push_str(&format!("# TYPE cache_hit_rate gauge\n"));
        out.push_str(&format!("cache_hit_rate {}\n", hit_rate));
        
        out
    }
}

impl Default for Metrics {
    fn default() -> Self {
        Self::new()
    }
}

