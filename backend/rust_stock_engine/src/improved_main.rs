use axum::{
    routing::{get, post},
    Router, extract::State, Json,
};
use std::net::SocketAddr;
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;
use serde::{Deserialize, Serialize};
use std::sync::Arc;

mod stock_analysis;
mod improved_stock_analysis;
mod options_models;
mod options_calculator;
mod options_service;
mod api;
mod models;
mod config;

use improved_stock_analysis::ImprovedStockAnalyzer;
use options_service::OptionsService;
use options_models::{OptionsAnalysisRequest, OptionsAnalysisResponse, OptionsScreeningCriteria};
use config::Config;

#[derive(Clone)]
struct AppState {
    analyzer: Arc<ImprovedStockAnalyzer>,
    options_service: Arc<OptionsService>,
}

#[derive(Deserialize)]
struct AnalyzeRequest {
    symbol: String,
    include_technical: Option<bool>,
    include_fundamental: Option<bool>,
}

#[derive(Deserialize)]
struct RecommendationsRequest {
    user_income: Option<f64>,
    risk_tolerance: Option<String>,
    investment_goals: Option<Vec<String>>,
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    service: String,
    version: String,
    timestamp: String,
    features: Vec<String>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging with better formatting
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .with_target(false)
        .with_thread_ids(true)
        .with_thread_names(true)
        .finish();
    tracing::subscriber::set_global_default(subscriber)?;

    info!("🚀 Starting Improved Stock Analysis Engine...");

    // Load configuration
    let config = Config::load().unwrap_or_else(|_| {
        info!("Using default configuration");
        Config::default()
    });
    info!("📊 Configuration loaded successfully");

    // Initialize the improved analyzer and options service
    let analyzer = Arc::new(ImprovedStockAnalyzer::new(config.clone()));
    let options_service = Arc::new(OptionsService::new(config));
    let app_state = AppState { analyzer, options_service };

    // Create router with improved API endpoints
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/analyze", post(analyze_stock))
        .route("/recommendations", post(get_recommendations))
        .route("/indicators", post(calculate_indicators))
        .route("/batch-analyze", post(batch_analyze))
        // Options analysis endpoints
        .route("/options/analyze", post(analyze_options))
        .route("/options/chain", post(get_options_chain))
        .route("/options/flow", post(get_unusual_flow))
        .route("/options/strategies", post(get_options_strategies))
        .route("/options/screen", post(screen_options))
        .with_state(app_state);

    // Start server
    let addr = SocketAddr::from(([127, 0, 0, 1], 3001));
    info!("🌐 Improved Stock Engine listening on {}", addr);
    info!("📈 Features: Parallel processing, caching, rate limiting, retry logic");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

async fn health_check(State(state): State<AppState>) -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "healthy".to_string(),
        service: "Improved Stock Analysis Engine".to_string(),
        version: "2.0.0".to_string(),
        timestamp: chrono::Utc::now().to_rfc3339(),
        features: vec![
            "Parallel API calls".to_string(),
            "Intelligent caching".to_string(),
            "Rate limiting".to_string(),
            "Retry logic with exponential backoff".to_string(),
            "Async technical indicators".to_string(),
            "Connection pooling".to_string(),
            "Batch processing".to_string(),
            "Options chain analysis".to_string(),
            "Black-Scholes Greeks calculation".to_string(),
            "Unusual options flow detection".to_string(),
            "Options strategies analysis".to_string(),
            "Options screening".to_string(),
        ],
    })
}

async fn analyze_stock(
    State(state): State<AppState>,
    Json(request): Json<AnalyzeRequest>,
) -> Result<Json<models::StockAnalysis>, String> {
    info!("Analyzing stock: {}", request.symbol);
    
    let include_technical = request.include_technical.unwrap_or(true);
    let include_fundamental = request.include_fundamental.unwrap_or(true);
    
    match state.analyzer.analyze_stock(
        &request.symbol,
        include_technical,
        include_fundamental,
    ).await {
        Ok(analysis) => {
            info!("✅ Analysis completed for {}", request.symbol);
            Ok(Json(analysis))
        }
        Err(e) => {
            tracing::error!("❌ Analysis failed for {}: {}", request.symbol, e);
            Err(format!("Analysis failed: {}", e))
        }
    }
}

async fn calculate_indicators(
    State(state): State<AppState>,
    Json(request): Json<AnalyzeRequest>,
) -> Result<Json<models::TechnicalIndicators>, String> {
    info!("Calculating indicators for: {}", request.symbol);
    
    match state.analyzer.calculate_technical_indicators_async(&request.symbol).await {
        Ok(indicators) => {
            info!("✅ Indicators calculated for {}", request.symbol);
            Ok(Json(indicators))
        }
        Err(e) => {
            tracing::error!("❌ Indicator calculation failed for {}: {}", request.symbol, e);
            Err(format!("Indicator calculation failed: {}", e))
        }
    }
}

