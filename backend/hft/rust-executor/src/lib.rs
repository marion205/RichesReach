use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use anyhow::{Result, anyhow};
use serde::{Deserialize, Serialize};
use crossbeam_queue::ArrayQueue;
use prometheus::{register_histogram_vec, HistogramVec, register_counter_vec, CounterVec};
use core::sync::atomic::{AtomicBool, Ordering};

// Zero-copy L2 tick optimized for cache lines
#[repr(C, align(64))]
#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub struct L2 {
    pub ts_ns: u64,
    pub bid_px: f64, pub bid_sz: u64,
    pub ask_px: f64, pub ask_sz: u64,
    pub bid2_px: f64, pub bid2_sz: u64,
    pub ask2_px: f64, pub ask2_sz: u64,
    pub volume: u64,
    pub spread_bps: f64,
    pub microprice: f64,
    pub imbalance: f64,
}

// Enums
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Side { Buy, Sell }

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Tif { Day, IOC, FOK }

#[derive(Debug, Clone)]
pub struct OrderReq {
    pub symbol: String,
    pub side: Side,
    pub qty: u64,
    pub limit_px: Option<f64>,
    pub tif: Tif,
    pub client_id: String,  // Idempotency
    pub priority: u8,       // 1-10, higher = more priority
}

// Traits (stable for swaps)
pub trait MarketDataFeed: Send + Sync {
    fn start(&self) -> Result<()>;  // Spawn threads
    fn try_pop(&self) -> Option<(String, L2)>;  // Non-blocking
    fn stop(&self) -> Result<()>;
}

pub trait OrderGateway: Send + Sync {
    fn post(&self, o: &OrderReq) -> Result<()>;
    fn replace(&self, id: &str, new_px: f64) -> Result<()>;
    fn cancel(&self, id: &str) -> Result<()>;
}

// Metrics
lazy_static::lazy_static! {
    static ref LATENCY_HISTOGRAM: HistogramVec = register_histogram_vec!(
        "trading_latency_seconds",
        "Latency for trading operations",
        &["operation"],
        vec![0.000001, 0.00001, 0.0001, 0.001, 0.01, 0.1]
    ).unwrap();
    
    static ref ORDER_COUNTER: CounterVec = register_counter_vec!(
        "trading_orders_total",
        "Total number of orders",
        &["side", "symbol", "status"]
    ).unwrap();
    
    static ref TICK_COUNTER: CounterVec = register_counter_vec!(
        "trading_ticks_total",
        "Total number of ticks processed",
        &["symbol"]
    ).unwrap();
}

pub fn nanos() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos() as u64
}

fn side_tag(side: &Side) -> &'static str {
    match side {
        Side::Buy => "B",
        Side::Sell => "S",
    }
}

#[derive(Debug, Clone)]
pub struct RiskLimits {
    pub max_spread_bps: f64,
    pub max_notional: f64,
    pub daily_loss_cap: f64,
    pub max_orders_per_second: u32,
    pub pdt_enabled: bool,
}

impl RiskLimits {
    pub fn allow(&self, sym: &str, mid_px: f64, current_notional: f64) -> bool {
        // PDT check
        if self.pdt_enabled && current_notional > 25000.0 {
            return false;
        }
        
        // Daily loss cap
        if current_notional > self.daily_loss_cap {
            return false;
        }
        
        // Notional per symbol
        mid_px * 100.0 <= self.max_notional
    }
}

// Microstructure signals
#[inline]
pub fn orderbook_imbalance(bid_sz: u64, ask_sz: u64) -> f64 {
    let denom = (bid_sz + ask_sz).max(1) as f64;
    (bid_sz as f64 - ask_sz as f64) / denom
}

#[inline]
pub fn microprice(bid_px: f64, bid_sz: u64, ask_px: f64, ask_sz: u64) -> f64 {
    let total_sz = (bid_sz + ask_sz) as f64;
    if total_sz == 0.0 { return (bid_px + ask_px) / 2.0; }
    (ask_px * bid_sz as f64 + bid_px * ask_sz as f64) / total_sz
}

#[inline]
pub fn spread_bps(bid_px: f64, ask_px: f64) -> f64 {
    let mid = (bid_px + ask_px) / 2.0;
    if mid == 0.0 { return 0.0; }
    10_000.0 * (ask_px - bid_px) / mid
}

// HFT Strategy enum
#[derive(Debug, Clone, Copy)]
pub enum HFTStrategy {
    Scalping,      // Ultra-fast profit taking
    MarketMaking,  // Provide liquidity
    Arbitrage,     // Price differences
    Momentum,      // Trend following
}

impl HFTStrategy {
    pub fn thresholds(&self) -> (f64, f64, f64) {
        match self {
            HFTStrategy::Scalping => (0.2, 2.0, 1.0),      // obi_thresh, profit_bps, stop_bps
            HFTStrategy::MarketMaking => (0.1, 0.5, 2.0),   // obi_thresh, profit_bps, stop_bps
            HFTStrategy::Arbitrage => (0.3, 5.0, 1.0),     // obi_thresh, profit_bps, stop_bps
            HFTStrategy::Momentum => (0.4, 10.0, 5.0),     // obi_thresh, profit_bps, stop_bps
        }
    }
}

