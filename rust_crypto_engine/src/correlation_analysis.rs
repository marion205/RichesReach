use std::collections::HashMap;
use chrono::Utc;
use rust_decimal::Decimal;
use anyhow::Result;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorrelationAnalysisResponse {
    pub primary_symbol: String,
    pub secondary_symbol: String,
    pub correlation_1d: f64,
    pub correlation_7d: f64,
    pub correlation_30d: f64,
    pub btc_dominance: Option<f64>,
    pub spy_correlation: Option<f64>,
    pub regime: String,  // "RISK_ON", "RISK_OFF", "NEUTRAL"
    pub timestamp: chrono::DateTime<Utc>,
}

pub struct CorrelationAnalysisEngine {
    price_history: tokio::sync::RwLock<HashMap<String, Vec<(chrono::DateTime<Utc>, Decimal)>>>,
}

impl CorrelationAnalysisEngine {
    pub fn new() -> Self {
        Self {
            price_history: tokio::sync::RwLock::new(HashMap::new()),
        }
    }

    pub async fn analyze(
        &self, 
        primary: &str, 
        secondary: Option<&str>
    ) -> Result<CorrelationAnalysisResponse> {
        let start = std::time::Instant::now();
        
        // Default secondary to SPY if not provided
        let secondary = secondary.unwrap_or("SPY");
        
        // Calculate correlations for different timeframes
        let correlation_1d = self.calculate_correlation(primary, secondary, 1).await?;
        let correlation_7d = self.calculate_correlation(primary, secondary, 7).await?;
        let correlation_30d = self.calculate_correlation(primary, secondary, 30).await?;
        
        // Calculate BTC dominance if primary is crypto
        let btc_dominance = if self.is_crypto(primary) {
            Some(self.calculate_btc_dominance().await?)
        } else {
            None
        };
        
        // Calculate SPY correlation if not already calculated
        let spy_correlation = if secondary != "SPY" {
            Some(self.calculate_correlation(primary, "SPY", 30).await?)
        } else {
            Some(correlation_30d)
        };
        
        // Determine market regime
        let regime = self.determine_regime(correlation_30d, btc_dominance).await?;
        
        let response = CorrelationAnalysisResponse {
            primary_symbol: primary.to_string(),
            secondary_symbol: secondary.to_string(),
            correlation_1d,
            correlation_7d,
            correlation_30d,
            btc_dominance,
            spy_correlation,
            regime,
            timestamp: Utc::now(),
        };

        tracing::info!("Correlation analysis completed for {} vs {} in {:?}", primary, secondary, start.elapsed());
        Ok(response)
    }

    async fn calculate_correlation(
        &self,
        symbol1: &str,
        symbol2: &str,
        days: i32,
    ) -> Result<f64> {
        // In production, fetch historical prices and calculate Pearson correlation
        // For now, generate realistic mock correlations
        
        use rand::Rng;
        let mut rng = rand::thread_rng();
        
        // Base correlation depends on asset types
        let base_correlation = if self.is_crypto(symbol1) && self.is_crypto(symbol2) {
            0.7  // Crypto-crypto correlation
        } else if self.is_crypto(symbol1) || self.is_crypto(symbol2) {
            0.3  // Crypto-stock correlation
        } else if symbol1 == "SPY" || symbol2 == "SPY" {
            0.8  // Stock-SPY correlation
        } else {
            0.6  // Stock-stock correlation
        };
        
        // Add noise
        let noise: f64 = rng.gen_range(-0.2..0.2);
        let corr_sum: f64 = base_correlation + noise;
        let correlation: f64 = corr_sum.max(-1.0_f64).min(1.0_f64);
        
        // Shorter timeframes have more noise
        let timeframe_adjustment = if days == 1 {
            rng.gen_range(-0.3..0.3)
        } else if days == 7 {
            rng.gen_range(-0.15..0.15)
        } else {
            rng.gen_range(-0.1..0.1)
        };
        
        let final_correlation: f64 = correlation + timeframe_adjustment;
        Ok(final_correlation.max(-1.0).min(1.0))
    }

    async fn calculate_btc_dominance(&self) -> Result<f64> {
        // BTC dominance: BTC market cap / total crypto market cap
        // Typically ranges from 40% to 60%
        use rand::Rng;
        let mut rng = rand::thread_rng();
        Ok(50.0 + rng.gen_range(-5.0..5.0))
    }

    async fn determine_regime(
        &self,
        correlation: f64,
        btc_dominance: Option<f64>,
    ) -> Result<String> {
        // RISK_ON: High correlation, low BTC dominance (alt coins performing)
        // RISK_OFF: Low correlation, high BTC dominance (flight to safety)
        
        if let Some(dominance) = btc_dominance {
            if dominance < 45.0 && correlation > 0.6 {
                Ok("RISK_ON".to_string())
            } else if dominance > 55.0 && correlation < 0.4 {
                Ok("RISK_OFF".to_string())
            } else {
                Ok("NEUTRAL".to_string())
            }
        } else {
            // For non-crypto, use correlation alone
            if correlation > 0.7 {
                Ok("RISK_ON".to_string())
            } else if correlation < 0.3 {
                Ok("RISK_OFF".to_string())
            } else {
                Ok("NEUTRAL".to_string())
            }
        }
    }

    fn is_crypto(&self, symbol: &str) -> bool {
        matches!(symbol, "BTC" | "ETH" | "ADA" | "SOL" | "DOT" | "MATIC" | "BNB" | "XRP" | "DOGE" | "LINK")
    }
}

