use anyhow::Result;
use chrono::{DateTime, Utc};
use governor::{clock::DefaultClock, state::keyed::DefaultKeyedStateStore, Quota, RateLimiter};
use governor::middleware::NoOpMiddleware;
use nonzero_ext::nonzero;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, net::SocketAddr, sync::Arc, time::Duration};
use tokio::sync::RwLock;
use tracing::{error, info, instrument, Level};
use tracing_subscriber::{fmt, EnvFilter};
use uuid::Uuid;
use warp::{Filter, http::{HeaderMap, StatusCode}};

mod crypto_analysis;
mod stock_analysis;
mod options_analysis;
mod forex_analysis;
mod sentiment_analysis;
mod correlation_analysis;
mod ml_models;
mod cache;
mod websocket;

use cache::CacheManager;
use crypto_analysis::CryptoAnalysisEngine;
use stock_analysis::StockAnalysisEngine;
use options_analysis::{OptionsAnalysisEngine, OptionsAnalysisResponse};
use forex_analysis::{ForexAnalysisEngine, ForexAnalysisResponse};
use sentiment_analysis::{SentimentAnalysisEngine, SentimentAnalysisResponse};
use correlation_analysis::{CorrelationAnalysisEngine, CorrelationAnalysisResponse};
use websocket::WebSocketManager;

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
    pub options_engine: Arc<OptionsAnalysisEngine>,
    pub forex_engine: Arc<ForexAnalysisEngine>,
    pub sentiment_engine: Arc<SentimentAnalysisEngine>,
    pub correlation_engine: Arc<CorrelationAnalysisEngine>,
    pub cache_manager: Arc<CacheManager>,
    pub websocket_manager: Arc<WebSocketManager>,
    pub limiter: Arc<RateLimiter<String, DefaultKeyedStateStore<String>, DefaultClock, NoOpMiddleware>>,
    pub api_token: Option<String>,
    pub ready_flag: Arc<RwLock<bool>>,
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
    let filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new("info,warp=info"));
    fmt()
        .with_env_filter(filter)
        .with_target(false)
        .with_level(true)
        .json()
        .init();

    // ---- components
    let crypto_engine = Arc::new(CryptoAnalysisEngine::new());
    let stock_engine = Arc::new(StockAnalysisEngine::new());
    let options_engine = Arc::new(OptionsAnalysisEngine::new());
    let forex_engine = Arc::new(ForexAnalysisEngine::new());
    let sentiment_engine = Arc::new(SentimentAnalysisEngine::new());
    let correlation_engine = Arc::new(CorrelationAnalysisEngine::new());
    let cache_manager = Arc::new(CacheManager::new());
    let websocket_manager = Arc::new(WebSocketManager::new());

    // ---- rate limiter (100 req / 10s per key)
    let quota = Quota::with_period(Duration::from_secs(10)).unwrap().allow_burst(nonzero!(100u32));
    let limiter = Arc::new(RateLimiter::keyed(quota));

    // ---- config
    let api_token = std::env::var("API_TOKEN").ok();
    let ready_flag = Arc::new(RwLock::new(false));

    let state = AppState {
        crypto_engine,
        stock_engine,
        options_engine,
        forex_engine,
        sentiment_engine,
        correlation_engine,
        cache_manager,
        websocket_manager,
        limiter,
        api_token,
        ready_flag: ready_flag.clone(),
    };

    // Start WebSocket heartbeat
    state.websocket_manager.start_heartbeat().await;

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
    info!("💱 Forex:          POST /v1/forex/analyze");
    info!("📰 Sentiment:      POST /v1/sentiment/analyze");
    info!("🔗 Correlation:    POST /v1/correlation/analyze");
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
    let metrics = warp::path("metrics")
        .and(warp::get())
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

    let websocket = v1
        .and(warp::path("ws"))
        .and(warp::ws())
        .and(with_req_meta.clone())
        .and(with_state.clone())
        .and_then(websocket_handler);

    // Compose + middlewares
    health_live
        .or(health_ready)
        .or(metrics)
        .or(analyze)
        .or(recommendations)
        .or(options_analyze)
        .or(forex_analyze)
        .or(sentiment_analyze)
        .or(correlation_analyze)
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
    };
    Ok(warp::reply::json(&resp))
}

#[instrument(skip(state))]
async fn health_ready_handler(state: AppState) -> Result<impl warp::Reply, warp::Rejection> {
    let ready = *state.ready_flag.read().await;
    let cache_stats = state.cache_manager.get_stats().await;
    let resp = HealthResponse {
        status: if ready { "ready" } else { "starting" }.into(),
        service: "unified-market-analysis-engine".into(),
        timestamp: Utc::now(),
        version: "2.0.0".into(),
        cache_stats,
        ready,
    };
    let reply = warp::reply::json(&resp);
    let code = if ready { StatusCode::OK } else { StatusCode::SERVICE_UNAVAILABLE };
    Ok(warp::reply::with_status(reply, code))
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
        error!("analysis error: {:#}", e.0);
        let reply = warp::reply::json(&json_error("analysis_failed", "Unable to complete analysis"));
        return Ok(warp::reply::with_status(reply, StatusCode::BAD_REQUEST));
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

async fn metrics_handler() -> Result<impl warp::Reply, warp::Rejection> {
    Ok(warp::reply::with_header(
        "# HELP app_up 1 if up\n# TYPE app_up gauge\napp_up 1\n",
        "content-type",
        "text/plain; version=0.0.4",
    ))
}
