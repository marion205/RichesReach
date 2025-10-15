use std::{convert::Infallible, sync::Arc, time::Duration};
use warp::{Filter, hyper::StatusCode};
use serde::{Deserialize, Serialize};
use tracing::{info, error};
use tracing_subscriber::{fmt, EnvFilter};
use governor::{Quota, RateLimiter, state::InMemoryState, clock::DefaultClock};
use governor::middleware::NoOpMiddleware;
use uuid::Uuid;

mod crypto_analysis;
mod cache;
mod websocket;
mod ml_models;

use crypto_analysis::CryptoAnalysisEngine;
use cache::CacheManager;
use websocket::WebSocketManager;
use ml_models::CryptoMLPredictor;

#[derive(Clone)]
struct AppState {
    analysis_engine: Arc<CryptoAnalysisEngine>,
    cache_manager: Arc<CacheManager>,
    websocket_manager: Arc<WebSocketManager>,
    limiter: Arc<RateLimiter<InMemoryState, DefaultClock, NoOpMiddleware>>,
}

#[derive(Debug, Serialize)]
struct ErrorBody { 
    code: &'static str, 
    message: String, 
    request_id: String 
}

#[tokio::main]
async fn main() {
    // Tracing
    fmt().with_env_filter(EnvFilter::from_default_env().add_directive("warp=info".parse().unwrap()))
        .json()
        .init();

    // Components
    let state = AppState {
        analysis_engine: Arc::new(CryptoAnalysisEngine::new()),
        cache_manager: Arc::new(CacheManager::new()),
        websocket_manager: Arc::new(WebSocketManager::new()),
        limiter: Arc::new(RateLimiter::direct(Quota::per_second(nonzero_ext::nonzero!(25u32)))),
    };
    let state = Arc::new(state);

    // Common filters
    let with_state = warp::any().map(move || state.clone());
    let with_req_id = warp::any().map(|| Uuid::new_v4().to_string());

    // CORS (tight)
    let cors = warp::cors()
        .allow_origin("https://your-app.example") // TODO: configure via env
        .allow_headers(vec!["content-type", "authorization"])
        .allow_methods(vec!["GET", "POST", "OPTIONS"]);

    // Routes
    let health = warp::path("health")
        .and(warp::get())
        .and(with_state.clone())
        .and(with_req_id.clone())
        .and_then(health_handler);

    let analyze = warp::path("analyze")
        .and(warp::post())
        .and(warp::body::json())
        .and(with_state.clone())
        .and(with_req_id.clone())
        .and_then(analyze_handler);

    let recommendations = warp::path("recommendations")
        .and(warp::get())
        .and(warp::query::<std::collections::HashMap<String, String>>())
        .and(with_state.clone())
        .and(with_req_id.clone())
        .and_then(recommendations_handler);

    let ws = warp::path("ws")
        .and(warp::ws())
        .and(with_state.clone())
        .and(with_req_id.clone())
        .map(|ws: warp::ws::Ws, state: Arc<AppState>, req_id: String| {
            ws.on_upgrade(move |socket| async move {
                info!(request_id=%req_id, "websocket connected");
                state.websocket_manager.handle_connection(socket).await;
            })
        });

    // Rate limit & error recovery
    let limited = warp::any()
        .and(with_state.clone())
        .and_then(|state: Arc<AppState>| async move {
            state.limiter.check().map_err(|_| warp::reject::custom(TooManyRequests))
        });

    let routes = limited
        .untuple_one()
        .and(health.or(analyze).or(recommendations).or(ws))
        .with(cors)
        .recover(handle_rejection);

    info!("🚀 crypto-analysis on :3001");
    warp::serve(routes).run(([0, 0, 0, 0], 3001)).await;
}

#[derive(Debug)]
struct TooManyRequests;
impl warp::reject::Reject for TooManyRequests {}

async fn handle_rejection(err: warp::Rejection) -> Result<impl warp::Reply, Infallible> {
    let req_id = Uuid::new_v4().to_string();
    let (code, msg): (StatusCode, &'static str) = if err.find::<TooManyRequests>().is_some() {
        (StatusCode::TOO_MANY_REQUESTS, "rate_limit")
    } else if err.is_not_found() {
        (StatusCode::NOT_FOUND, "not_found")
    } else {
        error!(?err, "unhandled rejection");
        (StatusCode::INTERNAL_SERVER_ERROR, "internal")
    };
    let body = warp::reply::json(&ErrorBody{ code: msg, message: msg.into(), request_id: req_id });
    Ok(warp::reply::with_status(body, code))
}

#[derive(Debug, Deserialize)]
struct AnalyzeReq { 
    symbol: String, 
    timeframe: Option<String> 
}

#[derive(Debug, Serialize)]
struct Health { 
    status: &'static str, 
    service: &'static str, 
    version: &'static str, 
    ts: String, 
    cache_hits: f64 
}

async fn health_handler(state: Arc<AppState>, req_id: String) -> Result<impl warp::Reply, warp::Rejection> {
    let stats = state.cache_manager.get_stats().await;
    let body = Health {
        status: "ok",
        service: "crypto-analysis",
        version: "1.1.0",
        ts: chrono::Utc::now().to_rfc3339(),
        cache_hits: stats.hit_rate,
    };
    Ok(warp::reply::with_status(warp::reply::json(&body), StatusCode::OK))
}

async fn analyze_handler(req: AnalyzeReq, state: Arc<AppState>, req_id: String)
    -> Result<impl warp::Reply, warp::Rejection>
{
    let symbol = req.symbol.to_uppercase();
    let start = std::time::Instant::now();

    // cache first
    if let Some(cached) = state.cache_manager.get_prediction(&symbol).await {
        info!(%req_id, %symbol, ms=?start.elapsed().as_millis(), "cache_hit");
        return Ok(warp::reply::json(&cached));
    }

    // hard timeout to avoid 2-minute stalls
    let fut = state.analysis_engine.analyze(&symbol);
    let res = tokio::time::timeout(Duration::from_millis(900), fut).await;
    let analysis = res.map_err(|_| warp::reject::custom(TooManyRequests)) // reuse for timeout -> 429
        .and_then(|r| r.map_err(|e| warp::reject::custom(InternalErr(e.to_string()))))?;

    state.cache_manager.store_prediction(&symbol, &analysis).await;
    info!(%req_id, %symbol, ms=?start.elapsed().as_millis(), "analysis_ok");
    Ok(warp::reply::json(&analysis))
}

async fn recommendations_handler(
    query: std::collections::HashMap<String, String>, 
    state: Arc<AppState>, 
    req_id: String
) -> Result<impl warp::Reply, warp::Rejection> {
    let limit = query.get("limit")
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(10);
    
    let recommendations = state.analysis_engine.get_recommendations(limit).await
        .map_err(|e| warp::reject::custom(InternalErr(e.to_string())))?;
    
    info!(%req_id, limit, "recommendations_served");
    Ok(warp::reply::json(&recommendations))
}

#[derive(Debug)]
struct InternalErr(String);
impl warp::reject::Reject for InternalErr {}
