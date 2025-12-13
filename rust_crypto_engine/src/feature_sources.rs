use std::collections::HashMap;
use anyhow::Result;
use async_trait::async_trait;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AssetClass {
    Stock,
    Crypto,
    Forex,
    Options,
}

#[async_trait]
pub trait FeatureSource: Send + Sync {
    fn asset_class(&self) -> AssetClass;
    async fn build_features(&self, symbol: &str) -> Result<HashMap<String, f64>>;
}

