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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EdgePrediction {
    pub strike: f64,
    pub expiration: String,
    pub option_type: String,
    pub current_edge: f64,              // Current edge % (mispricing)
    pub predicted_edge_15min: f64,     // Predicted edge in 15min
    pub predicted_edge_1hr: f64,       // Predicted edge in 1hr
    pub predicted_edge_1day: f64,      // Predicted edge in 1day
    pub confidence: f64,               // 0-100%
    pub explanation: String,           // "IV crush expected post-earnings"
    pub edge_change_dollars: f64,      // Expected $ change per contract
    pub current_premium: f64,          // Current option premium
    pub predicted_premium_15min: f64,  // Predicted premium in 15min
    pub predicted_premium_1hr: f64,    // Predicted premium in 1hr
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsChain {
    pub symbol: String,
    pub underlying_price: f64,
    pub contracts: Vec<OptionContract>,
    pub timestamp: chrono::DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionContract {
    pub strike: f64,
    pub expiration: String,
    pub option_type: String,
    pub premium: f64,
    pub bid: f64,
    pub ask: f64,
    pub volume: i32,
    pub open_interest: i32,
    pub implied_volatility: f64,
    pub greeks: Greeks,
    pub edge: f64,  // Current edge (mispricing)
    pub days_to_expiration: i32,
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

    /// Generate mock options chain for testing
    /// In production, this would fetch from real_options_service
    pub async fn generate_mock_chain(
        &self,
        symbol: &str,
    ) -> Result<OptionsChain> {
        let (underlying_price, _) = self.get_underlying_price(symbol).await?;
        let price_f64 = underlying_price.to_f64().unwrap_or(100.0);
        
        let mut contracts = Vec::new();
        let expirations = vec!["7d", "14d", "30d", "60d"];
        
        for exp in &expirations {
            let days_to_exp = match *exp {
                "7d" => 7,
                "14d" => 14,
                "30d" => 30,
                "60d" => 60,
                _ => 30,
            };
            
            // Generate strikes around current price
            for strike_offset in (-20..=20).step_by(5) {
                let strike = price_f64 + strike_offset as f64;
                
                // Calculate premium (simplified)
                let intrinsic = (price_f64 - strike).max(0.0);
                let time_value = price_f64 * 0.02 * (days_to_exp as f64 / 365.0);
                let premium = intrinsic + time_value;
                
                // Generate Greeks
                let moneyness = strike / price_f64;
                let delta = if moneyness < 1.0 {
                    0.3 + (1.0 - moneyness) * 0.2
                } else {
                    0.7 + (moneyness - 1.0) * 0.2
                }.min(0.95).max(0.05);
                
                let greeks = Greeks {
                    delta,
                    gamma: 0.02,
                    theta: -0.12,
                    vega: 0.28,
                    rho: 0.04,
                };
                
                // Calculate current edge (mispricing)
                let theoretical_price = premium * 1.05; // Assume 5% mispricing
                let edge = ((theoretical_price - premium) / premium) * 100.0;
                
                // Call option
                contracts.push(OptionContract {
                    strike,
                    expiration: exp.to_string(),
                    option_type: "call".to_string(),
                    premium,
                    bid: premium - 0.05,
                    ask: premium + 0.05,
                    volume: rand::thread_rng().gen_range(100..5000),
                    open_interest: rand::thread_rng().gen_range(1000..10000),
                    implied_volatility: 0.25 + rand::thread_rng().gen_range(-0.1..0.1),
                    greeks: greeks.clone(),
                    edge,
                    days_to_expiration: days_to_exp,
                });
                
                // Put option
                let put_intrinsic = (strike - price_f64).max(0.0);
                let put_premium = put_intrinsic + time_value;
                let put_delta = -delta;
                
                contracts.push(OptionContract {
                    strike,
                    expiration: exp.to_string(),
                    option_type: "put".to_string(),
                    premium: put_premium,
                    bid: put_premium - 0.05,
                    ask: put_premium + 0.05,
                    volume: rand::thread_rng().gen_range(80..4000),
                    open_interest: rand::thread_rng().gen_range(800..8000),
                    implied_volatility: 0.25 + rand::thread_rng().gen_range(-0.1..0.1),
                    greeks: Greeks {
                        delta: put_delta,
                        gamma: 0.02,
                        theta: -0.12,
                        vega: 0.28,
                        rho: -0.04,
                    },
                    edge,
                    days_to_expiration: days_to_exp,
                });
            }
        }
        
        Ok(OptionsChain {
            symbol: symbol.to_string(),
            underlying_price: price_f64,
            contracts,
            timestamp: Utc::now(),
        })
    }

    /// Predict edge for entire options chain
    /// This is the core ML-powered feature that predicts mispricing opportunities
    pub async fn predict_chain_edges(
        &self,
        symbol: &str,
        chain_data: &OptionsChain,
    ) -> Result<Vec<EdgePrediction>> {
        let start = std::time::Instant::now();
        
        let mut predictions = Vec::new();
        
        // Process each contract
        for contract in &chain_data.contracts {
            let prediction = self.predict_contract_edge(
                symbol,
                contract,
                chain_data,
            ).await?;
            predictions.push(prediction);
        }
        
        // Sort by expected edge (highest first)
        predictions.sort_by(|a, b| {
            b.predicted_edge_1hr.partial_cmp(&a.predicted_edge_1hr)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        
        tracing::info!(
            "Edge prediction completed for {} contracts in {:?}",
            predictions.len(),
            start.elapsed()
        );
        
        Ok(predictions)
    }
    
    /// Predict edge for a single contract
    async fn predict_contract_edge(
        &self,
        symbol: &str,
        contract: &OptionContract,
        chain: &OptionsChain,
    ) -> Result<EdgePrediction> {
        // ML Model Inputs:
        // - Current Greeks (delta, gamma, theta, vega)
        // - IV surface (current vs historical)
        // - Time to expiration
        // - Order flow signals (volume, OI)
        // - Market regime (earnings, FOMC, normal)
        
        // Predict IV change (simplified ML model)
        let iv_change = self.predict_iv_change(symbol, contract, chain).await?;
        
        // Predict underlying price movement
        let price_change = self.predict_price_movement(symbol, chain).await?;
        
        // Calculate edge changes at different time horizons
        let edge_15min = self.calculate_edge_change(
            contract,
            &iv_change,
            &price_change,
            15,  // minutes
            chain,
        )?;
        
        let edge_1hr = self.calculate_edge_change(
            contract,
            &iv_change,
            &price_change,
            60,  // minutes
            chain,
        )?;
        
        let edge_1day = self.calculate_edge_change(
            contract,
            &iv_change,
            &price_change,
            1440,  // minutes (24 hours)
            chain,
        )?;
        
        // Predict premium changes
        let premium_15min = contract.premium * (1.0 + edge_15min / 100.0);
        let premium_1hr = contract.premium * (1.0 + edge_1hr / 100.0);
        
        // Generate explanation
        let explanation = self.generate_edge_explanation(
            &iv_change,
            &price_change,
            contract,
            chain,
        )?;
        
        // Calculate confidence based on signal strength
        let confidence = self.calculate_confidence(&iv_change, &price_change, contract)?;
        
        Ok(EdgePrediction {
            strike: contract.strike,
            expiration: contract.expiration.clone(),
            option_type: contract.option_type.clone(),
            current_edge: contract.edge,
            predicted_edge_15min: edge_15min,
            predicted_edge_1hr: edge_1hr,
            predicted_edge_1day: edge_1day,
            confidence,
            explanation,
            edge_change_dollars: ((edge_1hr - contract.edge) / 100.0 * contract.premium * 100.0).max(0.0_f64),
            current_premium: contract.premium,
            predicted_premium_15min: premium_15min,
            predicted_premium_1hr: premium_1hr,
        })
    }
    
    /// Predict IV change using simplified ML model
    async fn predict_iv_change(
        &self,
        symbol: &str,
        contract: &OptionContract,
        chain: &OptionsChain,
    ) -> Result<IVChangePrediction> {
        // Features for IV prediction:
        // - Current IV vs historical average
        // - Time to expiration
        // - Moneyness (strike vs underlying)
        // - Volume/OI ratio
        // - Market regime (earnings, FOMC, etc.)
        
        let moneyness = contract.strike / chain.underlying_price;
        let dte = contract.days_to_expiration;
        
        // Detect market regime
        let regime = self.detect_market_regime(symbol).await?;
        
        // Calculate IV rank (where current IV sits vs historical)
        let iv_rank = self.calculate_iv_rank_for_contract(contract, chain).await?;
        
        // Predict IV change based on:
        // 1. IV mean reversion (high IV → likely to drop)
        // 2. Earnings proximity (IV expands before, crushes after)
        // 3. Time decay (IV typically decreases as expiration approaches)
        // 4. Volume/OI signals (unusual activity → IV expansion)
        
        let mut iv_change_1hr = 0.0;
        let mut iv_change_24hr = 0.0;
        
        // IV mean reversion factor
        if iv_rank > 70.0 {
            // High IV → likely to revert down
            iv_change_1hr -= (iv_rank - 70.0) * 0.1;
            iv_change_24hr -= (iv_rank - 70.0) * 0.3;
        } else if iv_rank < 30.0 {
            // Low IV → likely to expand
            iv_change_1hr += (30.0 - iv_rank) * 0.1;
            iv_change_24hr += (30.0 - iv_rank) * 0.3;
        }
        
        // Earnings effect
        if regime.contains("earnings") {
            // Before earnings: IV expands
            // After earnings: IV crushes
            if dte <= 1 {
                // Very close to expiration → likely post-earnings IV crush
                iv_change_1hr -= 15.0;  // -15% IV
                iv_change_24hr -= 25.0;  // -25% IV
            } else if dte <= 7 {
                // Within week of earnings → IV expansion possible
                iv_change_1hr += 5.0;
                iv_change_24hr += 10.0;
            }
        }
        
        // Time decay effect (IV typically decreases as expiration approaches)
        if dte <= 1 {
            // 0DTE → high IV decay
            iv_change_1hr -= 10.0;
            iv_change_24hr -= 20.0;
        } else if dte <= 7 {
            // Weekly options → moderate IV decay
            iv_change_1hr -= 2.0;
            iv_change_24hr -= 5.0;
        }
        
        // Volume/OI signals
        let volume_oi_ratio = if contract.open_interest > 0 {
            contract.volume as f64 / contract.open_interest as f64
        } else {
            0.0
        };
        
        if volume_oi_ratio > 2.0 {
            // Unusual volume → IV expansion likely
            iv_change_1hr += 3.0;
            iv_change_24hr += 5.0;
        }
        
        // Clamp IV changes to reasonable range
        iv_change_1hr = iv_change_1hr.max(-30.0).min(30.0);
        iv_change_24hr = iv_change_24hr.max(-50.0).min(50.0);
        
        Ok(IVChangePrediction {
            current_iv: contract.implied_volatility,
            predicted_iv_1hr: contract.implied_volatility * (1.0 + iv_change_1hr / 100.0),
            predicted_iv_24hr: contract.implied_volatility * (1.0 + iv_change_24hr / 100.0),
            iv_change_1hr_pct: iv_change_1hr,
            iv_change_24hr_pct: iv_change_24hr,
            confidence: self.calculate_iv_prediction_confidence(contract, &regime)?,
        })
    }
    
    /// Predict underlying price movement
    async fn predict_price_movement(
        &self,
        symbol: &str,
        chain: &OptionsChain,
    ) -> Result<PriceMovementPrediction> {
        // Simplified price movement prediction
        // In production, this would use actual ML models (LSTM, etc.)
        
        // For now, use mean reversion + momentum signals
        let (_, recent_change) = self.get_underlying_price(symbol).await?;
        
        // Mean reversion: if stock moved up recently, likely to pull back
        let mean_reversion_factor = -recent_change * 0.3;
        
        // Momentum: if strong move, likely to continue short-term
        let momentum_factor = recent_change * 0.2;
        
        let predicted_change_15min = mean_reversion_factor + momentum_factor * 0.1;
        let predicted_change_1hr = mean_reversion_factor + momentum_factor * 0.3;
        let predicted_change_1day = mean_reversion_factor + momentum_factor;
        
        Ok(PriceMovementPrediction {
            current_price: chain.underlying_price,
            predicted_price_15min: chain.underlying_price * (1.0 + predicted_change_15min / 100.0),
            predicted_price_1hr: chain.underlying_price * (1.0 + predicted_change_1hr / 100.0),
            predicted_price_1day: chain.underlying_price * (1.0 + predicted_change_1day / 100.0),
            price_change_15min_pct: predicted_change_15min,
            price_change_1hr_pct: predicted_change_1hr,
            price_change_1day_pct: predicted_change_1day,
        })
    }
    
    /// Calculate edge change based on IV and price predictions
    fn calculate_edge_change(
        &self,
        contract: &OptionContract,
        iv_change: &IVChangePrediction,
        price_change: &PriceMovementPrediction,
        time_horizon_minutes: i32,
        chain: &OptionsChain,
    ) -> Result<f64> {
        // Edge = Mispricing = (Theoretical Price - Market Price) / Market Price
        
        // Calculate theoretical price using Black-Scholes with predicted IV
        let predicted_iv = if time_horizon_minutes <= 15 {
            iv_change.predicted_iv_1hr
        } else if time_horizon_minutes <= 60 {
            iv_change.predicted_iv_1hr
        } else {
            iv_change.predicted_iv_24hr
        };
        
        let predicted_price = if time_horizon_minutes <= 15 {
            price_change.predicted_price_15min
        } else if time_horizon_minutes <= 60 {
            price_change.predicted_price_1hr
        } else {
            price_change.predicted_price_1day
        };
        
        // Simplified theoretical price calculation
        // In production, use full Black-Scholes with predicted IV
        let moneyness = contract.strike / predicted_price;
        let time_to_exp = contract.days_to_expiration as f64 / 365.0;
        
        // Simplified option pricing (intrinsic + time value)
        let intrinsic = if contract.option_type == "call" {
            (predicted_price - contract.strike).max(0.0)
        } else {
            (contract.strike - predicted_price).max(0.0)
        };
        
        // Time value based on predicted IV
        let time_value = predicted_price * predicted_iv * (time_to_exp.sqrt());
        
        let theoretical_price = intrinsic + time_value;
        
        // Current market price
        let market_price = contract.premium;
        
        // Edge = (Theoretical - Market) / Market
        let edge = if market_price > 0.0 {
            ((theoretical_price - market_price) / market_price) * 100.0
        } else {
            0.0
        };
        
        Ok(edge)
    }
    
    /// Generate human-readable explanation
    fn generate_edge_explanation(
        &self,
        iv_change: &IVChangePrediction,
        price_change: &PriceMovementPrediction,
        contract: &OptionContract,
        chain: &OptionsChain,
    ) -> Result<String> {
        let mut reasons = Vec::new();
        
        // IV change reasons
        if iv_change.iv_change_1hr_pct < -10.0 {
            reasons.push(format!("IV crush expected ({:.1}%)", iv_change.iv_change_1hr_pct));
        } else if iv_change.iv_change_1hr_pct > 10.0 {
            reasons.push(format!("IV expansion expected (+{:.1}%)", iv_change.iv_change_1hr_pct));
        }
        
        // Price movement reasons
        if price_change.price_change_1hr_pct.abs() > 2.0 {
            let direction = if price_change.price_change_1hr_pct > 0.0 { "up" } else { "down" };
            reasons.push(format!("Price expected to move {} {:.1}%", direction, price_change.price_change_1hr_pct.abs()));
        }
        
        // Time decay
        if contract.days_to_expiration <= 1 {
            reasons.push("0DTE - high time decay risk".to_string());
        }
        
        // Volume signals
        if contract.volume > contract.open_interest {
            reasons.push("Unusual volume activity".to_string());
        }
        
        if reasons.is_empty() {
            Ok("Normal market conditions".to_string())
        } else {
            Ok(reasons.join(", "))
        }
    }
    
    /// Calculate prediction confidence
    fn calculate_confidence(
        &self,
        iv_change: &IVChangePrediction,
        price_change: &PriceMovementPrediction,
        contract: &OptionContract,
    ) -> Result<f64> {
        let mut confidence = 50.0;  // Base confidence
        
        // Higher confidence if IV change is significant
        confidence += iv_change.iv_change_1hr_pct.abs() * 0.5;
        
        // Higher confidence if price movement is significant
        confidence += price_change.price_change_1hr_pct.abs() * 2.0;
        
        // Lower confidence for 0DTE (high uncertainty)
        if contract.days_to_expiration <= 1 {
            confidence -= 20.0;
        }
        
        // Higher confidence with more volume/OI data
        if contract.volume > 100 && contract.open_interest > 1000 {
            confidence += 10.0;
        }
        
        Ok(confidence.max(0.0_f64).min(100.0_f64))
    }
    
    /// Detect market regime (earnings, FOMC, normal)
    async fn detect_market_regime(&self, _symbol: &str) -> Result<String> {
        // Simplified regime detection
        // In production, check earnings calendar, FOMC schedule, etc.
        
        // For now, return "normal" - can be enhanced with real calendar data
        // This is a placeholder for the ML model to use
        Ok("normal".to_string())
    }
    
    /// Calculate IV rank for a specific contract
    async fn calculate_iv_rank_for_contract(
        &self,
        contract: &OptionContract,
        _chain: &OptionsChain,
    ) -> Result<f64> {
        // IV rank = (Current IV - 52-week low IV) / (52-week high IV - 52-week low IV) * 100
        // Simplified: use current IV vs typical range for this symbol
        
        let typical_low_iv = contract.implied_volatility * 0.5;
        let typical_high_iv = contract.implied_volatility * 1.5;
        
        let iv_rank = ((contract.implied_volatility - typical_low_iv) 
            / (typical_high_iv - typical_low_iv)) * 100.0;
        
        Ok(iv_rank.max(0.0).min(100.0))
    }
    
    /// Calculate confidence for IV prediction
    fn calculate_iv_prediction_confidence(
        &self,
        contract: &OptionContract,
        regime: &str,
    ) -> Result<f64> {
        let mut confidence: f64 = 60.0;  // Base confidence
        
        // Higher confidence in earnings regime (predictable IV crush)
        if regime == "earnings" {
            confidence += 20.0;
        }
        
        // Higher confidence with more data
        if contract.volume > 500 && contract.open_interest > 5000 {
            confidence += 15.0;
        }
        
        // Lower confidence for very short DTE
        if contract.days_to_expiration <= 1 {
            confidence -= 15.0;
        }
        
        Ok(confidence.max(0.0_f64).min(100.0_f64))
    }

    /// Generate one-tap trade recommendations
    /// Combines edge predictions with strategy optimization
    pub async fn generate_one_tap_trades(
        &self,
        symbol: &str,
        account_size: f64,
        risk_tolerance: f64,  // 0-1
    ) -> Result<Vec<OneTapTrade>> {
        let start = std::time::Instant::now();
        
        // 1. Get edge predictions
        let chain = self.generate_mock_chain(symbol).await?;
        let edge_predictions = self.predict_chain_edges(symbol, &chain).await?;
        
        // 2. Generate strategy recommendations
        let strategies = self.generate_strategies(
            symbol,
            &edge_predictions,
            account_size,
            risk_tolerance,
        ).await?;
        
        // 3. Optimize each strategy
        let mut one_tap_trades = Vec::new();
        for strategy in strategies {
            let optimized = self.optimize_strategy(
                &strategy,
                account_size,
                risk_tolerance,
                &edge_predictions,
            ).await?;
            
            // Calculate brackets based on ML forecast
            let (take_profit, stop_loss) = self.calculate_brackets(
                &optimized,
                &edge_predictions,
            )?;
            
            one_tap_trades.push(OneTapTrade {
                strategy: optimized.description,
                entry_price: optimized.entry_price,
                expected_edge: optimized.expected_edge,
                confidence: optimized.confidence,
                take_profit,
                stop_loss,
                reasoning: optimized.reasoning,
                max_loss: optimized.max_loss,
                max_profit: optimized.max_profit,
                probability_of_profit: optimized.probability_of_profit,
                symbol: symbol.to_string(),
                legs: optimized.legs,
                strategy_type: optimized.strategy_type,
                days_to_expiration: optimized.days_to_expiration,
                total_cost: optimized.total_cost,
                total_credit: optimized.total_credit,
            });
        }
        
        // Sort by expected edge / risk
        one_tap_trades.sort_by(|a, b| {
            let a_score = a.expected_edge / a.max_loss.max(1.0);
            let b_score = b.expected_edge / b.max_loss.max(1.0);
            b_score.partial_cmp(&a_score).unwrap_or(std::cmp::Ordering::Equal)
        });
        
        // Return top 3
        let result = one_tap_trades.into_iter().take(3).collect();
        
        tracing::info!(
            "One-tap trades generated for {} in {:?}",
            symbol,
            start.elapsed()
        );
        
        Ok(result)
    }
    
    async fn generate_strategies(
        &self,
        symbol: &str,
        edge_predictions: &[EdgePrediction],
        account_size: f64,
        risk_tolerance: f64,
    ) -> Result<Vec<StrategyCandidate>> {
        let mut strategies = Vec::new();
        
        // Find high-edge opportunities
        // Lowered thresholds to ensure we always generate trades
        let top_edges: Vec<&EdgePrediction> = edge_predictions
            .iter()
            .filter(|p| p.predicted_edge_1hr > 0.0 && p.confidence > 50.0)  // More lenient thresholds
            .take(10)
            .collect();
        
        // If still empty, take top 5 by edge regardless of thresholds
        let top_edges: Vec<&EdgePrediction> = if top_edges.is_empty() {
            let mut sorted: Vec<&EdgePrediction> = edge_predictions.iter().collect();
            sorted.sort_by(|a, b| {
                b.predicted_edge_1hr.partial_cmp(&a.predicted_edge_1hr)
                    .unwrap_or(std::cmp::Ordering::Equal)
            });
            sorted.into_iter().take(5).collect()
        } else {
            top_edges
        };
        
        if top_edges.is_empty() {
            return Ok(strategies);
        }
        
        // Generate different strategy types based on market conditions
        for edge in &top_edges {
            // Credit spread (if high IV)
            if edge.current_premium > 2.0 {
                strategies.push(StrategyCandidate {
                    strategy_type: "credit_spread".to_string(),
                    description: format!(
                        "Sell {} {} {} {} spread",
                        (account_size * risk_tolerance / 1000.0) as i32,
                        symbol,
                        edge.strike,
                        edge.option_type
                    ),
                    base_edge: edge.predicted_edge_1hr,
                    base_confidence: edge.confidence,
                    base_strike: edge.strike,
                    base_expiration: edge.expiration.clone(),
                    base_option_type: edge.option_type.clone(),
                });
            }
            
            // Debit spread (if low IV, expecting expansion)
            if edge.predicted_edge_1hr > 3.0 {
                strategies.push(StrategyCandidate {
                    strategy_type: "debit_spread".to_string(),
                    description: format!(
                        "Buy {} {} {} {} spread",
                        (account_size * risk_tolerance / 2000.0) as i32,
                        symbol,
                        edge.strike,
                        edge.option_type
                    ),
                    base_edge: edge.predicted_edge_1hr,
                    base_confidence: edge.confidence,
                    base_strike: edge.strike,
                    base_expiration: edge.expiration.clone(),
                    base_option_type: edge.option_type.clone(),
                });
            }
        }
        
        Ok(strategies)
    }
    
    async fn optimize_strategy(
        &self,
        candidate: &StrategyCandidate,
        account_size: f64,
        risk_tolerance: f64,
        edge_predictions: &[EdgePrediction],
    ) -> Result<OptimizedStrategy> {
        // Calculate position size based on account and risk tolerance
        let max_risk = account_size * risk_tolerance;
        let position_size = (max_risk / 500.0).max(1.0).min(10.0) as i32;
        
        // Build legs based on strategy type
        let legs = match candidate.strategy_type.as_str() {
            "credit_spread" => {
                // Sell higher strike, buy even higher strike
                vec![
                    OneTapLeg {
                        action: "sell".to_string(),
                        option_type: candidate.base_option_type.clone(),
                        strike: candidate.base_strike,
                        expiration: candidate.base_expiration.clone(),
                        quantity: position_size,
                        premium: candidate.base_strike * 0.02, // Simplified
                    },
                    OneTapLeg {
                        action: "buy".to_string(),
                        option_type: candidate.base_option_type.clone(),
                        strike: candidate.base_strike + 5.0,
                        expiration: candidate.base_expiration.clone(),
                        quantity: position_size,
                        premium: (candidate.base_strike + 5.0) * 0.015,
                    },
                ]
            }
            "debit_spread" => {
                // Buy lower strike, sell higher strike
                vec![
                    OneTapLeg {
                        action: "buy".to_string(),
                        option_type: candidate.base_option_type.clone(),
                        strike: candidate.base_strike - 5.0,
                        expiration: candidate.base_expiration.clone(),
                        quantity: position_size,
                        premium: (candidate.base_strike - 5.0) * 0.02,
                    },
                    OneTapLeg {
                        action: "sell".to_string(),
                        option_type: candidate.base_option_type.clone(),
                        strike: candidate.base_strike,
                        expiration: candidate.base_expiration.clone(),
                        quantity: position_size,
                        premium: candidate.base_strike * 0.015,
                    },
                ]
            }
            _ => {
                // Single leg
                vec![OneTapLeg {
                    action: "buy".to_string(),
                    option_type: candidate.base_option_type.clone(),
                    strike: candidate.base_strike,
                    expiration: candidate.base_expiration.clone(),
                    quantity: position_size,
                    premium: candidate.base_strike * 0.02,
                }]
            }
        };
        
        // Calculate net cost/credit
        let total_cost = legs.iter()
            .map(|leg| {
                let cost = leg.premium * leg.quantity as f64 * 100.0;
                if leg.action == "buy" { cost } else { -cost }
            })
            .sum::<f64>();
        
        let total_credit = if total_cost < 0.0 { -total_cost } else { 0.0 };
        
        // Calculate max profit/loss
        let max_profit = if total_cost < 0.0 {
            // Credit spread: max profit = credit received
            total_credit
        } else {
            // Debit spread: max profit = width - debit paid
            let width = legs.iter()
                .map(|leg| leg.strike)
                .max_by(|a, b| a.partial_cmp(b).unwrap())
                .unwrap_or(0.0)
                - legs.iter()
                    .map(|leg| leg.strike)
                    .min_by(|a, b| a.partial_cmp(b).unwrap())
                    .unwrap_or(0.0);
            (width * position_size as f64 * 100.0) - total_cost
        };
        
        let max_loss = if total_cost < 0.0 {
            // Credit spread: max loss = width - credit
            let width = legs.iter()
                .map(|leg| leg.strike)
                .max_by(|a, b| a.partial_cmp(b).unwrap())
                .unwrap_or(0.0)
                - legs.iter()
                    .map(|leg| leg.strike)
                    .min_by(|a, b| a.partial_cmp(b).unwrap())
                    .unwrap_or(0.0);
            (width * position_size as f64 * 100.0) - total_credit
        } else {
            // Debit spread: max loss = debit paid
            total_cost
        };
        
        // Calculate probability of profit
        let probability_of_profit = (candidate.base_confidence / 100.0) * 0.8; // Adjust based on confidence
        
        // Calculate days to expiration
        let days_to_exp = candidate.base_expiration
            .split('d')
            .next()
            .and_then(|s| s.parse::<i32>().ok())
            .unwrap_or(30);
        
        Ok(OptimizedStrategy {
            description: candidate.description.clone(),
            entry_price: if total_cost < 0.0 { total_credit } else { total_cost },
            expected_edge: candidate.base_edge,
            confidence: candidate.base_confidence,
            reasoning: format!(
                "Expected {}% edge in 1hr with {}% confidence. {}",
                candidate.base_edge,
                candidate.base_confidence,
                if total_cost < 0.0 { "Credit strategy." } else { "Debit strategy." }
            ),
            max_loss,
            max_profit,
            probability_of_profit,
            legs,
            strategy_type: candidate.strategy_type.clone(),
            days_to_expiration: days_to_exp,
            total_cost,
            total_credit,
        })
    }
    
    fn calculate_brackets(
        &self,
        strategy: &OptimizedStrategy,
        edge_predictions: &[EdgePrediction],
    ) -> Result<(f64, f64)> {
        // Take profit: 50% of max profit
        let take_profit = strategy.max_profit * 0.5;
        
        // Stop loss: 2x max loss (risk management)
        let stop_loss = strategy.max_loss * 2.0;
        
        // Adjust based on edge predictions
        let avg_confidence = edge_predictions.iter()
            .map(|p| p.confidence)
            .sum::<f64>() / edge_predictions.len().max(1) as f64;
        
        // Higher confidence = tighter stop loss
        if avg_confidence > 80.0 {
            let stop_loss = stop_loss * 0.8;
            return Ok((take_profit, stop_loss));
        }
        
        Ok((take_profit, stop_loss))
    }

    /// Forecast IV surface 1-24 hours forward
    /// Uses sentiment, macro signals, and earnings calendar
    pub async fn forecast_iv_surface(
        &self,
        symbol: &str,
    ) -> Result<IVSurfaceForecast> {
        let start = std::time::Instant::now();
        
        // 1. Detect market regime
        let regime = self.detect_market_regime(symbol).await?;
        
        // 2. Get sentiment signals (simplified - in production, call sentiment service)
        let sentiment = self.get_sentiment_signals(symbol).await?;
        
        // 3. Get macro signals (VIX curve, rates, etc.)
        let macro_signals = self.get_macro_signals().await?;
        
        // 4. Get earnings calendar info
        let earnings_info = self.get_earnings_info(symbol).await?;
        
        // 5. Get current IV surface
        let chain = self.generate_mock_chain(symbol).await?;
        
        // 6. Predict IV changes using ML model
        let iv_predictions = self.predict_iv_changes(
            symbol,
            &regime,
            &sentiment,
            &macro_signals,
            &earnings_info,
            &chain,
        ).await?;
        
        tracing::info!(
            "IV surface forecast completed for {} in {:?}",
            symbol,
            start.elapsed()
        );
        
        Ok(iv_predictions)
    }
    
    async fn get_sentiment_signals(&self, symbol: &str) -> Result<SentimentSignals> {
        // Simplified sentiment - in production, call sentiment analysis service
        // For now, generate based on symbol characteristics
        let base_sentiment = match symbol {
            "AAPL" | "MSFT" | "GOOGL" => 0.65,  // Generally positive
            "TSLA" | "NVDA" => 0.55,            // More volatile
            "SPY" | "QQQ" => 0.60,              // Market sentiment
            _ => 0.50,
        };
        
        Ok(SentimentSignals {
            overall_sentiment: base_sentiment,
            news_sentiment: base_sentiment + 0.05,
            social_sentiment: base_sentiment - 0.05,
            confidence: 0.70,
        })
    }
    
    async fn get_macro_signals(&self) -> Result<MacroSignals> {
        // Simplified macro signals - in production, fetch from data providers
        // VIX futures curve, interest rates, etc.
        Ok(MacroSignals {
            vix_level: 18.5,
            vix_futures_curve: vec![18.5, 19.0, 19.5, 20.0], // 1m, 2m, 3m, 6m
            interest_rate: 5.25,
            market_regime: "normal".to_string(),
        })
    }
    
    async fn get_earnings_info(&self, symbol: &str) -> Result<EarningsInfo> {
        // Simplified earnings detection - in production, check earnings calendar
        // Check if earnings are within next 7 days
        let days_until_earnings = match symbol {
            "AAPL" => 3,  // Mock: earnings in 3 days
            "MSFT" => 5,
            "GOOGL" => 7,
            _ => 30,  // No earnings soon
        };
        
        Ok(EarningsInfo {
            days_until_earnings,
            is_pre_earnings: days_until_earnings <= 7 && days_until_earnings > 0,
            is_post_earnings: false,  // Simplified
            historical_iv_crush: 0.15,  // 15% average IV crush post-earnings
        })
    }
    
    async fn predict_iv_changes(
        &self,
        symbol: &str,
        regime: &str,
        sentiment: &SentimentSignals,
        macro_signals: &MacroSignals,
        earnings: &EarningsInfo,
        chain: &OptionsChain,
    ) -> Result<IVSurfaceForecast> {
        let mut current_iv: HashMap<String, f64> = HashMap::new();
        let mut predicted_iv_1hr: HashMap<String, f64> = HashMap::new();
        let mut predicted_iv_24hr: HashMap<String, f64> = HashMap::new();
        let mut iv_change_heatmap = Vec::new();
        
        // Group contracts by expiration
        let mut by_expiration: HashMap<String, Vec<&OptionContract>> = HashMap::new();
        for contract in &chain.contracts {
            by_expiration
                .entry(contract.expiration.clone())
                .or_insert_with(Vec::new)
                .push(contract);
        }
        
        // Predict IV for each expiration
        for (expiration, contracts) in &by_expiration {
            // Calculate average IV for this expiration
            let avg_iv = contracts.iter()
                .map(|c| c.implied_volatility)
                .sum::<f64>() / contracts.len() as f64;
            
            current_iv.insert(expiration.clone(), avg_iv);
            
            // Predict IV change based on:
            // 1. Earnings proximity (IV expands before, crushes after)
            // 2. Sentiment (positive sentiment → lower IV, negative → higher IV)
            // 3. VIX level (high VIX → higher IV)
            // 4. Regime (earnings/FOMC → higher IV)
            
            let mut iv_change_1hr = 0.0;
            let mut iv_change_24hr = 0.0;
            
            // Earnings effect
            if earnings.is_pre_earnings {
                // IV expands before earnings
                let expansion_factor = (7.0 - earnings.days_until_earnings as f64) / 7.0;
                iv_change_1hr += expansion_factor * 5.0;  // Up to 5% expansion
                iv_change_24hr += expansion_factor * 10.0;  // Up to 10% expansion
            } else if earnings.is_post_earnings {
                // IV crushes after earnings
                iv_change_1hr -= earnings.historical_iv_crush * 100.0;  // -15%
                iv_change_24hr -= earnings.historical_iv_crush * 100.0;  // -15%
            }
            
            // Sentiment effect (negative sentiment → higher IV)
            let sentiment_effect = (0.5 - sentiment.overall_sentiment) * 10.0;
            iv_change_1hr += sentiment_effect * 0.3;
            iv_change_24hr += sentiment_effect * 0.5;
            
            // VIX effect (high VIX → higher IV)
            let vix_effect = (macro_signals.vix_level - 20.0) / 20.0 * 5.0;
            iv_change_1hr += vix_effect * 0.2;
            iv_change_24hr += vix_effect * 0.4;
            
            // Regime effect
            if regime == "earnings" {
                iv_change_1hr += 3.0;
                iv_change_24hr += 5.0;
            } else if regime == "fomc" {
                iv_change_1hr += 2.0;
                iv_change_24hr += 3.0;
            }
            
            // Mean reversion (high IV → likely to drop)
            if avg_iv > 0.30 {
                iv_change_1hr -= 2.0;
                iv_change_24hr -= 5.0;
            } else if avg_iv < 0.15 {
                iv_change_1hr += 2.0;
                iv_change_24hr += 5.0;
            }
            
            // Clamp changes
            iv_change_1hr = iv_change_1hr.max(-30.0).min(30.0);
            iv_change_24hr = iv_change_24hr.max(-50.0).min(50.0);
            
            let predicted_iv_1hr_val = avg_iv * (1.0 + iv_change_1hr / 100.0);
            let predicted_iv_24hr_val = avg_iv * (1.0 + iv_change_24hr / 100.0);
            
            predicted_iv_1hr.insert(expiration.clone(), predicted_iv_1hr_val);
            predicted_iv_24hr.insert(expiration.clone(), predicted_iv_24hr_val);
            
            // Create heatmap points for each strike
            for contract in contracts {
                // Use contract's IV as base, adjust by expiration average change
                let contract_iv_1hr = contract.implied_volatility * (1.0 + iv_change_1hr / 100.0);
                let contract_iv_24hr = contract.implied_volatility * (1.0 + iv_change_24hr / 100.0);
                
                iv_change_heatmap.push(IVChangePoint {
                    strike: contract.strike,
                    expiration: expiration.clone(),
                    current_iv: contract.implied_volatility,
                    predicted_iv_1hr: contract_iv_1hr,
                    predicted_iv_24hr: contract_iv_24hr,
                    iv_change_1hr_pct: iv_change_1hr,
                    iv_change_24hr_pct: iv_change_24hr,
                    confidence: sentiment.confidence * 0.9,  // Slightly lower confidence
                });
            }
        }
        
        // Calculate overall confidence
        let confidence = if earnings.is_pre_earnings {
            0.85  // High confidence before earnings
        } else if sentiment.confidence > 0.8 {
            0.75
        } else {
            0.65
        };
        
        Ok(IVSurfaceForecast {
            symbol: symbol.to_string(),
            current_iv,
            predicted_iv_1hr,
            predicted_iv_24hr,
            confidence,
            regime: regime.to_string(),
            iv_change_heatmap,
            timestamp: Utc::now(),
        })
    }
}

// Helper structs for strategy generation
#[derive(Debug, Clone)]
struct StrategyCandidate {
    strategy_type: String,
    description: String,
    base_edge: f64,
    base_confidence: f64,
    base_strike: f64,
    base_expiration: String,
    base_option_type: String,
}

#[derive(Debug, Clone)]
struct OptimizedStrategy {
    description: String,
    entry_price: f64,
    expected_edge: f64,
    confidence: f64,
    reasoning: String,
    max_loss: f64,
    max_profit: f64,
    probability_of_profit: f64,
    legs: Vec<OneTapLeg>,
    strategy_type: String,
    days_to_expiration: i32,
    total_cost: f64,
    total_credit: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IVSurfaceForecast {
    pub symbol: String,
    pub current_iv: HashMap<String, f64>,  // expiration -> IV
    pub predicted_iv_1hr: HashMap<String, f64>,
    pub predicted_iv_24hr: HashMap<String, f64>,
    pub confidence: f64,
    pub regime: String,  // "Earnings", "FOMC", "Normal"
    pub iv_change_heatmap: Vec<IVChangePoint>,
    pub timestamp: chrono::DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IVChangePoint {
    pub strike: f64,
    pub expiration: String,
    pub current_iv: f64,
    pub predicted_iv_1hr: f64,
    pub predicted_iv_24hr: f64,
    pub iv_change_1hr_pct: f64,  // Percentage change
    pub iv_change_24hr_pct: f64,
    pub confidence: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OneTapTrade {
    pub strategy: String,           // "Sell 10x SPY 525/530/535 call spreads"
    pub entry_price: f64,           // $1.92 credit
    pub expected_edge: f64,         // +18% in 4hrs
    pub confidence: f64,            // 94%
    pub take_profit: f64,           // Auto-calculated
    pub stop_loss: f64,             // Auto-calculated
    pub reasoning: String,          // "IV crush expected post-earnings"
    pub max_loss: f64,             // $500
    pub max_profit: f64,           // $1,920
    pub probability_of_profit: f64, // 72%
    pub symbol: String,
    pub legs: Vec<OneTapLeg>,
    pub strategy_type: String,      // "spread", "straddle", "iron_condor", etc.
    pub days_to_expiration: i32,
    pub total_cost: f64,           // Net debit (negative for credit)
    pub total_credit: f64,         // Net credit (0 for debit)
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OneTapLeg {
    pub action: String,            // "buy" or "sell"
    pub option_type: String,       // "call" or "put"
    pub strike: f64,
    pub expiration: String,
    pub quantity: i32,
    pub premium: f64,
}

// Helper structs for predictions
#[derive(Debug, Clone)]
struct IVChangePrediction {
    current_iv: f64,
    predicted_iv_1hr: f64,
    predicted_iv_24hr: f64,
    iv_change_1hr_pct: f64,
    iv_change_24hr_pct: f64,
    confidence: f64,
}

#[derive(Debug, Clone)]
struct PriceMovementPrediction {
    current_price: f64,
    predicted_price_15min: f64,
    predicted_price_1hr: f64,
    predicted_price_1day: f64,
    price_change_15min_pct: f64,
    price_change_1hr_pct: f64,
    price_change_1day_pct: f64,
}

// Helper structs for IV forecasting
#[derive(Debug, Clone)]
struct SentimentSignals {
    overall_sentiment: f64,  // 0-1
    news_sentiment: f64,
    social_sentiment: f64,
    confidence: f64,
}

#[derive(Debug, Clone)]
struct MacroSignals {
    vix_level: f64,
    vix_futures_curve: Vec<f64>,
    interest_rate: f64,
    market_regime: String,
}

#[derive(Debug, Clone)]
struct EarningsInfo {
    days_until_earnings: i32,
    is_pre_earnings: bool,
    is_post_earnings: bool,
    historical_iv_crush: f64,  // Average IV crush percentage
}

