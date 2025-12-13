// src/execution.rs
// Execution Layer - OneTapTrade → Alpaca API → FilledOrderReceipt
// Asynchronous, safe, logged, idempotent

use std::sync::Arc;
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};
use tokio::sync::RwLock;
use uuid::Uuid;

use crate::options_core::OneTapTrade;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderRequest {
    pub user_id: String,
    pub trade: OneTapTrade,
    pub account_equity: f64,
    pub idempotency_key: Option<String>, // Prevent duplicate submissions
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum OrderStatus {
    Pending,
    Submitted,
    PartiallyFilled,
    Filled,
    Rejected,
    Cancelled,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderReceipt {
    pub order_id: String,
    pub user_id: String,
    pub symbol: String,
    pub status: OrderStatus,
    pub submitted_at: DateTime<Utc>,
    pub filled_at: Option<DateTime<Utc>>,
    pub filled_price: Option<f64>,
    pub filled_quantity: Option<i32>,
    pub total_cost: f64,
    pub commission: f64,
    pub rejection_reason: Option<String>,
    pub alpaca_order_id: Option<String>, // External broker order ID
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionConfig {
    pub alpaca_api_key: Option<String>,
    pub alpaca_secret_key: Option<String>,
    pub alpaca_base_url: String, // "https://paper-api.alpaca.markets" or "https://api.alpaca.markets"
    pub enable_live_trading: bool,
    pub max_order_value: f64, // Safety limit
    pub commission_per_contract: f64, // e.g., 0.65
}

impl Default for ExecutionConfig {
    fn default() -> Self {
        Self {
            alpaca_api_key: None,
            alpaca_secret_key: None,
            alpaca_base_url: "https://paper-api.alpaca.markets".to_string(),
            enable_live_trading: false,
            max_order_value: 100_000.0,
            commission_per_contract: 0.65,
        }
    }
}

pub struct ExecutionEngine {
    config: ExecutionConfig,
    orders: Arc<RwLock<std::collections::HashMap<String, OrderReceipt>>>, // order_id -> receipt
    idempotency_keys: Arc<RwLock<std::collections::HashSet<String>>>, // Track used keys
}

impl ExecutionEngine {
    pub fn new(config: ExecutionConfig) -> Self {
        Self {
            config,
            orders: Arc::new(RwLock::new(std::collections::HashMap::new())),
            idempotency_keys: Arc::new(RwLock::new(std::collections::HashSet::new())),
        }
    }

    /// Submit an order (async, idempotent, logged)
    pub async fn submit_order(&self, request: OrderRequest) -> anyhow::Result<OrderReceipt> {
        // Check idempotency
        if let Some(key) = &request.idempotency_key {
            let mut keys = self.idempotency_keys.write().await;
            if keys.contains(key) {
                // Return existing order
                let orders = self.orders.read().await;
                if let Some(existing) = orders.values().find(|o| {
                    o.user_id == request.user_id && o.symbol == request.trade.symbol
                }) {
                    return Ok(existing.clone());
                }
            }
            keys.insert(key.clone());
        }

        let order_id = Uuid::new_v4().to_string();
        let now = Utc::now();

        // Build Alpaca order
        let alpaca_order = self.build_alpaca_order(&request.trade)?;

        // Validate order
        self.validate_order(&request, &alpaca_order)?;

        // Create receipt (pending)
        let mut receipt = OrderReceipt {
            order_id: order_id.clone(),
            user_id: request.user_id.clone(),
            symbol: request.trade.symbol.clone(),
            status: OrderStatus::Pending,
            submitted_at: now,
            filled_at: None,
            filled_price: None,
            filled_quantity: None,
            total_cost: request.trade.total_cost,
            commission: self.calculate_commission(&request.trade),
            rejection_reason: None,
            alpaca_order_id: None,
        };

        // Store receipt
        {
            let mut orders = self.orders.write().await;
            orders.insert(order_id.clone(), receipt.clone());
        }

        // Submit to Alpaca (async, non-blocking)
        let engine_clone = self.clone_for_async();
        let request_clone = request.clone();
        let alpaca_order_clone = alpaca_order.clone();

        tokio::spawn(async move {
            if let Err(e) = engine_clone.execute_alpaca_order(order_id, alpaca_order_clone).await {
                tracing::error!("Failed to execute Alpaca order: {}", e);
            }
        });

        Ok(receipt)
    }

    /// Get order status
    pub async fn get_order_status(&self, order_id: &str) -> anyhow::Result<Option<OrderReceipt>> {
        let orders = self.orders.read().await;
        Ok(orders.get(order_id).cloned())
    }

    /// Cancel an order
    pub async fn cancel_order(&self, order_id: &str) -> anyhow::Result<()> {
        // TODO: Implement Alpaca cancellation
        let mut orders = self.orders.write().await;
        if let Some(receipt) = orders.get_mut(order_id) {
            receipt.status = OrderStatus::Cancelled;
        }
        Ok(())
    }

    // ───────────────────── Private helpers ─────────────────────

    fn build_alpaca_order(&self, trade: &OneTapTrade) -> anyhow::Result<AlpacaOrder> {
        // Convert OneTapTrade to Alpaca order format
        // For now, handle single-leg orders (can extend to multi-leg)
        if trade.legs.len() != 1 {
            anyhow::bail!("Multi-leg orders not yet supported");
        }

        let leg = &trade.legs[0];
        let symbol = format!("{}{}{}{}", 
            trade.symbol,
            leg.expiration.replace("-", ""),
            if leg.option_type == "call" { "C" } else { "P" },
            (leg.strike * 1000.0) as i32
        );

        Ok(AlpacaOrder {
            symbol,
            qty: leg.quantity,
            side: if leg.action == "buy" { "buy" } else { "sell" }.to_string(),
            r#type: "limit".to_string(),
            time_in_force: "day".to_string(),
            limit_price: leg.premium,
            extended_hours: false,
        })
    }

    fn validate_order(&self, request: &OrderRequest, alpaca_order: &AlpacaOrder) -> anyhow::Result<()> {
        // Check max order value
        let order_value = alpaca_order.limit_price * alpaca_order.qty as f64;
        if order_value > self.config.max_order_value {
            anyhow::bail!(
                "Order value ${:.2} exceeds max ${:.2}",
                order_value,
                self.config.max_order_value
            );
        }

        // Check if live trading is enabled
        if !self.config.enable_live_trading && self.config.alpaca_base_url.contains("api.alpaca.markets") {
            anyhow::bail!("Live trading is disabled");
        }

        // Validate symbol format
        if alpaca_order.symbol.len() < 10 {
            anyhow::bail!("Invalid option symbol format");
        }

        Ok(())
    }

    fn calculate_commission(&self, trade: &OneTapTrade) -> f64 {
        let total_contracts: i32 = trade.legs.iter().map(|l| l.quantity).sum();
        total_contracts as f64 * self.config.commission_per_contract
    }

    async fn execute_alpaca_order(&self, order_id: String, alpaca_order: AlpacaOrder) -> anyhow::Result<()> {
        // Update status to Submitted
        {
            let mut orders = self.orders.write().await;
            if let Some(receipt) = orders.get_mut(&order_id) {
                receipt.status = OrderStatus::Submitted;
            }
        }

        // If no API keys, simulate fill (for testing)
        if self.config.alpaca_api_key.is_none() {
            tracing::warn!("No Alpaca API keys - simulating order fill");
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
            
            let mut orders = self.orders.write().await;
            if let Some(receipt) = orders.get_mut(&order_id) {
                receipt.status = OrderStatus::Filled;
                receipt.filled_at = Some(Utc::now());
                receipt.filled_price = Some(alpaca_order.limit_price);
                receipt.filled_quantity = Some(alpaca_order.qty);
            }
            return Ok(());
        }

        // TODO: Implement actual Alpaca API call
        // Use reqwest or similar to POST to Alpaca API
        // Handle authentication, rate limiting, error responses
        // Update receipt with Alpaca order ID and status

        tracing::info!("Alpaca order execution not yet implemented - API keys present");
        Ok(())
    }

    fn clone_for_async(&self) -> Self {
        Self {
            config: self.config.clone(),
            orders: self.orders.clone(),
            idempotency_keys: self.idempotency_keys.clone(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct AlpacaOrder {
    symbol: String,
    qty: i32,
    side: String, // "buy" | "sell"
    r#type: String, // "market" | "limit" | "stop" | "stop_limit"
    time_in_force: String, // "day" | "gtc" | "opg" | "cls" | "ioc" | "fok"
    limit_price: f64,
    extended_hours: bool,
}

impl Clone for ExecutionEngine {
    fn clone(&self) -> Self {
        Self {
            config: self.config.clone(),
            orders: self.orders.clone(),
            idempotency_keys: self.idempotency_keys.clone(),
        }
    }
}

