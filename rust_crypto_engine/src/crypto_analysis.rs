use crate::{CryptoAnalysisResponse, CryptoRecommendation};
use std::collections::HashMap;
use chrono::Utc;
use rust_decimal::Decimal;
use anyhow::Result;
use rust_decimal::prelude::ToPrimitive;
use rand::Rng;

pub struct CryptoAnalysisEngine {
    // In-memory cache for fast lookups
    price_cache: HashMap<String, (Decimal, f64, chrono::DateTime<Utc>)>,
}

impl CryptoAnalysisEngine {
    pub fn new() -> Self {
        Self {
            price_cache: HashMap::new(),
        }
    }

    pub async fn analyze(&self, symbol: &str) -> Result<CryptoAnalysisResponse> {
        let start = std::time::Instant::now();
        
        // Simulate high-performance crypto analysis
        let (price_usd, price_change_24h) = self.get_crypto_price(symbol).await?;
        let volatility = self.calculate_volatility(symbol).await?;
        let risk_score = self.calculate_risk_score(symbol, volatility).await?;
        
        // ML-based prediction (simulated for now)
        let prediction_type = self.predict_movement(symbol, &price_usd, volatility).await?;
        let probability = self.calculate_probability(symbol, &prediction_type).await?;
        let confidence_level = self.determine_confidence(probability).await?;
        
        // Generate features for ML model
        let features = self.extract_features(symbol, &price_usd, volatility, risk_score).await?;
        
        // Generate explanation
        let explanation = self.generate_explanation(symbol, &prediction_type, probability, &confidence_level).await?;
        
        let response = CryptoAnalysisResponse {
            symbol: symbol.to_string(),
            prediction_type,
            probability,
            confidence_level,
            explanation,
            features,
            model_version: "rust-v1.0.0".to_string(),
            timestamp: Utc::now(),
            price_usd: Some(price_usd),
            price_change_24h: Some(price_change_24h),
            volatility,
            risk_score,
        };

        tracing::info!("Analysis completed for {} in {:?}", symbol, start.elapsed());
        Ok(response)
    }

