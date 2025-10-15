use crate::options_models::{GreeksParams, BlackScholesResult, OptionType};
use statrs::function::erf::erf;
use std::f64::consts::{PI, E};
/// Black-Scholes options pricing and Greeks calculator
pub struct OptionsCalculator;
impl OptionsCalculator {
/// Calculate Black-Scholes option price and all Greeks
pub fn calculate_black_scholes(params: &GreeksParams, option_type: &OptionType) -> BlackScholesResult {
let S = params.spot_price;
let K = params.strike_price;
let T = params.time_to_expiration;
let r = params.risk_free_rate;
let q = params.dividend_yield;
let sigma = params.volatility;
// Calculate d1 and d2
let d1 = (S.ln() / K + (r - q + 0.5 * sigma * sigma) * T) / (sigma * T.sqrt());
let d2 = d1 - sigma * T.sqrt();
// Calculate cumulative normal distribution
let N_d1 = Self::cumulative_normal_distribution(d1);
let N_d2 = Self::cumulative_normal_distribution(d2);
let N_neg_d1 = Self::cumulative_normal_distribution(-d1);
let N_neg_d2 = Self::cumulative_normal_distribution(-d2);
// Calculate option price
let option_price = match option_type {
OptionType::Call => S * E.powf(-q * T) * N_d1 - K * E.powf(-r * T) * N_d2,
OptionType::Put => K * E.powf(-r * T) * N_neg_d2 - S * E.powf(-q * T) * N_neg_d1,
};
// Calculate intrinsic value
let intrinsic_value = match option_type {
OptionType::Call => (S - K).max(0.0),
OptionType::Put => (K - S).max(0.0),
};
// Calculate time value
let time_value = option_price - intrinsic_value;
// Calculate Greeks
let delta = match option_type {
OptionType::Call => E.powf(-q * T) * N_d1,
OptionType::Put => -E.powf(-q * T) * N_neg_d1,
};
let gamma = E.powf(-q * T) * Self::normal_density(d1) / (S * sigma * T.sqrt());
let theta = match option_type {
OptionType::Call => {
-S * E.powf(-q * T) * Self::normal_density(d1) * sigma / (2.0 * T.sqrt())
- r * K * E.powf(-r * T) * N_d2
+ q * S * E.powf(-q * T) * N_d1
}
OptionType::Put => {
-S * E.powf(-q * T) * Self::normal_density(d1) * sigma / (2.0 * T.sqrt())
+ r * K * E.powf(-r * T) * N_neg_d2
- q * S * E.powf(-q * T) * N_neg_d1
}
};
let vega = S * E.powf(-q * T) * Self::normal_density(d1) * T.sqrt();
let rho = match option_type {
OptionType::Call => K * T * E.powf(-r * T) * N_d2,
OptionType::Put => -K * T * E.powf(-r * T) * N_neg_d2,
};
BlackScholesResult {
option_price,
delta,
gamma,
theta,
vega,
rho,
intrinsic_value,
time_value,
}
}
/// Calculate implied volatility using Newton-Raphson method
pub fn calculate_implied_volatility(
market_price: f64,
params: &GreeksParams,
option_type: &OptionType,
max_iterations: usize,
tolerance: f64,
) -> Option<f64> {
let mut volatility = 0.3; // Initial guess
for _ in 0..max_iterations {
let mut params_with_vol = params.clone();
params_with_vol.volatility = volatility;
let result = Self::calculate_black_scholes(&params_with_vol, option_type);
let price_diff = result.option_price - market_price;
if price_diff.abs() < tolerance {
return Some(volatility);
}
// Calculate vega for Newton-Raphson
let vega = result.vega;
if vega.abs() < 1e-10 {
break; // Avoid division by zero
}
volatility = volatility - price_diff / vega;
// Keep volatility in reasonable bounds
volatility = volatility.max(0.001).min(5.0);
}
None
}
/// Calculate probability of profit for a strategy
pub fn calculate_probability_of_profit(
breakeven_points: &[f64],
current_price: f64,
volatility: f64,
time_to_expiration: f64,
) -> f64 {
if breakeven_points.is_empty() {
return 0.0;
}
let mut total_probability = 0.0;
for &breakeven in breakeven_points {
let z = (breakeven - current_price) / (current_price * volatility * time_to_expiration.sqrt());
let probability = Self::cumulative_normal_distribution(z);
total_probability += probability;
}
total_probability / breakeven_points.len() as f64
}
/// Calculate risk-reward ratio
pub fn calculate_risk_reward_ratio(max_profit: f64, max_loss: f64) -> f64 {
if max_loss.abs() < 1e-10 {
return f64::INFINITY;
}
max_profit / max_loss.abs()
}
/// Cumulative normal distribution function
fn cumulative_normal_distribution(x: f64) -> f64 {
0.5 * (1.0 + erf(x / 2.0_f64.sqrt()))
}
/// Normal probability density function
fn normal_density(x: f64) -> f64 {
E.powf(-0.5 * x * x) / (2.0 * PI).sqrt()
}
/// Calculate put-call ratio for sentiment analysis
pub fn calculate_put_call_ratio(call_volume: u64, put_volume: u64) -> f64 {
if call_volume == 0 {
return f64::INFINITY;
}
put_volume as f64 / call_volume as f64
}
/// Calculate implied volatility skew
pub fn calculate_volatility_skew(
atm_iv: f64,
otm_call_iv: f64,
otm_put_iv: f64,
) -> f64 {
(otm_put_iv - otm_call_iv) / atm_iv
}
/// Calculate implied volatility rank (percentile)
pub fn calculate_iv_rank(current_iv: f64, iv_history: &[f64]) -> f64 {
if iv_history.is_empty() {
return 0.0;
}
let mut sorted_iv = iv_history.to_vec();
sorted_iv.sort_by(|a, b| a.partial_cmp(b).unwrap());
let rank = sorted_iv.iter().position(|&x| x >= current_iv).unwrap_or(sorted_iv.len());
rank as f64 / sorted_iv.len() as f64 * 100.0
}
}
#[cfg(test)]
mod tests {
use super::*;
use chrono::Utc;
#[test]
fn test_black_scholes_call() {
let params = GreeksParams {
spot_price: 100.0,
strike_price: 100.0,
time_to_expiration: 0.25, // 3 months
risk_free_rate: 0.05,
dividend_yield: 0.0,
volatility: 0.2,
};
let result = OptionsCalculator::calculate_black_scholes(&params, &OptionType::Call);
// Basic sanity checks
assert!(result.option_price > 0.0);
assert!(result.delta > 0.0 && result.delta < 1.0);
assert!(result.gamma > 0.0);
assert!(result.theta < 0.0); // Time decay
assert!(result.vega > 0.0);
}
#[test]
fn test_black_scholes_put() {
let params = GreeksParams {
spot_price: 100.0,
strike_price: 100.0,
time_to_expiration: 0.25,
risk_free_rate: 0.05,
dividend_yield: 0.0,
volatility: 0.2,
};
let result = OptionsCalculator::calculate_black_scholes(&params, &OptionType::Put);
// Basic sanity checks
assert!(result.option_price > 0.0);
assert!(result.delta < 0.0 && result.delta > -1.0);
assert!(result.gamma > 0.0);
assert!(result.theta < 0.0); // Time decay
assert!(result.vega > 0.0);
}
#[test]
fn test_put_call_ratio() {
let ratio = OptionsCalculator::calculate_put_call_ratio(1000, 800);
assert!((ratio - 0.8).abs() < 1e-10);
}
}
