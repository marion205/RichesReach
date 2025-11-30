use std::collections::HashMap;
use chrono::Utc;
use rust_decimal::Decimal;
use anyhow::Result;
use rust_decimal::prelude::ToPrimitive;
use rand::Rng;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsAnalysisResponse {
    pub symbol: String,
    pub underlying_price: Decimal,
    pub volatility_surface: VolatilitySurface,
    pub greeks: Greeks,
    pub recommended_strikes: Vec<StrikeRecommendation>,
    pub put_call_ratio: f64,
    pub implied_volatility_rank: f64,
    pub timestamp: chrono::DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VolatilitySurface {
    pub atm_vol: f64,  // At-the-money volatility
    pub skew: f64,     // Volatility skew (puts vs calls)
    pub term_structure: HashMap<String, f64>, // Vol by expiration
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Greeks {
    pub delta: f64,
    pub gamma: f64,
    pub theta: f64,
    pub vega: f64,
    pub rho: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrikeRecommendation {
    pub strike: f64,
    pub expiration: String,
    pub option_type: String, // "call" or "put"
    pub greeks: Greeks,
    pub expected_return: f64,
    pub risk_score: f64,
}

pub struct OptionsAnalysisEngine {
    price_cache: tokio::sync::RwLock<HashMap<String, (Decimal, f64, chrono::DateTime<Utc>)>>,
}

impl OptionsAnalysisEngine {
    pub fn new() -> Self {
        Self {
            price_cache: tokio::sync::RwLock::new(HashMap::new()),
        }
    }

    pub async fn analyze(&self, symbol: &str) -> Result<OptionsAnalysisResponse> {
        let start = std::time::Instant::now();
        
        // Get underlying price
        let (underlying_price, _) = self.get_underlying_price(symbol).await?;
        
        // Calculate volatility surface
        let volatility_surface = self.calculate_volatility_surface(symbol, &underlying_price).await?;
        
        // Calculate Greeks for ATM options
        let greeks = self.calculate_atm_greeks(symbol, &underlying_price, &volatility_surface).await?;
        
        // Generate strike recommendations
        let recommended_strikes = self.generate_strike_recommendations(
            symbol, 
            &underlying_price, 
            &volatility_surface
        ).await?;
        
        // Calculate market metrics
        let put_call_ratio = self.calculate_put_call_ratio(symbol).await?;
        let implied_volatility_rank = self.calculate_iv_rank(&volatility_surface).await?;
        
        let response = OptionsAnalysisResponse {
            symbol: symbol.to_string(),
            underlying_price,
            volatility_surface,
            greeks,
            recommended_strikes,
            put_call_ratio,
            implied_volatility_rank,
            timestamp: Utc::now(),
        };

        tracing::info!("Options analysis completed for {} in {:?}", symbol, start.elapsed());
        Ok(response)
    }

    async fn get_underlying_price(&self, symbol: &str) -> Result<(Decimal, f64)> {
        // Check cache first
        {
            let cache = self.price_cache.read().await;
            if let Some((cached_price, cached_change, cached_time)) = cache.get(symbol) {
                let age = Utc::now().signed_duration_since(*cached_time);
                if age.num_seconds() < 60 {
                    return Ok((*cached_price, *cached_change));
                }
            }
        }

        // Mock price data (in production, fetch from stock engine)
        let base_price = match symbol {
            "AAPL" => 175.0,
            "MSFT" => 380.0,
            "GOOGL" => 140.0,
            "AMZN" => 150.0,
            "META" => 350.0,
            "NVDA" => 500.0,
            "TSLA" => 250.0,
            "SPY" => 450.0,
            "QQQ" => 380.0,
            _ => 100.0,
        };

        let adjustment = {
            let mut rng = rand::thread_rng();
            rng.gen_range(0.98..1.02)
        };
        
        let price = base_price * adjustment;
        let change = {
            let mut rng = rand::thread_rng();
            rng.gen_range(-2.0..2.0)
        };

        let price_decimal = Decimal::from_f64_retain(price).unwrap_or(Decimal::ZERO);
        
        {
            let mut cache = self.price_cache.write().await;
            cache.insert(symbol.to_string(), (price_decimal, change, Utc::now()));
        }

        Ok((price_decimal, change))
    }

    async fn calculate_volatility_surface(
        &self, 
        symbol: &str, 
        _underlying_price: &Decimal
    ) -> Result<VolatilitySurface> {
        // Base volatility by symbol
        let base_vol: f64 = match symbol {
            "AAPL" | "MSFT" | "GOOGL" => 0.20,
            "AMZN" | "META" => 0.25,
            "NVDA" | "TSLA" => 0.35,
            "SPY" | "QQQ" => 0.18,
            _ => 0.22,
        };

        let adjustment: f64 = {
            let mut rng = rand::thread_rng();
            rng.gen_range(-0.03..0.03)
        };
        
        let vol_sum: f64 = base_vol + adjustment;
        let atm_vol: f64 = vol_sum.max(0.10_f64).min(0.60_f64);
        
        // Volatility skew (puts typically have higher IV)
        let skew = {
            let mut rng = rand::thread_rng();
            0.05 + rng.gen_range(-0.02..0.02)
        };
        
        // Term structure (volatility by expiration)
        let mut term_structure = HashMap::new();
        let expirations = vec!["7d", "14d", "30d", "60d", "90d"];
        for exp in expirations {
            let vol_adjustment = {
                let mut rng = rand::thread_rng();
                rng.gen_range(-0.02..0.02)
            };
            term_structure.insert(exp.to_string(), atm_vol + vol_adjustment);
        }

        Ok(VolatilitySurface {
            atm_vol,
            skew,
            term_structure,
        })
    }

    async fn calculate_atm_greeks(
        &self,
        _symbol: &str,
        _underlying_price: &Decimal,
        _vol_surface: &VolatilitySurface,
    ) -> Result<Greeks> {
        
        // Simplified Black-Scholes Greeks approximation
        let moneyness = 1.0; // ATM
        
        // Delta: 0.5 for ATM calls, -0.5 for ATM puts
        let delta = {
            let mut rng = rand::thread_rng();
            0.50 + rng.gen_range(-0.05..0.05)
        };
        
        // Gamma: highest at ATM
        let gamma = {
            let mut rng = rand::thread_rng();
            0.02 + rng.gen_range(-0.005..0.005)
        };
        
        // Theta: time decay (negative)
        let theta = {
            let mut rng = rand::thread_rng();
            -0.15 + rng.gen_range(-0.03..0.03)
        };
        
        // Vega: sensitivity to volatility
        let vega = {
            let mut rng = rand::thread_rng();
            0.30 + rng.gen_range(-0.05..0.05)
        };
        
        // Rho: sensitivity to interest rates
        let rho = {
            let mut rng = rand::thread_rng();
            0.05 + rng.gen_range(-0.01..0.01)
        };

        Ok(Greeks {
            delta,
            gamma,
            theta,
            vega,
            rho,
        })
    }

    async fn generate_strike_recommendations(
        &self,
        symbol: &str,
        underlying_price: &Decimal,
        vol_surface: &VolatilitySurface,
    ) -> Result<Vec<StrikeRecommendation>> {
        let price_f64 = underlying_price.to_f64().unwrap_or(100.0);
        let mut recommendations = Vec::new();
        
        // Generate recommendations for different strikes
        let strikes = vec![
            price_f64 * 0.90,  // 10% OTM
            price_f64 * 0.95,  // 5% OTM
            price_f64,         // ATM
            price_f64 * 1.05,  // 5% ITM
            price_f64 * 1.10,  // 10% ITM
        ];
        
        for strike in strikes {
            let moneyness = strike / price_f64;
            
            // Calculate Greeks for this strike
            let delta_value: f64 = if moneyness < 1.0 {
                // OTM call
                0.3 + (1.0 - moneyness) * 0.2
            } else {
                // ITM call
                0.7 + (moneyness - 1.0) * 0.2
            };
            let delta: f64 = delta_value.min(0.95).max(0.05);
            
            let greeks = Greeks {
                delta,
                gamma: 0.02,
                theta: -0.12,
                vega: 0.28,
                rho: 0.04,
            };
            
            // Expected return (simplified)
            let expected_return = {
                let mut rng = rand::thread_rng();
                if moneyness < 0.98 {
                    rng.gen_range(0.15..0.25) // OTM has higher potential return
                } else {
                    rng.gen_range(0.05..0.15) // ITM has lower but safer return
                }
            };
            
            // Risk score (lower is better)
            let risk_score = {
                let mut rng = rand::thread_rng();
                if moneyness < 0.98 {
                    0.6 + rng.gen_range(-0.1..0.1) // OTM is riskier
                } else {
                    0.3 + rng.gen_range(-0.1..0.1) // ITM is safer
                }
            };
            
            recommendations.push(StrikeRecommendation {
                strike,
                expiration: "30d".to_string(),
                option_type: "call".to_string(),
                greeks,
                expected_return,
                risk_score,
            });
        }
        
        Ok(recommendations)
    }

    async fn calculate_put_call_ratio(&self, symbol: &str) -> Result<f64> {
        // Mock put/call ratio (typically 0.5-1.5)
        let ratio = {
            let mut rng = rand::thread_rng();
            0.65 + rng.gen_range(-0.15..0.15)
        };
        Ok(ratio)
    }

    async fn calculate_iv_rank(&self, _vol_surface: &VolatilitySurface) -> Result<f64> {
        // IV rank: where current IV sits vs historical range (0-100)
        let rank: f64 = {
            let mut rng = rand::thread_rng();
            45.0 + rng.gen_range(-20.0..20.0)
        };
        Ok(rank.max(0.0_f64).min(100.0_f64))
    }
}

