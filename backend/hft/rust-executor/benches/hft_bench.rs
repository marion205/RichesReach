use criterion::{black_box, criterion_group, criterion_main, Criterion};
use richesreach_exec::*;
use std::sync::Arc;
use crossbeam_queue::ArrayQueue;

fn benchmark_l2_processing(c: &mut Criterion) {
    let ring = Arc::new(ArrayQueue::new(10000));
    
    // Generate test data
    let test_l2 = L2 {
        ts_ns: 1234567890,
        bid_px: 100.0,
        bid_sz: 1000,
        ask_px: 100.01,
        ask_sz: 1000,
        bid2_px: 99.99,
        bid2_sz: 500,
        ask2_px: 100.02,
        ask2_sz: 500,
        volume: 10000,
        spread_bps: 1.0,
        microprice: 100.005,
        imbalance: 0.0,
    };

    c.bench_function("l2_processing", |b| b.iter(|| {
        // Benchmark L2 processing functions
        let spread = black_box(spread_bps(test_l2.bid_px, test_l2.ask_px));
        let microprice = black_box(microprice(test_l2.bid_px, test_l2.bid_sz, test_l2.ask_px, test_l2.ask_sz));
        let imbalance = black_box(orderbook_imbalance(test_l2.bid_sz, test_l2.ask_sz));
        
        // Ensure values are used
        black_box(spread);
        black_box(microprice);
        black_box(imbalance);
    }));
}

fn benchmark_ring_buffer(c: &mut Criterion) {
    let ring = Arc::new(ArrayQueue::new(10000));
    
    c.bench_function("ring_buffer_push_pop", |b| b.iter(|| {
        let l2 = L2 {
            ts_ns: black_box(1234567890),
            bid_px: black_box(100.0),
            bid_sz: black_box(1000),
            ask_px: black_box(100.01),
            ask_sz: black_box(1000),
            bid2_px: black_box(99.99),
            bid2_sz: black_box(500),
            ask2_px: black_box(100.02),
            ask2_sz: black_box(500),
            volume: black_box(10000),
            spread_bps: black_box(1.0),
            microprice: black_box(100.005),
            imbalance: black_box(0.0),
        };
        
        let _ = ring.push(black_box(("AAPL".to_string(), l2)));
        let _ = ring.pop();
    }));
}

fn benchmark_order_creation(c: &mut Criterion) {
    c.bench_function("order_creation", |b| b.iter(|| {
        let order = OrderReq {
            symbol: black_box("AAPL".to_string()),
            side: black_box(Side::Buy),
            qty: black_box(100),
            limit_px: black_box(Some(100.0)),
            tif: black_box(Tif::IOC),
            client_id: black_box(format!("test-{}", nanos())),
            priority: black_box(10),
        };
        
        black_box(order);
    }));
}

fn benchmark_microstructure_signals(c: &mut Criterion) {
    c.bench_function("microstructure_signals", |b| b.iter(|| {
        let bid_px = black_box(100.0);
        let bid_sz = black_box(1000);
        let ask_px = black_box(100.01);
        let ask_sz = black_box(1000);
        
        let spread = black_box(spread_bps(bid_px, ask_px));
        let microprice = black_box(microprice(bid_px, bid_sz, ask_px, ask_sz));
        let imbalance = black_box(orderbook_imbalance(bid_sz, ask_sz));
        
        // Strategy decision logic
        let mid = (bid_px + ask_px) / 2.0;
        let action = if imbalance > 0.2 && microprice > mid {
            Some(Side::Buy)
        } else if imbalance < -0.2 && microprice < mid {
            Some(Side::Sell)
        } else {
            None
        };
        
        black_box(action);
    }));
}

fn benchmark_hft_engine_loop(c: &mut Criterion) {
    let ring = Arc::new(ArrayQueue::new(10000));
    let gw = Arc::new(MockGateway::new());
    let risk = RiskLimits {
        max_spread_bps: 10.0,
        max_notional: 100000.0,
        daily_loss_cap: 50000.0,
        max_orders_per_second: 1000,
        pdt_enabled: true,
    };
    let strategy = HFTStrategy::Scalping;
    
    // Pre-populate ring with test data
    for i in 0..1000 {
        let l2 = L2 {
            ts_ns: nanos(),
            bid_px: 100.0 + (i as f64 * 0.001),
            bid_sz: 1000,
            ask_px: 100.01 + (i as f64 * 0.001),
            ask_sz: 1000,
            bid2_px: 99.99,
            bid2_sz: 500,
            ask2_px: 100.02,
            ask2_sz: 500,
            volume: 10000,
            spread_bps: 1.0,
            microprice: 100.005,
            imbalance: 0.1,
        };
        let _ = ring.push(("AAPL".to_string(), l2));
    }
    
    c.bench_function("hft_engine_loop", |b| b.iter(|| {
        let engine = Engine::new(ring.clone(), gw.clone(), risk.clone(), strategy);
        
        // Run engine loop for a few iterations
        let mut iterations = 0;
        while let Some((sym, l2)) = ring.try_pop() {
            if iterations >= 100 { break; } // Limit iterations for benchmark
            
            let mid = 0.5 * (l2.bid_px + l2.ask_px);
            let current_spread = spread_bps(l2.bid_px, l2.ask_px);
            
            if current_spread <= risk.max_spread_bps {
                let action = if l2.imbalance > 0.2 && l2.microprice > mid {
                    Some(Side::Buy)
                } else if l2.imbalance < -0.2 && l2.microprice < mid {
                    Some(Side::Sell)
                } else {
                    None
                };
                
                if let Some(side) = action {
                    let order = OrderReq {
                        symbol: sym.clone(),
                        side,
                        qty: 100,
                        limit_px: if side == Side::Buy { Some(l2.bid_px) } else { Some(l2.ask_px) },
                        tif: Tif::IOC,
                        client_id: format!("{}-{}", side_tag(&side), nanos()),
                        priority: 10,
                    };
                    
                    let _ = gw.post(&order);
                }
            }
            
            iterations += 1;
        }
        
        black_box(iterations);
    }));
}

criterion_group!(
    benches,
    benchmark_l2_processing,
    benchmark_ring_buffer,
    benchmark_order_creation,
    benchmark_microstructure_signals,
    benchmark_hft_engine_loop
);
criterion_main!(benches);
