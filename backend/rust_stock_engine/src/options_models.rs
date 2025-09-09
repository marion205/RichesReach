use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Options contract data structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionContract {
    pub symbol: String,
    pub contract_symbol: String,
    pub strike: f64,
    pub expiration_date: DateTime<Utc>,
    pub option_type: OptionType,
    pub bid: f64,
    pub ask: f64,
    pub last_price: f64,
    pub volume: u64,
    pub open_interest: u64,
    pub implied_volatility: f64,
    pub delta: f64,
    pub gamma: f64,
    pub theta: f64,
    pub vega: f64,
    pub rho: f64,
    pub intrinsic_value: f64,
    pub time_value: f64,
    pub days_to_expiration: i64,
    pub timestamp: DateTime<Utc>,
}

/// Option type (Call or Put)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OptionType {
    Call,
    Put,
}

/// Options chain for a specific stock
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsChain {
    pub underlying_symbol: String,
    pub underlying_price: f64,
    pub expiration_dates: Vec<DateTime<Utc>>,
    pub call_options: Vec<OptionContract>,
    pub put_options: Vec<OptionContract>,
    pub timestamp: DateTime<Utc>,
}

/// Options flow data for unusual activity detection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsFlow {
    pub symbol: String,
    pub contract_symbol: String,
    pub option_type: OptionType,
    pub strike: f64,
    pub expiration_date: DateTime<Utc>,
    pub volume: u64,
    pub open_interest: u64,
    pub premium: f64,
    pub implied_volatility: f64,
    pub unusual_activity_score: f64,
    pub activity_type: ActivityType,
    pub timestamp: DateTime<Utc>,
}

/// Type of unusual options activity
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ActivityType {
    Sweep,           // Large block trades
    Block,           // Institutional block trades
    UnusualVolume,   // High volume relative to average
    UnusualOI,       // High open interest
    GapUp,           // Price gap up
    GapDown,         // Price gap down
    Earnings,        // Earnings-related activity
    News,            // News-related activity
}

/// Options strategy analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsStrategy {
    pub strategy_name: String,
    pub strategy_type: StrategyType,
    pub contracts: Vec<OptionContract>,
    pub max_profit: f64,
    pub max_loss: f64,
    pub breakeven_points: Vec<f64>,
    pub probability_of_profit: f64,
    pub risk_reward_ratio: f64,
    pub days_to_expiration: i64,
    pub total_cost: f64,
    pub total_credit: f64,
}

/// Types of options strategies
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum StrategyType {
    CoveredCall,
    CashSecuredPut,
    BullCallSpread,
    BearCallSpread,
    BullPutSpread,
    BearPutSpread,
    IronCondor,
    IronButterfly,
    Straddle,
    Strangle,
    CalendarSpread,
    DiagonalSpread,
    Butterfly,
    Condor,
}

/// Options analysis request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsAnalysisRequest {
    pub symbol: String,
    pub include_chain: bool,
    pub include_flow: bool,
    pub include_strategies: bool,
    pub expiration_date: Option<DateTime<Utc>>,
    pub strike_range: Option<(f64, f64)>,
}

/// Options analysis response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsAnalysisResponse {
    pub success: bool,
    pub underlying_symbol: String,
    pub underlying_price: f64,
    pub options_chain: Option<OptionsChain>,
    pub unusual_flow: Vec<OptionsFlow>,
    pub recommended_strategies: Vec<OptionsStrategy>,
    pub market_sentiment: MarketSentiment,
    pub error: Option<String>,
}

/// Market sentiment based on options data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketSentiment {
    pub put_call_ratio: f64,
    pub implied_volatility_rank: f64,
    pub skew: f64,
    pub sentiment_score: f64,
    pub sentiment_description: String,
}

/// Greeks calculation parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GreeksParams {
    pub spot_price: f64,
    pub strike_price: f64,
    pub time_to_expiration: f64, // in years
    pub risk_free_rate: f64,
    pub dividend_yield: f64,
    pub volatility: f64,
}

/// Black-Scholes calculation result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlackScholesResult {
    pub option_price: f64,
    pub delta: f64,
    pub gamma: f64,
    pub theta: f64,
    pub vega: f64,
    pub rho: f64,
    pub intrinsic_value: f64,
    pub time_value: f64,
}

/// Options screening criteria
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsScreeningCriteria {
    pub min_volume: Option<u64>,
    pub max_volume: Option<u64>,
    pub min_open_interest: Option<u64>,
    pub max_open_interest: Option<u64>,
    pub min_implied_volatility: Option<f64>,
    pub max_implied_volatility: Option<f64>,
    pub min_delta: Option<f64>,
    pub max_delta: Option<f64>,
    pub min_days_to_expiration: Option<i64>,
    pub max_days_to_expiration: Option<i64>,
    pub option_type: Option<OptionType>,
    pub min_strike: Option<f64>,
    pub max_strike: Option<f64>,
}

/// Options screening result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptionsScreeningResult {
    pub contracts: Vec<OptionContract>,
    pub total_found: usize,
    pub screening_criteria: OptionsScreeningCriteria,
    pub timestamp: DateTime<Utc>,
}
