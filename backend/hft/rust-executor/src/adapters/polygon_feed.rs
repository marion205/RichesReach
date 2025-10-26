use crate::{MarketDataFeed, L2, RiskLimits, HFTStrategy, OrderGateway, OrderReq, Side, Tif};
use std::sync::{Arc, Mutex};
use crossbeam_queue::ArrayQueue;
use tokio::time::{interval, Duration};
use rand::Rng;
use anyhow::Result;
use tracing::{info, error};

pub struct PolygonFeed {
    ring: Arc<ArrayQueue<(String, L2)>>,
    api_key: String,
    running: Arc<std::sync::atomic::AtomicBool>,
}

impl PolygonFeed {
    pub fn new(api_key: String, ring: Arc<ArrayQueue<(String, L2)>>) -> Self {
        Self {
            ring,
            api_key,
            running: Arc::new(std::sync::atomic::AtomicBool::new(false)),
        }
    }
}

impl MarketDataFeed for PolygonFeed {
    fn start(&self) -> Result<()> {
        self.running.store(true, std::sync::atomic::Ordering::SeqCst);
        
        let ring_clone = self.ring.clone();
        let running_clone = self.running.clone();
        let api_key = self.api_key.clone();
        
        tokio::spawn(async move {
            let mut rng = rand::thread_rng();
            let mut interval = interval(Duration::from_millis(10)); // 100 ticks/sec
            
            info!("Starting Polygon feed simulation for HFT");
            
            while running_clone.load(std::sync::atomic::Ordering::Relaxed) {
                interval.tick().await;
                
                // Generate realistic L2 data for AAPL
                let base_price = 263.0;
                let volatility = 0.001; // 0.1% volatility
                let price_change = (rng.gen::<f64>() - 0.5) * volatility;
                
                let bid_px = base_price + price_change;
                let ask_px = bid_px + 0.01; // 1 cent spread
                let bid_sz = 100 + rng.gen_range(0..1000);
                let ask_sz = 100 + rng.gen_range(0..1000);
                
                let l2 = L2 {
                    ts_ns: crate::nanos(),
                    bid_px,
                    bid_sz,
                    ask_px,
                    ask_sz,
                    bid2_px: bid_px - 0.01,
                    bid2_sz: bid_sz / 2,
                    ask2_px: ask_px + 0.01,
                    ask2_sz: ask_sz / 2,
                    volume: rng.gen_range(1000..10000),
                    spread_bps: crate::spread_bps(bid_px, ask_px),
                    microprice: crate::microprice(bid_px, bid_sz, ask_px, ask_sz),
                    imbalance: crate::orderbook_imbalance(bid_sz, ask_sz),
                };
                
                if ring_clone.push(("AAPL".to_string(), l2)).is_err() {
                    // Ring buffer full - drop tick (backpressure)
                    error!("Ring buffer full, dropping tick");
                }
            }
            
            info!("Polygon feed stopped");
        });
        
        Ok(())
    }

    fn try_pop(&self) -> Option<(String, L2)> {
        self.ring.pop()
    }

    fn stop(&self) -> Result<()> {
        self.running.store(false, std::sync::atomic::Ordering::SeqCst);
        Ok(())
    }
}

// Real Polygon WebSocket implementation would go here
pub struct PolygonWebSocketFeed {
    ring: Arc<ArrayQueue<(String, L2)>>,
    api_key: String,
    symbols: Vec<String>,
    running: Arc<std::sync::atomic::AtomicBool>,
}

impl PolygonWebSocketFeed {
    pub fn new(api_key: String, symbols: Vec<String>, ring: Arc<ArrayQueue<(String, L2)>>) -> Self {
        Self {
            ring,
            api_key,
            symbols,
            running: Arc::new(std::sync::atomic::AtomicBool::new(false)),
        }
    }
}

impl MarketDataFeed for PolygonWebSocketFeed {
    fn start(&self) -> Result<()> {
        // Real implementation would:
        // 1. Connect to Polygon WebSocket
        // 2. Subscribe to L2 quotes for symbols
        // 3. Parse JSON messages into L2 structs
        // 4. Push to ring buffer
        
        self.running.store(true, std::sync::atomic::Ordering::SeqCst);
        
        let ring_clone = self.ring.clone();
        let running_clone = self.running.clone();
        let symbols = self.symbols.clone();
        
        tokio::spawn(async move {
            // Mock WebSocket connection
            info!("Connecting to Polygon WebSocket for symbols: {:?}", symbols);
            
            while running_clone.load(std::sync::atomic::Ordering::Relaxed) {
                // Simulate WebSocket message processing
                tokio::time::sleep(Duration::from_millis(5)).await;
                
                for symbol in &symbols {
                    let l2 = L2 {
                        ts_ns: crate::nanos(),
                        bid_px: 100.0 + rand::thread_rng().gen_range(0.0..10.0),
                        bid_sz: rand::thread_rng().gen_range(100..1000),
                        ask_px: 100.1 + rand::thread_rng().gen_range(0.0..10.0),
                        ask_sz: rand::thread_rng().gen_range(100..1000),
                        bid2_px: 99.9,
                        bid2_sz: 500,
                        ask2_px: 100.2,
                        ask2_sz: 500,
                        volume: rand::thread_rng().gen_range(1000..10000),
                        spread_bps: 10.0,
                        microprice: 100.05,
                        imbalance: 0.1,
                    };
                    
                    if ring_clone.push((symbol.clone(), l2)).is_err() {
                        error!("Ring buffer full for {}", symbol);
                    }
                }
            }
        });
        
        Ok(())
    }

    fn try_pop(&self) -> Option<(String, L2)> {
        self.ring.pop()
    }

    fn stop(&self) -> Result<()> {
        self.running.store(false, std::sync::atomic::Ordering::SeqCst);
        Ok(())
    }
}
