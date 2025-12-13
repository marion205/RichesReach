use std::{collections::HashMap, sync::Arc};
use chrono::Utc;
use serde::{Deserialize, Serialize};

use crate::alpha_oracle::{AlphaOracle, AlphaSignal};
use crate::position_sizing::{PositionSizingDecision, PositionSizingEngine};
use crate::regime::{MarketRegimeEngine, SimpleMarketRegime};
use crate::risk_guard::{RiskGuard, RiskGuardDecision};
use crate::feature_sources::{AssetClass, FeatureSource};
use crate::market_data::provider::MarketDataProvider;
use crate::options_edge::{EdgeForecastResponse, OptionsEdgeForecaster};
use anyhow::Result;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnifiedSignal {
    pub symbol: String,
    pub asset_class: AssetClass,

    pub regime: SimpleMarketRegime,
    pub alpha: AlphaSignal,

    pub position_sizing: Option<PositionSizingDecision>,
    pub risk_guard: Option<RiskGuardDecision>,

    pub options_forecast: Option<EdgeForecastResponse>,

    pub one_sentence: String,
    pub emoji: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnifiedSignalRequest {
    pub symbol: String,
    pub equity: Option<f64>,
    pub entry_price: Option<f64>,
    pub open_positions: Option<u32>,
    pub force_asset_class: Option<AssetClass>,
}

pub struct UnifiedAssetOracle {
    market: Arc<dyn MarketDataProvider>,
    regime: MarketRegimeEngine,
    alpha: AlphaOracle,
    sizing: PositionSizingEngine,
    risk: RiskGuard,
    stock_features: Arc<dyn FeatureSource>,
    crypto_features: Arc<dyn FeatureSource>,
    forex_features: Arc<dyn FeatureSource>,
    options_features: Arc<dyn FeatureSource>,
    options_forecaster: Option<Arc<OptionsEdgeForecaster>>,
}

impl UnifiedAssetOracle {
    pub fn new(
        market: Arc<dyn MarketDataProvider>,
        regime: MarketRegimeEngine,
        alpha: AlphaOracle,
        sizing: PositionSizingEngine,
        risk: RiskGuard,
        stock_features: Arc<dyn FeatureSource>,
        crypto_features: Arc<dyn FeatureSource>,
        forex_features: Arc<dyn FeatureSource>,
        options_features: Arc<dyn FeatureSource>,
        options_forecaster: Option<Arc<OptionsEdgeForecaster>>,
    ) -> Self {
        Self {
            market,
            regime,
            alpha,
            sizing,
            risk,
            stock_features,
            crypto_features,
            forex_features,
            options_features,
            options_forecaster,
        }
    }

    pub async fn signal(&self, req: UnifiedSignalRequest) -> Result<UnifiedSignal> {
        let symbol = req.symbol.trim().to_uppercase();
        let asset_class = req
            .force_asset_class
            .unwrap_or_else(|| Self::detect_asset_class(&symbol));

        let regime = self.regime.analyze_simple().await?;
        let features = self.build_features(asset_class, &symbol).await?;
        let alpha = self.alpha.generate_signal(&symbol, &features).await?;

        let options_forecast = if asset_class == AssetClass::Options {
            if let Some(forecaster) = &self.options_forecaster {
                forecaster.forecast_edges(&symbol).await.ok()
            } else {
                None
            }
        } else {
            None
        };

        let (position_sizing, risk_guard) = match (req.equity, req.entry_price) {
            (Some(equity), Some(entry_price)) if equity > 0.0 && entry_price > 0.0 => {
                let sizing = self.sizing.size_position(&alpha, equity, entry_price);
                let open_positions_vec = vec![]; // Placeholder for actual open positions
                let guard = self.risk.evaluate(equity, &open_positions_vec, &sizing);
                (Some(sizing), Some(guard))
            }
            _ => (None, None),
        };

        let mut one_sentence = alpha.one_sentence.clone();
        if let Some(fc) = &options_forecast {
            if let Some(best) = fc.one_tap_trades.first() {
                one_sentence = format!("{} → One-tap {} is ready.", one_sentence, best.strategy);
            }
        }

        Ok(UnifiedSignal {
            symbol: symbol.clone(),
            asset_class,
            regime,
            alpha: alpha.clone(),
            position_sizing,
            risk_guard,
            options_forecast,
            one_sentence,
            emoji: Self::conviction_to_emoji(&alpha.conviction),
            timestamp: Utc::now(),
        })
    }

    async fn build_features(&self, asset: AssetClass, symbol: &str) -> Result<HashMap<String, f64>> {
        let mut f = match asset {
            AssetClass::Stock => self.stock_features.build_features(symbol).await?,
            AssetClass::Crypto => self.crypto_features.build_features(symbol).await?,
            AssetClass::Forex => self.forex_features.build_features(symbol).await?,
            AssetClass::Options => self.options_features.build_features(symbol).await?,
            _ => anyhow::bail!("Unsupported asset class for feature building"),
        };

        f.insert("asset_class_stock".to_string(), (asset == AssetClass::Stock) as i32 as f64);
        f.insert("asset_class_crypto".to_string(), (asset == AssetClass::Crypto) as i32 as f64);
        f.insert("asset_class_forex".to_string(), (asset == AssetClass::Forex) as i32 as f64);
        f.insert("asset_class_options".to_string(), (asset == AssetClass::Options) as i32 as f64);

        Ok(f)
    }

    fn detect_asset_class(symbol: &str) -> AssetClass {
        if symbol.len() == 6 && symbol.chars().all(|c| c.is_ascii_uppercase()) {
            return AssetClass::Forex;
        }

        let crypto_like = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "BNB"];
        if crypto_like.contains(&symbol) || symbol.contains('-') {
            return AssetClass::Crypto;
        }

        if symbol.contains('C') || symbol.contains('P') {
            if symbol.chars().any(|c| c.is_ascii_digit()) && symbol.contains(' ') {
                return AssetClass::Options;
            }
        }

        AssetClass::Stock
    }

    fn conviction_to_emoji(conviction: &str) -> String {
        match conviction.to_uppercase().as_str() {
            "STRONG BUY" => "🚀".to_string(),
            "BUY" => "💎".to_string(),
            "WEAK BUY" => "📈".to_string(),
            "NEUTRAL" => "🔎".to_string(),
            "DUMP" | "SELL" => "☠️".to_string(),
            _ => "⚠️".to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::market_data::in_memory::InMemoryProvider;
    use crate::stock_analysis::StockAnalysisEngine;
    use crate::crypto_analysis::CryptoAnalysisEngine;
    use crate::forex_analysis::ForexAnalysisEngine;
    use crate::regime::MarketRegimeEngine;
    use crate::alpha_oracle::AlphaOracle;
    use crate::position_sizing::{PositionSizingEngine, PositionSizingConfig};
    use crate::risk_guard::{RiskGuard, RiskGuardConfig};

    #[tokio::test]
    async fn test_detect_asset_class() {
        assert_eq!(UnifiedAssetOracle::detect_asset_class("EURUSD"), AssetClass::Forex);
        assert_eq!(UnifiedAssetOracle::detect_asset_class("GBPUSD"), AssetClass::Forex);
        assert_eq!(UnifiedAssetOracle::detect_asset_class("BTC"), AssetClass::Crypto);
        assert_eq!(UnifiedAssetOracle::detect_asset_class("ETH"), AssetClass::Crypto);
        assert_eq!(UnifiedAssetOracle::detect_asset_class("AAPL"), AssetClass::Stock);
        assert_eq!(UnifiedAssetOracle::detect_asset_class("MSFT"), AssetClass::Stock);
    }

    #[test]
    fn test_conviction_to_emoji() {
        assert_eq!(UnifiedAssetOracle::conviction_to_emoji("STRONG BUY"), "🚀");
        assert_eq!(UnifiedAssetOracle::conviction_to_emoji("BUY"), "💎");
        assert_eq!(UnifiedAssetOracle::conviction_to_emoji("WEAK BUY"), "📈");
        assert_eq!(UnifiedAssetOracle::conviction_to_emoji("NEUTRAL"), "🔎");
        assert_eq!(UnifiedAssetOracle::conviction_to_emoji("SELL"), "☠️");
        assert_eq!(UnifiedAssetOracle::conviction_to_emoji("DUMP"), "☠️");
        assert_eq!(UnifiedAssetOracle::conviction_to_emoji("UNKNOWN"), "⚠️");
    }

    #[tokio::test]
    async fn test_unified_signal_stock() {
        let market_provider = Arc::new(InMemoryProvider::new());
        let market_ingest: Arc<dyn crate::market_data::provider::MarketDataIngest> = market_provider.clone();
        
        // Seed SPY data for regime engine
        let spy_quote = crate::market_data::provider::Quote {
            symbol: std::sync::Arc::from("SPY"),
            ts: chrono::Utc::now(),
            bid: rust_decimal::Decimal::from(400),
            ask: rust_decimal::Decimal::from(400),
        };
        market_ingest.ingest_quote(spy_quote).await.unwrap();
        
        let regime = MarketRegimeEngine::new(market_provider.clone());
        let alpha = AlphaOracle::new(market_provider.clone());
        let sizing = PositionSizingEngine::new(PositionSizingConfig::default());
        let risk = RiskGuard::new(RiskGuardConfig::default());

        let stock_features = Arc::new(StockAnalysisEngine::new());
        let crypto_features = Arc::new(CryptoAnalysisEngine::new());
        let forex_features = Arc::new(ForexAnalysisEngine::new(market_provider.clone()));
        let options_provider = Arc::new(crate::market_data::in_memory_options::InMemoryOptionsProvider::new());
        let options_forecaster = Arc::new(crate::options_edge::OptionsEdgeForecaster::new(
            market_provider.clone(),
            options_provider.clone(),
            AlphaOracle::new(market_provider.clone()),
            MarketRegimeEngine::new(market_provider.clone()),
        ));
        let options_features = Arc::new(crate::options_feature_source::OptionsFeatureSource::new(
            options_forecaster,
        ));

        let oracle = UnifiedAssetOracle::new(
            market_provider.clone(),
            regime,
            alpha,
            sizing,
            risk,
            stock_features,
            crypto_features,
            forex_features,
            options_features,
            None,
        );

        let req = UnifiedSignalRequest {
            symbol: "AAPL".to_string(),
            equity: Some(10000.0),
            entry_price: Some(150.0),
            open_positions: None,
            force_asset_class: None,
        };

        let signal = oracle.signal(req).await.unwrap();
        assert_eq!(signal.symbol, "AAPL");
        assert_eq!(signal.asset_class, AssetClass::Stock);
        assert!(!signal.one_sentence.is_empty());
        assert!(!signal.emoji.is_empty());
    }

    #[tokio::test]
    async fn test_unified_signal_crypto() {
        let market_provider = Arc::new(InMemoryProvider::new());
        let market_ingest: Arc<dyn crate::market_data::provider::MarketDataIngest> = market_provider.clone();
        
        // Seed SPY data for regime engine
        let spy_quote = crate::market_data::provider::Quote {
            symbol: std::sync::Arc::from("SPY"),
            ts: chrono::Utc::now(),
            bid: rust_decimal::Decimal::from(400),
            ask: rust_decimal::Decimal::from(400),
        };
        market_ingest.ingest_quote(spy_quote).await.unwrap();
        
        let regime = MarketRegimeEngine::new(market_provider.clone());
        let alpha = AlphaOracle::new(market_provider.clone());
        let sizing = PositionSizingEngine::new(PositionSizingConfig::default());
        let risk = RiskGuard::new(RiskGuardConfig::default());

        let stock_features = Arc::new(StockAnalysisEngine::new());
        let crypto_features = Arc::new(CryptoAnalysisEngine::new());
        let forex_features = Arc::new(ForexAnalysisEngine::new(market_provider.clone()));
        let options_provider = Arc::new(crate::market_data::in_memory_options::InMemoryOptionsProvider::new());
        let options_forecaster = Arc::new(crate::options_edge::OptionsEdgeForecaster::new(
            market_provider.clone(),
            options_provider.clone(),
            AlphaOracle::new(market_provider.clone()),
            MarketRegimeEngine::new(market_provider.clone()),
        ));
        let options_features = Arc::new(crate::options_feature_source::OptionsFeatureSource::new(
            options_forecaster,
        ));

        let oracle = UnifiedAssetOracle::new(
            market_provider.clone(),
            regime,
            alpha,
            sizing,
            risk,
            stock_features,
            crypto_features,
            forex_features,
            options_features,
            None,
        );

        let req = UnifiedSignalRequest {
            symbol: "BTC".to_string(),
            equity: None,
            entry_price: None,
            open_positions: None,
            force_asset_class: None,
        };

        let signal = oracle.signal(req).await.unwrap();
        assert_eq!(signal.symbol, "BTC");
        assert_eq!(signal.asset_class, AssetClass::Crypto);
    }

    #[tokio::test]
    async fn test_unified_signal_forex() {
        let market_provider = Arc::new(InMemoryProvider::new());
        let market_ingest: Arc<dyn crate::market_data::provider::MarketDataIngest> = market_provider.clone();
        
        // Seed SPY data for regime engine
        let spy_quote = crate::market_data::provider::Quote {
            symbol: std::sync::Arc::from("SPY"),
            ts: chrono::Utc::now(),
            bid: rust_decimal::Decimal::from(400),
            ask: rust_decimal::Decimal::from(400),
        };
        market_ingest.ingest_quote(spy_quote).await.unwrap();
        
        let regime = MarketRegimeEngine::new(market_provider.clone());
        let alpha = AlphaOracle::new(market_provider.clone());
        let sizing = PositionSizingEngine::new(PositionSizingConfig::default());
        let risk = RiskGuard::new(RiskGuardConfig::default());

        let stock_features = Arc::new(StockAnalysisEngine::new());
        let crypto_features = Arc::new(CryptoAnalysisEngine::new());
        let forex_features = Arc::new(ForexAnalysisEngine::new(market_provider.clone()));
        let options_provider = Arc::new(crate::market_data::in_memory_options::InMemoryOptionsProvider::new());
        let options_forecaster = Arc::new(crate::options_edge::OptionsEdgeForecaster::new(
            market_provider.clone(),
            options_provider.clone(),
            AlphaOracle::new(market_provider.clone()),
            MarketRegimeEngine::new(market_provider.clone()),
        ));
        let options_features = Arc::new(crate::options_feature_source::OptionsFeatureSource::new(
            options_forecaster,
        ));

        let oracle = UnifiedAssetOracle::new(
            market_provider.clone(),
            regime,
            alpha,
            sizing,
            risk,
            stock_features,
            crypto_features,
            forex_features,
            options_features,
            None,
        );

        let req = UnifiedSignalRequest {
            symbol: "EURUSD".to_string(),
            equity: None,
            entry_price: None,
            open_positions: None,
            force_asset_class: None,
        };

        let signal = oracle.signal(req).await.unwrap();
        assert_eq!(signal.symbol, "EURUSD");
        assert_eq!(signal.asset_class, AssetClass::Forex);
    }

    #[tokio::test]
    async fn test_unified_signal_with_position_sizing() {
        let market_provider = Arc::new(InMemoryProvider::new());
        let market_ingest: Arc<dyn crate::market_data::provider::MarketDataIngest> = market_provider.clone();
        
        // Seed SPY data for regime engine
        let spy_quote = crate::market_data::provider::Quote {
            symbol: std::sync::Arc::from("SPY"),
            ts: chrono::Utc::now(),
            bid: rust_decimal::Decimal::from(400),
            ask: rust_decimal::Decimal::from(400),
        };
        market_ingest.ingest_quote(spy_quote).await.unwrap();
        
        let regime = MarketRegimeEngine::new(market_provider.clone());
        let alpha = AlphaOracle::new(market_provider.clone());
        let sizing = PositionSizingEngine::new(PositionSizingConfig::default());
        let risk = RiskGuard::new(RiskGuardConfig::default());

        let stock_features = Arc::new(StockAnalysisEngine::new());
        let crypto_features = Arc::new(CryptoAnalysisEngine::new());
        let forex_features = Arc::new(ForexAnalysisEngine::new(market_provider.clone()));
        let options_provider = Arc::new(crate::market_data::in_memory_options::InMemoryOptionsProvider::new());
        let options_forecaster = Arc::new(crate::options_edge::OptionsEdgeForecaster::new(
            market_provider.clone(),
            options_provider.clone(),
            AlphaOracle::new(market_provider.clone()),
            MarketRegimeEngine::new(market_provider.clone()),
        ));
        let options_features = Arc::new(crate::options_feature_source::OptionsFeatureSource::new(
            options_forecaster,
        ));

        let oracle = UnifiedAssetOracle::new(
            market_provider.clone(),
            regime,
            alpha,
            sizing,
            risk,
            stock_features,
            crypto_features,
            forex_features,
            options_features,
            None,
        );

        let req = UnifiedSignalRequest {
            symbol: "AAPL".to_string(),
            equity: Some(50000.0),
            entry_price: Some(175.0),
            open_positions: Some(3),
            force_asset_class: Some(AssetClass::Stock),
        };

        let signal = oracle.signal(req).await.unwrap();
        assert!(signal.position_sizing.is_some());
        assert!(signal.risk_guard.is_some());
    }
}
