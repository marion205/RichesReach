use warp::ws::{WebSocket, Message};
use futures_util::{SinkExt, StreamExt};
use serde::{Serialize, Deserialize};
use serde_json;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{RwLock, broadcast};
use tokio::time::{interval, Duration};
use crate::{CryptoAnalysisResponse, CryptoRecommendation};
use crate::options_analysis::OptionsAnalysisResponse;
use crate::forex_analysis::ForexAnalysisResponse;
use crate::sentiment_analysis::SentimentAnalysisResponse;
use crate::correlation_analysis::CorrelationAnalysisResponse;
use anyhow::Result;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum WebSocketMessage {
    PredictionUpdate(CryptoAnalysisResponse),
    RecommendationUpdate(Vec<CryptoRecommendation>),
    PriceUpdate { symbol: String, price: f64, change_24h: f64 },
    OptionsUpdate { symbol: String, analysis: OptionsAnalysisResponse },
    ForexUpdate { pair: String, analysis: ForexAnalysisResponse },
    SentimentUpdate { symbol: String, analysis: SentimentAnalysisResponse },
    CorrelationUpdate { primary: String, secondary: String, analysis: CorrelationAnalysisResponse },
    Heartbeat,
}

impl WebSocketMessage {
    pub fn to_json(&self) -> Result<String> {
        Ok(serde_json::to_string(self)?)
    }
}

pub struct WebSocketManager {
    clients: Arc<RwLock<HashMap<String, broadcast::Sender<WebSocketMessage>>>>,
    broadcast_tx: broadcast::Sender<WebSocketMessage>,
}

impl WebSocketManager {
    pub fn new() -> Self {
        let (broadcast_tx, _) = broadcast::channel(1000);
        
        Self {
            clients: Arc::new(RwLock::new(HashMap::new())),
            broadcast_tx,
        }
    }

    pub async fn handle_connection(&self, websocket: WebSocket) {
        let client_id = uuid::Uuid::new_v4().to_string();
        let mut client_rx = self.broadcast_tx.subscribe();
        
        // Add client to registry
        {
            let mut clients = self.clients.write().await;
            clients.insert(client_id.clone(), self.broadcast_tx.clone());
        }

        let (mut ws_tx, mut ws_rx) = websocket.split();

        // Spawn task to send messages to this client
        let clients = self.clients.clone();
        let client_id_clone = client_id.clone();
        tokio::spawn(async move {
            while let Ok(msg) = client_rx.recv().await {
                if let Ok(json) = msg.to_json() {
                    if let Err(e) = ws_tx.send(Message::text(json)).await {
                        tracing::warn!("Failed to send message to client {}: {}", client_id_clone, e);
                        break;
                    }
                }
            }
            
            // Remove client when connection closes
            let mut clients = clients.write().await;
            clients.remove(&client_id_clone);
        });

        // Handle incoming messages from client
        while let Some(result) = ws_rx.next().await {
            match result {
                Ok(msg) => {
                    if let Ok(text) = msg.to_str() {
                        if let Err(e) = self.handle_client_message(&client_id, text).await {
                            tracing::warn!("Error handling client message: {}", e);
                        }
                    }
                }
                Err(e) => {
                    tracing::warn!("WebSocket error for client {}: {}", client_id, e);
                    break;
                }
            }
        }

        // Remove client when connection closes
        {
            let mut clients = self.clients.write().await;
            clients.remove(&client_id);
        }
    }

