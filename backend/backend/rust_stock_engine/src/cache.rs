use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::time::{Duration, Instant};
use tracing::{info, warn};

#[derive(Debug, Clone)]
pub struct CacheStats {
    pub hits: u64,
    pub misses: u64,
    pub hit_rate: f64,
}

#[derive(Debug)]
struct CacheEntry<T> {
    value: T,
    expires_at: Instant,
}

pub struct CacheManager {
    cache: Arc<RwLock<HashMap<String, CacheEntry<serde_json::Value>>>>,
    stats: Arc<RwLock<CacheStats>>,
    ttl: Duration,
}

impl CacheManager {
    pub fn new() -> Self {
        Self {
            cache: Arc::new(RwLock::new(HashMap::new())),
            stats: Arc::new(RwLock::new(CacheStats {
                hits: 0,
                misses: 0,
                hit_rate: 0.0,
            })),
            ttl: Duration::from_secs(300), // 5 minutes default TTL
        }
    }

    pub async fn get_prediction(&self, key: &str) -> Option<serde_json::Value> {
        let mut cache = self.cache.write().await;
        let mut stats = self.stats.write().await;
        
        if let Some(entry) = cache.get(key) {
            if entry.expires_at > Instant::now() {
                stats.hits += 1;
                self.update_hit_rate(&mut stats);
                info!(key = %key, "cache_hit");
                return Some(entry.value.clone());
            } else {
                // Expired entry, remove it
                cache.remove(key);
            }
        }
        
        stats.misses += 1;
        self.update_hit_rate(&mut stats);
        info!(key = %key, "cache_miss");
        None
    }

    pub async fn store_prediction(&self, key: &str, value: &serde_json::Value) {
        let mut cache = self.cache.write().await;
        let expires_at = Instant::now() + self.ttl;
        
        let entry = CacheEntry {
            value: value.clone(),
            expires_at,
        };
        
        cache.insert(key.to_string(), entry);
        info!(key = %key, "cache_stored");
    }

    pub async fn get_stats(&self) -> CacheStats {
        let stats = self.stats.read().await;
        stats.clone()
    }

    fn update_hit_rate(&self, stats: &mut CacheStats) {
        let total = stats.hits + stats.misses;
        if total > 0 {
            stats.hit_rate = stats.hits as f64 / total as f64;
        }
    }

    pub async fn cleanup_expired(&self) {
        let mut cache = self.cache.write().await;
        let now = Instant::now();
        let initial_size = cache.len();
        
        cache.retain(|_, entry| entry.expires_at > now);
        
        let removed = initial_size - cache.len();
        if removed > 0 {
            info!(removed, "cache_cleanup");
        }
    }
}

impl Default for CacheManager {
    fn default() -> Self {
        Self::new()
    }
}
