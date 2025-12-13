// src/cross_asset.rs
// Cross-Asset Fusion Engine
// Unified multi-market signals (BTC, SPX, GLD, DXY, VIX)

use std::collections::HashMap;
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};
use std::sync::Arc;
use tokio::sync::RwLock;
use rust_decimal::prelude::ToPrimitive;

use crate::regime::{MarketRegimeEngine, SimpleMarketRegime};
use crate::alpha_oracle::AlphaOracle;
use crate::market_data::provider::MarketDataProvider;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssetSignal {
    pub symbol: String,
    pub asset_class: AssetClass,
    pub alpha_score: f64,
    pub conviction: String,
    pub regime_alignment: f64, // How well aligned with current regime
    pub correlation_with_primary: f64, // Correlation with primary asset (e.g., SPX)
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum AssetClass {
    Equity,
    Crypto,
    Commodity,
    Currency,
    Volatility,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrossAssetSignal {
    pub primary_asset: String, // e.g., "SPX"
    pub regime: SimpleMarketRegime,
    pub asset_signals: Vec<AssetSignal>,
    pub fusion_recommendation: FusionRecommendation,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FusionRecommendation {
    pub action: String, // e.g., "When gold breaks out in Risk-Off, buy SPX puts"
    pub confidence: f64,
    pub reasoning: String,
    pub suggested_trades: Vec<SuggestedTrade>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SuggestedTrade {
    pub symbol: String,
    pub direction: String, // "long" | "short"
    pub strategy_type: String,
    pub reasoning: String,
    pub confidence: f64,
}

pub struct CrossAssetFusionEngine {
    market_provider: Arc<dyn MarketDataProvider>,
    regime_engine: MarketRegimeEngine,
    alpha_oracle: AlphaOracle,
    asset_configs: HashMap<String, AssetConfig>,
}

#[derive(Debug, Clone)]
struct AssetConfig {
    symbol: String,
    asset_class: AssetClass,
    regime_multipliers: HashMap<String, f64>, // regime mood -> multiplier
}

impl CrossAssetFusionEngine {
    pub fn new(
        market_provider: Arc<dyn MarketDataProvider>,
        regime_engine: MarketRegimeEngine,
        alpha_oracle: AlphaOracle,
    ) -> Self {
        let mut asset_configs = HashMap::new();

        // SPX (Equity)
        let mut spx_multipliers = HashMap::new();
        spx_multipliers.insert("Greed".to_string(), 1.2);
        spx_multipliers.insert("Euphoria".to_string(), 1.3);
        spx_multipliers.insert("Panic".to_string(), 0.5);
        spx_multipliers.insert("Fear".to_string(), 0.7);
        asset_configs.insert("SPX".to_string(), AssetConfig {
            symbol: "SPX".to_string(),
            asset_class: AssetClass::Equity,
            regime_multipliers: spx_multipliers,
        });

        // BTC (Crypto)
        let mut btc_multipliers = HashMap::new();
        btc_multipliers.insert("Greed".to_string(), 1.4);
        btc_multipliers.insert("Euphoria".to_string(), 1.5);
        btc_multipliers.insert("Panic".to_string(), 0.3);
        btc_multipliers.insert("Fear".to_string(), 0.6);
        asset_configs.insert("BTC".to_string(), AssetConfig {
            symbol: "BTC".to_string(),
            asset_class: AssetClass::Crypto,
            regime_multipliers: btc_multipliers,
        });

        // GLD (Gold/Commodity)
        let mut gld_multipliers = HashMap::new();
        gld_multipliers.insert("Panic".to_string(), 1.3);
        gld_multipliers.insert("Fear".to_string(), 1.2);
        gld_multipliers.insert("Greed".to_string(), 0.8);
        gld_multipliers.insert("Euphoria".to_string(), 0.7);
        asset_configs.insert("GLD".to_string(), AssetConfig {
            symbol: "GLD".to_string(),
            asset_class: AssetClass::Commodity,
            regime_multipliers: gld_multipliers,
        });

        // DXY (Dollar Index)
        let mut dxy_multipliers = HashMap::new();
        dxy_multipliers.insert("Panic".to_string(), 1.2);
        dxy_multipliers.insert("Fear".to_string(), 1.1);
        dxy_multipliers.insert("Greed".to_string(), 0.9);
        asset_configs.insert("DXY".to_string(), AssetConfig {
            symbol: "DXY".to_string(),
            asset_class: AssetClass::Currency,
            regime_multipliers: dxy_multipliers,
        });

        // VIX (Volatility)
        let mut vix_multipliers = HashMap::new();
        vix_multipliers.insert("Panic".to_string(), 1.5);
        vix_multipliers.insert("Fear".to_string(), 1.3);
        vix_multipliers.insert("Greed".to_string(), 0.6);
        vix_multipliers.insert("Euphoria".to_string(), 0.5);
        asset_configs.insert("VIX".to_string(), AssetConfig {
            symbol: "VIX".to_string(),
            asset_class: AssetClass::Volatility,
            regime_multipliers: vix_multipliers,
        });

        Self {
            market_provider,
            regime_engine,
            alpha_oracle,
            asset_configs,
        }
    }

    /// Generate cross-asset fusion signal
    pub async fn generate_fusion_signal(
        &self,
        primary_asset: &str, // e.g., "SPX" or "EURUSD"
    ) -> anyhow::Result<CrossAssetSignal> {
        // Get current regime (analyze_simple now degrades gracefully if SPY missing)
        let regime = self.regime_engine.analyze_simple().await?;

        // Get signals for all tracked assets
        let mut asset_signals = Vec::new();
        let tracked_assets = vec!["SPX", "BTC", "GLD", "DXY", "VIX"];

        for symbol in &tracked_assets {
            if let Some(config) = self.asset_configs.get(*symbol) {
                // Build features for AlphaOracle
                let mut features = HashMap::new();
                
                // Try to get price from provider
                if let Ok(quote) = self.market_provider.latest_quote(symbol).await {
                    features.insert("price_usd".to_string(), quote.mid().to_f64().unwrap_or(100.0));
                } else {
                    // Fallback
                    features.insert("price_usd".to_string(), 100.0);
                }
                features.insert("volatility".to_string(), 0.2);
                features.insert("rsi".to_string(), 50.0);
                features.insert("momentum_24h".to_string(), 0.0);
                features.insert("market_cap_rank".to_string(), 999.0);
                features.insert("risk_score".to_string(), 0.5);

                // Get alpha signal
                let alpha = self.alpha_oracle.generate_signal(symbol, &features).await?;

                // Apply regime multiplier
                let regime_multiplier = config.regime_multipliers
                    .get(&regime.mood)
                    .copied()
                    .unwrap_or(1.0);
                let adjusted_alpha = alpha.alpha_score * regime_multiplier;

                // Calculate correlation with primary (simplified)
                let correlation = if *symbol == primary_asset {
                    1.0
                } else {
                    // In production, calculate real correlation
                    match (*symbol, primary_asset) {
                        ("BTC", "SPX") | ("SPX", "BTC") => 0.6,
                        ("GLD", "SPX") | ("SPX", "GLD") => -0.2,
                        ("DXY", "SPX") | ("SPX", "DXY") => -0.3,
                        ("VIX", "SPX") | ("SPX", "VIX") => -0.7,
                        _ => 0.0,
                    }
                };

                asset_signals.push(AssetSignal {
                    symbol: symbol.to_string(),
                    asset_class: config.asset_class.clone(),
                    alpha_score: adjusted_alpha,
                    conviction: alpha.conviction,
                    regime_alignment: regime_multiplier,
                    correlation_with_primary: correlation,
                    timestamp: Utc::now(),
                });
            }
        }

        // Generate fusion recommendation
        let fusion = self.generate_fusion_recommendation(&regime, &asset_signals, primary_asset)?;

        Ok(CrossAssetSignal {
            primary_asset: primary_asset.to_string(),
            regime,
            asset_signals,
            fusion_recommendation: fusion,
            timestamp: Utc::now(),
        })
    }

    fn generate_fusion_recommendation(
        &self,
        regime: &SimpleMarketRegime,
        signals: &[AssetSignal],
        primary: &str,
    ) -> anyhow::Result<FusionRecommendation> {
        let mut suggested_trades = Vec::new();
        let mut reasoning_parts = Vec::new();

        // Example fusion logic: "When gold breaks out in Risk-Off, buy SPX puts"
        if regime.mood == "Panic" || regime.mood == "Fear" {
            // Find GLD signal
            if let Some(gld) = signals.iter().find(|s| s.symbol == "GLD") {
                if gld.alpha_score > 7.0 {
                    reasoning_parts.push(format!(
                        "Gold (GLD) is strong (alpha {:.1}) in {} regime",
                        gld.alpha_score,
                        regime.mood
                    ));

                    // Suggest SPX puts
                    if let Some(spx) = signals.iter().find(|s| s.symbol == "SPX") {
                        if spx.alpha_score < 5.0 {
                            suggested_trades.push(SuggestedTrade {
                                symbol: "SPX".to_string(),
                                direction: "short".to_string(),
                                strategy_type: "Long Put".to_string(),
                                reasoning: format!(
                                    "SPX weak (alpha {:.1}) while gold strong in {} regime",
                                    spx.alpha_score,
                                    regime.mood
                                ),
                                confidence: 0.75,
                            });
                        }
                    }
                }
            }

            // VIX spike in panic
            if let Some(vix) = signals.iter().find(|s| s.symbol == "VIX") {
                if vix.alpha_score > 8.0 && regime.mood == "Panic" {
                    reasoning_parts.push("VIX spiking in panic regime".to_string());
                    suggested_trades.push(SuggestedTrade {
                        symbol: "SPX".to_string(),
                        direction: "short".to_string(),
                        strategy_type: "Long Put".to_string(),
                        reasoning: "VIX spike indicates continued volatility".to_string(),
                        confidence: 0.8,
                    });
                }
            }
        }

        // Risk-on fusion: BTC + SPX correlation
        if regime.mood == "Greed" || regime.mood == "Euphoria" {
            if let (Some(btc), Some(spx)) = (
                signals.iter().find(|s| s.symbol == "BTC"),
                signals.iter().find(|s| s.symbol == "SPX"),
            ) {
                if btc.alpha_score > 7.0 && spx.alpha_score > 6.0 {
                    reasoning_parts.push(format!(
                        "BTC and SPX both strong (alpha {:.1} / {:.1}) in {} regime",
                        btc.alpha_score,
                        spx.alpha_score,
                        regime.mood
                    ));
                    suggested_trades.push(SuggestedTrade {
                        symbol: "SPX".to_string(),
                        direction: "long".to_string(),
                        strategy_type: "Long Call".to_string(),
                        reasoning: "Risk-on correlation: BTC and SPX aligned".to_string(),
                        confidence: 0.7,
                    });
                }
            }
        }

        let action = if !reasoning_parts.is_empty() {
            format!("{} regime: {}", regime.mood, reasoning_parts.join(" • "))
        } else {
            format!("{} regime: No strong cross-asset signals", regime.mood)
        };

        let confidence = if !suggested_trades.is_empty() {
            suggested_trades.iter().map(|t| t.confidence).sum::<f64>() / suggested_trades.len() as f64
        } else {
            0.5
        };

        Ok(FusionRecommendation {
            action,
            confidence,
            reasoning: reasoning_parts.join(" • "),
            suggested_trades,
        })
    }
}

