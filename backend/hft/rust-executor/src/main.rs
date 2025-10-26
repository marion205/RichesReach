mod adapters;
mod engine;
mod replay;

use std::env;
use std::sync::Arc;
use anyhow::Result;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
use adapters::polygon_feed::PolygonFeed;
use adapters::alpaca_gateway::{AlpacaGateway, MockGateway};
use engine::{Engine, AdvancedHFTEngine};
use crate::{RiskLimits, HFTStrategy, ArrayQueue};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    println!("🚀 RichesReach HFT Rust Executor Starting...");
    println!("⚡ Ultra-low latency trading engine");
    println!("📊 Microsecond precision order execution");
    println!("🎯 Multiple HFT strategies supported");
    println!("==========================================");

    // Configuration
    let api_key = env::var("ALPACA_API_KEY").unwrap_or("demo".to_string());
    let secret = env::var("ALPACA_SECRET_KEY").unwrap_or("demo".to_string());
    let paper = env::var("PAPER").unwrap_or("true".to_string()) == "true";
    let use_mock = env::var("USE_MOCK").unwrap_or("true".to_string()) == "true";

    // Create ring buffer for lock-free communication
    let ring = Arc::new(ArrayQueue::new(1024 * 1024)); // 1M tick capacity

    // Create market data feed
    let feed = if use_mock {
        Arc::new(PolygonFeed::new(api_key.clone(), ring.clone()))
    } else {
        Arc::new(PolygonFeed::new(api_key.clone(), ring.clone()))
    };

    // Create order gateway
    let gw: Arc<dyn crate::OrderGateway> = if use_mock {
        Arc::new(MockGateway::new())
    } else {
        Arc::new(AlpacaGateway::new(api_key, secret, paper))
    };

    // Risk limits
    let risk = RiskLimits {
        max_spread_bps: 10.0,      // Max 10 basis points spread
        max_notional: 100000.0,    // Max $100k per symbol
        daily_loss_cap: 50000.0,   // Daily loss limit
        max_orders_per_second: 1000,
        pdt_enabled: true,
    };

    // Choose strategy
    let strategy = match env::var("HFT_STRATEGY").unwrap_or("scalping".to_string()).as_str() {
        "scalping" => HFTStrategy::Scalping,
        "market_making" => HFTStrategy::MarketMaking,
        "arbitrage" => HFTStrategy::Arbitrage,
        "momentum" => HFTStrategy::Momentum,
        _ => HFTStrategy::Scalping,
    };

    println!("📈 Strategy: {:?}", strategy);
    println!("💰 Risk limits: spread_bps={}, notional={}", risk.max_spread_bps, risk.max_notional);
    println!("🔧 Using {} gateway", if use_mock { "mock" } else { "real" });

    // Start market data feed
    feed.start()?;

    // Create and start HFT engine
    let engine = Engine::new(ring.clone(), gw.clone(), risk.clone(), strategy);
    
    // Spawn engine in separate thread
    let engine_handle = std::thread::spawn(move || {
        engine.run();
    });

    // Optional: Start advanced multi-strategy engine
    let advanced_strategies = vec![
        HFTStrategy::Scalping,
        HFTStrategy::MarketMaking,
        HFTStrategy::Momentum,
    ];
    
    let advanced_engine = AdvancedHFTEngine::new(
        ring.clone(),
        gw.clone(),
        risk.clone(),
        advanced_strategies,
    );
    
    let advanced_handle = std::thread::spawn(move || {
        advanced_engine.run();
    });

    // Performance monitoring
    let monitor_ring = ring.clone();
    let monitor_handle = std::thread::spawn(move || {
        let mut last_stats = std::time::Instant::now();
        loop {
            std::thread::sleep(std::time::Duration::from_secs(5));
            
            let stats = monitor_ring.len();
            let elapsed = last_stats.elapsed();
            
            println!("📊 Performance: {} ticks in queue, {:?} elapsed", stats, elapsed);
            
            if stats > 100000 {
                println!("⚠️  Warning: High queue depth detected!");
            }
            
            last_stats = std::time::Instant::now();
        }
    });

    // Optional: Replay historical data
    if let Ok(csv_path) = env::var("REPLAY_CSV") {
        println!("📁 Replaying historical data from: {}", csv_path);
        let replay_handle = std::thread::spawn(move || {
            if let Err(e) = replay::replay(&csv_path, ring) {
                eprintln!("Replay error: {}", e);
            }
        });
        replay_handle.join().unwrap();
    }

    // Optional: Generate synthetic data for testing
    if let Ok(synthetic_duration) = env::var("SYNTHETIC_DURATION") {
        let duration: u64 = synthetic_duration.parse().unwrap_or(60);
        println!("🎲 Generating {} seconds of synthetic data", duration);
        
        let synthetic_handle = std::thread::spawn(move || {
            if let Err(e) = replay::generate_synthetic_data("AAPL", duration, 1000, ring) {
                eprintln!("Synthetic data error: {}", e);
            }
        });
        synthetic_handle.join().unwrap();
    }

    // Wait for engines to complete
    println!("🔄 HFT engines running... Press Ctrl+C to stop");
    
    // Handle graceful shutdown
    ctrlc::set_handler(move || {
        println!("\n🛑 Shutting down HFT engines...");
        std::process::exit(0);
    }).expect("Error setting Ctrl+C handler");

    // Keep main thread alive
    loop {
        std::thread::sleep(std::time::Duration::from_secs(1));
    }
}
