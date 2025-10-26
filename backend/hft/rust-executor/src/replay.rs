use crate::{MarketDataFeed, L2};
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::sync::Arc;
use std::thread;
use std::time::Duration;
use crossbeam_queue::ArrayQueue;
use anyhow::Result;
use tracing::{info, error};

pub fn replay(csv_path: &str, ring: Arc<ArrayQueue<(String, L2)>>) -> Result<()> {
    let file = File::open(csv_path)?;
    let reader = BufReader::new(file);
    
    info!("Starting replay from {}", csv_path);
    
    // Assume CSV format: ts_ns,symbol,bid_px,bid_sz,ask_px,ask_sz,bid2_px,bid2_sz,ask2_px,ask2_sz,volume
    let mut line_count = 0;
    for line in reader.lines() {
        let line = line?;
        let parts: Vec<&str> = line.split(',').collect();
        
        if parts.len() < 11 {
            error!("Invalid CSV line: {}", line);
            continue;
        }
        
        let l2 = L2 {
            ts_ns: parts[0].parse().unwrap_or(0),
            bid_px: parts[2].parse().unwrap_or(0.0),
            bid_sz: parts[3].parse().unwrap_or(0),
            ask_px: parts[4].parse().unwrap_or(0.0),
            ask_sz: parts[5].parse().unwrap_or(0),
            bid2_px: parts[6].parse().unwrap_or(0.0),
            bid2_sz: parts[7].parse().unwrap_or(0),
            ask2_px: parts[8].parse().unwrap_or(0.0),
            ask2_sz: parts[9].parse().unwrap_or(0),
            volume: parts[10].parse().unwrap_or(0),
            spread_bps: crate::spread_bps(
                parts[2].parse().unwrap_or(0.0),
                parts[4].parse().unwrap_or(0.0)
            ),
            microprice: crate::microprice(
                parts[2].parse().unwrap_or(0.0),
                parts[3].parse().unwrap_or(0),
                parts[4].parse().unwrap_or(0.0),
                parts[5].parse().unwrap_or(0)
            ),
            imbalance: crate::orderbook_imbalance(
                parts[3].parse().unwrap_or(0),
                parts[5].parse().unwrap_or(0)
            ),
        };
        
        if ring.push((parts[1].to_string(), l2)).is_err() {
            error!("Ring buffer full during replay");
            break;
        }
        
        line_count += 1;
        if line_count % 1000 == 0 {
            info!("Replayed {} ticks", line_count);
        }
        
        // Pace replay to simulate real-time
        thread::sleep(Duration::from_millis(10)); // 100 ticks/sec
    }
    
    info!("Replay completed: {} ticks processed", line_count);
    Ok(())
}

// Generate synthetic L2 data for testing
pub fn generate_synthetic_data(
    symbol: &str,
    duration_seconds: u64,
    ticks_per_second: u32,
    ring: Arc<ArrayQueue<(String, L2)>>,
) -> Result<()> {
    let base_price = 100.0;
    let volatility = 0.01; // 1% volatility
    let mut current_price = base_price;
    
    info!("Generating {} seconds of synthetic data for {} at {} ticks/sec", 
          duration_seconds, symbol, ticks_per_second);
    
    let total_ticks = duration_seconds * ticks_per_second as u64;
    let tick_interval = Duration::from_nanos(1_000_000_000 / ticks_per_second as u64);
    
    for i in 0..total_ticks {
        // Random walk price movement
        let price_change = (rand::thread_rng().gen::<f64>() - 0.5) * volatility;
        current_price += price_change;
        
        let spread = 0.01; // 1 cent spread
        let bid_px = current_price - spread / 2.0;
        let ask_px = current_price + spread / 2.0;
        
        let bid_sz = rand::thread_rng().gen_range(100..1000);
        let ask_sz = rand::thread_rng().gen_range(100..1000);
        
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
            volume: rand::thread_rng().gen_range(1000..10000),
            spread_bps: crate::spread_bps(bid_px, ask_px),
            microprice: crate::microprice(bid_px, bid_sz, ask_px, ask_sz),
            imbalance: crate::orderbook_imbalance(bid_sz, ask_sz),
        };
        
        if ring.push((symbol.to_string(), l2)).is_err() {
            error!("Ring buffer full during synthetic data generation");
            break;
        }
        
        if i % 1000 == 0 {
            info!("Generated {} ticks", i);
        }
        
        thread::sleep(tick_interval);
    }
    
    info!("Synthetic data generation completed: {} ticks", total_ticks);
    Ok(())
}

// Benchmark replay for performance testing
pub fn benchmark_replay(csv_path: &str, ring: Arc<ArrayQueue<(String, L2)>>) -> Result<()> {
    let start = std::time::Instant::now();
    let file = File::open(csv_path)?;
    let reader = BufReader::new(file);
    
    let mut tick_count = 0;
    let mut parse_errors = 0;
    
    for line in reader.lines() {
        let line = line?;
        let parts: Vec<&str> = line.split(',').collect();
        
        if parts.len() < 11 {
            parse_errors += 1;
            continue;
        }
        
        let l2 = L2 {
            ts_ns: parts[0].parse().unwrap_or(0),
            bid_px: parts[2].parse().unwrap_or(0.0),
            bid_sz: parts[3].parse().unwrap_or(0),
            ask_px: parts[4].parse().unwrap_or(0.0),
            ask_sz: parts[5].parse().unwrap_or(0),
            bid2_px: parts[6].parse().unwrap_or(0.0),
            bid2_sz: parts[7].parse().unwrap_or(0),
            ask2_px: parts[8].parse().unwrap_or(0.0),
            ask2_sz: parts[9].parse().unwrap_or(0),
            volume: parts[10].parse().unwrap_or(0),
            spread_bps: 0.0, // Skip calculation for benchmark
            microprice: 0.0,
            imbalance: 0.0,
        };
        
        if ring.push((parts[1].to_string(), l2)).is_err() {
            break;
        }
        
        tick_count += 1;
    }
    
    let elapsed = start.elapsed();
    let ticks_per_second = tick_count as f64 / elapsed.as_secs_f64();
    
    info!("Benchmark results:");
    info!("  Ticks processed: {}", tick_count);
    info!("  Parse errors: {}", parse_errors);
    info!("  Time elapsed: {:?}", elapsed);
    info!("  Ticks per second: {:.2}", ticks_per_second);
    
    Ok(())
}
