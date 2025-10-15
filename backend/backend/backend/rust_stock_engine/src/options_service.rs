use crate::options_models::*;
use crate::options_calculator::OptionsCalculator;
use crate::config::Config;
use anyhow::{Result, anyhow};
use reqwest::Client;
use tracing::{info, warn, error};
use chrono::{Utc, Duration};
use std::collections::HashMap;
/// Options analysis service for fetching and analyzing options data
pub struct OptionsService {
config: Config,
client: Client,
}
impl OptionsService {
pub fn new(config: Config) -> Self {
Self {
config,
client: Client::new(),
}
}
/// Fetch options chain for a given symbol
pub async fn fetch_options_chain(&self, symbol: &str) -> Result<OptionsChain> {
info!("Fetching options chain for {}", symbol);
// Get current stock price
let stock_price = self.fetch_stock_price(symbol).await?;
// Fetch options data from multiple sources
let mut call_options = Vec::new();
let mut put_options = Vec::new();
let mut expiration_dates = Vec::new();
// Try Alpha Vantage first
if let Ok(alpha_vantage_data) = self.fetch_alpha_vantage_options(symbol).await {
call_options.extend(alpha_vantage_data.0);
put_options.extend(alpha_vantage_data.1);
expiration_dates.extend(alpha_vantage_data.2);
}
// Try Polygon if available
if let Ok(polygon_data) = self.fetch_polygon_options(symbol).await {
call_options.extend(polygon_data.0);
put_options.extend(polygon_data.1);
expiration_dates.extend(polygon_data.2);
}
// If no real data, generate synthetic options chain
if call_options.is_empty() && put_options.is_empty() {
let synthetic_data = self.generate_synthetic_options_chain(symbol, stock_price);
call_options = synthetic_data.0;
put_options = synthetic_data.1;
expiration_dates = synthetic_data.2;
}
// Calculate Greeks for all options
self.calculate_greeks_for_chain(&mut call_options, stock_price);
self.calculate_greeks_for_chain(&mut put_options, stock_price);
// Sort by expiration date
expiration_dates.sort();
expiration_dates.dedup();
Ok(OptionsChain {
underlying_symbol: symbol.to_string(),
underlying_price: stock_price,
expiration_dates,
call_options,
put_options,
timestamp: Utc::now(),
})
}
/// Fetch unusual options flow activity
pub async fn fetch_unusual_options_flow(&self, symbol: &str) -> Result<Vec<OptionsFlow>> {
info!("Fetching unusual options flow for {}", symbol);
let mut unusual_flow = Vec::new();
// Try to fetch from real APIs
if let Ok(flow_data) = self.fetch_polygon_options_flow(symbol).await {
unusual_flow.extend(flow_data);
}
// If no real data, generate synthetic unusual activity
if unusual_flow.is_empty() {
unusual_flow = self.generate_synthetic_unusual_flow(symbol);
}
Ok(unusual_flow)
}
/// Analyze options strategies for a given symbol
pub fn analyze_options_strategies(
&self,
options_chain: &OptionsChain,
strategy_types: &[StrategyType],
) -> Vec<OptionsStrategy> {
let mut strategies = Vec::new();
for strategy_type in strategy_types {
if let Some(strategy) = self.calculate_strategy(options_chain, strategy_type) {
strategies.push(strategy);
}
}
// Sort by risk-reward ratio
strategies.sort_by(|a, b| b.risk_reward_ratio.partial_cmp(&a.risk_reward_ratio).unwrap());
strategies
}
/// Screen options based on criteria
pub fn screen_options(
&self,
options_chain: &OptionsChain,
criteria: &OptionsScreeningCriteria,
) -> OptionsScreeningResult {
let mut filtered_contracts = Vec::new();
// Combine all options
let mut all_options = options_chain.call_options.clone();
all_options.extend(options_chain.put_options.clone());
for option in all_options {
if self.matches_criteria(&option, criteria) {
filtered_contracts.push(option);
}
}
OptionsScreeningResult {
contracts: filtered_contracts,
total_found: filtered_contracts.len(),
screening_criteria: criteria.clone(),
timestamp: Utc::now(),
}
}
/// Calculate market sentiment from options data
pub fn calculate_market_sentiment(&self, options_chain: &OptionsChain) -> MarketSentiment {
let total_call_volume: u64 = options_chain.call_options.iter().map(|o| o.volume).sum();
let total_put_volume: u64 = options_chain.put_options.iter().map(|o| o.volume).sum();
let put_call_ratio = OptionsCalculator::calculate_put_call_ratio(total_call_volume, total_put_volume);
// Calculate average implied volatility
let all_options: Vec<&OptionContract> = options_chain.call_options.iter()
.chain(options_chain.put_options.iter())
.collect();
let avg_iv = if !all_options.is_empty() {
all_options.iter().map(|o| o.implied_volatility).sum::<f64>() / all_options.len() as f64
} else {
0.0
};
// Calculate skew (simplified)
let atm_calls: Vec<&OptionContract> = options_chain.call_options.iter()
.filter(|o| (o.strike - options_chain.underlying_price).abs() < options_chain.underlying_price * 0.05)
.collect();
let atm_puts: Vec<&OptionContract> = options_chain.put_options.iter()
.filter(|o| (o.strike - options_chain.underlying_price).abs() < options_chain.underlying_price * 0.05)
.collect();
let skew = if !atm_calls.is_empty() && !atm_puts.is_empty() {
let call_iv = atm_calls.iter().map(|o| o.implied_volatility).sum::<f64>() / atm_calls.len() as f64;
let put_iv = atm_puts.iter().map(|o| o.implied_volatility).sum::<f64>() / atm_puts.len() as f64;
(put_iv - call_iv) / avg_iv
} else {
0.0
};
// Calculate sentiment score (0-100)
let sentiment_score = self.calculate_sentiment_score(put_call_ratio, avg_iv, skew);
let sentiment_description = self.get_sentiment_description(sentiment_score);
MarketSentiment {
put_call_ratio,
implied_volatility_rank: avg_iv * 100.0, // Simplified IV rank
skew,
sentiment_score,
sentiment_description,
}
}
// Private helper methods
async fn fetch_stock_price(&self, symbol: &str) -> Result<f64> {
// Use existing stock price fetching logic
// This would integrate with your existing stock service
Ok(150.0) // Placeholder - replace with actual stock price fetching
}
async fn fetch_alpha_vantage_options(&self, symbol: &str) -> Result<(Vec<OptionContract>, Vec<OptionContract>, Vec<chrono::DateTime<Utc>>)> {
// Alpha Vantage options endpoint
let url = format!(
"https://www.alphavantage.co/query?function=OPTION_CHAIN&symbol={}&apikey={}",
symbol, self.config.alpha_vantage.api_key
);
let response = self.client.get(&url).send().await?;
let text = response.text().await?;
// Parse Alpha Vantage response (simplified)
// In a real implementation, you'd parse the JSON response
warn!("Alpha Vantage options not fully implemented, using synthetic data");
Err(anyhow!("Alpha Vantage options not available"))
}
async fn fetch_polygon_options(&self, symbol: &str) -> Result<(Vec<OptionContract>, Vec<OptionContract>, Vec<chrono::DateTime<Utc>>)> {
// Polygon.io options endpoint
let url = format!(
"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={}&apikey={}",
symbol, "your_polygon_key_here" // Replace with actual key
);
let response = self.client.get(&url).send().await?;
let text = response.text().await?;
// Parse Polygon response (simplified)
warn!("Polygon options not fully implemented, using synthetic data");
Err(anyhow!("Polygon options not available"))
}
async fn fetch_polygon_options_flow(&self, symbol: &str) -> Result<Vec<OptionsFlow>> {
// Polygon.io unusual options activity endpoint
let url = format!(
"https://api.polygon.io/v2/snapshot/options/{}/unusual?apikey={}",
symbol, "your_polygon_key_here"
);
let response = self.client.get(&url).send().await?;
let text = response.text().await?;
// Parse response (simplified)
warn!("Polygon options flow not fully implemented, using synthetic data");
Err(anyhow!("Polygon options flow not available"))
}
fn generate_synthetic_options_chain(
&self,
symbol: &str,
stock_price: f64,
) -> (Vec<OptionContract>, Vec<OptionContract>, Vec<chrono::DateTime<Utc>>) {
let mut call_options = Vec::new();
let mut put_options = Vec::new();
let mut expiration_dates = Vec::new();
// Generate options for next 4 expiration dates
for i in 1..=4 {
let expiration = Utc::now() + Duration::days(i * 7); // Weekly expirations
expiration_dates.push(expiration);
// Generate strikes around current price
let strikes = self.generate_strikes(stock_price, 10);
for strike in strikes {
// Generate call option
let call_option = self.generate_synthetic_option(
symbol, strike, expiration, OptionType::Call, stock_price
);
call_options.push(call_option);
// Generate put option
let put_option = self.generate_synthetic_option(
symbol, strike, expiration, OptionType::Put, stock_price
);
put_options.push(put_option);
}
}
(call_options, put_options, expiration_dates)
}
fn generate_strikes(&self, current_price: f64, count: usize) -> Vec<f64> {
let mut strikes = Vec::new();
let step = current_price * 0.05; // 5% steps
for i in 0..count {
let strike = current_price - (count as f64 / 2.0 - i as f64) * step;
strikes.push(strike.round());
}
strikes
}
fn generate_synthetic_option(
&self,
symbol: &str,
strike: f64,
expiration: chrono::DateTime<Utc>,
option_type: OptionType,
stock_price: f64,
) -> OptionContract {
let days_to_exp = (expiration - Utc::now()).num_days();
let time_to_exp = days_to_exp as f64 / 365.0;
// Calculate theoretical price using Black-Scholes
let params = GreeksParams {
spot_price: stock_price,
strike_price: strike,
time_to_expiration: time_to_exp,
risk_free_rate: 0.05,
dividend_yield: 0.0,
volatility: 0.25,
};
let bs_result = OptionsCalculator::calculate_black_scholes(&params, &option_type);
// Add some randomness to make it realistic
let bid = bs_result.option_price * 0.95;
let ask = bs_result.option_price * 1.05;
let last_price = (bid + ask) / 2.0;
OptionContract {
symbol: symbol.to_string(),
contract_symbol: format!("{}{}{}{}", symbol, expiration.format("%y%m%d"), option_type, strike),
strike,
expiration_date: expiration,
option_type,
bid,
ask,
last_price,
volume: (1000.0 * (1.0 - (strike - stock_price).abs() / stock_price)).max(100.0) as u64,
open_interest: (5000.0 * (1.0 - (strike - stock_price).abs() / stock_price)).max(500.0) as u64,
implied_volatility: 0.25 + (strike - stock_price).abs() / stock_price * 0.1,
delta: bs_result.delta,
gamma: bs_result.gamma,
theta: bs_result.theta,
vega: bs_result.vega,
rho: bs_result.rho,
intrinsic_value: bs_result.intrinsic_value,
time_value: bs_result.time_value,
days_to_expiration: days_to_exp,
timestamp: Utc::now(),
}
}
fn generate_synthetic_unusual_flow(&self, symbol: &str) -> Vec<OptionsFlow> {
let mut flow = Vec::new();
let stock_price = 150.0; // Placeholder
// Generate some unusual activity
let unusual_activities = vec![
(ActivityType::Sweep, 0.8),
(ActivityType::UnusualVolume, 0.7),
(ActivityType::Earnings, 0.9),
];
for (activity_type, score) in unusual_activities {
let strike = stock_price * (0.9 + 0.2 * (score * 10.0).sin());
let expiration = Utc::now() + Duration::days(30);
flow.push(OptionsFlow {
symbol: symbol.to_string(),
contract_symbol: format!("{}{}{}{}", symbol, expiration.format("%y%m%d"), "C", strike),
option_type: OptionType::Call,
strike,
expiration_date: expiration,
volume: (10000.0 * score) as u64,
open_interest: (50000.0 * score) as u64,
premium: strike * 0.1 * score,
implied_volatility: 0.3 + score * 0.2,
unusual_activity_score: score,
activity_type,
timestamp: Utc::now(),
});
}
flow
}
fn calculate_greeks_for_chain(&self, options: &mut Vec<OptionContract>, stock_price: f64) {
for option in options.iter_mut() {
let params = GreeksParams {
spot_price: stock_price,
strike_price: option.strike,
time_to_expiration: option.days_to_expiration as f64 / 365.0,
risk_free_rate: 0.05,
dividend_yield: 0.0,
volatility: option.implied_volatility,
};
let result = OptionsCalculator::calculate_black_scholes(&params, &option.option_type);
option.delta = result.delta;
option.gamma = result.gamma;
option.theta = result.theta;
option.vega = result.vega;
option.rho = result.rho;
option.intrinsic_value = result.intrinsic_value;
option.time_value = result.time_value;
}
}
fn calculate_strategy(&self, options_chain: &OptionsChain, strategy_type: &StrategyType) -> Option<OptionsStrategy> {
match strategy_type {
StrategyType::CoveredCall => self.calculate_covered_call(options_chain),
StrategyType::CashSecuredPut => self.calculate_cash_secured_put(options_chain),
StrategyType::BullCallSpread => self.calculate_bull_call_spread(options_chain),
StrategyType::IronCondor => self.calculate_iron_condor(options_chain),
_ => None, // Implement other strategies as needed
}
}
fn calculate_covered_call(&self, options_chain: &OptionsChain) -> Option<OptionsStrategy> {
// Find ATM call option
let atm_call = options_chain.call_options.iter()
.min_by(|a, b| (a.strike - options_chain.underlying_price).abs()
.partial_cmp(&(b.strike - options_chain.underlying_price).abs()).unwrap())?;
let max_profit = atm_call.strike - options_chain.underlying_price + atm_call.last_price;
let max_loss = options_chain.underlying_price - atm_call.last_price;
let breakeven = options_chain.underlying_price - atm_call.last_price;
Some(OptionsStrategy {
strategy_name: "Covered Call".to_string(),
strategy_type: StrategyType::CoveredCall,
contracts: vec![atm_call.clone()],
max_profit,
max_loss,
breakeven_points: vec![breakeven],
probability_of_profit: 0.6, // Simplified
risk_reward_ratio: max_profit / max_loss.abs(),
days_to_expiration: atm_call.days_to_expiration,
total_cost: -atm_call.last_price, // Credit received
total_credit: atm_call.last_price,
})
}
fn calculate_cash_secured_put(&self, options_chain: &OptionsChain) -> Option<OptionsStrategy> {
// Find ATM put option
let atm_put = options_chain.put_options.iter()
.min_by(|a, b| (a.strike - options_chain.underlying_price).abs()
.partial_cmp(&(b.strike - options_chain.underlying_price).abs()).unwrap())?;
let max_profit = atm_put.last_price;
let max_loss = atm_put.strike - atm_put.last_price;
let breakeven = atm_put.strike - atm_put.last_price;
Some(OptionsStrategy {
strategy_name: "Cash Secured Put".to_string(),
strategy_type: StrategyType::CashSecuredPut,
contracts: vec![atm_put.clone()],
max_profit,
max_loss,
breakeven_points: vec![breakeven],
probability_of_profit: 0.7, // Simplified
risk_reward_ratio: max_profit / max_loss.abs(),
days_to_expiration: atm_put.days_to_expiration,
total_cost: -atm_put.last_price, // Credit received
total_credit: atm_put.last_price,
})
}
fn calculate_bull_call_spread(&self, options_chain: &OptionsChain) -> Option<OptionsStrategy> {
// Find ITM and OTM calls
let itm_call = options_chain.call_options.iter()
.filter(|o| o.strike < options_chain.underlying_price)
.max_by(|a, b| a.strike.partial_cmp(&b.strike).unwrap())?;
let otm_call = options_chain.call_options.iter()
.filter(|o| o.strike > options_chain.underlying_price)
.min_by(|a, b| a.strike.partial_cmp(&b.strike).unwrap())?;
let net_debit = itm_call.last_price - otm_call.last_price;
let max_profit = otm_call.strike - itm_call.strike - net_debit;
let max_loss = net_debit;
let breakeven = itm_call.strike + net_debit;
Some(OptionsStrategy {
strategy_name: "Bull Call Spread".to_string(),
strategy_type: StrategyType::BullCallSpread,
contracts: vec![itm_call.clone(), otm_call.clone()],
max_profit,
max_loss,
breakeven_points: vec![breakeven],
probability_of_profit: 0.65, // Simplified
risk_reward_ratio: max_profit / max_loss.abs(),
days_to_expiration: itm_call.days_to_expiration,
total_cost: net_debit,
total_credit: 0.0,
})
}
fn calculate_iron_condor(&self, options_chain: &OptionsChain) -> Option<OptionsStrategy> {
// Simplified iron condor calculation
// In practice, you'd find the best strikes based on premium and probability
None // Placeholder - implement full iron condor logic
}
fn matches_criteria(&self, option: &OptionContract, criteria: &OptionsScreeningCriteria) -> bool {
if let Some(min_vol) = criteria.min_volume {
if option.volume < min_vol { return false; }
}
if let Some(max_vol) = criteria.max_volume {
if option.volume > max_vol { return false; }
}
if let Some(min_oi) = criteria.min_open_interest {
if option.open_interest < min_oi { return false; }
}
if let Some(max_oi) = criteria.max_open_interest {
if option.open_interest > max_oi { return false; }
}
if let Some(min_iv) = criteria.min_implied_volatility {
if option.implied_volatility < min_iv { return false; }
}
if let Some(max_iv) = criteria.max_implied_volatility {
if option.implied_volatility > max_iv { return false; }
}
if let Some(min_delta) = criteria.min_delta {
if option.delta < min_delta { return false; }
}
if let Some(max_delta) = criteria.max_delta {
if option.delta > max_delta { return false; }
}
if let Some(min_dte) = criteria.min_days_to_expiration {
if option.days_to_expiration < min_dte { return false; }
}
if let Some(max_dte) = criteria.max_days_to_expiration {
if option.days_to_expiration > max_dte { return false; }
}
if let Some(option_type) = &criteria.option_type {
if std::mem::discriminant(&option.option_type) != std::mem::discriminant(option_type) {
return false;
}
}
if let Some(min_strike) = criteria.min_strike {
if option.strike < min_strike { return false; }
}
if let Some(max_strike) = criteria.max_strike {
if option.strike > max_strike { return false; }
}
true
}
fn calculate_sentiment_score(&self, put_call_ratio: f64, avg_iv: f64, skew: f64) -> f64 {
// Simplified sentiment calculation
let mut score = 50.0; // Neutral starting point
// Put/call ratio impact
if put_call_ratio > 1.0 {
score -= (put_call_ratio - 1.0) * 20.0; // Bearish
} else {
score += (1.0 - put_call_ratio) * 20.0; // Bullish
}
// IV impact
if avg_iv > 0.3 {
score -= 10.0; // High IV suggests fear
} else if avg_iv < 0.15 {
score += 10.0; // Low IV suggests complacency
}
// Skew impact
if skew > 0.1 {
score -= 5.0; // Put skew suggests bearish sentiment
} else if skew < -0.1 {
score += 5.0; // Call skew suggests bullish sentiment
}
score.max(0.0).min(100.0)
}
fn get_sentiment_description(&self, score: f64) -> String {
match score {
s if s >= 80.0 => "Very Bullish".to_string(),
s if s >= 60.0 => "Bullish".to_string(),
s if s >= 40.0 => "Neutral".to_string(),
s if s >= 20.0 => "Bearish".to_string(),
_ => "Very Bearish".to_string(),
}
}
}
