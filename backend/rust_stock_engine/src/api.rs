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

#[derive(serde::Deserialize)]
pub struct RecommendationsRequest {
    pub user_income: Option<f64>,
    pub risk_tolerance: Option<String>,
    pub investment_goals: Option<Vec<String>>,
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
    Json(request): Json<RecommendationsRequest>,
) -> Json<serde_json::Value> {
    info!("Received recommendations request with user profile: income={:?}, risk={:?}", 
          request.user_income, request.risk_tolerance);
    
    let analyzer = StockAnalyzer::new(config);
    
    // Determine stock universe based on user income
    let stocks_to_analyze = match request.user_income {
        Some(income) if income < 30000.0 => {
            // Low income: Focus on stable, dividend-paying stocks
            vec![
                "JNJ", "PG", "KO", "PEP", "WMT", "MCD", "T", "VZ", "XOM", "CVX",
                "JPM", "BAC", "WFC", "C", "GS", "MS", "HD", "LOW", "COST", "TGT"
            ]
        },
        Some(income) if income < 75000.0 => {
            // Medium income: Mix of stable and growth stocks
            vec![
                "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "JPM", "JNJ", 
                "V", "PG", "UNH", "HD", "MA", "DIS", "PYPL", "ADBE", "CRM", "NFLX"
            ]
        },
        Some(income) if income < 150000.0 => {
            // Higher income: Include more growth and tech stocks
            vec![
                "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", 
                "JNJ", "V", "PG", "UNH", "HD", "MA", "DIS", "PYPL", "ADBE", "CRM",
                "NFLX", "AMD", "INTC", "ORCL", "IBM", "CSCO", "QCOM", "AVGO"
            ]
        },
        _ => {
            // High income or no profile: Best the market has to offer
            vec![
                "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", 
                "JNJ", "V", "PG", "UNH", "HD", "MA", "DIS", "PYPL", "ADBE", "CRM",
                "NFLX", "AMD", "INTC", "ORCL", "IBM", "CSCO", "QCOM", "AVGO",
                "BRK.B", "LLY", "ABBV", "PFE", "MRK", "KO", "PEP", "WMT"
            ]
        }
    };
    
    let mut recommendations = Vec::new();
    
    // Determine minimum score based on user profile
    let min_score = match request.user_income {
        Some(income) if income < 30000.0 => 75, // Higher standards for low income
        Some(income) if income < 75000.0 => 70, // Standard beginner score
        Some(income) if income < 150000.0 => 65, // Slightly lower for higher income
        _ => 60, // Lower threshold for high income or no profile
    };
    
    // Determine risk preference based on user profile
    let preferred_risk = match request.risk_tolerance.as_deref() {
        Some("conservative") => "Low",
        Some("moderate") => "Medium", 
        Some("aggressive") => "High",
        _ => "Any", // No preference
    };
    
    // Store the length before the loop
    let total_stocks = stocks_to_analyze.len();
    
    // Analyze each stock and collect recommendations
    for symbol in stocks_to_analyze {
        match analyzer.analyze_stock(symbol, true, true).await {
            Ok(analysis) => {
                // Filter based on user profile
                let risk_level_str = match analysis.risk_level {
                    crate::models::RiskLevel::Low => "Low",
                    crate::models::RiskLevel::Medium => "Medium", 
                    crate::models::RiskLevel::High => "High",
                    crate::models::RiskLevel::Unknown => "Unknown",
                };
                
                // Check if stock meets criteria
                let meets_score = analysis.beginner_friendly_score >= min_score;
                let meets_risk = preferred_risk == "Any" || risk_level_str == preferred_risk;
                
                if meets_score && meets_risk {
                    
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
        "user_profile": {
            "income": request.user_income,
            "risk_tolerance": request.risk_tolerance,
            "investment_goals": request.investment_goals
        },
        "analysis_summary": {
            "total_analyzed": total_stocks,
            "recommendations_count": top_recommendations.len(),
            "min_score_threshold": min_score,
            "risk_preference": preferred_risk
        },
        "recommendations": top_recommendations,
        "analysis_timestamp": chrono::Utc::now().to_rfc3339(),
        "criteria": {
            "min_beginner_score": min_score,
            "risk_tolerance": preferred_risk,
            "includes_technical_analysis": true,
            "includes_fundamental_analysis": true,
            "personalized_for_income": request.user_income.is_some()
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
