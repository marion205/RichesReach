use crate::models::*;
use crate::config::Config;
use anyhow::{Result, anyhow};
use reqwest::Client;
use tracing::{info, warn};
use chrono::Utc;
pub struct StockAnalyzer {
config: Config,
client: Client,
}
impl StockAnalyzer {
pub fn new(config: Config) -> Self {
Self {
config,
client: Client::new(),
}
}
pub async fn analyze_stock(&self, symbol: &str, include_technical: bool, include_fundamental: bool) -> Result<StockAnalysis> {
info!("Analyzing stock: {}", symbol);
// Fetch real stock data from Alpha Vantage
let stock_data = self.fetch_stock_data(symbol).await?;
// Calculate beginner-friendly score
let beginner_score = self.calculate_beginner_friendly_score(&stock_data);
// Calculate risk level
let risk_level = self.calculate_risk_level(&stock_data, beginner_score);
// Generate recommendation
let recommendation = self.generate_recommendation(beginner_score, &risk_level);
// Calculate technical indicators if requested
let technical_indicators = if include_technical {
match self.calculate_technical_indicators(symbol).await {
Ok(indicators) => indicators,
Err(e) => {
warn!("Failed to calculate technical indicators: {}", e);
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
}
} else {
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
};
// Calculate fundamental analysis if requested
let fundamental_analysis = if include_fundamental {
self.calculate_fundamental_analysis(&stock_data)
} else {
FundamentalAnalysis {
valuation_score: 0,
growth_score: 0,
stability_score: 0,
dividend_score: 0,
debt_score: 0,
}
};
// Generate reasoning
let reasoning = self.generate_reasoning(&stock_data, beginner_score, &risk_level);
Ok(StockAnalysis {
symbol: symbol.to_string(),
beginner_friendly_score: beginner_score,
risk_level,
recommendation,
technical_indicators,
fundamental_analysis,
reasoning,
})
}
pub async fn calculate_technical_indicators(&self, symbol: &str) -> Result<TechnicalIndicators> {
// Fetch historical data for technical analysis
let historical_data = self.fetch_historical_data(symbol).await?;
if historical_data.len() < self.config.analysis.min_historical_data_points {
return Err(anyhow!("Insufficient historical data for technical analysis. Need at least {} data points, got {}", 
self.config.analysis.min_historical_data_points, historical_data.len()));
}
// Extract close prices for calculations
let prices: Vec<f64> = historical_data.iter()
.map(|d| d.close_price)
.collect();
// Calculate RSI (14-period)
let rsi = self.calculate_rsi(&prices, 14);
// Calculate MACD (12, 26, 9)
let (macd, macd_signal, macd_histogram) = self.calculate_macd(&prices, 12, 26, 9);
// Calculate Simple Moving Averages
let sma_20 = self.calculate_sma(&prices, 20);
let sma_50 = self.calculate_sma(&prices, 50);
// Calculate Exponential Moving Averages
let ema_12 = self.calculate_ema(&prices, 12);
let ema_26 = self.calculate_ema(&prices, 26);
// Calculate Bollinger Bands (20-period, 2 standard deviations)
let (bb_upper, bb_lower, bb_middle) = self.calculate_bollinger_bands(&prices, 20, 2.0);
Ok(TechnicalIndicators {
rsi: Some(rsi),
macd: Some(macd),
macd_signal: Some(macd_signal),
macd_histogram: Some(macd_histogram),
sma_20: Some(sma_20),
sma_50: Some(sma_50),
ema_12: Some(ema_12),
ema_26: Some(ema_26),
bollinger_upper: Some(bb_upper),
bollinger_lower: Some(bb_lower),
bollinger_middle: Some(bb_middle),
})
}
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
// Debt ratio scoring (prefer low debt < 50%)
if let Some(debt) = stock_data.debt_ratio {
if debt < 20.0 {
score += 20;
} else if debt < 30.0 {
score += 15;
} else if debt < self.config.analysis.max_debt_ratio {
score += 5;
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
// Debt scoring
if let Some(debt) = stock_data.debt_ratio {
if debt < 20.0 {
debt_score = 25;
} else if debt < 30.0 {
debt_score = 20;
} else if debt < 50.0 {
debt_score = 15;
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
if let Some(debt) = stock_data.debt_ratio {
if debt < 30.0 {
reasons.push("Low debt levels indicate financial health".to_string());
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
async fn fetch_stock_data(&self, symbol: &str) -> Result<StockData> {
info!("Fetching stock data for {}", symbol);
// Fetch quote data
let quote_url = format!("{}?function=GLOBAL_QUOTE&symbol={}&apikey={}", 
self.config.alpha_vantage.base_url, symbol, self.config.alpha_vantage.api_key);
let quote_response = self.client.get(&quote_url).send().await?;
let quote_data: AlphaVantageQuoteResponse = quote_response.json().await?;
// Fetch company overview data
let overview_url = format!("{}?function=OVERVIEW&symbol={}&apikey={}", 
self.config.alpha_vantage.base_url, symbol, self.config.alpha_vantage.api_key);
let overview_response = self.client.get(&overview_url).send().await?;
let overview_data: AlphaVantageOverviewResponse = overview_response.json().await?;
// Parse quote data
let global_quote = quote_data.global_quote.ok_or_else(|| anyhow!("No quote data available"))?;
let current_price: f64 = global_quote.price.parse().unwrap_or(0.0);
let previous_close: f64 = global_quote.previous_close.parse().unwrap_or(0.0);
let price_change = current_price - previous_close;
let price_change_percent = if previous_close > 0.0 {
(price_change / previous_close) * 100.0
} else {
0.0
};
let volume: u64 = global_quote.volume.parse().unwrap_or(0);
// Parse overview data
let market_cap: u64 = overview_data.MarketCapitalization
.and_then(|s| s.parse().ok())
.unwrap_or(0);
let pe_ratio: Option<f64> = overview_data.PERatio
.and_then(|s| s.parse().ok());
let dividend_yield: Option<f64> = overview_data.DividendYield
.and_then(|s| s.trim_end_matches('%').parse::<f64>().ok())
.map(|y: f64| y / 100.0); // Convert percentage to decimal
let debt_ratio: Option<f64> = None; // Alpha Vantage doesn't provide debt ratio directly
Ok(StockData {
symbol: symbol.to_string(),
company_name: overview_data.Name,
current_price,
price_change,
price_change_percent,
market_cap,
pe_ratio,
dividend_yield,
debt_ratio,
volume,
timestamp: Utc::now(),
})
}
async fn fetch_historical_data(&self, symbol: &str) -> Result<Vec<HistoricalData>> {
info!("Fetching historical data for {}", symbol);
let url = format!("{}?function=TIME_SERIES_DAILY&symbol={}&apikey={}", 
self.config.alpha_vantage.base_url, symbol, self.config.alpha_vantage.api_key);
let response = self.client.get(&url).send().await?;
let data: AlphaVantageTimeSeriesResponse = response.json().await?;
let time_series = data.time_series_daily
.ok_or_else(|| anyhow!("No time series data available"))?;
let mut historical_data = Vec::new();
for (date_str, daily_data) in time_series.iter().take(100) { // Limit to 100 days
if let Ok(close_price) = daily_data.close.parse::<f64>() {
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
// Sort by timestamp (oldest first)
historical_data.sort_by(|a, b| a.timestamp.cmp(&b.timestamp));
Ok(historical_data)
}
// Technical Indicator Calculations
fn calculate_rsi(&self, prices: &[f64], period: usize) -> f64 {
if prices.len() < period + 1 {
return 50.0; // Default neutral RSI
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
return 50.0;
}
let avg_gain: f64 = gains.iter().rev().take(period).sum::<f64>() / period as f64;
let avg_loss: f64 = losses.iter().rev().take(period).sum::<f64>() / period as f64;
if avg_loss == 0.0 {
return 100.0;
}
let rs = avg_gain / avg_loss;
100.0 - (100.0 / (1.0 + rs))
}
fn calculate_macd(&self, prices: &[f64], fast_period: usize, slow_period: usize, _signal_period: usize) -> (f64, f64, f64) {
if prices.len() < slow_period {
return (0.0, 0.0, 0.0);
}
let ema_fast = self.calculate_ema(prices, fast_period);
let ema_slow = self.calculate_ema(prices, slow_period);
let macd_line = ema_fast - ema_slow;
// For signal line, we'd need to calculate EMA of MACD line
// For simplicity, using a placeholder
let signal_line = macd_line * 0.8; // Simplified
let histogram = macd_line - signal_line;
(macd_line, signal_line, histogram)
}
fn calculate_sma(&self, prices: &[f64], period: usize) -> f64 {
if prices.len() < period {
return prices.last().copied().unwrap_or(0.0);
}
let sum: f64 = prices.iter().rev().take(period).sum();
sum / period as f64
}
fn calculate_ema(&self, prices: &[f64], period: usize) -> f64 {
if prices.len() < period {
return prices.last().copied().unwrap_or(0.0);
}
let multiplier = 2.0 / (period as f64 + 1.0);
let mut ema = prices[0];
for &price in prices.iter().skip(1) {
ema = (price * multiplier) + (ema * (1.0 - multiplier));
}
ema
}
fn calculate_bollinger_bands(&self, prices: &[f64], period: usize, std_dev: f64) -> (f64, f64, f64) {
if prices.len() < period {
let price = prices.last().copied().unwrap_or(0.0);
return (price, price, price);
}
let sma = self.calculate_sma(prices, period);
// Calculate standard deviation
let variance: f64 = prices.iter().rev().take(period)
.map(|&p| (p - sma).powi(2))
.sum::<f64>() / period as f64;
let std_deviation = variance.sqrt();
let upper_band = sma + (std_deviation * std_dev);
let lower_band = sma - (std_deviation * std_dev);
(upper_band, lower_band, sma)
}
}