    pub async fn get_recommendations(&self, limit: usize, symbols: &[String]) -> Result<Vec<CryptoRecommendation>> {
        let start = std::time::Instant::now();
        
        let mut recommendations = Vec::new();
        
        // If no specific symbols requested, use top cryptocurrencies
        let target_symbols = if symbols.is_empty() {
            vec!["BTC".to_string(), "ETH".to_string(), "ADA".to_string(), "SOL".to_string(), "DOT".to_string(), "MATIC".to_string()]
        } else {
            symbols.to_vec()
        };

        for symbol in target_symbols.iter().take(limit) {
            if let Ok(rec) = self.generate_recommendation(symbol).await {
                recommendations.push(rec);
            }
        }

        // Sort by score (highest first)
        recommendations.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));

        tracing::info!("Generated {} recommendations in {:?}", recommendations.len(), start.elapsed());
        Ok(recommendations)
    }

    async fn get_crypto_price(&self, symbol: &str) -> Result<(Decimal, f64)> {
        // Simulate price fetching (in real implementation, this would call a crypto API)
        let mut rng = rand::thread_rng();
        
        // Mock price data based on symbol
        let base_price = match symbol {
            "BTC" => 45000.0,
            "ETH" => 3000.0,
            "ADA" => 0.45,
            "SOL" => 100.0,
            "DOT" => 6.5,
            "MATIC" => 0.85,
            _ => 1.0,
        };

        // Add some realistic volatility
        let volatility_factor = rng.gen_range(0.95..1.05);
        let price = base_price * volatility_factor;
        let change_24h = rng.gen_range(-15.0..15.0);

        Ok((Decimal::from_f64_retain(price).unwrap_or(Decimal::ZERO), change_24h))
    }

    async fn calculate_volatility(&self, symbol: &str) -> Result<f64> {
        // Simulate volatility calculation
        let mut rng = rand::thread_rng();
        
        let base_volatility = match symbol {
            "BTC" => 0.02,
            "ETH" => 0.03,
            "ADA" => 0.05,
            "SOL" => 0.06,
            "DOT" => 0.04,
            "MATIC" => 0.07,
            _ => 0.05,
        };

        Ok(base_volatility + rng.gen_range(-0.01..0.01))
    }

    async fn calculate_risk_score(&self, symbol: &str, volatility: f64) -> Result<f64> {
        // Risk score based on volatility and market cap
        let market_cap_factor = match symbol {
            "BTC" => 0.1,
            "ETH" => 0.2,
            "ADA" => 0.4,
            "SOL" => 0.5,
            "DOT" => 0.3,
            "MATIC" => 0.6,
            _ => 0.8,
        };

        Ok(volatility * 10.0 + market_cap_factor)
    }

    async fn predict_movement(&self, symbol: &str, price: &Decimal, volatility: f64) -> Result<String> {
        // Simulate ML-based movement prediction
        let mut rng = rand::thread_rng();
        
        // More sophisticated prediction based on price and volatility
        let price_f64 = price.to_f64().unwrap_or(0.0);
        let trend_factor = if price_f64 > 1000.0 { 0.6 } else { 0.4 };
        let volatility_factor = if volatility > 0.05 { 0.3 } else { 0.7 };
        
        let bullish_prob = trend_factor * volatility_factor + rng.gen_range(-0.2..0.2);
        
        if bullish_prob > 0.6 {
            Ok("BULLISH".to_string())
        } else if bullish_prob < 0.4 {
            Ok("BEARISH".to_string())
        } else {
            Ok("NEUTRAL".to_string())
        }
    }

    async fn calculate_probability(&self, symbol: &str, prediction_type: &str) -> Result<f64> {
        let mut rng = rand::thread_rng();
        
        let base_prob = match prediction_type {
            "BULLISH" => 0.65,
            "BEARISH" => 0.60,
            "NEUTRAL" => 0.50,
            _ => 0.50,
        };

        Ok(base_prob + rng.gen_range(-0.15..0.15))
    }

    async fn determine_confidence(&self, probability: f64) -> Result<String> {
        if probability >= 0.8 {
            Ok("HIGH".to_string())
        } else if probability >= 0.6 {
            Ok("MEDIUM".to_string())
        } else {
            Ok("LOW".to_string())
        }
    }

    async fn extract_features(&self, symbol: &str, price: &Decimal, volatility: f64, risk_score: f64) -> Result<HashMap<String, f64>> {
        let mut features = HashMap::new();
        
        features.insert("price_usd".to_string(), price.to_f64().unwrap_or(0.0));
        features.insert("volatility".to_string(), volatility);
        features.insert("risk_score".to_string(), risk_score);
        features.insert("market_cap_rank".to_string(), self.get_market_cap_rank(symbol));
        features.insert("volume_24h".to_string(), self.get_volume_24h(symbol));
        features.insert("rsi".to_string(), self.calculate_rsi(symbol));
        features.insert("macd".to_string(), self.calculate_macd(symbol));
        features.insert("sma_20".to_string(), self.calculate_sma(symbol, 20));
        features.insert("sma_50".to_string(), self.calculate_sma(symbol, 50));
        
        Ok(features)
    }

    async fn generate_explanation(&self, symbol: &str, prediction_type: &str, probability: f64, confidence: &str) -> Result<String> {
        let confidence_desc = match confidence {
            "HIGH" => "high confidence",
            "MEDIUM" => "moderate confidence", 
            "LOW" => "low confidence",
            _ => "uncertain",
        };

        let direction = match prediction_type {
            "BULLISH" => "upward",
            "BEARISH" => "downward",
            "NEUTRAL" => "sideways",
            _ => "uncertain",
        };

        Ok(format!(
            "Based on technical analysis and market indicators, {} shows {} momentum with {} ({}% probability). \
             The analysis considers price trends, volatility patterns, and trading volume to generate this prediction.",
            symbol, direction, confidence_desc, (probability * 100.0) as i32
        ))
    }

    async fn generate_recommendation(&self, symbol: &str) -> Result<CryptoRecommendation> {
        let (price_usd, _) = self.get_crypto_price(symbol).await?;
        let volatility = self.calculate_volatility(symbol).await?;
        let risk_score = self.calculate_risk_score(symbol, volatility).await?;
        
        let score = self.calculate_recommendation_score(symbol, &price_usd, volatility, risk_score).await?;
        let probability = self.calculate_probability(symbol, "BULLISH").await?;
        let confidence_level = self.determine_confidence(probability).await?;
        
        let volatility_tier = if volatility < 0.03 { "LOW" } else if volatility < 0.06 { "MEDIUM" } else { "HIGH" };
        let risk_level = if risk_score < 0.5 { "LOW" } else if risk_score < 0.8 { "MEDIUM" } else { "HIGH" };
        
        let recommendation = if score > 0.7 { "BUY" } else if score > 0.4 { "HOLD" } else { "AVOID" };
        
        let rationale = self.generate_recommendation_rationale(symbol, score, volatility, risk_score).await?;
        
        Ok(CryptoRecommendation {
            symbol: symbol.to_string(),
            score,
            probability,
            confidence_level,
            price_usd,
            volatility_tier: volatility_tier.to_string(),
            liquidity_24h_usd: price_usd * Decimal::from(1000000), // Mock liquidity
            rationale,
            recommendation: recommendation.to_string(),
            risk_level: risk_level.to_string(),
        })
    }

    async fn calculate_recommendation_score(&self, symbol: &str, price: &Decimal, volatility: f64, risk_score: f64) -> Result<f64> {
        let mut rng = rand::thread_rng();
        
        // Base score from market cap rank
        let base_score = match symbol {
            "BTC" => 0.8,
            "ETH" => 0.75,
            "ADA" => 0.6,
            "SOL" => 0.65,
            "DOT" => 0.55,
            "MATIC" => 0.5,
            _ => 0.4,
        };

        // Adjust for volatility (lower volatility = higher score)
        let volatility_adjustment = 1.0 - (volatility * 2.0).min(0.5);
        
        // Adjust for risk (lower risk = higher score)
        let risk_adjustment = 1.0 - (risk_score * 0.3).min(0.3);
        
        let final_score = base_score * volatility_adjustment * risk_adjustment + rng.gen_range(-0.1..0.1);
        
        Ok(final_score.max(0.0).min(1.0))
    }

    async fn generate_recommendation_rationale(&self, symbol: &str, score: f64, volatility: f64, risk_score: f64) -> Result<String> {
        let volatility_desc = if volatility < 0.03 { "low volatility" } else if volatility < 0.06 { "moderate volatility" } else { "high volatility" };
        let risk_desc = if risk_score < 0.5 { "low risk" } else if risk_score < 0.8 { "moderate risk" } else { "high risk" };
        
        Ok(format!(
            "{} shows strong fundamentals with {} and {} profile. \
             Technical indicators suggest favorable entry conditions with a score of {:.1}/10. \
             Consider your risk tolerance before investing.",
            symbol, volatility_desc, risk_desc, score * 10.0
        ))
    }

    // Helper methods for technical indicators
    fn get_market_cap_rank(&self, symbol: &str) -> f64 {
        match symbol {
            "BTC" => 1.0,
            "ETH" => 2.0,
            "ADA" => 8.0,
            "SOL" => 5.0,
            "DOT" => 12.0,
            "MATIC" => 15.0,
            _ => 100.0,
        }
    }

    fn get_volume_24h(&self, symbol: &str) -> f64 {
        match symbol {
            "BTC" => 25000000000.0,
            "ETH" => 15000000000.0,
            "ADA" => 2000000000.0,
            "SOL" => 3000000000.0,
            "DOT" => 800000000.0,
            "MATIC" => 1200000000.0,
            _ => 100000000.0,
        }
    }

    fn calculate_rsi(&self, symbol: &str) -> f64 {
        let mut rng = rand::thread_rng();
        rng.gen_range(30.0..70.0) // Mock RSI
    }

    fn calculate_macd(&self, symbol: &str) -> f64 {
        let mut rng = rand::thread_rng();
        rng.gen_range(-0.1..0.1) // Mock MACD
    }

    fn calculate_sma(&self, symbol: &str, period: u32) -> f64 {
        let (price, _) = self.get_crypto_price_sync(symbol);
        price.to_f64().unwrap_or(0.0) * (1.0 + rand::thread_rng().gen_range(-0.05..0.05))
    }

    fn get_crypto_price_sync(&self, symbol: &str) -> (Decimal, f64) {
        // Synchronous version for technical indicators
        let base_price = match symbol {
            "BTC" => 45000.0,
            "ETH" => 3000.0,
            "ADA" => 0.45,
            "SOL" => 100.0,
            "DOT" => 6.5,
            "MATIC" => 0.85,
            _ => 1.0,
        };
        
        (Decimal::from_f64_retain(base_price).unwrap_or(Decimal::ZERO), 0.0)
    }
}
