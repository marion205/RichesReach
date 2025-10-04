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
mod ml_models;
mod cache;
mod websocket;

use cache::CacheManager;
use crypto_analysis::CryptoAnalysisEngine;
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
    pub analysis_engine: Arc<CryptoAnalysisEngine>,
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
    let analysis_engine = Arc::new(CryptoAnalysisEngine::new());
    let cache_manager = Arc::new(CacheManager::new());
    let websocket_manager = Arc::new(WebSocketManager::new());

    // ---- rate limiter (100 req / 10s per key)
    let quota = Quota::with_period(Duration::from_secs(10)).unwrap().allow_burst(nonzero!(100u32));
    let limiter = Arc::new(RateLimiter::keyed(quota));

    // ---- config
    let api_token = std::env::var("API_TOKEN").ok();
    let ready_flag = Arc::new(RwLock::new(false));

    let state = AppState {
        analysis_engine,
        cache_manager,
        websocket_manager,
        limiter,
        api_token,
        ready_flag: ready_flag.clone(),
    };

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

    // Parse port from command line args
    let port = std::env::args()
        .nth(1)
        .and_then(|arg| arg.parse::<u16>().ok())
        .unwrap_or(3002);
    
    let addr: SocketAddr = ([0, 0, 0, 0], port).into();
    info!("🚀 Crypto Analysis Engine on http://{addr}");
    info!("📊 Health (live):  GET /health/live");
    info!("📊 Health (ready): GET /health/ready");
    info!("🔍 Analyze:        POST /v1/analyze");
    info!("💡 Recos:          GET  /v1/recommendations");
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
        service: "crypto-analysis-engine".into(),
        timestamp: Utc::now(),
        version: "1.1.0".into(),
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
        service: "crypto-analysis-engine".into(),
        timestamp: Utc::now(),
        version: "1.1.0".into(),
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

    // Cache check
    let cache_key = format!("{}::{}", body.symbol, body.timeframe.as_deref().unwrap_or("ALL"));
    if let Some(cached) = state.cache_manager.get_prediction(&cache_key).await {
        tracing::info!(%req_id, symbol=%body.symbol, "prediction cache hit");
        return Ok(warp::reply::with_status(warp::reply::json(&cached), StatusCode::OK));
    }

    // Analysis
    let analysis = state.analysis_engine
        .analyze(&body.symbol)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    state.cache_manager.store_prediction(&cache_key, &analysis).await;

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
    let mut recos = state.analysis_engine
        .get_recommendations(limit, &symbols)
        .await
        .map_err(|e| warp::reject::custom(AnalysisError(e)))?;

    // Sort by score desc
    recos.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));

    state.cache_manager.store_recommendations(&symbols, &recos).await;

    let envelope = serde_json::json!({
        "items": recos,
        "page_size": limit,
    });

    Ok(warp::reply::with_status(warp::reply::json(&envelope), StatusCode::OK))
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