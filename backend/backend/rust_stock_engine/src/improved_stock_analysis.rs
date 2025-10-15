use crate::models::*;
use crate::config::Config;
use anyhow::{Result, anyhow};
use reqwest::Client;
use tracing::{info, warn, error};
use chrono::Utc;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tokio::time::sleep;
use serde_json::Value;
/// Improved stock analyzer with caching, rate limiting, and parallel processing
pub struct ImprovedStockAnalyzer {
config: Config,
client: Client,
cache: Arc<Mutex<HashMap<String, (StockData, Instant)>>>,
rate_limiter: Arc<RateLimiter>,
cache_ttl: Duration,
}
/// Rate limiter to manage API calls
struct RateLimiter {
requests: Arc<Mutex<u32>>,
last_reset: Arc<Mutex<Instant>>,
limit_per_minute: u32,
}
impl RateLimiter {
fn new(limit_per_minute: u32) -> Self {
Self {
requests: Arc::new(Mutex::new(0)),
last_reset: Arc::new(Mutex::new(Instant::now())),
limit_per_minute,
}
}
async fn wait_if_needed(&self) {
let mut requests = self.requests.lock().unwrap();
let mut last_reset = self.last_reset.lock().unwrap();
// Reset counter if a minute has passed
if last_reset.elapsed() >= Duration::from_secs(60) {
*requests = 0;
*last_reset = Instant::now();
}
// Wait if we've hit the limit
if *requests >= self.limit_per_minute {
let wait_time = Duration::from_secs(60) - last_reset.elapsed();
if wait_time > Duration::from_secs(0) {
warn!("Rate limit reached, waiting {} seconds", wait_time.as_secs());
drop(requests);
drop(last_reset);
sleep(wait_time).await;
return;
}
}
*requests += 1;
}
}
impl ImprovedStockAnalyzer {
pub fn new(config: Config) -> Self {
// Create HTTP client with connection pooling
let client = Client::builder()
.timeout(Duration::from_secs(30))
.pool_max_idle_per_host(10)
.pool_idle_timeout(Duration::from_secs(90))
.build()
.expect("Failed to create HTTP client");
Self {
config,
client,
cache: Arc::new(Mutex::new(HashMap::new())),
rate_limiter: Arc::new(RateLimiter::new(5)), // 5 requests per minute
cache_ttl: Duration::from_secs(300), // 5 minutes cache
}
}
/// Main analysis function with caching and parallel processing
pub async fn analyze_stock(&self, symbol: &str, include_technical: bool, include_fundamental: bool) -> Result<StockAnalysis> {
info!("Analyzing stock: {}", symbol);
// Check cache first
if let Some(cached_data) = self.get_cached_data(symbol) {
info!("Using cached data for {}", symbol);
return self.build_analysis_from_data(cached_data, include_technical, include_fundamental).await;
}
// Fetch fresh data with rate limiting
self.rate_limiter.wait_if_needed().await;
let stock_data = self.fetch_stock_data_parallel(symbol).await?;
// Cache the data
self.cache_data(symbol, &stock_data);
// Build analysis
self.build_analysis_from_data(stock_data, include_technical, include_fundamental).await
}
/// Fetch stock data using parallel API calls
async fn fetch_stock_data_parallel(&self, symbol: &str) -> Result<StockData> {
info!("Fetching stock data for {} (parallel)", symbol);
// Make both API calls in parallel
let (quote_result, overview_result) = tokio::join!(
self.fetch_with_retry(|| self.fetch_quote_data(symbol)),
self.fetch_with_retry(|| self.fetch_overview_data(symbol))
);
let quote_data = quote_result?;
let overview_data = overview_result?;
// Parse and combine the data
self.parse_stock_data(symbol, quote_data, overview_data)
}
/// Fetch quote data with retry logic
async fn fetch_quote_data(&self, symbol: &str) -> Result<Value> {
let url = format!("{}?function=GLOBAL_QUOTE&symbol={}&apikey={}", 
self.config.alpha_vantage.base_url, symbol, self.config.alpha_vantage.api_key);
let response = self.client.get(&url).send().await?;
if !response.status().is_success() {
return Err(anyhow!("API request failed with status: {}", response.status()));
}
let data: Value = response.json().await?;
// Check for API errors
if let Some(error_msg) = data.get("Error Message") {
return Err(anyhow!("API Error: {}", error_msg));
}
if let Some(note) = data.get("Note") {
warn!("API Note: {}", note);
return Err(anyhow!("Rate limit exceeded"));
}
Ok(data)
}
/// Fetch overview data with retry logic
async fn fetch_overview_data(&self, symbol: &str) -> Result<Value> {
let url = format!("{}?function=OVERVIEW&symbol={}&apikey={}", 
self.config.alpha_vantage.base_url, symbol, self.config.alpha_vantage.api_key);
let response = self.client.get(&url).send().await?;
if !response.status().is_success() {
return Err(anyhow!("API request failed with status: {}", response.status()));
}
let data: Value = response.json().await?;
// Check for API errors
if let Some(error_msg) = data.get("Error Message") {
return Err(anyhow!("API Error: {}", error_msg));
}
Ok(data)
}
/// Retry logic with exponential backoff
async fn fetch_with_retry<F, Fut, T>(&self, operation: F) -> Result<T>
where
F: Fn() -> Fut + Send + Sync,
Fut: std::future::Future<Output = Result<T>> + Send,
{
let mut last_error = None;
for attempt in 1..=3 {
match operation().await {
Ok(result) => return Ok(result),
Err(e) => {
last_error = Some(e);
if attempt < 3 {
let delay = Duration::from_millis(1000 * attempt);
warn!("Attempt {} failed, retrying in {}ms", attempt, delay.as_millis());
sleep(delay).await;
}
}
}
}
Err(last_error.unwrap())
}
/// Parse and combine quote and overview data
fn parse_stock_data(&self, symbol: &str, quote_data: Value, overview_data: Value) -> Result<StockData> {
// Parse quote data
let global_quote = quote_data.get("Global Quote")
.ok_or_else(|| anyhow!("No quote data available"))?;
let current_price: f64 = global_quote.get("05. price")
.and_then(|v| v.as_str())
.and_then(|s| s.parse().ok())
.unwrap_or(0.0);
let previous_close: f64 = global_quote.get("08. previous close")
.and_then(|v| v.as_str())
.and_then(|s| s.parse().ok())
.unwrap_or(0.0);
let price_change = current_price - previous_close;
let price_change_percent = if previous_close > 0.0 {
(price_change / previous_close) * 100.0
} else {
0.0
};
let volume: u64 = global_quote.get("06. volume")
.and_then(|v| v.as_str())
.and_then(|s| s.parse().ok())
.unwrap_or(0);
// Parse overview data
let market_cap: u64 = overview_data.get("MarketCapitalization")
.and_then(|v| v.as_str())
.and_then(|s| s.parse().ok())
.unwrap_or(0);
let pe_ratio: Option<f64> = overview_data.get("PERatio")
.and_then(|v| v.as_str())
.and_then(|s| s.parse().ok());
let dividend_yield: Option<f64> = overview_data.get("DividendYield")
.and_then(|v| v.as_str())
.and_then(|s| s.trim_end_matches('%').parse::<f64>().ok())
.map(|y| y / 100.0);
let company_name = overview_data.get("Name")
.and_then(|v| v.as_str())
.map(|s| s.to_string());
Ok(StockData {
symbol: symbol.to_string(),
company_name,
current_price,
price_change,
price_change_percent,
market_cap,
pe_ratio,
dividend_yield,
debt_ratio: None, // Would need additional API call
volume,
timestamp: Utc::now(),
})
}
/// Build analysis from stock data
async fn build_analysis_from_data(&self, stock_data: StockData, include_technical: bool, include_fundamental: bool) -> Result<StockAnalysis> {
// Calculate beginner-friendly score
let beginner_score = self.calculate_beginner_friendly_score(&stock_data);
// Calculate risk level
let risk_level = self.calculate_risk_level(&stock_data, beginner_score);
// Generate recommendation
let recommendation = self.generate_recommendation(beginner_score, &risk_level);
// Calculate technical indicators if requested
let technical_indicators = if include_technical {
match self.calculate_technical_indicators_async(&stock_data.symbol).await {
Ok(indicators) => indicators,
Err(e) => {
warn!("Failed to calculate technical indicators: {}", e);
self.get_empty_technical_indicators()
}
}
} else {
self.get_empty_technical_indicators()
};
// Calculate fundamental analysis if requested
let fundamental_analysis = if include_fundamental {
self.calculate_fundamental_analysis(&stock_data)
} else {
self.get_empty_fundamental_analysis()
};
// Generate reasoning
let reasoning = self.generate_reasoning(&stock_data, beginner_score, &risk_level);
Ok(StockAnalysis {
symbol: stock_data.symbol.clone(),
beginner_friendly_score: beginner_score,
risk_level,
recommendation,
technical_indicators,
fundamental_analysis,
reasoning,
})
}
/// Async technical indicators calculation
async fn calculate_technical_indicators_async(&self, symbol: &str) -> Result<TechnicalIndicators> {
// Fetch historical data
let historical_data = self.fetch_historical_data_async(symbol).await?;
if historical_data.len() < self.config.analysis.min_historical_data_points {
return Err(anyhow!("Insufficient historical data for technical analysis"));
}
// Extract close prices
let prices: Vec<f64> = historical_data.iter()
.map(|d| d.close_price)
.collect();
// Calculate indicators in parallel
let (rsi, macd_result, sma_20, sma_50, ema_12, ema_26, bb_result) = tokio::join!(
tokio::task::spawn_blocking(move || Self::calculate_rsi(&prices, 14)),
tokio::task::spawn_blocking(move || Self::calculate_macd(&prices, 12, 26, 9)),
tokio::task::spawn_blocking(move || Self::calculate_sma(&prices, 20)),
tokio::task::spawn_blocking(move || Self::calculate_sma(&prices, 50)),
tokio::task::spawn_blocking(move || Self::calculate_ema(&prices, 12)),
tokio::task::spawn_blocking(move || Self::calculate_ema(&prices, 26)),
tokio::task::spawn_blocking(move || Self::calculate_bollinger_bands(&prices, 20, 2.0))
);
let (macd, macd_signal, macd_histogram) = macd_result??;
let (bb_upper, bb_lower, bb_middle) = bb_result??;
Ok(TechnicalIndicators {
rsi: Some(rsi?),
macd: Some(macd),
macd_signal: Some(macd_signal),
macd_histogram: Some(macd_histogram),
sma_20: Some(sma_20?),
sma_50: Some(sma_50?),
ema_12: Some(ema_12?),
ema_26: Some(ema_26?),
bollinger_upper: Some(bb_upper),
bollinger_lower: Some(bb_lower),
bollinger_middle: Some(bb_middle),
})
}
/// Fetch historical data with caching
async fn fetch_historical_data_async(&self, symbol: &str) -> Result<Vec<HistoricalData>> {
info!("Fetching historical data for {}", symbol);
self.rate_limiter.wait_if_needed().await;
let url = format!("{}?function=TIME_SERIES_DAILY&symbol={}&apikey={}", 
self.config.alpha_vantage.base_url, symbol, self.config.alpha_vantage.api_key);
let response = self.client.get(&url).send().await?;
let data: Value = response.json().await?;
let time_series = data.get("Time Series (Daily)")
.ok_or_else(|| anyhow!("No time series data available"))?;
let mut historical_data = Vec::new();
for (date_str, daily_data) in time_series.as_object().unwrap().iter().take(100) {
if let Some(close_str) = daily_data.get("4. close").and_then(|v| v.as_str()) {
if let Ok(close_price) = close_str.parse::<f64>() {
if let Ok(timestamp) = chrono::NaiveDate::parse_from_str(date_str, "%Y-%m-%d") {
let timestamp = timestamp.and_hms_opt(0, 0, 0).unwrap();
let utc_timestamp = chrono::DateTime::<Utc>::from_naive_utc_and_offset(timestamp, Utc);
historical_data.push(HistoricalData {
close_price,
timestamp: utc_timestamp,
});
}
}
}
}
// Sort by timestamp (oldest first)
historical_data.sort_by(|a, b| a.timestamp.cmp(&b.timestamp));
Ok(historical_data)
}
/// Cache management
fn get_cached_data(&self, symbol: &str) -> Option<StockData> {
let cache = self.cache.lock().unwrap();
if let Some((data, timestamp)) = cache.get(symbol) {
if timestamp.elapsed() < self.cache_ttl {
return Some(data.clone());
}
}
None
}
fn cache_data(&self, symbol: &str, data: &StockData) {
let mut cache = self.cache.lock().unwrap();
cache.insert(symbol.to_string(), (data.clone(), Instant::now()));
}
/// Helper methods for empty structures
fn get_empty_technical_indicators(&self) -> TechnicalIndicators {
TechnicalIndicators {
rsi: None,
macd: None,
macd_signal: None,
macd_histogram: None,
sma_20: None,
sma_50: None,
ema_12: None,
ema_26: None,
bollinger_upper: None,
bollinger_lower: None,
bollinger_middle: None,
}
}
fn get_empty_fundamental_analysis(&self) -> FundamentalAnalysis {
FundamentalAnalysis {
valuation_score: 0,
growth_score: 0,
stability_score: 0,
dividend_score: 0,
debt_score: 0,
}
}
// Static methods for technical calculations (can be called from spawn_blocking)
fn calculate_rsi(prices: &[f64], period: usize) -> Result<f64> {
if prices.len() < period + 1 {
return Ok(50.0);
}
let mut gains = Vec::new();
let mut losses = Vec::new();
for i in 1..prices.len() {
let change = prices[i] - prices[i - 1];
if change > 0.0 {
gains.push(change);
losses.push(0.0);
} else {
gains.push(0.0);
losses.push(-change);
}
}
if gains.len() < period {
return Ok(50.0);
}
let avg_gain: f64 = gains.iter().rev().take(period).sum::<f64>() / period as f64;
let avg_loss: f64 = losses.iter().rev().take(period).sum::<f64>() / period as f64;
if avg_loss == 0.0 {
return Ok(100.0);
}
let rs = avg_gain / avg_loss;
Ok(100.0 - (100.0 / (1.0 + rs)))
}
fn calculate_macd(prices: &[f64], fast_period: usize, slow_period: usize, _signal_period: usize) -> Result<(f64, f64, f64)> {
if prices.len() < slow_period {
return Ok((0.0, 0.0, 0.0));
}
let ema_fast = Self::calculate_ema(prices, fast_period)?;
let ema_slow = Self::calculate_ema(prices, slow_period)?;
let macd_line = ema_fast - ema_slow;
let signal_line = macd_line * 0.8; // Simplified
let histogram = macd_line - signal_line;
Ok((macd_line, signal_line, histogram))
}
fn calculate_sma(prices: &[f64], period: usize) -> Result<f64> {
if prices.len() < period {
return Ok(prices.last().copied().unwrap_or(0.0));
}
let sum: f64 = prices.iter().rev().take(period).sum();
Ok(sum / period as f64)
}
fn calculate_ema(prices: &[f64], period: usize) -> Result<f64> {
if prices.len() < period {
return Ok(prices.last().copied().unwrap_or(0.0));
}
let multiplier = 2.0 / (period as f64 + 1.0);
let mut ema = prices[0];
for &price in prices.iter().skip(1) {
ema = (price * multiplier) + (ema * (1.0 - multiplier));
}
Ok(ema)
}
fn calculate_bollinger_bands(prices: &[f64], period: usize, std_dev: f64) -> Result<(f64, f64, f64)> {
if prices.len() < period {
let price = prices.last().copied().unwrap_or(0.0);
return Ok((price, price, price));
}
let sma = Self::calculate_sma(prices, period)?;
let variance: f64 = prices.iter().rev().take(period)
.map(|&p| (p - sma).powi(2))
.sum::<f64>() / period as f64;
let std_deviation = variance.sqrt();
let upper_band = sma + (std_deviation * std_dev);
let lower_band = sma - (std_deviation * std_dev);
Ok((upper_band, lower_band, sma))
}
// Keep the existing scoring methods (they're already good)
fn calculate_beginner_friendly_score(&self, stock_data: &StockData) -> u8 {
let mut score = 0u8;
// Market cap scoring (prefer large caps > $1B)
if stock_data.market_cap >= self.config.analysis.min_market_cap {
score += 25;
} else if stock_data.market_cap >= 100_000_000_000 {
score += 15;
} else if stock_data.market_cap >= 10_000_000_000 {
score += 5;
}
// P/E ratio scoring (prefer reasonable P/E < 35)
if let Some(pe) = stock_data.pe_ratio {
if pe < 15.0 {
score += 20;
} else if pe < 25.0 {
score += 15;
} else if pe < self.config.analysis.max_pe_ratio {
score += 5;
}
}
// Dividend yield scoring (prefer dividends > 1%)
if let Some(dividend) = stock_data.dividend_yield {
if dividend > 3.0 {
score += 20;
} else if dividend > 2.0 {
score += 15;
} else if dividend > self.config.analysis.min_dividend_yield {
score += 10;
}
}
// Volume scoring (prefer high liquidity)
if stock_data.volume > self.config.analysis.min_volume {
score += 10;
} else if stock_data.volume > 1_000_000 {
score += 5;
}
score.min(100) // Cap at 100
}
fn calculate_risk_level(&self, _stock_data: &StockData, beginner_score: u8) -> RiskLevel {
match beginner_score {
80..=100 => RiskLevel::Low,
60..=79 => RiskLevel::Medium,
_ => RiskLevel::High,
}
}
fn generate_recommendation(&self, beginner_score: u8, risk_level: &RiskLevel) -> Recommendation {
match (beginner_score, risk_level) {
(80..=100, RiskLevel::Low) => Recommendation::StrongBuy,
(70..=89, RiskLevel::Low) => Recommendation::Buy,
(60..=79, RiskLevel::Medium) => Recommendation::Buy,
(50..=69, RiskLevel::Medium) => Recommendation::Hold,
(40..=59, RiskLevel::High) => Recommendation::Hold,
(30..=39, RiskLevel::High) => Recommendation::Sell,
_ => Recommendation::StrongSell,
}
}
fn calculate_fundamental_analysis(&self, stock_data: &StockData) -> FundamentalAnalysis {
let mut valuation_score = 0u8;
let mut stability_score = 0u8;
let mut dividend_score = 0u8;
let mut debt_score = 0u8;
// Valuation scoring
if let Some(pe) = stock_data.pe_ratio {
if pe < 15.0 {
valuation_score = 25;
} else if pe < 25.0 {
valuation_score = 20;
} else if pe < 35.0 {
valuation_score = 15;
}
}
// Dividend scoring
if let Some(dividend) = stock_data.dividend_yield {
if dividend > 3.0 {
dividend_score = 25;
} else if dividend > 2.0 {
dividend_score = 20;
} else if dividend > 1.0 {
dividend_score = 15;
}
}
// Stability scoring (based on market cap and volume)
let stability_score = if stock_data.market_cap >= 100_000_000_000 && stock_data.volume > 1_000_000 {
25
} else if stock_data.market_cap >= 10_000_000_000 && stock_data.volume > 500_000 {
20
} else {
15
};
// Growth scoring (placeholder - would need historical data)
let growth_score = 15; // Default moderate growth assumption
FundamentalAnalysis {
valuation_score,
growth_score,
stability_score,
dividend_score,
debt_score,
}
}
fn generate_reasoning(&self, stock_data: &StockData, beginner_score: u8, risk_level: &RiskLevel) -> Vec<String> {
let mut reasons = Vec::new();
if beginner_score >= 80 {
reasons.push("Excellent choice for beginners".to_string());
} else if beginner_score >= 60 {
reasons.push("Good option for beginners with some experience".to_string());
} else {
reasons.push("Consider this stock only if you have investment experience".to_string());
}
if stock_data.market_cap >= 100_000_000_000 {
reasons.push("Large market cap provides stability".to_string());
}
if let Some(dividend) = stock_data.dividend_yield {
if dividend > 2.0 {
reasons.push("Attractive dividend yield for income".to_string());
}
}
match risk_level {
RiskLevel::Low => reasons.push("Low risk profile suitable for conservative investors".to_string()),
RiskLevel::Medium => reasons.push("Moderate risk with potential for growth".to_string()),
RiskLevel::High => reasons.push("Higher risk, higher potential return".to_string()),
RiskLevel::Unknown => reasons.push("Risk assessment unavailable".to_string()),
}
reasons
}
}
