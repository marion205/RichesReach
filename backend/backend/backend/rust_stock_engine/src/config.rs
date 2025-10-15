use config::{Config as ConfigSource, Environment, File};
use serde::Deserialize;
#[derive(Debug, Clone, Deserialize)]
pub struct Config {
pub server: ServerConfig,
pub alpha_vantage: AlphaVantageConfig,
pub analysis: AnalysisConfig,
}
#[derive(Debug, Clone, Deserialize)]
pub struct ServerConfig {
pub host: String,
pub port: u16,
pub log_level: String,
}
#[derive(Debug, Clone, Deserialize)]
pub struct AlphaVantageConfig {
pub api_key: String,
pub base_url: String,
pub rate_limit_per_minute: u32,
pub rate_limit_per_day: u32,
}
#[derive(Debug, Clone, Deserialize)]
pub struct AnalysisConfig {
pub min_historical_data_points: usize,
pub min_market_cap: u64,
pub max_pe_ratio: f64,
pub min_dividend_yield: f64,
pub max_debt_ratio: f64,
pub min_volume: u64,
}
impl Config {
pub fn load() -> Result<Self, config::ConfigError> {
let config = ConfigSource::builder()
.add_source(File::with_name("config").required(false))
.add_source(Environment::with_prefix("STOCK_ENGINE"))
.build()?;
config.try_deserialize()
}
}
impl Default for Config {
fn default() -> Self {
Self {
server: ServerConfig {
host: "127.0.0.1".to_string(),
port: 3001,
log_level: "info".to_string(),
},
alpha_vantage: AlphaVantageConfig {
api_key: "".to_string(),
base_url: "https://www.alphavantage.co/query".to_string(),
rate_limit_per_minute: 5,
rate_limit_per_day: 500,
},
analysis: AnalysisConfig {
min_historical_data_points: 50,
min_market_cap: 1_000_000_000,
max_pe_ratio: 35.0,
min_dividend_yield: 1.0,
max_debt_ratio: 50.0,
min_volume: 500_000,
},
}
}
}
