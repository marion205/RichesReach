use crate::{OrderGateway, OrderReq, Side, Tif};
use reqwest::Client;
use anyhow::Result;
use std::sync::Arc;
use tokio::time::sleep;
use std::time::Duration;
use tracing::{info, error, warn};

pub struct AlpacaGateway {
    client: Arc<Client>,
    api_key: String,
    secret_key: String,
    base_url: String,
    paper: bool,
}

impl AlpacaGateway {
    pub fn new(api_key: String, secret_key: String, paper: bool) -> Self {
        let url = if paper { 
            "https://paper-api.alpaca.markets" 
        } else { 
            "https://api.alpaca.markets" 
        }.to_string();
        
        let client = Client::builder()
            .timeout(Duration::from_millis(100)) // Ultra-low timeout for HFT
            .build()
            .expect("Failed to create HTTP client");
        
        Self {
            client: Arc::new(client),
            api_key,
            secret_key,
            base_url: url,
            paper,
        }
    }
}

impl OrderGateway for AlpacaGateway {
    fn post(&self, o: &OrderReq) -> Result<()> {
        let start = std::time::Instant::now();
        
        // Map to Alpaca order format
        let alpaca_order = serde_json::json!({
            "symbol": o.symbol,
            "qty": o.qty,
            "side": if o.side == Side::Buy { "buy" } else { "sell" },
            "type": if o.limit_px.is_some() { "limit" } else { "market" },
            "time_in_force": match o.tif {
                Tif::Day => "day",
                Tif::IOC => "ioc",
                Tif::FOK => "fok",
            },
            "client_order_id": o.client_id.clone(),
            "limit_price": o.limit_px,
            "extended_hours": false, // Regular hours only for HFT
        });
        
        // For HFT, we want synchronous execution
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let response = self.client
                .post(&format!("{}/v2/orders", self.base_url))
                .basic_auth(&self.api_key, Some(&self.secret_key))
                .json(&alpaca_order)
                .send()
                .await;
            
            match response {
                Ok(resp) => {
                    if resp.status().is_success() {
                        let order_response: serde_json::Value = resp.json().await.unwrap_or_default();
                        info!("Order posted successfully: {:?}", order_response);
                        Ok(())
                    } else {
                        let error_text = resp.text().await.unwrap_or_default();
                        error!("Order failed with status {}: {}", resp.status(), error_text);
                        Err(anyhow::anyhow!("Order failed: {}", error_text))
                    }
                }
                Err(e) => {
                    error!("Network error posting order: {}", e);
                    Err(anyhow::anyhow!("Network error: {}", e))
                }
            }
        });
        
        // Record latency
        let latency = start.elapsed();
        crate::LATENCY_HISTOGRAM.with_label_values(&["post"]).observe(latency.as_secs_f64());
        
        if latency > Duration::from_millis(50) {
            warn!("High latency order: {:?}", latency);
        }
        
        result
    }

    fn replace(&self, id: &str, new_px: f64) -> Result<()> {
        let start = std::time::Instant::now();
        
        let replace_order = serde_json::json!({
            "limit_price": new_px,
        });
        
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let response = self.client
                .patch(&format!("{}/v2/orders/{}", self.base_url, id))
                .basic_auth(&self.api_key, Some(&self.secret_key))
                .json(&replace_order)
                .send()
                .await;
            
            match response {
                Ok(resp) => {
                    if resp.status().is_success() {
                        info!("Order {} replaced with price {}", id, new_px);
                        Ok(())
                    } else {
                        let error_text = resp.text().await.unwrap_or_default();
                        error!("Replace failed: {}", error_text);
                        Err(anyhow::anyhow!("Replace failed: {}", error_text))
                    }
                }
                Err(e) => {
                    error!("Network error replacing order: {}", e);
                    Err(anyhow::anyhow!("Network error: {}", e))
                }
            }
        });
        
        crate::LATENCY_HISTOGRAM.with_label_values(&["replace"]).observe(start.elapsed().as_secs_f64());
        result
    }

    fn cancel(&self, id: &str) -> Result<()> {
        let start = std::time::Instant::now();
        
        let rt = tokio::runtime::Handle::current();
        let result = rt.block_on(async {
            let response = self.client
                .delete(&format!("{}/v2/orders/{}", self.base_url, id))
                .basic_auth(&self.api_key, Some(&self.secret_key))
                .send()
                .await;
            
            match response {
                Ok(resp) => {
                    if resp.status().is_success() {
                        info!("Order {} cancelled", id);
                        Ok(())
                    } else {
                        let error_text = resp.text().await.unwrap_or_default();
                        error!("Cancel failed: {}", error_text);
                        Err(anyhow::anyhow!("Cancel failed: {}", error_text))
                    }
                }
                Err(e) => {
                    error!("Network error cancelling order: {}", e);
                    Err(anyhow::anyhow!("Network error: {}", e))
                }
            }
        });
        
        crate::LATENCY_HISTOGRAM.with_label_values(&["cancel"]).observe(start.elapsed().as_secs_f64());
        result
    }
}

// Mock gateway for testing
pub struct MockGateway {
    order_count: std::sync::atomic::AtomicU64,
}

impl MockGateway {
    pub fn new() -> Self {
        Self {
            order_count: std::sync::atomic::AtomicU64::new(0),
        }
    }
}

impl OrderGateway for MockGateway {
    fn post(&self, o: &OrderReq) -> Result<()> {
        let count = self.order_count.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
        info!("Mock order #{}: {:?}", count, o);
        
        // Simulate network latency
        std::thread::sleep(Duration::from_micros(100)); // 100 microseconds
        
        Ok(())
    }

    fn replace(&self, id: &str, new_px: f64) -> Result<()> {
        info!("Mock replace order {} with price {}", id, new_px);
        Ok(())
    }

    fn cancel(&self, id: &str) -> Result<()> {
        info!("Mock cancel order {}", id);
        Ok(())
    }
}