    async fn handle_client_message(&self, client_id: &str, message: &str) -> Result<()> {
        // Parse client message and handle different types
        let msg: serde_json::Value = serde_json::from_str(message)?;
        
        if let Some(msg_type) = msg.get("type").and_then(|t| t.as_str()) {
            match msg_type {
                "subscribe" => {
                    if let Some(symbol) = msg.get("symbol").and_then(|s| s.as_str()) {
                        tracing::info!("Client {} subscribed to {}", client_id, symbol);
                        // In a real implementation, you'd track subscriptions per client
                    }
                }
                "unsubscribe" => {
                    if let Some(symbol) = msg.get("symbol").and_then(|s| s.as_str()) {
                        tracing::info!("Client {} unsubscribed from {}", client_id, symbol);
                    }
                }
                "ping" => {
                    // Send pong response
                    let pong = serde_json::json!({
                        "type": "pong",
                        "timestamp": chrono::Utc::now()
                    });
                    // This would need to be sent back to the specific client
                    tracing::debug!("Received ping from client {}", client_id);
                }
                _ => {
                    tracing::warn!("Unknown message type from client {}: {}", client_id, msg_type);
                }
            }
        }

        Ok(())
    }

    pub async fn broadcast_prediction(&self, prediction: CryptoAnalysisResponse) -> Result<()> {
        let msg = WebSocketMessage::PredictionUpdate(prediction);
        let json = msg.to_json()?;
        
        if let Err(e) = self.broadcast_tx.send(msg) {
            tracing::warn!("Failed to broadcast prediction: {}", e);
        }
        
        Ok(())
    }

    pub async fn broadcast_recommendations(&self, recommendations: Vec<CryptoRecommendation>) -> Result<()> {
        let msg = WebSocketMessage::RecommendationUpdate(recommendations);
        let json = msg.to_json()?;
        
        if let Err(e) = self.broadcast_tx.send(msg) {
            tracing::warn!("Failed to broadcast recommendations: {}", e);
        }
        
        Ok(())
    }

    pub async fn broadcast_price_update(&self, symbol: String, price: f64, change_24h: f64) -> Result<()> {
        let msg = WebSocketMessage::PriceUpdate { symbol, price, change_24h };
        
        if let Err(e) = self.broadcast_tx.send(msg) {
            tracing::warn!("Failed to broadcast price update: {}", e);
        }
        
        Ok(())
    }

    pub async fn broadcast_options_update(&self, symbol: String, analysis: OptionsAnalysisResponse) -> Result<()> {
        let msg = WebSocketMessage::OptionsUpdate { symbol, analysis };
        
        if let Err(e) = self.broadcast_tx.send(msg) {
            tracing::warn!("Failed to broadcast options update: {}", e);
        }
        
        Ok(())
    }

    pub async fn broadcast_forex_update(&self, pair: String, analysis: ForexAnalysisResponse) -> Result<()> {
        let msg = WebSocketMessage::ForexUpdate { pair, analysis };
        
        if let Err(e) = self.broadcast_tx.send(msg) {
            tracing::warn!("Failed to broadcast forex update: {}", e);
        }
        
        Ok(())
    }

    pub async fn broadcast_sentiment_update(&self, symbol: String, analysis: SentimentAnalysisResponse) -> Result<()> {
        let msg = WebSocketMessage::SentimentUpdate { symbol, analysis };
        
        if let Err(e) = self.broadcast_tx.send(msg) {
            tracing::warn!("Failed to broadcast sentiment update: {}", e);
        }
        
        Ok(())
    }

    pub async fn broadcast_correlation_update(
        &self,
        primary: String,
        secondary: String,
        analysis: CorrelationAnalysisResponse,
    ) -> Result<()> {
        let msg = WebSocketMessage::CorrelationUpdate { primary, secondary, analysis };
        
        if let Err(e) = self.broadcast_tx.send(msg) {
            tracing::warn!("Failed to broadcast correlation update: {}", e);
        }
        
        Ok(())
    }

    pub async fn get_client_count(&self) -> usize {
        self.clients.read().await.len()
    }

    pub async fn start_heartbeat(&self) {
        let broadcast_tx = self.broadcast_tx.clone();
        
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(30));
            
            loop {
                interval.tick().await;
                
                let heartbeat = WebSocketMessage::Heartbeat;
                if let Err(e) = broadcast_tx.send(heartbeat) {
                    tracing::warn!("Failed to send heartbeat: {}", e);
                }
            }
        });
    }
}
