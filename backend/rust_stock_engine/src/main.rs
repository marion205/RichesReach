use axum::{
    routing::{get, post},
    Router,
};
use std::net::SocketAddr;
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;

mod stock_analysis;
mod api;
mod models;
mod config;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .finish();
    tracing::subscriber::set_global_default(subscriber)?;

    info!("🚀 Starting Stock Analysis Engine...");

    // Load configuration
    let config = config::Config::load()?;
    info!("📊 Configuration loaded successfully");

    // Create router with API endpoints
    let app = Router::new()
        .route("/health", get(api::health_check))
        .route("/analyze", post(api::analyze_stock))
        .route("/recommendations", post(api::get_recommendations))
        .route("/indicators", post(api::calculate_indicators))
        .with_state(config);

    // Start server
    let addr = SocketAddr::from(([127, 0, 0, 1], 3001));
    info!("🌐 Stock Engine listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
