#![recursion_limit = "256"]

use anyhow::Result;
use chrono::{DateTime, Utc};
use governor::{clock::DefaultClock, state::keyed::DefaultKeyedStateStore, Quota, RateLimiter};
use governor::middleware::NoOpMiddleware;
use nonzero_ext::nonzero;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, net::SocketAddr, str::FromStr, sync::Arc, time::Duration};
use tokio::sync::RwLock;
use tokio::time::{interval as tokio_interval, Duration as TokioDuration};
use tracing::{error, info, instrument, Level};
use uuid::Uuid;
use warp::{Filter, http::{HeaderMap, StatusCode}};

mod crypto_analysis;
mod stock_analysis;
mod options_analysis; // Legacy - kept for backward compatibility
mod options_core; // New: shared types
mod options_engine; // New: production engine
mod options_edge; // New: edge forecaster
mod forex_analysis;
mod sentiment_analysis;
mod correlation_analysis;
mod raha_regime_integration;
mod ml_models;
mod cache;
mod websocket;
mod market_data;
mod utils;
mod regime;
mod metrics;
mod alpha_oracle;
mod position_sizing;
mod risk_guard;
mod portfolio_memory;
mod execution;
mod safety_guardrails;
mod backtesting;
mod cross_asset;
mod reinforcement_learning;
mod quant_terminal;
mod feature_sources;
mod options_feature_source;
mod unified_asset_oracle;

use cache::CacheManager;
use crypto_analysis::CryptoAnalysisEngine;
use stock_analysis::StockAnalysisEngine;
use options_analysis::OptionsAnalysisEngine as LegacyOptionsEngine;
use options_core::*;
use options_engine::OptionsAnalysisEngine as ProductionOptionsEngine;
use options_edge::{OptionsEdgeForecaster, EdgeForecastResponse};
use forex_analysis::{ForexAnalysisEngine, ForexAnalysisResponse};
use sentiment_analysis::{SentimentAnalysisEngine, SentimentAnalysisResponse};
use correlation_analysis::{CorrelationAnalysisEngine, CorrelationAnalysisResponse};
use websocket::WebSocketManager;
use market_data::{ProviderBundle, build_provider_bundle, MarketDataProvider, MarketDataIngest, ProviderError, InMemoryOptionsProvider};
use regime::{MarketRegimeEngine, SimpleMarketRegime};
use metrics::Metrics;
use alpha_oracle::{AlphaOracle, AlphaSignal};
use position_sizing::{PositionSizingEngine, PositionSizingConfig, PositionSizingDecision};
use risk_guard::{RiskGuard, RiskGuardConfig, RiskGuardDecision, OpenRiskPosition};
use portfolio_memory::{PortfolioMemoryEngine, TradeRecord, TradeOutcome, PersonalizedRecommendation};
use execution::{ExecutionEngine, ExecutionConfig, OrderRequest, OrderReceipt};
use safety_guardrails::{SafetyGuardrailsEngine, SafetyConfig, SafetyCheck};
use backtesting::{BacktestingEngine, BacktestConfig, TradeSignal};
use cross_asset::{CrossAssetFusionEngine, CrossAssetSignal};
use reinforcement_learning::{ReinforcementLearningEngine, StrategyContext, RewardSignal};
use quant_terminal::QuantTerminal;
use feature_sources::{FeatureSource, AssetClass};
use options_feature_source::OptionsFeatureSource;
use unified_asset_oracle::{UnifiedAssetOracle, UnifiedSignalRequest, UnifiedSignal};

/* ----------------------------- types ----------------------------- */

#[derive(Debug)]
struct AnalysisError(anyhow::Error);
impl warp::reject::Reject for AnalysisError {}

