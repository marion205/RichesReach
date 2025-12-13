// src/market_data/in_memory_options.rs
// In-memory implementation of OptionsDataProvider for dev/testing

use async_trait::async_trait;
use chrono::{DateTime, Utc};
use std::collections::HashMap;
use crate::options_core::{OptionsChain, OptionContract, Greeks};
use crate::market_data::options_provider::OptionsDataProvider;

pub struct InMemoryOptionsProvider {
    chains: dashmap::DashMap<String, OptionsChain>,
    underlying_prices: dashmap::DashMap<String, (f64, DateTime<Utc>)>,
}

impl InMemoryOptionsProvider {
    pub fn new() -> Self {
        let provider = Self {
            chains: dashmap::DashMap::new(),
            underlying_prices: dashmap::DashMap::new(),
        };
        provider.initialize_default_chains();
        provider
    }

    fn initialize_default_chains(&self) {
        // Initialize with some default chains for common symbols
        let symbols = vec!["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "SPY", "QQQ"];
        for symbol in symbols {
            let price = match symbol {
                "AAPL" => 175.0,
                "MSFT" => 380.0,
                "GOOGL" => 140.0,
                "NVDA" => 500.0,
                "TSLA" => 250.0,
                "SPY" => 450.0,
                "QQQ" => 380.0,
                _ => 100.0,
            };
            self.underlying_prices.insert(symbol.to_string(), (price, Utc::now()));
            
            // Generate a simple options chain
            let chain = self.generate_mock_chain(symbol, price);
            self.chains.insert(symbol.to_string(), chain);
        }
    }

    fn generate_mock_chain(&self, symbol: &str, spot: f64) -> OptionsChain {
        let mut contracts = Vec::new();
        let expirations = vec!["2025-01-17", "2025-02-21", "2025-03-21"];
        let strikes = self.generate_strikes(spot);
        
        for exp in &expirations {
            for strike in &strikes {
                // Call option
                let call_iv = 0.20 + (strike - spot).abs() / spot * 0.10;
                let call_premium = self.black_scholes_approx(spot, *strike, call_iv, 30.0, true);
                contracts.push(OptionContract {
                    strike: *strike,
                    expiration: exp.to_string(),
                    option_type: "call".to_string(),
                    premium: call_premium,
                    bid: call_premium * 0.98,
                    ask: call_premium * 1.02,
                    volume: 100,
                    open_interest: 1000,
                    implied_volatility: call_iv,
                    greeks: self.calculate_greeks(spot, *strike, call_iv, 30.0, true),
                    edge: 0.05, // 5% edge
                    days_to_expiration: 30,
                });

                // Put option
                let put_iv = 0.22 + (strike - spot).abs() / spot * 0.10; // Slight put skew
                let put_premium = self.black_scholes_approx(spot, *strike, put_iv, 30.0, false);
                contracts.push(OptionContract {
                    strike: *strike,
                    expiration: exp.to_string(),
                    option_type: "put".to_string(),
                    premium: put_premium,
                    bid: put_premium * 0.98,
                    ask: put_premium * 1.02,
                    volume: 80,
                    open_interest: 800,
                    implied_volatility: put_iv,
                    greeks: self.calculate_greeks(spot, *strike, put_iv, 30.0, false),
                    edge: 0.05,
                    days_to_expiration: 30,
                });
            }
        }

        OptionsChain {
            symbol: symbol.to_string(),
            underlying_price: spot,
            contracts,
            timestamp: Utc::now(),
        }
    }

    fn generate_strikes(&self, spot: f64) -> Vec<f64> {
        // Generate strikes around spot (±20%)
        let mut strikes = Vec::new();
        for i in -5..=5 {
            let strike = spot * (1.0 + (i as f64) * 0.05);
            strikes.push(strike.round());
        }
        strikes
    }

    fn black_scholes_approx(&self, s: f64, k: f64, iv: f64, t: f64, is_call: bool) -> f64 {
        // Simplified Black-Scholes approximation
        let moneyness = s / k;
        let time_value = iv * s * (t / 365.0).sqrt() * 0.4; // Rough approximation
        let intrinsic = if is_call {
            (s - k).max(0.0)
        } else {
            (k - s).max(0.0)
        };
        intrinsic + time_value
    }

    fn calculate_greeks(&self, s: f64, k: f64, iv: f64, t: f64, is_call: bool) -> Greeks {
        let moneyness = s / k;
        let delta = if is_call {
            if moneyness > 1.0 { 0.7 } else if moneyness < 0.9 { 0.3 } else { 0.5 }
        } else {
            if moneyness > 1.0 { -0.3 } else if moneyness < 0.9 { -0.7 } else { -0.5 }
        };
        
        Greeks {
            delta,
            gamma: 0.02,
            theta: -0.15,
            vega: 0.30,
            rho: 0.05,
        }
    }
}

#[async_trait]
impl OptionsDataProvider for InMemoryOptionsProvider {
    async fn get_underlying_price(&self, symbol: &str) -> anyhow::Result<(f64, DateTime<Utc>)> {
        if let Some(entry) = self.underlying_prices.get(symbol) {
            let (price, timestamp) = entry.value();
            Ok((*price, *timestamp))
        } else {
            // Default fallback
            Ok((100.0, Utc::now()))
        }
    }

    async fn get_options_chain(&self, symbol: &str) -> anyhow::Result<OptionsChain> {
        if let Some(chain) = self.chains.get(symbol) {
            Ok(chain.clone())
        } else {
            // Generate a new chain on the fly
            let (price, _) = self.get_underlying_price(symbol).await?;
            let chain = self.generate_mock_chain(symbol, price);
            self.chains.insert(symbol.to_string(), chain.clone());
            Ok(chain)
        }
    }
}