async fn get_recommendations(
    State(_state): State<AppState>,
    Json(request): Json<RecommendationsRequest>,
) -> Result<Json<serde_json::Value>, String> {
    info!("Getting personalized recommendations");
    
    // This would integrate with your existing recommendation logic
    let recommendations = match request.user_income {
        Some(income) if income < 30_000.0 => {
            vec![
                serde_json::json!({
                    "symbol": "JNJ",
                    "action": "BUY",
                    "confidence": 0.85,
                    "reason": "Stable dividend stock suitable for low income"
                }),
                serde_json::json!({
                    "symbol": "PG",
                    "action": "BUY", 
                    "confidence": 0.82,
                    "reason": "Consumer staples with consistent dividends"
                }),
            ]
        }
        Some(income) if income < 75_000.0 => {
            vec![
                serde_json::json!({
                    "symbol": "AAPL",
                    "action": "BUY",
                    "confidence": 0.88,
                    "reason": "Strong fundamentals and growth potential"
                }),
                serde_json::json!({
                    "symbol": "MSFT",
                    "action": "BUY",
                    "confidence": 0.85,
                    "reason": "Stable tech stock with good dividends"
                }),
            ]
        }
        _ => {
            vec![
                serde_json::json!({
                    "symbol": "GOOGL",
                    "action": "BUY",
                    "confidence": 0.90,
                    "reason": "High growth potential for higher income investors"
                }),
                serde_json::json!({
                    "symbol": "TSLA",
                    "action": "HOLD",
                    "confidence": 0.75,
                    "reason": "High volatility, consider for growth portfolio"
                }),
            ]
        }
    };
    
    Ok(Json(serde_json::json!({
        "recommendations": recommendations,
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "user_profile": {
            "income": request.user_income,
            "risk_tolerance": request.risk_tolerance,
            "goals": request.investment_goals
        }
    })))
}

#[derive(Deserialize)]
struct BatchAnalyzeRequest {
    symbols: Vec<String>,
    include_technical: Option<bool>,
    include_fundamental: Option<bool>,
}

async fn batch_analyze(
    State(state): State<AppState>,
    Json(request): Json<BatchAnalyzeRequest>,
) -> Result<Json<serde_json::Value>, String> {
    info!("Batch analyzing {} stocks", request.symbols.len());
    
    let include_technical = request.include_technical.unwrap_or(true);
    let include_fundamental = request.include_fundamental.unwrap_or(true);
    
    // Process stocks in parallel (but with rate limiting)
    let mut tasks = Vec::new();
    
    for symbol in request.symbols {
        let analyzer = state.analyzer.clone();
        let task = tokio::spawn(async move {
            analyzer.analyze_stock(&symbol, include_technical, include_fundamental).await
        });
        tasks.push((symbol, task));
    }
    
    let mut results = Vec::new();
    let mut errors = Vec::new();
    
    for (symbol, task) in tasks {
        match task.await {
            Ok(Ok(analysis)) => {
                results.push(serde_json::json!({
                    "symbol": symbol,
                    "analysis": analysis
                }));
            }
            Ok(Err(e)) => {
                errors.push(format!("{}: {}", symbol, e));
            }
            Err(e) => {
                errors.push(format!("{}: Task failed: {}", symbol, e));
            }
        }
    }
    
    info!("✅ Batch analysis completed: {} successful, {} errors", results.len(), errors.len());
    
    Ok(Json(serde_json::json!({
        "results": results,
        "errors": errors,
        "summary": {
            "total": results.len() + errors.len(),
            "successful": results.len(),
            "failed": errors.len()
        },
        "timestamp": chrono::Utc::now().to_rfc3339()
    })))
}

// Options Analysis Endpoints

async fn analyze_options(
    State(state): State<AppState>,
    Json(request): Json<OptionsAnalysisRequest>,
) -> Result<Json<OptionsAnalysisResponse>, String> {
    info!("Analyzing options for: {}", request.symbol);
    
    match state.options_service.fetch_options_chain(&request.symbol).await {
        Ok(options_chain) => {
            let mut unusual_flow = Vec::new();
            let mut recommended_strategies = Vec::new();
            
            if request.include_flow {
                match state.options_service.fetch_unusual_options_flow(&request.symbol).await {
                    Ok(flow) => unusual_flow = flow,
                    Err(e) => warn!("Failed to fetch unusual flow: {}", e),
                }
            }
            
            if request.include_strategies {
                let strategy_types = vec![
                    options_models::StrategyType::CoveredCall,
                    options_models::StrategyType::CashSecuredPut,
                    options_models::StrategyType::BullCallSpread,
                ];
                recommended_strategies = state.options_service.analyze_options_strategies(&options_chain, &strategy_types);
            }
            
            let market_sentiment = state.options_service.calculate_market_sentiment(&options_chain);
            
            Ok(Json(OptionsAnalysisResponse {
                success: true,
                underlying_symbol: request.symbol,
                underlying_price: options_chain.underlying_price,
                options_chain: if request.include_chain { Some(options_chain) } else { None },
                unusual_flow,
                recommended_strategies,
                market_sentiment,
                error: None,
            }))
        }
        Err(e) => {
            error!("Options analysis failed for {}: {}", request.symbol, e);
            Ok(Json(OptionsAnalysisResponse {
                success: false,
                underlying_symbol: request.symbol,
                underlying_price: 0.0,
                options_chain: None,
                unusual_flow: Vec::new(),
                recommended_strategies: Vec::new(),
                market_sentiment: options_models::MarketSentiment {
                    put_call_ratio: 0.0,
                    implied_volatility_rank: 0.0,
                    skew: 0.0,
                    sentiment_score: 50.0,
                    sentiment_description: "Unknown".to_string(),
                },
                error: Some(e.to_string()),
            }))
        }
    }
}

