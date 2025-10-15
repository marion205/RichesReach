use crate::{CryptoAnalysisResponse, CryptoRecommendation, CacheStats};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use chrono::{DateTime, Utc, Duration};
use anyhow::Result;

#[derive(Clone)]
struct CachedPrediction {
    data: CryptoAnalysisResponse,
    cached_at: DateTime<Utc>,
    ttl: Duration,
}

#[derive(Clone)]
struct CachedRecommendations {
    data: Vec<CryptoRecommendation>,
    cached_at: DateTime<Utc>,
    ttl: Duration,
}

pub struct CacheManager {
    predictions: Arc<RwLock<HashMap<String, CachedPrediction>>>,
    recommendations: Arc<RwLock<HashMap<String, CachedRecommendations>>>,
    hit_count: Arc<RwLock<u64>>,
    miss_count: Arc<RwLock<u64>>,
}

impl CacheManager {
    pub fn new() -> Self {
        Self {
            predictions: Arc::new(RwLock::new(HashMap::new())),
            recommendations: Arc::new(RwLock::new(HashMap::new())),
            hit_count: Arc::new(RwLock::new(0)),
            miss_count: Arc::new(RwLock::new(0)),
        }
    }

    pub async fn get_prediction(&self, symbol: &str) -> Option<CryptoAnalysisResponse> {
        let mut predictions = self.predictions.write().await;
        
        if let Some(cached) = predictions.get(symbol) {
            if Utc::now() < cached.cached_at + cached.ttl {
                // Cache hit
                *self.hit_count.write().await += 1;
                return Some(cached.data.clone());
            } else {
                // Expired, remove from cache
                predictions.remove(symbol);
            }
        }
        
        // Cache miss
        *self.miss_count.write().await += 1;
        None
    }

    pub async fn store_prediction(&self, symbol: &str, prediction: &CryptoAnalysisResponse) {
        let cached = CachedPrediction {
            data: prediction.clone(),
            cached_at: Utc::now(),
            ttl: Duration::minutes(5), // 5-minute TTL for predictions
        };

        let mut predictions = self.predictions.write().await;
        predictions.insert(symbol.to_string(), cached);
    }

    pub async fn get_recommendations(&self, symbols: &[String]) -> Option<Vec<CryptoRecommendation>> {
        let cache_key = if symbols.is_empty() {
            "default".to_string()
        } else {
            symbols.join(",")
        };

        let mut recommendations = self.recommendations.write().await;
        
        if let Some(cached) = recommendations.get(&cache_key) {
            if Utc::now() < cached.cached_at + cached.ttl {
                // Cache hit
                *self.hit_count.write().await += 1;
                return Some(cached.data.clone());
            } else {
                // Expired, remove from cache
                recommendations.remove(&cache_key);
            }
        }
        
        // Cache miss
        *self.miss_count.write().await += 1;
        None
    }

    pub async fn store_recommendations(&self, symbols: &[String], recommendations: &[CryptoRecommendation]) {
        let cache_key = if symbols.is_empty() {
            "default".to_string()
        } else {
            symbols.join(",")
        };

        let cached = CachedRecommendations {
            data: recommendations.to_vec(),
            cached_at: Utc::now(),
            ttl: Duration::minutes(10), // 10-minute TTL for recommendations
        };

        let mut rec_cache = self.recommendations.write().await;
        rec_cache.insert(cache_key, cached);
    }

    pub async fn get_stats(&self) -> CacheStats {
        let predictions_count = self.predictions.read().await.len();
        let recommendations_count = self.recommendations.read().await.len();
        
        let hits = *self.hit_count.read().await;
        let misses = *self.miss_count.read().await;
        let total = hits + misses;
        
        let hit_rate = if total > 0 {
            hits as f64 / total as f64
        } else {
            0.0
        };

        CacheStats {
            predictions_cached: predictions_count,
            recommendations_cached: recommendations_count,
            hit_rate,
        }
    }

    pub async fn clear_expired(&self) {
        let now = Utc::now();
        
        // Clear expired predictions
        {
            let mut predictions = self.predictions.write().await;
            predictions.retain(|_, cached| now < cached.cached_at + cached.ttl);
        }
        
        // Clear expired recommendations
        {
            let mut recommendations = self.recommendations.write().await;
            recommendations.retain(|_, cached| now < cached.cached_at + cached.ttl);
        }
    }

    pub async fn clear_all(&self) {
        self.predictions.write().await.clear();
        self.recommendations.write().await.clear();
        *self.hit_count.write().await = 0;
        *self.miss_count.write().await = 0;
    }
}
