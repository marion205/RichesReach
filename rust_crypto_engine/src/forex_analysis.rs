use std::collections::HashMap;
use chrono::Utc;
use rust_decimal::Decimal;
use anyhow::Result;
use rust_decimal::prelude::ToPrimitive;
use rand::Rng;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ForexAnalysisResponse {
    pub pair: String,
    pub bid: Decimal,
    pub ask: Decimal,
    pub spread: f64,
    pub pip_value: f64,
    pub volatility: f64,
    pub trend: String,  // "BULLISH", "BEARISH", "NEUTRAL"
    pub support_level: Decimal,
    pub resistance_level: Decimal,
    pub correlation_24h: f64,
    pub timestamp: chrono::DateTime<Utc>,
}

pub struct ForexAnalysisEngine {
    price_cache: tokio::sync::RwLock<HashMap<String, (Decimal, Decimal, chrono::DateTime<Utc>)>>,
}

impl ForexAnalysisEngine {
    pub fn new() -> Self {
        Self {
            price_cache: tokio::sync::RwLock::new(HashMap::new()),
        }
    }

    pub async fn analyze(&self, pair: &str) -> Result<ForexAnalysisResponse> {
        let start = std::time::Instant::now();
        
        // Get current rates
        let (bid, ask) = self.get_forex_rate(pair).await?;
        let spread = (ask - bid).to_f64().unwrap_or(0.0);
        
        // Calculate pip value
        let pip_value = self.calculate_pip_value(pair, &bid).await?;
        
        // Calculate volatility
        let volatility = self.calculate_volatility(pair).await?;
        
        // Determine trend
        let trend = self.determine_trend(pair, &bid).await?;
        
        // Calculate support/resistance
        let (support, resistance) = self.calculate_support_resistance(pair, &bid).await?;
        
        // 24h correlation (vs USD index)
        let correlation_24h = self.calculate_correlation_24h(pair).await?;
        
        let response = ForexAnalysisResponse {
            pair: pair.to_string(),
            bid,
            ask,
            spread,
            pip_value,
            volatility,
            trend,
            support_level: support,
            resistance_level: resistance,
            correlation_24h,
            timestamp: Utc::now(),
        };

        tracing::info!("Forex analysis completed for {} in {:?}", pair, start.elapsed());
        Ok(response)
    }

    async fn get_forex_rate(&self, pair: &str) -> Result<(Decimal, Decimal)> {
        // Check cache
        {
            let cache = self.price_cache.read().await;
            if let Some((cached_bid, cached_ask, cached_time)) = cache.get(pair) {
                let age = Utc::now().signed_duration_since(*cached_time);
                if age.num_seconds() < 30 {
                    // Forex cache valid for 30 seconds
                    return Ok((*cached_bid, *cached_ask));
                }
            }
        }

        // Mock rates for major pairs
        let base_rate = match pair {
            "EURUSD" => 1.0850,
            "GBPUSD" => 1.2650,
            "USDJPY" => 149.50,
            "AUDUSD" => 0.6550,
            "USDCAD" => 1.3500,
            "USDCHF" => 0.8750,
            "NZDUSD" => 0.6050,
            "EURGBP" => 0.8570,
            "EURJPY" => 162.20,
            "GBPJPY" => 189.10,
            _ => 1.0000,
        };

        let adjustment = {
            let mut rng = rand::thread_rng();
            rng.gen_range(-0.001..0.001)
        };
        
        let mid_rate = base_rate + adjustment;
        let spread_pips = {
            let mut rng = rand::thread_rng();
            rng.gen_range(1.0..3.0) / 10000.0 // 1-3 pips
        };
        
        let bid = Decimal::from_f64_retain(mid_rate - spread_pips / 2.0).unwrap_or(Decimal::ONE);
        let ask = Decimal::from_f64_retain(mid_rate + spread_pips / 2.0).unwrap_or(Decimal::ONE);
        
        {
            let mut cache = self.price_cache.write().await;
            cache.insert(pair.to_string(), (bid, ask, Utc::now()));
        }

        Ok((bid, ask))
    }

    async fn calculate_pip_value(&self, pair: &str, rate: &Decimal) -> Result<f64> {
        // Pip value depends on pair and lot size (standard lot = 100,000 units)
        let rate_f64 = rate.to_f64().unwrap_or(1.0);
        
        // For JPY pairs, pip is 0.01; for others, it's 0.0001
        let pip_size = if pair.contains("JPY") { 0.01 } else { 0.0001 };
        let pip_value = pip_size * 100000.0 / rate_f64;
        
        Ok(pip_value)
    }

    async fn calculate_volatility(&self, pair: &str) -> Result<f64> {
        // Forex volatility is typically lower than stocks/crypto
        let base_vol = match pair {
            "EURUSD" | "GBPUSD" => 0.006,  // Major pairs
            "USDJPY" => 0.007,
            "AUDUSD" | "NZDUSD" => 0.008,  // Commodity currencies
            "USDCAD" | "USDCHF" => 0.005,
            _ => 0.007,
        };

        let adjustment: f64 = {
            let mut rng = rand::thread_rng();
            rng.gen_range(-0.002..0.002)
        };

        let vol_value: f64 = base_vol + adjustment;
        Ok(vol_value.max(0.001_f64).min(0.020_f64))
    }

    async fn determine_trend(&self, pair: &str, current_rate: &Decimal) -> Result<String> {
        // Simplified trend detection
        let trend_score = {
            let mut rng = rand::thread_rng();
            rng.gen_range(-0.5..0.5)
        };
        
        if trend_score > 0.2 {
            Ok("BULLISH".to_string())
        } else if trend_score < -0.2 {
            Ok("BEARISH".to_string())
        } else {
            Ok("NEUTRAL".to_string())
        }
    }

    async fn calculate_support_resistance(
        &self, 
        pair: &str, 
        current_rate: &Decimal
    ) -> Result<(Decimal, Decimal)> {
        let rate_f64 = current_rate.to_f64().unwrap_or(1.0);
        
        // Support: 1% below current
        let support = Decimal::from_f64_retain(rate_f64 * 0.99).unwrap_or(*current_rate);
        
        // Resistance: 1% above current
        let resistance = Decimal::from_f64_retain(rate_f64 * 1.01).unwrap_or(*current_rate);
        
        Ok((support, resistance))
    }

    async fn calculate_correlation_24h(&self, pair: &str) -> Result<f64> {
        // Correlation with USD index (simplified)
        let correlation_value: f64 = {
            let mut rng = rand::thread_rng();
            if pair.starts_with("USD") {
                0.7 + rng.gen_range(-0.2..0.2) // Positive correlation
            } else {
                -0.6 + rng.gen_range(-0.2..0.2) // Negative correlation
            }
        };
        
        Ok(correlation_value.max(-1.0_f64).min(1.0_f64))
    }
}

