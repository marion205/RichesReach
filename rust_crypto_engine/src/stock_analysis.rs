use crate::CryptoAnalysisResponse;
use crate::feature_sources::{AssetClass, FeatureSource};
use std::collections::HashMap;
use anyhow::Result;
use async_trait::async_trait;
use chrono::Utc;
use rust_decimal::Decimal;
use rust_decimal::prelude::ToPrimitive;

/// FNV-1a 64-bit hash (deterministic across builds/machines)
fn fnv1a64(bytes: &[u8]) -> u64 {
    const FNV_OFFSET: u64 = 0xcbf29ce484222325;
    const FNV_PRIME: u64 = 0x100000001b3;

    let mut hash = FNV_OFFSET;
    for &b in bytes {
        hash ^= b as u64;
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

/// Deterministic noise in [min, max) based on (symbol, salt)
fn deterministic_noise(symbol: &str, salt: &str, min: f64, max: f64) -> f64 {
    let mut buf = Vec::with_capacity(symbol.len() + 1 + salt.len());
    buf.extend_from_slice(symbol.as_bytes());
    buf.push(b'|');
    buf.extend_from_slice(salt.as_bytes());

    let h = fnv1a64(&buf);
    let unit = (h as f64) / (u64::MAX as f64); // 0..1
    min + unit * (max - min)
}

pub struct StockAnalysisEngine {
    price_cache: tokio::sync::RwLock<HashMap<String, (Decimal, f64, chrono::DateTime<Utc>)>>,
    finnhub_key: Option<String>,
    alpha_vantage_key: Option<String>,
}

impl StockAnalysisEngine {
    pub fn new() -> Self {
        Self {
            price_cache: tokio::sync::RwLock::new(HashMap::new()),
            finnhub_key: std::env::var("FINNHUB_API_KEY").ok(),
            alpha_vantage_key: std::env::var("ALPHA_VANTAGE_API_KEY").ok(),
        }
    }

    pub async fn analyze(&self, symbol: &str) -> Result<CryptoAnalysisResponse> {
        let start = std::time::Instant::now();

        // 1) Get price (API → deterministic fallback)
        let (price_usd, price_change_24h) = self.get_stock_price(symbol).await?;

        // 2) Core stats
        let volatility = self.calculate_volatility(symbol, &price_usd).await?;
        let risk_score = self.calculate_risk_score(symbol, volatility).await?;

        // 3) Direction + probability
        let prediction_type = self.predict_movement(symbol, &price_usd, volatility).await?;
        let probability = self.calculate_probability(symbol, &prediction_type).await?;
        let confidence_level = self.determine_confidence(probability).await?;

        // 4) Feature vector (for ML / AlphaOracle fusion)
        let features = self
            .extract_features(symbol, &price_usd, volatility, risk_score)
            .await?;

        // 5) Human-readable explanation (Jobs-style but toned for stocks)
        let explanation =
            self.generate_explanation(symbol, &prediction_type, probability, &confidence_level)
                .await?;

        let response = CryptoAnalysisResponse {
            symbol: symbol.to_string(),
            prediction_type,
            probability,
            confidence_level,
            explanation,
            features,
            model_version: "rust-stock-v1.0.0".to_string(),
            timestamp: Utc::now(),
            price_usd: Some(price_usd),
            price_change_24h: Some(price_change_24h),
            volatility,
            risk_score,
        };

        tracing::info!(
            "Stock analysis completed for {} in {:?}",
            symbol,
            start.elapsed()
        );
        Ok(response)
    }

    // ─────────────────────────────────────
    // PRICING
    // ─────────────────────────────────────
    async fn get_stock_price(&self, symbol: &str) -> Result<(Decimal, f64)> {
        // Cache hit (≤ 60s)
        {
            let cache = self.price_cache.read().await;
            if let Some((cached_price, cached_change, cached_time)) = cache.get(symbol) {
                let age = Utc::now().signed_duration_since(*cached_time);
                if age.num_seconds() < 60 {
                    return Ok((*cached_price, *cached_change));
                }
            }
        }

        // Try real APIs
        if let Some(price_data) = self.fetch_real_price(symbol).await {
            let (price_f, change_pct) = price_data;
            let price = Decimal::from_f64_retain(price_f).unwrap_or(Decimal::ZERO);
            {
                let mut cache = self.price_cache.write().await;
                cache.insert(symbol.to_string(), (price, change_pct, Utc::now()));
            }
            return Ok((price, change_pct));
        }

        // Deterministic fallback — no randomness
        let base_price = match symbol {
            "AAPL" => 175.0,
            "MSFT" => 380.0,
            "GOOGL" => 140.0,
            "AMZN" => 150.0,
            "META" => 350.0,
            "NVDA" => 500.0,
            "TSLA" => 250.0,
            "JPM" => 150.0,
            "V" => 250.0,
            "JNJ" => 160.0,
            _ => 100.0,
        };

        let vol_factor = deterministic_noise(symbol, "price_factor", 0.98, 1.02);
        let price = base_price * vol_factor;

        // Change 24h as deterministic "pseudo-history" signal
        let change_24h = deterministic_noise(symbol, "change_24h", -3.0, 3.0);
        let price_decimal = Decimal::from_f64_retain(price).unwrap_or(Decimal::ZERO);
        {
            let mut cache = self.price_cache.write().await;
            cache.insert(symbol.to_string(), (price_decimal, change_24h, Utc::now()));
        }
        Ok((price_decimal, change_24h))
    }

    async fn fetch_real_price(&self, symbol: &str) -> Option<(f64, f64)> {
        if let Some(ref key) = self.finnhub_key {
            if let Ok(price_data) = self.fetch_finnhub_price(symbol, key).await {
                return Some(price_data);
            }
        }

        if let Some(ref key) = self.alpha_vantage_key {
            if let Ok(price_data) = self.fetch_alpha_vantage_price(symbol, key).await {
                return Some(price_data);
            }
        }

        None
    }

    async fn fetch_finnhub_price(&self, symbol: &str, api_key: &str) -> Result<(f64, f64)> {
        let client = reqwest::Client::new();
        let url = format!(
            "https://finnhub.io/api/v1/quote?symbol={}&token={}",
            symbol, api_key
        );
        let response = client
            .get(&url)
            .timeout(std::time::Duration::from_secs(5))
            .send()
            .await?;

        if response.status().is_success() {
            let data: serde_json::Value = response.json().await?;
            if let (Some(c), Some(_d), Some(dp)) = (
                data.get("c").and_then(|v| v.as_f64()),
                data.get("d").and_then(|v| v.as_f64()),
                data.get("dp").and_then(|v| v.as_f64()),
            ) {
                if c > 0.0 {
                    return Ok((c, dp));
                }
            }
        }
        Err(anyhow::anyhow!("Invalid Finnhub response"))
    }

    async fn fetch_alpha_vantage_price(&self, symbol: &str, api_key: &str) -> Result<(f64, f64)> {
        let client = reqwest::Client::new();
        let url = format!(
            "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={}&apikey={}",
            symbol, api_key
        );
        let response = client
            .get(&url)
            .timeout(std::time::Duration::from_secs(5))
            .send()
            .await?;

        if response.status().is_success() {
            let data: serde_json::Value = response.json().await?;
            if let Some(quote) = data.get("Global Quote") {
                if let (Some(price_str), Some(_change_str), Some(change_pct_str)) = (
                    quote.get("05. price").and_then(|v| v.as_str()),
                    quote.get("09. change").and_then(|v| v.as_str()),
                    quote.get("10. change percent").and_then(|v| v.as_str()),
                ) {
                    if let (Ok(price), Ok(change_pct)) = (
                        price_str.parse::<f64>(),
                        change_pct_str.trim_end_matches('%').parse::<f64>(),
                    ) {
                        if price > 0.0 {
                            return Ok((price, change_pct));
                        }
                    }
                }
            }
        }
        Err(anyhow::anyhow!("Invalid Alpha Vantage response"))
    }

    // ─────────────────────────────────────
    // CORE METRICS
    // ─────────────────────────────────────
    async fn calculate_volatility(&self, symbol: &str, _price: &Decimal) -> Result<f64> {
        let base = match symbol {
            "AAPL" | "MSFT" | "GOOGL" => 0.015,
            "AMZN" | "META" | "NVDA" => 0.020,
            "TSLA" => 0.035,
            "JPM" | "V" | "JNJ" => 0.012,
            _ => 0.018,
        };
        let adj = deterministic_noise(symbol, "volatility", -0.004, 0.004);
        Ok((base + adj).max(0.005))
    }

    async fn calculate_risk_score(&self, symbol: &str, volatility: f64) -> Result<f64> {
        let market_cap_factor = match symbol {
            "AAPL" | "MSFT" | "GOOGL" | "AMZN" => 0.10,
            "META" | "NVDA" | "TSLA" => 0.20,
            "JPM" | "V" | "JNJ" => 0.15,
            _ => 0.30,
        };
        Ok((volatility * 15.0 + market_cap_factor).clamp(0.0, 1.5))
    }

    // ─────────────────────────────────────
    // DIRECTION / PROBABILITY
    // ─────────────────────────────────────
    async fn predict_movement(
        &self,
        symbol: &str,
        price: &Decimal,
        volatility: f64,
    ) -> Result<String> {
        let price_f64 = price.to_f64().unwrap_or(0.0);

        // Trend tilt: large caps drifting up, smaller more mixed
        let trend_factor = if price_f64 > 200.0 { 0.56 } else { 0.48 };

        // Vol tilt: high vol → more two-sided, low vol → grind up / mean reversion
        let vol_factor = if volatility > 0.025 { 0.45 } else { 0.58 };

        // Deterministic noise to avoid constant behavior per symbol
        let noise = deterministic_noise(symbol, "direction", -0.12, 0.12);
        let bullish_score = trend_factor * vol_factor + noise;

        let prediction = if bullish_score > 0.55 {
            "BULLISH"
        } else if bullish_score < 0.45 {
            "BEARISH"
        } else {
            "NEUTRAL"
        };

        Ok(prediction.to_string())
    }

    async fn calculate_probability(&self, symbol: &str, prediction_type: &str) -> Result<f64> {
        let base = match prediction_type {
            "BULLISH" => 0.62,
            "BEARISH" => 0.58,
            "NEUTRAL" => 0.50,
            _ => 0.50,
        };

        // Small deterministic wiggle per symbol / direction
        let wiggle = deterministic_noise(symbol, prediction_type, -0.08, 0.08);
        let prob = (base + wiggle).clamp(0.40, 0.85);
        Ok(prob)
    }

    async fn determine_confidence(&self, probability: f64) -> Result<String> {
        let conf = if probability >= 0.75 {
            "HIGH"
        } else if probability >= 0.60 {
            "MEDIUM"
        } else {
            "LOW"
        };
        Ok(conf.to_string())
    }

    // ─────────────────────────────────────
    // FEATURES
    // ─────────────────────────────────────
    async fn extract_features(
        &self,
        symbol: &str,
        price: &Decimal,
        volatility: f64,
        risk_score: f64,
    ) -> Result<HashMap<String, f64>> {
        let mut features = HashMap::new();
        let p = price.to_f64().unwrap_or(0.0);

        features.insert("price_usd".to_string(), p);
        features.insert("volatility".to_string(), volatility);
        features.insert("risk_score".to_string(), risk_score);
        features.insert("market_cap_rank".to_string(), self.get_market_cap_rank(symbol));
        features.insert("volume_24h".to_string(), self.get_volume_24h(symbol));
        features.insert("rsi".to_string(), self.calculate_rsi(symbol));
        features.insert("macd".to_string(), self.calculate_macd(symbol));
        features.insert("sma_20".to_string(), self.calculate_sma(symbol, 20));
        features.insert("sma_50".to_string(), self.calculate_sma(symbol, 50));
        features.insert("pe_ratio".to_string(), self.get_pe_ratio(symbol));
        features.insert("dividend_yield".to_string(), self.get_dividend_yield(symbol));

        Ok(features)
    }

    async fn generate_explanation(
        &self,
        symbol: &str,
        prediction_type: &str,
        probability: f64,
        confidence: &str,
    ) -> Result<String> {
        let confidence_desc = match confidence {
            "HIGH" => "high confidence",
            "MEDIUM" => "moderate confidence",
            "LOW" => "low confidence",
            _ => "uncertain confidence",
        };

        let direction = match prediction_type {
            "BULLISH" => "upward",
            "BEARISH" => "downward",
            "NEUTRAL" => "sideways",
            _ => "uncertain",
        };

        Ok(format!(
            "{} looks tilted toward **{} movement** with {} (~{}% probability).\n\
             This view blends price trend, volatility, and market-cap profile — \
             meant to guide sizing and timing, not replace full research.",
            symbol,
            direction,
            confidence_desc,
            (probability * 100.0).round()
        ))
    }

    // ─────────────────────────────────────
    // HELPER "FUNDAMENTAL" & TECH SIGNALS
    // (still deterministic, symbol-driven)
    // ─────────────────────────────────────
    fn get_market_cap_rank(&self, symbol: &str) -> f64 {
        match symbol {
            "AAPL" => 1.0,
            "MSFT" => 2.0,
            "GOOGL" => 3.0,
            "AMZN" => 4.0,
            "META" => 7.0,
            "NVDA" => 6.0,
            "TSLA" => 8.0,
            "JPM" => 15.0,
            "V" => 12.0,
            "JNJ" => 18.0,
            _ => 50.0,
        }
    }

    fn get_volume_24h(&self, symbol: &str) -> f64 {
        match symbol {
            "AAPL" => 50_000_000.0,
            "MSFT" => 25_000_000.0,
            "GOOGL" => 20_000_000.0,
            "AMZN" => 30_000_000.0,
            "META" => 15_000_000.0,
            "NVDA" => 40_000_000.0,
            "TSLA" => 80_000_000.0,
            "JPM" => 10_000_000.0,
            "V" => 5_000_000.0,
            "JNJ" => 8_000_000.0,
            _ => 5_000_000.0,
        }
    }

    fn calculate_rsi(&self, symbol: &str) -> f64 {
        // Pseudo-tech based on deterministic noise
        deterministic_noise(symbol, "rsi", 35.0, 65.0)
    }

    fn calculate_macd(&self, symbol: &str) -> f64 {
        deterministic_noise(symbol, "macd", -2.0, 2.0)
    }

    fn calculate_sma(&self, symbol: &str, _period: u32) -> f64 {
        let base_price = match symbol {
            "AAPL" => 175.0,
            "MSFT" => 380.0,
            "GOOGL" => 140.0,
            "AMZN" => 150.0,
            "META" => 350.0,
            "NVDA" => 500.0,
            "TSLA" => 250.0,
            "JPM" => 150.0,
            "V" => 250.0,
            "JNJ" => 160.0,
            _ => 100.0,
        };
        let drift = deterministic_noise(symbol, "sma", -0.03, 0.03);
        base_price * (1.0 + drift)
    }

    fn get_pe_ratio(&self, symbol: &str) -> f64 {
        match symbol {
            "AAPL" => 28.0,
            "MSFT" => 32.0,
            "GOOGL" => 24.0,
            "AMZN" => 45.0,
            "META" => 22.0,
            "NVDA" => 60.0,
            "TSLA" => 50.0,
            "JPM" => 12.0,
            "V" => 35.0,
            "JNJ" => 25.0,
            _ => 20.0,
        }
    }

    fn get_dividend_yield(&self, symbol: &str) -> f64 {
        match symbol {
            "AAPL" => 0.005,
            "MSFT" => 0.007,
            "GOOGL" => 0.0,
            "AMZN" => 0.0,
            "META" => 0.0,
            "NVDA" => 0.0,
            "TSLA" => 0.0,
            "JPM" => 0.025,
            "V" => 0.008,
            "JNJ" => 0.030,
            _ => 0.015,
        }
    }
}

#[async_trait]
impl FeatureSource for StockAnalysisEngine {
    fn asset_class(&self) -> AssetClass {
        AssetClass::Stock
    }

    async fn build_features(&self, symbol: &str) -> Result<HashMap<String, f64>> {
        let resp = self.analyze(symbol).await?;
        Ok(resp.features)
    }
}
