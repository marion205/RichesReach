// src/analysis/forex.rs
use crate::market_data::provider::MarketDataProvider;
use crate::utils::stats::{daily_mid_prices, atr};
use chrono::{Utc, Duration};
use rust_decimal::Decimal;
use rust_decimal::prelude::ToPrimitive;
use serde::{Serialize, Deserialize};
use anyhow::Result;
use std::sync::Arc;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ForexAnalysisResponse {
    pub pair: String,
    pub bid: Decimal,
    pub ask: Decimal,
    pub spread_bps: f64,
    pub atr_14: f64,
    pub trend: String,
    pub support: Decimal,
    pub resistance: Decimal,
    pub timestamp: chrono::DateTime<Utc>,
}

pub struct ForexAnalysisEngine {
    provider: Arc<dyn MarketDataProvider>,
}

impl ForexAnalysisEngine {
    pub fn new(provider: Arc<dyn MarketDataProvider>) -> Self {
        Self { provider }
    }

    pub async fn analyze(&self, pair: &str) -> Result<ForexAnalysisResponse> {
        let start = std::time::Instant::now();

        let (ts, bid, ask) = self.provider.get_latest_fx(pair).await?;

        let mid = (bid + ask) / Decimal::TWO;
        let spread_bps = ((ask - bid) / mid * Decimal::from(10_000))
            .to_f64().unwrap_or(0.0);

        // fetch 30 days
        let end = Utc::now();
        let start_time = end - Duration::days(30);
        let fx = self.provider.get_fx_history(pair, start_time, end).await?;

        let daily = daily_mid_prices(&fx)?;
        let atr_14 = atr(&daily, 14)?;

        let trend = self.calc_trend(&daily)?;
        let (support, resistance) = self.calc_pivots(&daily)?;

        let response = ForexAnalysisResponse {
            pair: pair.into(),
            bid,
            ask,
            spread_bps,
            atr_14,
            trend,
            support,
            resistance,
            timestamp: Utc::now(),
        };

        tracing::info!("Forex analysis completed for {} in {:?}", pair, start.elapsed());
        Ok(response)
    }

    fn calc_trend(&self, daily: &[(f64, f64, f64)]) -> Result<String> {
        if daily.len() < 20 { return Ok("SIDEWAYS".into()); }

        let closes: Vec<f64> = daily.iter().map(|(_, _, c)| *c).collect();
        let recent = closes[closes.len()-10..].iter().sum::<f64>() / 10.0;
        let older = closes[closes.len()-20..closes.len()-10].iter().sum::<f64>() / 10.0;

        Ok(if recent > older * 1.001 {
            "BULLISH".into()
        } else if recent < older * 0.999 {
            "BEARISH".into()
        } else {
            "SIDEWAYS".into()
        })
    }

    fn calc_pivots(&self, daily: &[(f64, f64, f64)]) -> Result<(Decimal, Decimal)> {
        if daily.len() < 2 {
            return Err(anyhow::anyhow!("not enough data for pivots"));
        }

        let (h, l, c) = daily[daily.len() - 2];
        let pivot = (h + l + c) / 3.0;

        let r1 = 2.0 * pivot - l;
        let s1 = 2.0 * pivot - h;

        Ok((
            Decimal::from_f64_retain(s1).unwrap_or_default(),
            Decimal::from_f64_retain(r1).unwrap_or_default(),
        ))
    }
}
