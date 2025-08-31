use axum::{
    extract::State,
    Json,
};
use crate::{
    models::*,
    stock_analysis::StockAnalyzer,
    config::Config,
};
use tracing::{info, error};

#[derive(serde::Deserialize)]
pub struct IndicatorsRequest {
    pub symbol: String,
}

pub async fn health_check() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "healthy",
        "service": "Stock Analysis Engine",
        "timestamp": chrono::Utc::now().to_rfc3339()
    }))
}

pub async fn analyze_stock(
    State(config): State<Config>,
    Json(request): Json<AnalysisRequest>,
) -> Json<AnalysisResponse> {
    info!("Received analysis request for symbol: {}", request.symbol);
    
    let analyzer = StockAnalyzer::new(config);
    
    match analyzer.analyze_stock(
        &request.symbol,
        request.include_technical,
        request.include_fundamental,
    ).await {
        Ok(analysis) => {
            info!("Successfully analyzed stock: {}", request.symbol);
            Json(AnalysisResponse {
                success: true,
                analysis: Some(analysis),
                error: None,
            })
        }
        Err(e) => {
            error!("Failed to analyze stock {}: {}", request.symbol, e);
            Json(AnalysisResponse {
                success: false,
                analysis: None,
                error: Some(e.to_string()),
            })
        }
    }
}

pub async fn get_recommendations(
    State(_config): State<Config>,
) -> Json<serde_json::Value> {
    info!("Received recommendations request");
    
    // For now, return a placeholder response
    // In the future, this could analyze multiple stocks and return top picks
    Json(serde_json::json!({
        "success": true,
        "recommendations": [
            {
                "symbol": "AAPL",
                "reason": "Large market cap, consistent earnings, strong brand",
                "risk_level": "Low",
                "beginner_score": 85
            },
            {
                "symbol": "MSFT",
                "reason": "Cloud leader, strong fundamentals, low volatility",
                "risk_level": "Low",
                "beginner_score": 82
            }
        ]
    }))
}

pub async fn calculate_indicators(
    State(config): State<Config>,
    Json(request): Json<IndicatorsRequest>,
) -> Json<serde_json::Value> {
    let symbol = &request.symbol;
    info!("Received indicators request for symbol: {}", symbol);
    
    let analyzer = StockAnalyzer::new(config);
    
    match analyzer.calculate_technical_indicators(symbol).await {
        Ok(indicators) => {
            info!("Successfully calculated indicators for: {}", symbol);
            Json(serde_json::json!({
                "success": true,
                "symbol": symbol,
                "indicators": indicators
            }))
        }
        Err(e) => {
            error!("Failed to calculate indicators for {}: {}", symbol, e);
            Json(serde_json::json!({
                "success": false,
                "symbol": symbol,
                "error": e.to_string()
            }))
        }
    }
}
