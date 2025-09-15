use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StockData {
pub symbol: String,
pub company_name: String,
pub current_price: f64,
pub price_change: f64,
pub price_change_percent: f64,
pub market_cap: u64,
pub pe_ratio: Option<f64>,
pub dividend_yield: Option<f64>,
pub debt_ratio: Option<f64>,
pub volume: u64,
pub timestamp: DateTime<Utc>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TechnicalIndicators {
pub rsi: Option<f64>,
pub macd: Option<f64>,
pub macd_signal: Option<f64>,
pub macd_histogram: Option<f64>,
pub sma_20: Option<f64>,
pub sma_50: Option<f64>,
pub ema_12: Option<f64>,
pub ema_26: Option<f64>,
pub bollinger_upper: Option<f64>,
pub bollinger_lower: Option<f64>,
pub bollinger_middle: Option<f64>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StockAnalysis {
pub symbol: String,
pub beginner_friendly_score: u8,
pub risk_level: RiskLevel,
pub recommendation: Recommendation,
pub technical_indicators: TechnicalIndicators,
pub fundamental_analysis: FundamentalAnalysis,
pub reasoning: Vec<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RiskLevel {
Low,
Medium,
High,
Unknown,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Recommendation {
StrongBuy,
Buy,
Hold,
Sell,
StrongSell,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FundamentalAnalysis {
pub valuation_score: u8,
pub growth_score: u8,
pub stability_score: u8,
pub dividend_score: u8,
pub debt_score: u8,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisRequest {
pub symbol: String,
pub include_technical: bool,
pub include_fundamental: bool,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisResponse {
pub success: bool,
pub analysis: Option<StockAnalysis>,
pub error: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HistoricalData {
pub close_price: f64,
pub timestamp: DateTime<Utc>,
}
// Alpha Vantage API Response Models
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageQuoteResponse {
#[serde(rename = "Global Quote")]
pub global_quote: Option<GlobalQuote>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlobalQuote {
#[serde(rename = "01. symbol")]
pub symbol: String,
#[serde(rename = "02. open")]
pub open: String,
#[serde(rename = "03. high")]
pub high: String,
#[serde(rename = "04. low")]
pub low: String,
#[serde(rename = "05. price")]
pub price: String,
#[serde(rename = "06. volume")]
pub volume: String,
#[serde(rename = "07. latest trading day")]
pub latest_trading_day: String,
#[serde(rename = "08. previous close")]
pub previous_close: String,
#[serde(rename = "09. change")]
pub change: String,
#[serde(rename = "10. change percent")]
pub change_percent: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageOverviewResponse {
pub Symbol: String,
pub AssetType: String,
pub Name: String,
pub Description: Option<String>,
#[serde(rename = "CIK")]
pub cik: Option<String>,
pub Exchange: String,
pub Currency: String,
pub Country: String,
pub Sector: Option<String>,
pub Industry: Option<String>,
pub Address: Option<String>,
pub FiscalYearEnd: Option<String>,
pub LatestQuarter: Option<String>,
pub MarketCapitalization: Option<String>,
pub EBITDA: Option<String>,
pub PERatio: Option<String>,
pub PEGRatio: Option<String>,
pub BookValue: Option<String>,
pub DividendPerShare: Option<String>,
pub DividendYield: Option<String>,
pub EPS: Option<String>,
pub RevenuePerShareTTM: Option<String>,
pub ProfitMargin: Option<String>,
pub OperatingMarginTTM: Option<String>,
pub ReturnOnAssetsTTM: Option<String>,
pub ReturnOnEquityTTM: Option<String>,
pub RevenueTTM: Option<String>,
pub GrossProfitTTM: Option<String>,
pub DilutedEPSTTM: Option<String>,
pub QuarterlyEarningsGrowthYOY: Option<String>,
pub QuarterlyRevenueGrowthYOY: Option<String>,
pub AnalystTargetPrice: Option<String>,
pub TrailingPE: Option<String>,
pub ForwardPE: Option<String>,
pub PriceToBookRatio: Option<String>,
pub PriceToSalesRatioTTM: Option<String>,
pub EVToRevenue: Option<String>,
pub EVToEBITDA: Option<String>,
pub Beta: Option<String>,
pub FiftyTwoWeekHigh: Option<String>,
pub FiftyTwoWeekLow: Option<String>,
pub FiftyDayAverage: Option<String>,
pub TwoHundredDayAverage: Option<String>,
pub SharesOutstanding: Option<String>,
pub DividendDate: Option<String>,
pub ExDividendDate: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlphaVantageTimeSeriesResponse {
#[serde(rename = "Time Series (Daily)")]
pub time_series_daily: Option<std::collections::HashMap<String, DailyData>>,
#[serde(rename = "Meta Data")]
pub meta_data: Option<MetaData>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DailyData {
#[serde(rename = "1. open")]
pub open: String,
#[serde(rename = "2. high")]
pub high: String,
#[serde(rename = "3. low")]
pub low: String,
#[serde(rename = "4. close")]
pub close: String,
#[serde(rename = "5. volume")]
pub volume: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetaData {
#[serde(rename = "1. Information")]
pub information: String,
#[serde(rename = "2. Symbol")]
pub symbol: String,
#[serde(rename = "3. Last Refreshed")]
pub last_refreshed: String,
#[serde(rename = "4. Output Size")]
pub output_size: String,
#[serde(rename = "5. Time Zone")]
pub time_zone: String,
}