#[derive(Debug, Serialize, Deserialize)]
pub struct CryptoAnalysisRequest {
    pub symbol: String,
    #[serde(default)]
    pub timeframe: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OptionsAnalysisRequest {
    pub symbol: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EdgePredictionRequest {
    pub symbol: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OneTapTradeRequest {
    pub symbol: String,
    pub account_size: Option<f64>,
    pub risk_tolerance: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct IVForecastRequest {
    pub symbol: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ForexAnalysisRequest {
    pub pair: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SentimentAnalysisRequest {
    pub symbol: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CorrelationAnalysisRequest {
    pub primary: String,
    #[serde(default)]
    pub secondary: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct IngestPriceRequest {
    pub symbol: String,
    pub price: String,  // Decimal as string
    pub timestamp: String,  // ISO 8601 timestamp
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AlphaSignalRequest {
    pub symbol: String,
    pub features: HashMap<String, f64>,
    pub equity: Option<f64>,
    pub entry_price: Option<f64>,
    pub open_positions: Option<Vec<OpenRiskPosition>>,
}

// Phase 1: Portfolio Memory Engine requests
#[derive(Debug, Serialize, Deserialize)]
pub struct RecordTradeRequest {
    pub user_id: String,
    pub symbol: String,
    pub strategy_type: String,
    pub entry_price: f64,
    pub entry_iv: f64,
    pub days_to_expiration: i32,
    pub position_size: f64,
    pub risk_fraction: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RecordExitRequest {
    pub user_id: String,
    pub trade_id: Option<String>,
    pub exit_price: f64,
    pub outcome: String, // "Win" | "Loss" | "Breakeven"
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GetRecommendationRequest {
    pub user_id: String,
    pub symbol: String,
    pub proposed_strategy: String,
    pub proposed_size: f64,
    pub account_equity: f64,
    pub current_iv: f64,
    pub dte: i32,
}

// Phase 1: Execution Layer requests
#[derive(Debug, Serialize, Deserialize)]
pub struct SubmitOrderRequest {
    pub user_id: String,
    pub trade: OneTapTrade,
    pub account_equity: f64,
    pub idempotency_key: Option<String>,
}

// Phase 1: Safety & Guardrails requests
#[derive(Debug, Serialize, Deserialize)]
pub struct SafetyCheckRequest {
    pub user_id: String,
    pub trade: OneTapTrade,
    pub account_equity: f64,
    pub current_iv: f64,
    pub open_positions_risk: f64,
}

// Phase 2: Backtesting requests
#[derive(Debug, Serialize, Deserialize)]
pub struct RunBacktestRequest {
    pub strategy_name: String,
    pub symbol: String,
    pub signals: Vec<TradeSignal>,
    pub config: Option<BacktestConfig>,
}

// Phase 2: Cross-Asset Fusion requests
#[derive(Debug, Serialize, Deserialize)]
pub struct CrossAssetRequest {
    pub primary_asset: String, // e.g., "SPX"
}

// Phase 2: RL requests
#[derive(Debug, Serialize, Deserialize)]
pub struct RLRecommendRequest {
    pub user_id: String,
    pub context: StrategyContext,
    pub available_strategies: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RLUpdateRequest {
    pub reward: RewardSignal,
}

// Phase 3: Quant Terminal requests
#[derive(Debug, Serialize, Deserialize)]
pub struct VolSurfaceRequest {
    pub symbol: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EdgeDecayRequest {
    pub strategy_name: String,
    pub symbol: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RegimeTimelineRequest {
    pub start_date: String, // ISO date string
    pub end_date: String,   // ISO date string
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CryptoAnalysisResponse {
    pub symbol: String,
    pub prediction_type: String,
    pub probability: f64,
    pub confidence_level: String,
    pub explanation: String,
    pub features: HashMap<String, f64>,
    pub model_version: String,
    pub timestamp: DateTime<Utc>,
    pub price_usd: Option<Decimal>,
    pub price_change_24h: Option<f64>,
    pub volatility: f64,
    pub risk_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CryptoRecommendation {
    pub symbol: String,
    pub score: f64,
    pub probability: f64,
    pub confidence_level: String,
    pub price_usd: Decimal,
    pub volatility_tier: String,
    pub liquidity_24h_usd: Decimal,
    pub rationale: String,
    pub recommendation: String,
    pub risk_level: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub service: String,
    pub timestamp: DateTime<Utc>,
    pub version: String,
    pub cache_stats: CacheStats,
    pub ready: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub backend: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CacheStats {
    pub predictions_cached: usize,
    pub recommendations_cached: usize,
    pub hit_rate: f64,
}

/* ----------------------------- state ----------------------------- */

#[derive(Clone)]
pub struct AppState {
    pub crypto_engine: Arc<CryptoAnalysisEngine>,
    pub stock_engine: Arc<StockAnalysisEngine>,
    pub options_engine: Arc<LegacyOptionsEngine>, // Legacy - kept for backward compatibility
    pub options_engine_v2: Arc<ProductionOptionsEngine>, // Production engine
    pub options_edge_forecaster: Arc<OptionsEdgeForecaster>, // Edge forecaster
    pub forex_engine: Arc<ForexAnalysisEngine>,
    pub sentiment_engine: Arc<SentimentAnalysisEngine>,
    pub correlation_engine: Arc<CorrelationAnalysisEngine>,
    pub regime_engine: Arc<MarketRegimeEngine>,
    pub cache_manager: Arc<CacheManager>,
    pub websocket_manager: Arc<WebSocketManager>,
    pub limiter: Arc<RateLimiter<String, DefaultKeyedStateStore<String>, DefaultClock, NoOpMiddleware>>,
    pub api_token: Option<String>,
    pub ready_flag: Arc<RwLock<bool>>,
    pub market: Arc<dyn MarketDataProvider>,
    pub ingest: Arc<dyn MarketDataIngest>,
    pub metrics: Arc<Metrics>,
    pub alpha_oracle: Arc<AlphaOracle>,
    pub position_sizing: Arc<PositionSizingEngine>,
    pub risk_guard: Arc<RiskGuard>,
    pub portfolio_memory: Arc<PortfolioMemoryEngine>,
    pub execution_engine: Arc<ExecutionEngine>,
    pub safety_guardrails: Arc<SafetyGuardrailsEngine>,
    pub backtesting_engine: Arc<BacktestingEngine>,
    pub cross_asset_fusion: Arc<CrossAssetFusionEngine>,
    pub rl_engine: Arc<ReinforcementLearningEngine>,
    pub quant_terminal: Arc<QuantTerminal>,
    pub unified_oracle: Arc<unified_asset_oracle::UnifiedAssetOracle>,
}

/* ------------------------ utilities ------------------------ */

fn bearer_from_headers(headers: &HeaderMap) -> Option<String> {
    headers.get("authorization")
        .and_then(|h| h.to_str().ok())
        .and_then(|v| v.strip_prefix("Bearer ").map(|s| s.to_string()))
}

fn request_id(headers: &HeaderMap) -> String {
    headers.get("x-request-id")
        .and_then(|h| h.to_str().ok())
        .map(|s| s.to_string())
        .unwrap_or_else(|| Uuid::new_v4().to_string())
}

fn validate_symbol(sym: &str) -> bool {
    sym.len() >= 2 && sym.len() <= 15 &&
        sym.chars().all(|c| c.is_ascii_alphanumeric())
}

fn is_crypto_symbol(sym: &str) -> bool {
    // Common crypto symbols (can be extended)
    matches!(sym, "BTC" | "ETH" | "ADA" | "SOL" | "DOT" | "MATIC" | "BNB" | "XRP" | "DOGE" | "LINK")
}

fn is_forex_pair(pair: &str) -> bool {
    pair.len() == 6 && pair.chars().all(|c| c.is_ascii_alphabetic())
}

/* --------------------------- main entry --------------------------- */

#[tokio::main]
async fn main() -> Result<()> {
    // ---- tracing
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .with_target(false)
        .with_level(true)
        .json()
        .init();

    // ---- unified market data provider (shared across engines)
    let provider_bundle = build_provider_bundle().await
        .map_err(|e| anyhow::anyhow!("Failed to build provider bundle: {}", e))?;
    
    info!("Market data backend: {}", std::env::var("MARKET_DATA_BACKEND").unwrap_or_else(|_| "in_memory".to_string()));

    // ---- components
    let crypto_engine = Arc::new(CryptoAnalysisEngine::new());
    let stock_engine = Arc::new(StockAnalysisEngine::new());
    let legacy_options_engine = Arc::new(LegacyOptionsEngine::new()); // Keep for backward compatibility
    let sentiment_engine = Arc::new(SentimentAnalysisEngine::new());
    let correlation_engine = Arc::new(CorrelationAnalysisEngine::new());
    let cache_manager = Arc::new(CacheManager::new());
    let websocket_manager = Arc::new(WebSocketManager::new());
    
    // ---- provider-based engines
    let forex_engine = Arc::new(ForexAnalysisEngine::new(provider_bundle.read.clone()));
    let regime_engine = Arc::new(MarketRegimeEngine::new(provider_bundle.read.clone()));

    // ---- Alpha Oracle system
    let alpha_oracle = Arc::new(AlphaOracle::new(provider_bundle.read.clone()));
    let position_sizing = Arc::new(PositionSizingEngine::new(PositionSizingConfig::default()));
    let risk_guard = Arc::new(RiskGuard::new(RiskGuardConfig::default()));

    // ---- Phase 1: Portfolio Memory, Execution, Safety
    let portfolio_memory = Arc::new(PortfolioMemoryEngine::new());
    let execution_config = ExecutionConfig {
        alpaca_api_key: std::env::var("ALPACA_API_KEY").ok(),
        alpaca_secret_key: std::env::var("ALPACA_SECRET_KEY").ok(),
        alpaca_base_url: std::env::var("ALPACA_BASE_URL")
            .unwrap_or_else(|_| "https://paper-api.alpaca.markets".to_string()),
        enable_live_trading: std::env::var("ENABLE_LIVE_TRADING")
            .map(|v| v == "true")
            .unwrap_or(false),
        max_order_value: 100_000.0,
        commission_per_contract: 0.65,
    };
    let execution_engine = Arc::new(ExecutionEngine::new(execution_config));
    let safety_guardrails = Arc::new(SafetyGuardrailsEngine::new(
        SafetyConfig::default(),
        portfolio_memory.clone(),
    ));

    // ---- Phase 2: Backtesting + Cross-Asset Fusion + RL
    let backtesting_engine = Arc::new(BacktestingEngine::new());
    let cross_asset_fusion = Arc::new(CrossAssetFusionEngine::new(
        provider_bundle.read.clone(),
        MarketRegimeEngine::new(provider_bundle.read.clone()),
        AlphaOracle::new(provider_bundle.read.clone()),
    ));
    let rl_engine = Arc::new(ReinforcementLearningEngine::new(portfolio_memory.clone()));

    // ---- Phase 3: Quant Terminal
    let quant_terminal = Arc::new(QuantTerminal::new(
        backtesting_engine.clone(),
        MarketRegimeEngine::new(provider_bundle.read.clone()),
        portfolio_memory.clone(),
    ));

    // ---- Production Options Engine (wired into unified brain)
    let options_provider = Arc::new(InMemoryOptionsProvider::new());
    let options_engine = Arc::new(ProductionOptionsEngine::new(
        provider_bundle.read.clone(),
        options_provider.clone(),
        AlphaOracle::new(provider_bundle.read.clone()),
    ));
    
    // ---- Options Edge Forecaster
    let options_edge_forecaster = Arc::new(OptionsEdgeForecaster::new(
        provider_bundle.read.clone(),
        options_provider.clone(),
        AlphaOracle::new(provider_bundle.read.clone()),
        MarketRegimeEngine::new(provider_bundle.read.clone()),
    ));

    // ---- Unified Asset Oracle (THE FINAL BRAIN)
    let stock_features: Arc<dyn FeatureSource> = stock_engine.clone();
    let crypto_features: Arc<dyn FeatureSource> = crypto_engine.clone();
    let forex_features: Arc<dyn FeatureSource> = forex_engine.clone();
    let options_features: Arc<dyn FeatureSource> = Arc::new(OptionsFeatureSource::new(options_edge_forecaster.clone()));
    
    let unified_oracle = Arc::new(UnifiedAssetOracle::new(
        provider_bundle.read.clone(),
        MarketRegimeEngine::new(provider_bundle.read.clone()),
        AlphaOracle::new(provider_bundle.read.clone()),
        PositionSizingEngine::new(PositionSizingConfig::default()),
        RiskGuard::new(RiskGuardConfig::default()),
        stock_features,
        crypto_features,
        forex_features,
        options_features,
        Some(options_edge_forecaster.clone()),
    ));

    // ---- rate limiter (100 req / 10s per key)
    let quota = Quota::with_period(Duration::from_secs(10)).unwrap().allow_burst(nonzero!(100u32));
    let limiter = Arc::new(RateLimiter::keyed(quota));

    // ---- config
    let api_token = std::env::var("API_TOKEN").ok();
    let ready_flag = Arc::new(RwLock::new(false));
    let metrics = Arc::new(Metrics::new());

    let state = AppState {
        crypto_engine,
        stock_engine,
        options_engine: legacy_options_engine, // Legacy for backward compatibility
        options_engine_v2: options_engine.clone(), // Production engine
        options_edge_forecaster: options_edge_forecaster.clone(),
        forex_engine,
        sentiment_engine,
        correlation_engine,
        regime_engine,
        cache_manager,
        websocket_manager,
        limiter,
        api_token,
        ready_flag: ready_flag.clone(),
        market: provider_bundle.read.clone(),
        ingest: provider_bundle.ingest,
        metrics: metrics.clone(),
        alpha_oracle: alpha_oracle.clone(),
        position_sizing: position_sizing.clone(),
        risk_guard: risk_guard.clone(),
        portfolio_memory: portfolio_memory.clone(),
        execution_engine: execution_engine.clone(),
        safety_guardrails: safety_guardrails.clone(),
        backtesting_engine: backtesting_engine.clone(),
        cross_asset_fusion: cross_asset_fusion.clone(),
        rl_engine: rl_engine.clone(),
        quant_terminal: quant_terminal.clone(),
        unified_oracle: unified_oracle.clone(),
    };

    // Start WebSocket heartbeat
    state.websocket_manager.start_heartbeat().await;
    
    // Start real-time forex price updates (simulate market data feed)
    let state_clone = state.clone();
    tokio::spawn(async move {
        start_forex_price_updates(state_clone).await;
    });

    // mark ready after warmup
    {
        let s = state.clone();
        tokio::spawn(async move {
            *s.ready_flag.write().await = true;
            info!("Service warmed and ready.");
        });
    }

    // ---------------- routes ----------------
    let api = build_routes(state.clone());

    let addr: SocketAddr = ([0, 0, 0, 0], 3001).into();
    info!("🚀 Unified Market Analysis Engine on http://{addr}");
    info!("📊 Health (live):  GET /health/live");
    info!("📊 Health (ready): GET /health/ready");
    info!("🔍 Analyze:        POST /v1/analyze (auto-detects crypto/stock)");
    info!("💡 Recos:          GET  /v1/recommendations");
    info!("📈 Options:        POST /v1/options/analyze");
    info!("⚡ Edge Predict:   POST /v1/options/edge-predict");
    info!("🎯 One-Tap Trades: POST /v1/options/one-tap-trades");
    info!("📊 IV Forecast:    POST /v1/options/iv-forecast");
    info!("💱 Forex:          POST /v1/forex/analyze");
    info!("📰 Sentiment:      POST /v1/sentiment/analyze");
    info!("🔗 Correlation:    POST /v1/correlation/analyze");
    info!("📥 Ingest Price:    POST /v1/correlation/ingest-price");
    info!("🌍 Market Regime:   GET  /v1/regime (quant) | GET /v1/regime/simple (Jobs edition)");
    info!("📈 Metrics:        GET  /metrics");
    info!("⚡ WS:             WS   /v1/ws");

    // Start server
    let (_, server) = warp::serve(api)
        .bind_with_graceful_shutdown(addr, async {
            tokio::select! {
                _ = tokio::signal::ctrl_c() => {},
            }
            info!("Shutdown signal received. Draining...");
            tokio::time::sleep(Duration::from_millis(500)).await;
        });

    server.await;

    Ok(())
}

/* -------------------------- route builder ------------------------- */

fn build_routes(state: AppState) -> impl Filter<Extract = impl warp::Reply, Error = warp::Rejection> + Clone {
    let with_state = warp::any().map(move || state.clone());

    let with_req_meta = warp::any()
        .and(warp::addr::remote())
        .and(warp::header::headers_cloned())
        .map(|addr: Option<SocketAddr>, headers: HeaderMap| {
            let ip = addr.map(|a| a.ip().to_string()).unwrap_or_else(|| "unknown".into());
            let req_id = request_id(&headers);
            (ip, req_id, headers)
        });

    // security headers
    let sec_headers = warp::reply::with::headers({
        let mut h = HeaderMap::new();
        h.insert("x-content-type-options", "nosniff".parse().unwrap());
        h.insert("x-frame-options", "DENY".parse().unwrap());
        h.insert("x-xss-protection", "1; mode=block".parse().unwrap());
        h
    });

    // CORS
    let cors = warp::cors()
        .allow_any_origin()
        .allow_headers(vec!["content-type", "authorization", "x-request-id"])
        .allow_methods(vec!["GET", "POST", "OPTIONS"]);

    // ---- health endpoints
    let health_live = warp::path!("health" / "live")
        .and(warp::get())
        .and(with_state.clone())
        .and_then(health_live_handler);

    let health_ready = warp::path!("health" / "ready")
        .and(warp::get())
        .and(with_state.clone())
        .and_then(health_ready_handler);

    // ---- metrics
    let metrics_endpoint = warp::path("metrics")
        .and(warp::get())
        .and(with_state.clone())
        .and_then(metrics_handler);

    // ---- v1 API
    let v1 = warp::path("v1");

    let analyze = v1
        .and(warp::path("analyze"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(analyze_handler)
        .with(sec_headers.clone());

    let recommendations = v1
        .and(warp::path("recommendations"))
        .and(warp::get())
        .and(with_req_meta.clone())
        .and(warp::query::<HashMap<String, String>>())
        .and(with_state.clone())
        .and_then(recommendations_handler)
        .with(sec_headers.clone());

    // Options analysis endpoint
    let options_analyze = v1
        .and(warp::path("options"))
        .and(warp::path("analyze"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(options_analyze_handler)
        .with(sec_headers.clone());

    // Edge prediction endpoint
    let edge_predict = v1
        .and(warp::path("options"))
        .and(warp::path("edge-predict"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(edge_predict_handler)
        .with(sec_headers.clone());

    // One-tap trades endpoint
    let one_tap_trades = v1
        .and(warp::path("options"))
        .and(warp::path("one-tap-trades"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(one_tap_trades_handler)
        .with(sec_headers.clone());

    // IV surface forecast endpoint
    let iv_forecast = v1
        .and(warp::path("options"))
        .and(warp::path("iv-forecast"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(iv_forecast_handler)
        .with(sec_headers.clone());

    // Forex analysis endpoint
    let forex_analyze = v1
        .and(warp::path("forex"))
        .and(warp::path("analyze"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(forex_analyze_handler)
        .with(sec_headers.clone());

    // Sentiment analysis endpoint
    let sentiment_analyze = v1
        .and(warp::path("sentiment"))
        .and(warp::path("analyze"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(sentiment_analyze_handler)
        .with(sec_headers.clone());

    // Correlation analysis endpoint
    let correlation_analyze = v1
        .and(warp::path("correlation"))
        .and(warp::path("analyze"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(correlation_analyze_handler)
        .with(sec_headers.clone());

    // Price ingestion endpoint for regime oracle
    let ingest_price = v1
        .and(warp::path("correlation"))
        .and(warp::path("ingest-price"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(ingest_price_handler)
        .with(sec_headers.clone());

    // Market regime endpoint (quant edition)
    let regime_analyze = v1
        .and(warp::path("regime"))
        .and(warp::get())
        .and(with_req_meta.clone())
        .and(with_state.clone())
        .and_then(regime_analyze_handler)
        .with(sec_headers.clone());

    // Market regime endpoint (Jobs edition - simple/human-readable)
    let regime_simple = v1
        .and(warp::path("regime"))
        .and(warp::path("simple"))
        .and(warp::get())
        .and(with_req_meta.clone())
        .and(with_state.clone())
        .and_then(regime_simple_handler)
        .with(sec_headers.clone());

    // Alpha Oracle endpoint
    let alpha_signal = v1
        .and(warp::path!("alpha" / "signal"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(alpha_signal_handler)
        .with(sec_headers.clone());

    // Phase 1: Portfolio Memory Engine endpoints
    let portfolio_record_trade = v1
        .and(warp::path!("portfolio" / "record-trade"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(portfolio_record_trade_handler)
        .with(sec_headers.clone());

    let portfolio_record_exit = v1
        .and(warp::path!("portfolio" / "record-exit"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(portfolio_record_exit_handler)
        .with(sec_headers.clone());

    let portfolio_profile = v1
        .and(warp::path!("portfolio" / "profile" / String))
        .and(warp::get())
        .and(with_req_meta.clone())
        .and(with_state.clone())
        .and_then(portfolio_profile_handler)
        .with(sec_headers.clone());

    let portfolio_recommendation = v1
        .and(warp::path!("portfolio" / "recommendation"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(portfolio_recommendation_handler)
        .with(sec_headers.clone());

    // Phase 1: Execution Layer endpoints
    let execution_submit = v1
        .and(warp::path!("execution" / "submit"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(execution_submit_handler)
        .with(sec_headers.clone());

    let execution_status = v1
        .and(warp::path!("execution" / "status" / String))
        .and(warp::get())
        .and(with_req_meta.clone())
        .and(with_state.clone())
        .and_then(execution_status_handler)
        .with(sec_headers.clone());

    // Phase 1: Safety & Guardrails endpoint
    let safety_check = v1
        .and(warp::path!("safety" / "check"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(safety_check_handler)
        .with(sec_headers.clone());

    // Phase 2: Backtesting endpoints
    let backtest_run = v1
        .and(warp::path!("backtest" / "run"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(backtest_run_handler)
        .with(sec_headers.clone());

    let backtest_score = v1
        .and(warp::path!("backtest" / "score" / String / String)) // strategy_name / symbol
        .and(warp::get())
        .and(with_req_meta.clone())
        .and(with_state.clone())
        .and_then(backtest_score_handler)
        .with(sec_headers.clone());

    // Phase 2: Cross-Asset Fusion endpoint
    let cross_asset_signal = v1
        .and(warp::path!("cross-asset" / "signal"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(cross_asset_signal_handler)
        .with(sec_headers.clone());

    // Phase 2: RL endpoints
    let rl_recommend = v1
        .and(warp::path!("rl" / "recommend"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(rl_recommend_handler)
        .with(sec_headers.clone());

    let rl_update = v1
        .and(warp::path!("rl" / "update"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(rl_update_handler)
        .with(sec_headers.clone());

    // Phase 3: Quant Terminal endpoints
    let vol_surface = v1
        .and(warp::path!("quant" / "vol-surface"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(vol_surface_handler)
        .with(sec_headers.clone());

    let edge_decay = v1
        .and(warp::path!("quant" / "edge-decay"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(edge_decay_handler)
        .with(sec_headers.clone());

    let regime_timeline = v1
        .and(warp::path!("quant" / "regime-timeline"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(regime_timeline_handler)
        .with(sec_headers.clone());

    let portfolio_dna = v1
        .and(warp::path!("quant" / "portfolio-dna" / String)) // user_id
        .and(warp::get())
        .and(with_req_meta.clone())
        .and(with_state.clone())
        .and_then(portfolio_dna_handler)
        .with(sec_headers.clone());

    // Unified Asset Oracle endpoint (THE FINAL BRAIN)
    let unified_signal = v1
        .and(warp::path!("unified" / "signal"))
        .and(warp::post())
        .and(with_req_meta.clone())
        .and(warp::body::json())
        .and(with_state.clone())
        .and_then(unified_signal_handler)
        .with(sec_headers.clone());

    let websocket = v1
        .and(warp::path("ws"))
        .and(warp::ws())
        .and(with_req_meta.clone())
        .and(with_state.clone())
        .and_then(websocket_handler);

    // Compose + middlewares
    health_live
        .or(health_ready)
        .or(metrics_endpoint)
        .or(analyze)
        .or(recommendations)
        .or(options_analyze)
        .or(edge_predict)
        .or(one_tap_trades)
        .or(iv_forecast)
        .or(forex_analyze)
        .or(sentiment_analyze)
        .or(correlation_analyze)
        .or(ingest_price)
        .or(regime_analyze)
        .or(regime_simple)
        .or(alpha_signal)
        .or(portfolio_record_trade)
        .or(portfolio_record_exit)
        .or(portfolio_profile)
        .or(portfolio_recommendation)
        .or(execution_submit)
        .or(execution_status)
        .or(safety_check)
        .or(backtest_run)
        .or(backtest_score)
        .or(cross_asset_signal)
        .or(rl_recommend)
        .or(rl_update)
        .or(vol_surface)
        .or(edge_decay)
        .or(regime_timeline)
        .or(portfolio_dna)
        .or(websocket)
        .with(cors)
        .with(warp::log::custom(|info| {
            tracing::event!(
                Level::INFO,
                method = %info.method(),
                path = info.path(),
                status = info.status().as_u16(),
                elapsed_ms = info.elapsed().as_millis() as u64,
                "http_request"
            );
        }))
        .recover(handle_rejection)
}

/* ------------------------------ handlers ------------------------------ */

#[instrument(skip(state))]
async fn health_live_handler(state: AppState) -> Result<impl warp::Reply, warp::Rejection> {
    let cache_stats = state.cache_manager.get_stats().await;
    let resp = HealthResponse {
        status: "live".into(),
        service: "unified-market-analysis-engine".into(),
        timestamp: Utc::now(),
        version: "2.0.0".into(),
        cache_stats,
        ready: *state.ready_flag.read().await,
        backend: std::env::var("MARKET_DATA_BACKEND").ok(),
        error: None,
    };
    Ok(warp::reply::json(&resp))
}

#[instrument(skip(state))]
async fn health_ready_handler(state: AppState) -> Result<impl warp::Reply, warp::Rejection> {
    let ready = *state.ready_flag.read().await;
    let cache_stats = state.cache_manager.get_stats().await;
    let backend = std::env::var("MARKET_DATA_BACKEND").unwrap_or_else(|_| "in_memory".to_string());
    
    // Validate provider backend (cheap, deterministic probe)
    let (provider_healthy, error_msg) = validate_provider_health(&state.market, &backend).await;
    
    // Check for required symbols (SPY is critical for regime engine)
    let mut missing_symbols = Vec::new();
    let required_symbols = vec!["SPY"]; // Add more as needed: "BTC", "DXY", etc.
    
    for symbol in &required_symbols {
        if state.market.latest_quote(symbol).await.is_err() {
            missing_symbols.push(symbol.to_string());
        }
    }
    
    let is_ready = ready && provider_healthy && missing_symbols.is_empty();
    let mut final_error_msg = error_msg;
    
    if !missing_symbols.is_empty() {
        final_error_msg = Some(format!("Missing required symbols: {}. Ingest market data before using regime/alpha/unified endpoints.", missing_symbols.join(", ")));
    }
    
    let resp = HealthResponse {
        status: if is_ready { "ready" } else { "unhealthy" }.into(),
        service: "unified-market-analysis-engine".into(),
        timestamp: Utc::now(),
        version: "2.0.0".into(),
        cache_stats,
        ready: is_ready,
        backend: Some(backend),
        error: final_error_msg,
    };
    let reply = warp::reply::json(&resp);
    let code = if is_ready { StatusCode::OK } else { StatusCode::SERVICE_UNAVAILABLE };
    Ok(warp::reply::with_status(reply, code))
}

/// Validate provider backend health (cheap, deterministic probe)
/// Returns (is_healthy, error_message)
#[tracing::instrument(skip(provider))]
async fn validate_provider_health(provider: &Arc<dyn MarketDataProvider>, backend: &str) -> (bool, Option<String>) {
    // Use a test symbol that likely doesn't exist (we just want to check connectivity)
    match provider.latest_quote("__HEALTH_CHECK__").await {
        Ok(_) => (true, None), // Provider is working
        Err(ProviderError::NotFound(_)) => (true, None), // Provider is working, just symbol not found
        Err(ProviderError::Backend(e)) => (false, Some(format!("{} backend error: {}", backend, e))),
        Err(ProviderError::Invalid(e)) => (false, Some(format!("{} invalid request: {}", backend, e))),
        Err(e) => (false, Some(format!("{} error: {}", backend, e))),
    }
}

#[instrument(skip(state, body, headers), fields(req_id=%request_id(&headers)))]
async fn analyze_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    mut body: CryptoAnalysisRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    // Auth (optional)
    if let Some(ref token) = state.api_token {
        let provided = bearer_from_headers(&headers);
        if provided.as_deref() != Some(token.as_str()) {
            return Ok(warp::reply::with_status(
                warp::reply::json(&json_error("unauthorized", "Missing or invalid bearer token")),
                StatusCode::UNAUTHORIZED,
            ));
        }
    }

    // Validate
    body.symbol = body.symbol.trim().to_uppercase();
    if !validate_symbol(&body.symbol) {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("bad_request", "Invalid symbol")),
            StatusCode::BAD_REQUEST,
        ));
    }

    let start = std::time::Instant::now();

    // Determine if symbol is crypto or stock and route accordingly
    let is_crypto = is_crypto_symbol(&body.symbol);
    let asset_type = if is_crypto { "crypto" } else { "stock" };
    
    // Cache check (include asset type in cache key)
    let cache_key = format!("{}::{}::{}", asset_type, body.symbol, body.timeframe.as_deref().unwrap_or("ALL"));
    if let Some(cached) = state.cache_manager.get_prediction(&cache_key).await {
        tracing::info!(%req_id, symbol=%body.symbol, asset_type=%asset_type, "prediction cache hit");
        return Ok(warp::reply::with_status(warp::reply::json(&cached), StatusCode::OK));
    }

    // Route to appropriate engine
    let analysis = if is_crypto {
        tracing::info!(%req_id, symbol=%body.symbol, "routing to crypto engine");
        state.crypto_engine
            .analyze(&body.symbol)
            .await
            .map_err(|e| warp::reject::custom(AnalysisError(e)))?
    } else {
        tracing::info!(%req_id, symbol=%body.symbol, "routing to stock engine");
        state.stock_engine
            .analyze(&body.symbol)
            .await
            .map_err(|e| warp::reject::custom(AnalysisError(e)))?
    };

    state.cache_manager.store_prediction(&cache_key, &analysis).await;

    // Broadcast via WebSocket
    let _ = state.websocket_manager.broadcast_prediction(analysis.clone()).await;

    tracing::info!(%req_id, symbol=%body.symbol, ms = start.elapsed().as_millis() as u64, "analysis_ok");

    Ok(warp::reply::with_status(warp::reply::json(&analysis), StatusCode::OK))
}

#[instrument(skip(state, query, headers), fields(req_id=%request_id(&headers)))]
async fn recommendations_handler(
    (ip, _req_id, headers): (String, String, HeaderMap),
    query: HashMap<String, String>,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    // Auth
    if let Some(ref token) = state.api_token {
        let provided = bearer_from_headers(&headers);
        if provided.as_deref() != Some(token.as_str()) {
            return Ok(warp::reply::with_status(
                warp::reply::json(&json_error("unauthorized", "Missing or invalid bearer token")),
                StatusCode::UNAUTHORIZED,
            ));
        }
    }

    // Query parsing
    let limit = query.get("limit").and_then(|s| s.parse::<usize>().ok()).map(|n| n.min(50)).unwrap_or(10);
    let symbols: Vec<String> = query.get("symbols")
        .map(|s| s.split(',').map(|s| s.trim().to_uppercase()).filter(|s| validate_symbol(s)).collect())
        .unwrap_or_default();

    // Cache first
    if let Some(cached) = state.cache_manager.get_recommendations(&symbols).await {
        tracing::info!("recommendations cache hit {:?}", symbols);
        return Ok(warp::reply::with_status(warp::reply::json(&cached), StatusCode::OK));
    }

    // Compute
    let mut recos = state.crypto_engine
        .get_recommendations(limit, &symbols)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    // Sort by score desc
    recos.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));

    state.cache_manager.store_recommendations(&symbols, &recos).await;

    // Broadcast via WebSocket
    let _ = state.websocket_manager.broadcast_recommendations(recos.clone()).await;

    let envelope = serde_json::json!({
        "items": recos,
        "page_size": limit,
    });

    Ok(warp::reply::with_status(warp::reply::json(&envelope), StatusCode::OK))
}

#[instrument(skip(state, body, headers), fields(req_id=%request_id(&headers)))]
async fn options_analyze_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    mut body: OptionsAnalysisRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    // Validate
    body.symbol = body.symbol.trim().to_uppercase();
    if !validate_symbol(&body.symbol) {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("bad_request", "Invalid symbol")),
            StatusCode::BAD_REQUEST,
        ));
    }

    let start = std::time::Instant::now();

    // Analyze options
    let analysis = state.options_engine
        .analyze(&body.symbol)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    // Broadcast via WebSocket
    let _ = state.websocket_manager.broadcast_options_update(
        body.symbol.clone(),
        analysis.clone()
    ).await;

    tracing::info!(%req_id, symbol=%body.symbol, ms = start.elapsed().as_millis() as u64, "options_analysis_ok");

    Ok(warp::reply::with_status(warp::reply::json(&analysis), StatusCode::OK))
}

#[instrument(skip(state, body, headers), fields(req_id=%request_id(&headers)))]
async fn edge_predict_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    mut body: EdgePredictionRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    // Validate
    body.symbol = body.symbol.trim().to_uppercase();
    if !validate_symbol(&body.symbol) {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("bad_request", "Invalid symbol")),
            StatusCode::BAD_REQUEST,
        ));
    }

    let start = std::time::Instant::now();

    // Generate mock chain (in production, fetch from real_options_service)
    let chain = state.options_engine
        .generate_mock_chain(&body.symbol)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    // Predict edges for all contracts
    let predictions = state.options_engine
        .predict_chain_edges(&body.symbol, &chain)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        symbol=%body.symbol,
        predictions=%predictions.len(),
        ms = start.elapsed().as_millis() as u64,
        "edge_prediction_ok"
    );

    Ok(warp::reply::with_status(warp::reply::json(&predictions), StatusCode::OK))
}

#[instrument(skip(state, body, headers), fields(req_id=%request_id(&headers)))]
async fn one_tap_trades_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    mut body: OneTapTradeRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    // Validate
    body.symbol = body.symbol.trim().to_uppercase();
    if !validate_symbol(&body.symbol) {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("bad_request", "Invalid symbol")),
            StatusCode::BAD_REQUEST,
        ));
    }

    let account_size = body.account_size.unwrap_or(10000.0);
    let risk_tolerance = body.risk_tolerance.unwrap_or(0.1).max(0.01).min(1.0);

    let start = std::time::Instant::now();

    // Generate one-tap trades
    let trades = state.options_engine
        .generate_one_tap_trades(&body.symbol, account_size, risk_tolerance)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        symbol=%body.symbol,
        trades=%trades.len(),
        ms = start.elapsed().as_millis() as u64,
        "one_tap_trades_ok"
    );

    Ok(warp::reply::with_status(warp::reply::json(&trades), StatusCode::OK))
}

#[instrument(skip(state, body, headers), fields(req_id=%request_id(&headers)))]
async fn iv_forecast_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    mut body: IVForecastRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    // Validate
    body.symbol = body.symbol.trim().to_uppercase();
    if !validate_symbol(&body.symbol) {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("bad_request", "Invalid symbol")),
            StatusCode::BAD_REQUEST,
        ));
    }

    let start = std::time::Instant::now();

    // Forecast IV surface
    let forecast = state.options_engine
        .forecast_iv_surface(&body.symbol)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        symbol=%body.symbol,
        heatmap_points=%forecast.iv_change_heatmap.len(),
        ms = start.elapsed().as_millis() as u64,
        "iv_forecast_ok"
    );

    Ok(warp::reply::with_status(warp::reply::json(&forecast), StatusCode::OK))
}

/// Start periodic forex price updates to simulate real-time market data
async fn start_forex_price_updates(state: AppState) {
    use rust_decimal::prelude::*;
    use rand::Rng;
    
    let mut update_interval = tokio_interval(TokioDuration::from_secs(5)); // Update every 5 seconds
    let forex_pairs = vec![
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
        "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURCHF", "GBPCHF",
        "USDCNH", "USDMXN", "USDZAR", "USDBRL", "USDTRY", "USDINR",
        "USDSGD", "USDHKD", "USDNOK", "USDSEK",
    ];
    
    tracing::info!("Starting real-time forex price updates for {} pairs", forex_pairs.len());
    
    loop {
        update_interval.tick().await;
        
        for pair in &forex_pairs {
            // Simulate small price movements
            // Generate random variation BEFORE await (to avoid Send issues)
            let variation = {
                let mut rng = rand::thread_rng();
                (rng.gen_range(0.0..1.0) - 0.5) * 0.0002
            };
            
            if let Ok(quote) = state.market.latest_quote(pair).await {
                let mid = quote.mid();
                let spread = quote.ask - quote.bid;
                let variation_decimal = Decimal::from_f64_retain(variation).unwrap_or_default();
                let new_mid = mid * (Decimal::ONE + variation_decimal);
                
                let spread_half = spread / Decimal::from(2);
                let new_bid = new_mid - spread_half;
                let new_ask = new_mid + spread_half;
                
                // Update in-memory provider
                let new_quote = crate::market_data::provider::Quote {
                    symbol: quote.symbol.clone(),
                    ts: Utc::now(),
                    bid: new_bid,
                    ask: new_ask,
                };
                
                // Ingest the new quote
                if let Ok(()) = state.ingest.ingest_quote(new_quote.clone()).await {
                    // Re-analyze and broadcast
                    if let Ok(analysis) = state.forex_engine.analyze(pair).await {
                        let _ = state.websocket_manager.broadcast_forex_update(
                            pair.to_string(),
                            analysis
                        ).await;
                    }
                }
            }
        }
    }
}

#[instrument(skip(state, body, headers), fields(req_id=%request_id(&headers)))]
async fn forex_analyze_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    mut body: ForexAnalysisRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    // Validate
    body.pair = body.pair.trim().to_uppercase();
    if !is_forex_pair(&body.pair) {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("bad_request", "Invalid forex pair")),
            StatusCode::BAD_REQUEST,
        ));
    }

    let start = std::time::Instant::now();

    // Analyze forex
    let analysis = state.forex_engine
        .analyze(&body.pair)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    // Broadcast via WebSocket
    let _ = state.websocket_manager.broadcast_forex_update(
        body.pair.clone(),
        analysis.clone()
    ).await;

    tracing::info!(%req_id, pair=%body.pair, ms = start.elapsed().as_millis() as u64, "forex_analysis_ok");

    Ok(warp::reply::with_status(warp::reply::json(&analysis), StatusCode::OK))
}

#[instrument(skip(state, body, headers), fields(req_id=%request_id(&headers)))]
async fn sentiment_analyze_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    mut body: SentimentAnalysisRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    // Validate
    body.symbol = body.symbol.trim().to_uppercase();
    if !validate_symbol(&body.symbol) {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("bad_request", "Invalid symbol")),
            StatusCode::BAD_REQUEST,
        ));
    }

    let start = std::time::Instant::now();

    // Analyze sentiment
    let analysis = state.sentiment_engine
        .analyze(&body.symbol)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    // Broadcast via WebSocket
    let _ = state.websocket_manager.broadcast_sentiment_update(
        body.symbol.clone(),
        analysis.clone()
    ).await;

    tracing::info!(%req_id, symbol=%body.symbol, ms = start.elapsed().as_millis() as u64, "sentiment_analysis_ok");

    Ok(warp::reply::with_status(warp::reply::json(&analysis), StatusCode::OK))
}

#[instrument(skip(state, body, headers), fields(req_id=%request_id(&headers)))]
async fn correlation_analyze_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    mut body: CorrelationAnalysisRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    // Validate
    body.primary = body.primary.trim().to_uppercase();
    if let Some(ref mut sec) = body.secondary {
        *sec = sec.trim().to_uppercase();
        if !validate_symbol(sec) {
            return Ok(warp::reply::with_status(
                warp::reply::json(&json_error("bad_request", "Invalid secondary symbol")),
                StatusCode::BAD_REQUEST,
            ));
        }
    }
    
    if !validate_symbol(&body.primary) {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("bad_request", "Invalid primary symbol")),
            StatusCode::BAD_REQUEST,
        ));
    }

    let start = std::time::Instant::now();

    // Analyze correlation
    let analysis = state.correlation_engine
        .analyze(&body.primary, body.secondary.as_deref())
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    // Broadcast via WebSocket
    let _ = state.websocket_manager.broadcast_correlation_update(
        body.primary.clone(),
        analysis.secondary_symbol.clone(),
        analysis.clone()
    ).await;

    tracing::info!(%req_id, primary=%body.primary, ms = start.elapsed().as_millis() as u64, "correlation_analysis_ok");

    Ok(warp::reply::with_status(warp::reply::json(&analysis), StatusCode::OK))
}

#[instrument(skip(state, headers))]
async fn ingest_price_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: IngestPriceRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let start = std::time::Instant::now();
    
    // Parse timestamp (ISO 8601 or RFC3339)
    let timestamp = match DateTime::parse_from_rfc3339(&body.timestamp) {
        Ok(dt) => dt.with_timezone(&Utc),
        Err(_) => {
            // Try ISO 8601 format
            match DateTime::parse_from_str(&body.timestamp, "%+") {
                Ok(dt) => dt.with_timezone(&Utc),
                Err(_) => Utc::now(),
            }
        }
    };
    
    // Parse price as Decimal
    let price = match Decimal::from_str(&body.price) {
        Ok(p) => p,
        Err(_) => {
            return Ok(warp::reply::with_status(
                warp::reply::json(&json_error("invalid_price", "Invalid price format")),
                StatusCode::BAD_REQUEST,
            ));
        }
    };
    
    // Validate symbol
    let symbol = body.symbol.trim().to_uppercase();
    if !validate_symbol(&symbol) {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("bad_request", "Invalid symbol")),
            StatusCode::BAD_REQUEST,
        ));
    }
    
    // Ingest price into correlation engine (legacy)
    state.correlation_engine.ingest_price(&symbol, timestamp, price).await;
    
    // Also ingest into shared provider for forex/regime engines (new architecture)
    use crate::market_data::Quote;
    use std::sync::Arc as StdArc;
    let quote = Quote {
        symbol: StdArc::from(symbol.as_str()),
        ts: timestamp,
        bid: price,
        ask: price,
    };
    if let Err(e) = state.ingest.ingest_quote(quote).await {
        tracing::warn!(%req_id, error=%e, "failed to ingest quote into provider");
    }
    
    tracing::info!(
        %req_id,
        symbol=%symbol,
        price=%body.price,
        ms = start.elapsed().as_millis() as u64,
        "price_ingested"
    );
    
    Ok(warp::reply::with_status(
        warp::reply::json(&serde_json::json!({
            "success": true,
            "symbol": symbol,
            "timestamp": timestamp.to_rfc3339(),
        })),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn regime_analyze_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let start = std::time::Instant::now();
    
    tracing::info!(endpoint = "v1/regime", %req_id, "starting regime analysis");

    // Analyze regime (quant edition)
    let analysis = state.regime_engine
        .analyze()
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        regime=?analysis.regime,
        confidence=%analysis.confidence,
        ms = start.elapsed().as_millis() as u64,
        "regime_analysis_ok"
    );

    Ok(warp::reply::with_status(warp::reply::json(&analysis), StatusCode::OK))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn regime_simple_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let start = std::time::Instant::now();

    // Analyze regime (Jobs edition - human-readable)
    let analysis = state.regime_engine
        .analyze_simple()
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        headline=%analysis.headline,
        mood=%analysis.mood,
        ms = start.elapsed().as_millis() as u64,
        "regime_simple_ok"
    );

    Ok(warp::reply::with_status(warp::reply::json(&analysis), StatusCode::OK))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn alpha_signal_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: AlphaSignalRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    // Rate limit
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    if !validate_symbol(&body.symbol) {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("bad_request", "Invalid symbol")),
            StatusCode::BAD_REQUEST,
        ));
    }

    let start = std::time::Instant::now();
    
    tracing::info!(endpoint = "v1/alpha/signal", %req_id, symbol = %body.symbol, "starting alpha signal generation");

    // Generate alpha signal
    let alpha = state.alpha_oracle
        .generate_signal(&body.symbol, &body.features)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    // If equity and entry_price provided, also compute position sizing
    let mut response: serde_json::Value = serde_json::to_value(&alpha).unwrap();

    if let (Some(equity), Some(entry_price)) = (body.equity, body.entry_price) {
        let sizing = state.position_sizing.size_position(&alpha, equity, entry_price);

        // If open positions provided, run through risk guard
        let guard_decision = if let Some(open_positions) = body.open_positions {
            state.risk_guard.evaluate(equity, &open_positions, &sizing)
        } else {
            RiskGuardDecision {
                allow: sizing.dollar_risk > 0.0,
                adjusted: Some(sizing.clone()),
                reason: "No open positions provided".to_string(),
            }
        };

        response["position_sizing"] = serde_json::to_value(&sizing).unwrap();
        response["risk_guard"] = serde_json::to_value(&guard_decision).unwrap();
    }

    tracing::info!(
        %req_id,
        symbol=%body.symbol,
        alpha_score=alpha.alpha_score,
        conviction=%alpha.conviction,
        ms = start.elapsed().as_millis() as u64,
        "alpha_signal_ok"
    );

    Ok(warp::reply::with_status(
        warp::reply::json(&response),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers))]
async fn websocket_handler(
    ws: warp::ws::Ws,
    (_ip, _req_id, headers): (String, String, HeaderMap),
    state: AppState,
) -> Result<Box<dyn warp::Reply>, warp::Rejection> {
    // Auth for WS
    let token_ok = if let Some(ref token) = state.api_token {
        let bearer = bearer_from_headers(&headers);
        bearer.as_deref() == Some(token.as_str())
    } else { true };

    if !token_ok {
        return Ok(Box::new(warp::reply::with_status(
            warp::reply::json(&json_error("unauthorized", "Missing or invalid token")),
            StatusCode::UNAUTHORIZED,
        )));
    }

    let mgr = Arc::clone(&state.websocket_manager);
    Ok(Box::new(ws.on_upgrade(move |socket| async move {
        mgr.handle_connection(socket).await;
    })))
}

/* -------------------------- Phase 1 handlers -------------------------- */

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn portfolio_record_trade_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: RecordTradeRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let trade = TradeRecord {
        user_id: body.user_id.clone(),
        symbol: body.symbol.clone(),
        strategy_type: body.strategy_type.clone(),
        entry_price: body.entry_price,
        exit_price: None,
        pnl: None,
        pnl_pct: None,
        entry_iv: body.entry_iv,
        days_to_expiration: body.days_to_expiration,
        position_size: body.position_size,
        risk_fraction: body.risk_fraction,
        timestamp: Utc::now(),
        exit_timestamp: None,
        outcome: None,
    };

    state.portfolio_memory.record_trade(trade).await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(%req_id, user_id=%body.user_id, symbol=%body.symbol, "trade_recorded");

    Ok(warp::reply::with_status(
        warp::reply::json(&serde_json::json!({
            "success": true,
            "message": "Trade recorded"
        })),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn portfolio_record_exit_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: RecordExitRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let outcome = match body.outcome.as_str() {
        "Win" => TradeOutcome::Win,
        "Loss" => TradeOutcome::Loss,
        "Breakeven" => TradeOutcome::Breakeven,
        _ => TradeOutcome::Breakeven,
    };

    state.portfolio_memory.record_exit(&body.user_id, body.trade_id, body.exit_price, outcome).await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(%req_id, user_id=%body.user_id, "trade_exit_recorded");

    Ok(warp::reply::with_status(
        warp::reply::json(&serde_json::json!({
            "success": true,
            "message": "Trade exit recorded"
        })),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn portfolio_profile_handler(
    user_id: String,
    (ip, req_id, headers): (String, String, HeaderMap),
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let profile = state.portfolio_memory.get_profile(&user_id).await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    Ok(warp::reply::with_status(
        warp::reply::json(&profile),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn portfolio_recommendation_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: GetRecommendationRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let recommendation = state.portfolio_memory.get_recommendation(
        &body.user_id,
        &body.symbol,
        &body.proposed_strategy,
        body.proposed_size,
        body.account_equity,
        body.current_iv,
        body.dte,
    ).await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    Ok(warp::reply::with_status(
        warp::reply::json(&recommendation),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn execution_submit_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: SubmitOrderRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let order_request = OrderRequest {
        user_id: body.user_id,
        trade: body.trade,
        account_equity: body.account_equity,
        idempotency_key: body.idempotency_key,
    };

    let receipt = state.execution_engine.submit_order(order_request).await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(%req_id, order_id=%receipt.order_id, "order_submitted");

    Ok(warp::reply::with_status(
        warp::reply::json(&receipt),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn execution_status_handler(
    order_id: String,
    (ip, req_id, headers): (String, String, HeaderMap),
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let receipt = state.execution_engine.get_order_status(&order_id).await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    match receipt {
        Some(r) => Ok(warp::reply::with_status(
            warp::reply::json(&r),
            StatusCode::OK,
        )),
        None => Ok(warp::reply::with_status(
            warp::reply::json(&json_error("not_found", "Order not found")),
            StatusCode::NOT_FOUND,
        )),
    }
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn safety_check_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: SafetyCheckRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let check = state.safety_guardrails.check_trade(
        &body.user_id,
        &body.trade,
        body.account_equity,
        body.current_iv,
        body.open_positions_risk,
    ).await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        user_id=%body.user_id,
        symbol=%body.trade.symbol,
        passed=%check.passed,
        confidence=%check.confidence,
        "safety_check_completed"
    );

    Ok(warp::reply::with_status(
        warp::reply::json(&check),
        StatusCode::OK,
    ))
}

/* -------------------------- Phase 2 handlers -------------------------- */

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn backtest_run_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: RunBacktestRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let config = body.config.unwrap_or_default();
    let result = state.backtesting_engine
        .run_backtest(&body.strategy_name, &body.symbol, body.signals, config)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        strategy=%body.strategy_name,
        symbol=%body.symbol,
        total_return=%result.total_return_pct,
        "backtest_completed"
    );

    Ok(warp::reply::with_status(
        warp::reply::json(&result),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn backtest_score_handler(
    strategy_name: String,
    symbol: String,
    (ip, req_id, headers): (String, String, HeaderMap),
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let score = state.backtesting_engine
        .get_strategy_score(&strategy_name, &symbol)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    match score {
        Some(s) => Ok(warp::reply::with_status(
            warp::reply::json(&s),
            StatusCode::OK,
        )),
        None => Ok(warp::reply::with_status(
            warp::reply::json(&json_error("not_found", "No backtest results found")),
            StatusCode::NOT_FOUND,
        )),
    }
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn cross_asset_signal_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: CrossAssetRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let signal = state.cross_asset_fusion
        .generate_fusion_signal(&body.primary_asset)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        primary_asset=%body.primary_asset,
        regime=%signal.regime.mood,
        "cross_asset_signal_generated"
    );

    Ok(warp::reply::with_status(
        warp::reply::json(&signal),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn rl_recommend_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: RLRecommendRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let recommendation = state.rl_engine
        .recommend_strategies(&body.user_id, body.context, body.available_strategies)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        user_id=%body.user_id,
        strategies=%recommendation.recommended_strategies.len(),
        "rl_recommendation_generated"
    );

    Ok(warp::reply::with_status(
        warp::reply::json(&recommendation),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn rl_update_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: RLUpdateRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let reward = body.reward.clone();
    let user_id = reward.user_id();
    let reward_value = reward.reward;
    let strategy_name = reward.action.strategy_name.clone();

    state.rl_engine
        .update_policy(reward)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        user_id=%user_id,
        reward=%reward_value,
        strategy=%strategy_name,
        "rl_policy_updated"
    );
    Ok(warp::reply::with_status(
        warp::reply::json(&serde_json::json!({
            "success": true,
            "message": "Policy updated"
        })),
        StatusCode::OK,
    ))
}

/* -------------------------- Unified Asset Oracle handler -------------------------- */

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn unified_signal_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: UnifiedSignalRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let start = std::time::Instant::now();
    
    // Rate limiting
    let key = format!("unified:{}", ip);
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&serde_json::json!({
                "error": "Rate limit exceeded",
                "req_id": req_id,
            })),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    tracing::info!(endpoint = "v1/unified/signal", %req_id, symbol = %body.symbol, "starting unified signal generation");
    
    match state.unified_oracle.signal(body).await {
        Ok(signal) => {
            tracing::info!(
                "Unified signal generated for {} in {:?}",
                signal.symbol,
                start.elapsed()
            );
            Ok(warp::reply::with_status(
                warp::reply::json(&signal),
                StatusCode::OK,
            ))
        }
        Err(e) => {
            tracing::error!("Unified signal error: {:?}", e);
            Ok(warp::reply::with_status(
                warp::reply::json(&serde_json::json!({
                    "error": format!("{}", e),
                    "req_id": req_id,
                })),
                StatusCode::INTERNAL_SERVER_ERROR,
            ))
        }
    }
}

/* -------------------------- Phase 3: Quant Terminal handlers -------------------------- */

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn vol_surface_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: VolSurfaceRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let heatmap = state.quant_terminal
        .generate_vol_surface_heatmap(&body.symbol)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        symbol=%body.symbol,
        strikes=%heatmap.strikes.len(),
        expirations=%heatmap.expirations.len(),
        "vol_surface_generated"
    );

    Ok(warp::reply::with_status(
        warp::reply::json(&heatmap),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn edge_decay_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: EdgeDecayRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let curve = state.quant_terminal
        .calculate_edge_decay(&body.strategy_name, &body.symbol)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        strategy=%body.strategy_name,
        symbol=%body.symbol,
        decay_rate=%curve.decay_rate,
        "edge_decay_calculated"
    );

    Ok(warp::reply::with_status(
        warp::reply::json(&curve),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn regime_timeline_handler(
    (ip, req_id, headers): (String, String, HeaderMap),
    body: RegimeTimelineRequest,
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let start_date = chrono::NaiveDate::parse_from_str(&body.start_date, "%Y-%m-%d")
        .map_err(|e| warp::reject::custom(AnalysisError(anyhow::anyhow!("Invalid start_date: {}", e))))?;
    let end_date = chrono::NaiveDate::parse_from_str(&body.end_date, "%Y-%m-%d")
        .map_err(|e| warp::reject::custom(AnalysisError(anyhow::anyhow!("Invalid end_date: {}", e))))?;

    let timeline = state.quant_terminal
        .generate_regime_timeline(start_date, end_date)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        start_date=%body.start_date,
        end_date=%body.end_date,
        events=%timeline.events.len(),
        "regime_timeline_generated"
    );

    Ok(warp::reply::with_status(
        warp::reply::json(&timeline),
        StatusCode::OK,
    ))
}

#[instrument(skip(state, headers), fields(req_id=%request_id(&headers)))]
async fn portfolio_dna_handler(
    user_id: String,
    (ip, req_id, headers): (String, String, HeaderMap),
    state: AppState,
) -> Result<impl warp::Reply, warp::Rejection> {
    let key = bearer_from_headers(&headers).unwrap_or_else(|| ip.clone());
    if state.limiter.check_key(&key).is_err() {
        return Ok(warp::reply::with_status(
            warp::reply::json(&json_error("rate_limited", "Too many requests")),
            StatusCode::TOO_MANY_REQUESTS,
        ));
    }

    let dna = state.quant_terminal
        .generate_portfolio_dna(&user_id)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    tracing::info!(
        %req_id,
        user_id=%user_id,
        archetype=%dna.archetype,
        "portfolio_dna_generated"
    );

    Ok(warp::reply::with_status(
        warp::reply::json(&dna),
        StatusCode::OK,
    ))
}

/* -------------------------- middleware/errors -------------------------- */

#[derive(Debug, Serialize)]
struct JsonError { code: &'static str, message: &'static str }
fn json_error(code: &'static str, message: &'static str) -> JsonError { JsonError { code, message } }

async fn handle_rejection(err: warp::Rejection) -> Result<impl warp::Reply, warp::Rejection> {
    if err.is_not_found() {
        let reply = warp::reply::json(&json_error("not_found", "Route not found"));
        return Ok(warp::reply::with_status(reply, StatusCode::NOT_FOUND));
    }
    if let Some(e) = err.find::<AnalysisError>() {
        let error_msg = format!("{:#}", e.0);
        error!("analysis error: {}", error_msg);
        
        // Check if it's a missing data error (SPY, BTC, DXY, etc.)
        let (status_code, error_type, hint) = if error_msg.contains("no SPY data") || 
                                                   error_msg.contains("missing") ||
                                                   error_msg.contains("not found") {
            (
                StatusCode::FAILED_DEPENDENCY,
                "missing_market_data",
                "Ingest SPY quotes (and required benchmarks) before calling regime/alpha/unified endpoints."
            )
        } else {
            (
                StatusCode::UNPROCESSABLE_ENTITY,
                "analysis_failed",
                "Unable to complete analysis"
            )
        };
        
        let reply = warp::reply::json(&serde_json::json!({
            "error": error_type,
            "message": error_msg,
            "hint": hint
        }));
        return Ok(warp::reply::with_status(reply, status_code));
    }
    if let Some(_) = err.find::<warp::filters::body::BodyDeserializeError>() {
        let reply = warp::reply::json(&json_error("bad_request", "Invalid JSON body"));
        return Ok(warp::reply::with_status(reply, StatusCode::BAD_REQUEST));
    }
    if let Some(_) = err.find::<warp::reject::InvalidHeader>() {
        let reply = warp::reply::json(&json_error("bad_request", "Invalid header"));
        return Ok(warp::reply::with_status(reply, StatusCode::BAD_REQUEST));
    }
    // fallback
    error!("unhandled rejection: {:?}", err);
    let reply = warp::reply::json(&json_error("internal_error", "Something went wrong"));
    Ok(warp::reply::with_status(reply, StatusCode::INTERNAL_SERVER_ERROR))
}

/* ---------------------------- metrics ---------------------------- */

#[instrument(skip(state))]
async fn metrics_handler(state: AppState) -> Result<impl warp::Reply, warp::Rejection> {
    let prometheus_text = state.metrics.format_prometheus();
    Ok(warp::reply::with_header(
        prometheus_text,
        "content-type",
        "text/plain; version=0.0.4",
    ))
}