async fn get_options_chain(
    State(state): State<AppState>,
    Json(request): Json<serde_json::Value>,
) -> Result<Json<options_models::OptionsChain>, String> {
    let symbol = request.get("symbol")
        .and_then(|v| v.as_str())
        .ok_or("Missing symbol parameter")?;
    
    info!("Fetching options chain for: {}", symbol);
    
    match state.options_service.fetch_options_chain(symbol).await {
        Ok(chain) => Ok(Json(chain)),
        Err(e) => Err(format!("Failed to fetch options chain: {}", e)),
    }
}

async fn get_unusual_flow(
    State(state): State<AppState>,
    Json(request): Json<serde_json::Value>,
) -> Result<Json<Vec<options_models::OptionsFlow>>, String> {
    let symbol = request.get("symbol")
        .and_then(|v| v.as_str())
        .ok_or("Missing symbol parameter")?;
    
    info!("Fetching unusual options flow for: {}", symbol);
    
    match state.options_service.fetch_unusual_options_flow(symbol).await {
        Ok(flow) => Ok(Json(flow)),
        Err(e) => Err(format!("Failed to fetch unusual flow: {}", e)),
    }
}

async fn get_options_strategies(
    State(state): State<AppState>,
    Json(request): Json<serde_json::Value>,
) -> Result<Json<Vec<options_models::OptionsStrategy>>, String> {
    let symbol = request.get("symbol")
        .and_then(|v| v.as_str())
        .ok_or("Missing symbol parameter")?;
    
    info!("Analyzing options strategies for: {}", symbol);
    
    match state.options_service.fetch_options_chain(symbol).await {
        Ok(options_chain) => {
            let strategy_types = vec![
                options_models::StrategyType::CoveredCall,
                options_models::StrategyType::CashSecuredPut,
                options_models::StrategyType::BullCallSpread,
                options_models::StrategyType::IronCondor,
            ];
            
            let strategies = state.options_service.analyze_options_strategies(&options_chain, &strategy_types);
            Ok(Json(strategies))
        }
        Err(e) => Err(format!("Failed to analyze strategies: {}", e)),
    }
}

async fn screen_options(
    State(state): State<AppState>,
    Json(request): Json<serde_json::Value>,
) -> Result<Json<options_models::OptionsScreeningResult>, String> {
    let symbol = request.get("symbol")
        .and_then(|v| v.as_str())
        .ok_or("Missing symbol parameter")?;
    
    info!("Screening options for: {}", symbol);
    
    match state.options_service.fetch_options_chain(symbol).await {
        Ok(options_chain) => {
            // Parse screening criteria from request
            let criteria = OptionsScreeningCriteria {
                min_volume: request.get("min_volume").and_then(|v| v.as_u64()),
                max_volume: request.get("max_volume").and_then(|v| v.as_u64()),
                min_open_interest: request.get("min_open_interest").and_then(|v| v.as_u64()),
                max_open_interest: request.get("max_open_interest").and_then(|v| v.as_u64()),
                min_implied_volatility: request.get("min_implied_volatility").and_then(|v| v.as_f64()),
                max_implied_volatility: request.get("max_implied_volatility").and_then(|v| v.as_f64()),
                min_delta: request.get("min_delta").and_then(|v| v.as_f64()),
                max_delta: request.get("max_delta").and_then(|v| v.as_f64()),
                min_days_to_expiration: request.get("min_days_to_expiration").and_then(|v| v.as_i64()),
                max_days_to_expiration: request.get("max_days_to_expiration").and_then(|v| v.as_i64()),
                option_type: None, // Would need to parse from string
                min_strike: request.get("min_strike").and_then(|v| v.as_f64()),
                max_strike: request.get("max_strike").and_then(|v| v.as_f64()),
            };
            
            let result = state.options_service.screen_options(&options_chain, &criteria);
            Ok(Json(result))
        }
        Err(e) => Err(format!("Failed to screen options: {}", e)),
    }
}
