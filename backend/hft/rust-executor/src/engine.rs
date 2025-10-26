use crate::{HFTEngine, L2, RiskLimits, HFTStrategy, OrderGateway, MarketDataFeed, PerformanceMonitor};
use crossbeam_queue::ArrayQueue;
use std::sync::Arc;
use std::thread;
use std::time::Duration;
use tracing::{info, error, warn};

pub struct Engine {
    ring: Arc<ArrayQueue<(String, L2)>>,
    gw: Arc<dyn OrderGateway>,
    risk: RiskLimits,
    strategy: HFTStrategy,
    monitor: Arc<std::sync::Mutex<PerformanceMonitor>>,
}

impl Engine {
    pub fn new(
        ring: Arc<ArrayQueue<(String, L2)>>,
        gw: Arc<dyn OrderGateway>,
        risk: RiskLimits,
        strategy: HFTStrategy,
    ) -> Self {
        Self {
            ring,
            gw,
            risk,
            strategy,
            monitor: Arc::new(std::sync::Mutex::new(PerformanceMonitor::new())),
        }
    }

    pub fn run(&self) {
        // Pin to CPU core 1 for deterministic performance
        if let Some(core_id) = core_affinity::get_core_ids().and_then(|cores| cores.get(1)) {
            core_affinity::set_for_current(*core_id);
            info!("Pinned HFT engine to CPU core {}", core_id.id);
        }

        let (obi_thresh, profit_bps, stop_bps) = self.strategy.thresholds();
        let mut order_count = 0u32;
        let mut last_second = std::time::SystemTime::now();
        let mut total_pnl = 0.0;

        info!("Starting HFT engine with strategy: {:?}", self.strategy);
        info!("Risk limits: spread_bps={}, notional={}", self.risk.max_spread_bps, self.risk.max_notional);

        loop {
            if let Some((sym, l2)) = self.ring.try_pop() {
                let start = std::time::Instant::now();
                
                // Update performance monitor
                if let Ok(mut monitor) = self.monitor.lock() {
                    monitor.record_tick();
                }

                // Update tick counter
                crate::TICK_COUNTER.with_label_values(&[&sym]).inc();

                let mid = 0.5 * (l2.bid_px + l2.ask_px);
                let current_spread = crate::spread_bps(l2.bid_px, l2.ask_px);
                
                // Risk checks
                if !self.risk.allow(&sym, mid, total_pnl) || 
                   current_spread > self.risk.max_spread_bps {
                    continue;
                }

                // Strategy logic based on microstructure signals
                let action = if l2.imbalance > obi_thresh && l2.microprice > mid {
                    Some(crate::Side::Buy)
                } else if l2.imbalance < -obi_thresh && l2.microprice < mid {
                    Some(crate::Side::Sell)
                } else {
                    None
                };

                if let Some(side) = action {
                    let order = crate::OrderReq {
                        symbol: sym.clone(),
                        side,
                        qty: self.calculate_position_size(&l2),
                        limit_px: if side == crate::Side::Buy { Some(l2.bid_px) } else { Some(l2.ask_px) },
                        tif: crate::Tif::IOC,
                        client_id: format!("{}-{}", crate::side_tag(&side), crate::nanos()),
                        priority: 10, // High priority for HFT
                    };

                    if let Err(e) = self.gw.post(&order) {
                        error!("Order failed: {}", e);
                        crate::ORDER_COUNTER.with_label_values(&[crate::side_tag(&side), &sym, "failed"]).inc();
                    } else {
                        crate::ORDER_COUNTER.with_label_values(&[crate::side_tag(&side), &sym, "success"]).inc();
                        order_count += 1;
                        
                        // Update PnL (simplified calculation)
                        let pnl = if side == crate::Side::Buy {
                            (l2.ask_px - l2.bid_px) * order.qty as f64
                        } else {
                            (l2.bid_px - l2.ask_px) * order.qty as f64
                        };
                        total_pnl += pnl;
                        
                        // Update performance monitor
                        if let Ok(mut monitor) = self.monitor.lock() {
                            monitor.record_order();
                        }
                    }
                }

                // Update metrics
                crate::LATENCY_HISTOGRAM.with_label_values(&["tick_to_order"]).observe(start.elapsed().as_secs_f64());
                
                // Orders per second tracking
                let now = std::time::SystemTime::now();
                if now.duration_since(last_second).unwrap() >= Duration::from_secs(1) {
                    if order_count > 0 {
                        info!("Orders per second: {}", order_count);
                    }
                    order_count = 0;
                    last_second = now;
                }
            } else {
                // No ticks available, yield CPU
                thread::yield_now();
            }
        }
    }

    fn calculate_position_size(&self, l2: &L2) -> u64 {
        // Position sizing based on volatility and risk limits
        let volatility = l2.spread_bps / 100.0; // Convert bps to decimal
        let base_size = 100u64;
        
        // Reduce size in high volatility
        if volatility > 0.01 { // > 1% spread
            base_size / 2
        } else {
            base_size
        }
    }

    pub fn get_performance_stats(&self) -> Option<crate::PerformanceStats> {
        self.monitor.lock().ok().map(|monitor| monitor.get_stats())
    }
}

// Advanced HFT strategies
pub struct AdvancedHFTEngine {
    ring: Arc<ArrayQueue<(String, L2)>>,
    gw: Arc<dyn OrderGateway>,
    risk: RiskLimits,
    strategies: Vec<HFTStrategy>,
    running: Arc<std::sync::atomic::AtomicBool>,
}