// Main HFT Engine
pub struct HFTEngine {
    ring: Arc<ArrayQueue<(String, L2)>>,
    gw: Arc<dyn OrderGateway>,
    risk: RiskLimits,
    strategy: HFTStrategy,
    running: Arc<AtomicBool>,
    orders_per_second: Arc<prometheus::IntCounter>,
    total_pnl: f64,
}

impl HFTEngine {
    pub fn new(
        ring: Arc<ArrayQueue<(String, L2)>>,
        gw: Arc<dyn OrderGateway>,
        risk: RiskLimits,
        strategy: HFTStrategy,
    ) -> Self {
        let orders_per_second = prometheus::IntCounter::new(
            "orders_per_second_total",
            "Orders per second counter"
        ).unwrap();
        
        Self {
            ring,
            gw,
            risk,
            strategy,
            running: Arc::new(AtomicBool::new(true)),
            orders_per_second: Arc::new(orders_per_second),
            total_pnl: 0.0,
        }
    }

    pub fn run(&self) {
        // Pin to CPU core 1 for deterministic performance
        if let Some(core_id) = core_affinity::get_core_ids().and_then(|cores| cores.get(1)) {
            core_affinity::set_for_current(*core_id);
        }

        let (obi_thresh, profit_bps, stop_bps) = self.strategy.thresholds();
        let mut order_count = 0u32;
        let mut last_second = SystemTime::now();

        while self.running.load(Ordering::Relaxed) {
            if let Some((sym, l2)) = self.ring.pop() {
                let start = std::time::Instant::now();
                
                // Update tick counter
                TICK_COUNTER.with_label_values(&[&sym]).inc();

                let mid = 0.5 * (l2.bid_px + l2.ask_px);
                let current_spread = spread_bps(l2.bid_px, l2.ask_px);
                
                // Risk checks
                if !self.risk.allow(&sym, mid, self.total_pnl) || 
                   current_spread > self.risk.max_spread_bps {
                    continue;
                }

                // Strategy logic
                let action = if l2.imbalance > obi_thresh && l2.microprice > mid {
                    Some(Side::Buy)
                } else if l2.imbalance < -obi_thresh && l2.microprice < mid {
                    Some(Side::Sell)
                } else {
                    None
                };

                if let Some(side) = action {
                    let order = OrderReq {
                        symbol: sym.to_string(),
                        side,
                        qty: 100,  // Position sizing
                        limit_px: if side == Side::Buy { Some(l2.bid_px) } else { Some(l2.ask_px) },
                        tif: Tif::IOC,
                        client_id: format!("{}-{}", side_tag(&side), nanos()),
                        priority: 10, // High priority for HFT
                    };

                    if let Err(e) = self.gw.post(&order) {
                        tracing::error!("Order failed: {}", e);
                        ORDER_COUNTER.with_label_values(&[side_tag(&side), &sym, "failed"]).inc();
                    } else {
                        ORDER_COUNTER.with_label_values(&[side_tag(&side), &sym, "success"]).inc();
                        order_count += 1;
                        
                        // Update PnL (simplified)
                        let pnl = if side == Side::Buy {
                            (l2.ask_px - l2.bid_px) * order.qty as f64
                        } else {
                            (l2.bid_px - l2.ask_px) * order.qty as f64
                        };
                        self.total_pnl += pnl;
                    }
                }

                // Update metrics
                LATENCY_HISTOGRAM.with_label_values(&["tick_to_order"]).observe(start.elapsed().as_secs_f64());
                
                // Orders per second tracking
                let now = SystemTime::now();
                if now.duration_since(last_second).unwrap() >= Duration::from_secs(1) {
                    self.orders_per_second.inc_by(order_count as u64);
                    order_count = 0;
                    last_second = now;
                }
            }
        }
    }

    pub fn stop(&self) {
        self.running.store(false, Ordering::SeqCst);
    }

    pub fn get_metrics(&self) -> HFTMetrics {
        HFTMetrics {
            total_pnl: self.total_pnl,
            orders_per_second: self.orders_per_second.get() as u32,
            strategy: self.strategy,
            risk_limits: self.risk.clone(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct HFTMetrics {
    pub total_pnl: f64,
    pub orders_per_second: u32,
    pub strategy: HFTStrategy,
    pub risk_limits: RiskLimits,
}

// Performance monitoring
pub struct PerformanceMonitor {
    start_time: SystemTime,
    tick_count: u64,
    order_count: u64,
}

impl PerformanceMonitor {
    pub fn new() -> Self {
        Self {
            start_time: SystemTime::now(),
            tick_count: 0,
            order_count: 0,
        }
    }

    pub fn record_tick(&mut self) {
        self.tick_count += 1;
    }

    pub fn record_order(&mut self) {
        self.order_count += 1;
    }

    pub fn get_stats(&self) -> PerformanceStats {
        let elapsed = self.start_time.elapsed().unwrap().as_secs_f64();
        PerformanceStats {
            ticks_per_second: self.tick_count as f64 / elapsed,
            orders_per_second: self.order_count as f64 / elapsed,
            uptime_seconds: elapsed,
        }
    }
}

#[derive(Debug)]
pub struct PerformanceStats {
    pub ticks_per_second: f64,
    pub orders_per_second: f64,
    pub uptime_seconds: f64,
}
