use axum::{
    extract::State,
    Json,
};
use crate::{
    models::*,
    stock_analysis::StockAnalyzer,
    config::Config,
};
use tracing::{info, error, warn};

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
    State(config): State<Config>,
) -> Json<serde_json::Value> {
    info!("Received recommendations request");
    
    let analyzer = StockAnalyzer::new(config);
    
    // List of popular stocks to analyze for recommendations
    let stocks_to_analyze = vec![
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", 
        "JNJ", "V", "PG", "UNH", "HD", "MA", "DIS", "PYPL", "ADBE", "CRM"
    ];
    
    let mut recommendations = Vec::new();
    
    // Analyze each stock and collect recommendations
    for symbol in stocks_to_analyze {
        match analyzer.analyze_stock(symbol, true, true).await {
            Ok(analysis) => {
                // Only include stocks with good beginner scores (70+)
                if analysis.beginner_friendly_score >= 70 {
                    let risk_level_str = match analysis.risk_level {
                        crate::models::RiskLevel::Low => "Low",
                        crate::models::RiskLevel::Medium => "Medium", 
                        crate::models::RiskLevel::High => "High",
                        crate::models::RiskLevel::Unknown => "Unknown",
                    };
                    
                    let recommendation_str = match analysis.recommendation {
                        crate::models::Recommendation::StrongBuy => "Strong Buy",
                        crate::models::Recommendation::Buy => "Buy",
                        crate::models::Recommendation::Hold => "Hold",
                        crate::models::Recommendation::Sell => "Sell",
                        crate::models::Recommendation::StrongSell => "Strong Sell",
                    };
                    
                    // Create a summary reason from the analysis
                    let reason = if analysis.reasoning.is_empty() {
                        format!("Good fundamentals with {} risk profile", risk_level_str.to_lowercase())
                    } else {
                        analysis.reasoning.join("; ")
                    };
                    
                    recommendations.push(serde_json::json!({
                        "symbol": symbol,
                        "company_name": analysis.symbol, // This will be the symbol, but could be enhanced
                        "recommendation": recommendation_str,
                        "risk_level": risk_level_str,
                        "beginner_score": analysis.beginner_friendly_score,
                        "reason": reason,
                        "technical_indicators": {
                            "rsi": analysis.technical_indicators.rsi,
                            "macd": analysis.technical_indicators.macd,
                            "sma_20": analysis.technical_indicators.sma_20,
                            "sma_50": analysis.technical_indicators.sma_50
                        },
                        "fundamental_analysis": {
                            "valuation_score": analysis.fundamental_analysis.valuation_score,
                            "stability_score": analysis.fundamental_analysis.stability_score,
                            "dividend_score": analysis.fundamental_analysis.dividend_score,
                            "debt_score": analysis.fundamental_analysis.debt_score
                        }
                    }));
                }
            }
            Err(e) => {
                warn!("Failed to analyze {}: {}", symbol, e);
                // Continue with other stocks even if one fails
            }
        }
        
        // Add a small delay to respect API rate limits
        tokio::time::sleep(tokio::time::Duration::from_millis(200)).await;
    }
    
    // Sort by beginner score (highest first) and take top 10
    recommendations.sort_by(|a, b| {
        let score_a = a["beginner_score"].as_u64().unwrap_or(0);
        let score_b = b["beginner_score"].as_u64().unwrap_or(0);
        score_b.cmp(&score_a)
    });
    
    let top_recommendations: Vec<_> = recommendations.into_iter().take(10).collect();
    
    Json(serde_json::json!({
        "success": true,
        "total_analyzed": stocks_to_analyze.len(),
        "recommendations_count": top_recommendations.len(),
        "recommendations": top_recommendations,
        "analysis_timestamp": chrono::Utc::now().to_rfc3339(),
        "criteria": {
            "min_beginner_score": 70,
            "includes_technical_analysis": true,
            "includes_fundamental_analysis": true
        }
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