impl AdvancedHFTEngine {
    pub fn new(
        ring: Arc<ArrayQueue<(String, L2)>>,
        gw: Arc<dyn OrderGateway>,
        risk: RiskLimits,
        strategies: Vec<HFTStrategy>,
    ) -> Self {
        Self {
            ring,
            gw,
            risk,
            strategies,
            running: Arc::new(std::sync::atomic::AtomicBool::new(true)),
        }
    }

    pub fn run(&self) {
        // Pin to CPU core 2 for advanced strategies
        if let Some(core_id) = core_affinity::get_core_ids().and_then(|cores| cores.get(2)) {
            core_affinity::set_for_current(*core_id);
            info!("Pinned advanced HFT engine to CPU core {}", core_id.id);
        }

        info!("Starting advanced HFT engine with {} strategies", self.strategies.len());

        while self.running.load(std::sync::atomic::Ordering::Relaxed) {
            if let Some((sym, l2)) = self.ring.try_pop() {
                // Run all strategies in parallel
                for strategy in &self.strategies {
                    self.execute_strategy(strategy, &sym, &l2);
                }
            } else {
                thread::yield_now();
            }
        }
    }

    fn execute_strategy(&self, strategy: &HFTStrategy, symbol: &str, l2: &L2) {
        let (obi_thresh, profit_bps, stop_bps) = strategy.thresholds();
        
        match strategy {
            HFTStrategy::Scalping => self.execute_scalping(symbol, l2, obi_thresh),
            HFTStrategy::MarketMaking => self.execute_market_making(symbol, l2),
            HFTStrategy::Arbitrage => self.execute_arbitrage(symbol, l2),
            HFTStrategy::Momentum => self.execute_momentum(symbol, l2, obi_thresh),
        }
    }

    fn execute_scalping(&self, symbol: &str, l2: &L2, obi_thresh: f64) {
        // Ultra-fast profit taking
        if l2.spread_bps > 2.0 && l2.imbalance.abs() > obi_thresh {
            let side = if l2.imbalance > 0.0 { crate::Side::Buy } else { crate::Side::Sell };
            let order = crate::OrderReq {
                symbol: symbol.to_string(),
                side,
                qty: 50, // Small size for scalping
                limit_px: if side == crate::Side::Buy { Some(l2.bid_px) } else { Some(l2.ask_px) },
                tif: crate::Tif::IOC,
                client_id: format!("scalp-{}", crate::nanos()),
                priority: 9,
            };
            
            if let Err(e) = self.gw.post(&order) {
                error!("Scalping order failed: {}", e);
            }
        }
    }

    fn execute_market_making(&self, symbol: &str, l2: &L2) {
        // Provide liquidity on both sides
        if l2.spread_bps > 1.0 {
            // Place bid order
            let bid_order = crate::OrderReq {
                symbol: symbol.to_string(),
                side: crate::Side::Buy,
                qty: 100,
                limit_px: Some(l2.bid_px + 0.01), // Slightly better than market
                tif: crate::Tif::Day,
                client_id: format!("mm-bid-{}", crate::nanos()),
                priority: 5,
            };
            
            // Place ask order
            let ask_order = crate::OrderReq {
                symbol: symbol.to_string(),
                side: crate::Side::Sell,
                qty: 100,
                limit_px: Some(l2.ask_px - 0.01), // Slightly better than market
                tif: crate::Tif::Day,
                client_id: format!("mm-ask-{}", crate::nanos()),
                priority: 5,
            };
            
            if let Err(e) = self.gw.post(&bid_order) {
                error!("Market making bid failed: {}", e);
            }
            if let Err(e) = self.gw.post(&ask_order) {
                error!("Market making ask failed: {}", e);
            }
        }
    }

    fn execute_arbitrage(&self, symbol: &str, l2: &L2) {
        // Look for arbitrage opportunities
        // This is simplified - real arbitrage would compare multiple exchanges
        if symbol == "SPY" {
            // Compare with SPXL (3x leveraged SPY)
            let theoretical_spxl = l2.bid_px * 3.0;
            let spxl_spread = 0.05; // 5 cent spread threshold
            
            if l2.ask_px * 3.0 < theoretical_spxl - spxl_spread {
                // SPXL is underpriced, buy SPXL, sell SPY
                let order = crate::OrderReq {
                    symbol: "SPXL".to_string(),
                    side: crate::Side::Buy,
                    qty: 300,
                    limit_px: Some(theoretical_spxl - spxl_spread),
                    tif: crate::Tif::IOC,
                    client_id: format!("arb-{}", crate::nanos()),
                    priority: 8,
                };
                
                if let Err(e) = self.gw.post(&order) {
                    error!("Arbitrage order failed: {}", e);
                }
            }
        }
    }

    fn execute_momentum(&self, symbol: &str, l2: &L2, obi_thresh: f64) {
        // Trend following based on order flow
        if l2.imbalance.abs() > obi_thresh {
            let side = if l2.imbalance > 0.0 { crate::Side::Buy } else { crate::Side::Sell };
            let order = crate::OrderReq {
                symbol: symbol.to_string(),
                side,
                qty: 200, // Larger size for momentum
                limit_px: if side == crate::Side::Buy { Some(l2.ask_px) } else { Some(l2.bid_px) },
                tif: crate::Tif::IOC,
                client_id: format!("mom-{}", crate::nanos()),
                priority: 7,
            };
            
            if let Err(e) = self.gw.post(&order) {
                error!("Momentum order failed: {}", e);
            }
        }
    }

    pub fn stop(&self) {
        self.running.store(false, std::sync::atomic::Ordering::SeqCst);
    }
}
