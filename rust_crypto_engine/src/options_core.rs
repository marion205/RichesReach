// src/options_core.rs
// Shared types for options analysis - extracted from options_analysis.rs

use std::collections::HashMap;
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
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
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VolatilitySurface {
    pub atm_vol: f64,
    pub skew: f64,
    pub term_structure: HashMap<String, f64>, // expiration -> IV
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
    pub current_edge: f64,
    pub predicted_edge_15min: f64,
    pub predicted_edge_1hr: f64,
    pub predicted_edge_1day: f64,
    pub confidence: f64,
    pub explanation: String,
    pub edge_change_dollars: f64,
    pub current_premium: f64,
    pub predicted_premium_15min: f64,
    pub predicted_premium_1hr: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsChain {
    pub symbol: String,
    pub underlying_price: f64,
    pub contracts: Vec<OptionContract>,
    pub timestamp: DateTime<Utc>,
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
    pub edge: f64,
    pub days_to_expiration: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OneTapTrade {
    pub strategy: String,
    pub entry_price: f64,
    pub expected_edge: f64,
    pub confidence: f64,
    pub take_profit: f64,
    pub stop_loss: f64,
    pub reasoning: String,
    pub max_loss: f64,
    pub max_profit: f64,
    pub probability_of_profit: f64,
    pub symbol: String,
    pub legs: Vec<OneTapLeg>,
    pub strategy_type: String,
    pub days_to_expiration: i32,
    pub total_cost: f64,
    pub total_credit: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OneTapLeg {
    pub action: String,      // "buy" or "sell"
    pub option_type: String, // "call" or "put"
    pub strike: f64,
    pub expiration: String,
    pub quantity: i32,
    pub premium: f64,
}

