use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Test the improved stock analyzer
    println!("🧪 Testing Improved Stock Analysis Engine");
    
    let base_url = "http://localhost:3001";
    
    // Test health check
    println!("1. Testing health check...");
    let health_response = reqwest::get(&format!("{}/health", base_url)).await?;
    if health_response.status().is_success() {
        let health: serde_json::Value = health_response.json().await?;
        println!("✅ Health check passed: {:?}", health);
    } else {
        println!("❌ Health check failed");
        return Ok(());
    }
    
    // Test single stock analysis
    println!("\n2. Testing single stock analysis...");
    let analyze_request = serde_json::json!({
        "symbol": "AAPL",
        "include_technical": true,
        "include_fundamental": true
    });
    
    let client = reqwest::Client::new();
    let response = client
        .post(&format!("{}/analyze", base_url))
        .json(&analyze_request)
        .send()
        .await?;
    
    if response.status().is_success() {
        let analysis: serde_json::Value = response.json().await?;
        println!("✅ AAPL analysis completed");
        println!("   Recommendation: {:?}", analysis["recommendation"]);
        println!("   Risk Level: {:?}", analysis["risk_level"]);
        println!("   Beginner Score: {:?}", analysis["beginner_friendly_score"]);
    } else {
        println!("❌ AAPL analysis failed: {}", response.status());
    }
    
    // Test batch analysis
    println!("\n3. Testing batch analysis...");
    let batch_request = serde_json::json!({
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "include_technical": true,
        "include_fundamental": true
    });
    
    let response = client
        .post(&format!("{}/batch-analyze", base_url))
        .json(&batch_request)
        .send()
        .await?;
    
    if response.status().is_success() {
        let batch_result: serde_json::Value = response.json().await?;
        println!("✅ Batch analysis completed");
        println!("   Total: {:?}", batch_result["summary"]["total"]);
        println!("   Successful: {:?}", batch_result["summary"]["successful"]);
        println!("   Failed: {:?}", batch_result["summary"]["failed"]);
    } else {
        println!("❌ Batch analysis failed: {}", response.status());
    }
    
    // Test recommendations
    println!("\n4. Testing personalized recommendations...");
    let rec_request = serde_json::json!({
        "user_income": 50000.0,
        "risk_tolerance": "moderate",
        "investment_goals": ["retirement", "growth"]
    });
    
    let response = client
        .post(&format!("{}/recommendations", base_url))
        .json(&rec_request)
        .send()
        .await?;
    
    if response.status().is_success() {
        let recommendations: serde_json::Value = response.json().await?;
        println!("✅ Recommendations generated");
        println!("   Count: {:?}", recommendations["recommendations"].as_array().unwrap().len());
    } else {
        println!("❌ Recommendations failed: {}", response.status());
    }
    
    println!("\n🎉 All tests completed!");
    Ok(())
}
