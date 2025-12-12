use std::collections::{HashMap, BTreeMap};
use chrono::{DateTime, Duration, NaiveDate, Utc};
use rust_decimal::Decimal;
use rust_decimal::prelude::ToPrimitive;
use anyhow::{Result, Context, bail};
use serde::{Serialize, Deserialize};

/// Market regime classification for global market context
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum GlobalRegime {
    EquityRiskOn,
    EquityRiskOff,
    CryptoAltSeason,
    CryptoBtcDominance,
    Neutral,
}

/// Local context for individual tickers (decoupling / name-specific edge)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum LocalContext {
    IdiosyncraticBreakout,
    ChoppyMeanRevert,
    Normal,
}

/// Complete market regime analysis response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorrelationAnalysisResponse {
    pub primary_symbol: String,
    pub secondary_symbol: String,
    pub correlation_1d: f64,
    pub correlation_7d: f64,
    pub correlation_30d: f64,
    pub btc_dominance: Option<f64>,
    pub spy_correlation: Option<f64>,
    pub global_regime: GlobalRegime,
    pub local_context: LocalContext,
    pub timestamp: chrono::DateTime<Utc>,
}

/// Production-grade correlation analysis engine
/// Uses real price history to compute correlations and classify market regimes
pub struct CorrelationAnalysisEngine {
    /// Price history: symbol -> [(timestamp, price), ...]
    /// Assumes prices are ingested regularly (daily closes or intraday snapshots)
    price_history: tokio::sync::RwLock<HashMap<String, Vec<(DateTime<Utc>, Decimal)>>>,
}

impl CorrelationAnalysisEngine {
    pub fn new() -> Self {
        Self {
            price_history: tokio::sync::RwLock::new(HashMap::new()),
        }
    }

    /// Ingest a new price tick (e.g., daily close or intraday snapshot).
    /// Call this from your price feed service to populate history.
    pub async fn ingest_price(
        &self,
        symbol: &str,
        timestamp: DateTime<Utc>,
        price: Decimal,
    ) {
        let mut history = self.price_history.write().await;
        let entry = history.entry(symbol.to_string()).or_default();
        entry.push((timestamp, price));
        
        // Keep only last 90 days of history to manage memory
        let cutoff = Utc::now() - Duration::days(90);
        entry.retain(|(ts, _)| *ts >= cutoff);
    }

    /// Get current market regime snapshot for a symbol (uses SPY as default secondary)
    pub async fn current_regime(
        &self,
        symbol: &str,
        secondary: Option<&str>
    ) -> Option<CorrelationAnalysisResponse> {
        match self.analyze(symbol, secondary).await {
            Ok(response) => Some(response),
            Err(_) => None,
        }
    }

    /// Main analysis method: computes correlations and classifies regime
    pub async fn analyze(
        &self,
        primary: &str,
        secondary: Option<&str>
    ) -> Result<CorrelationAnalysisResponse> {
        let start = std::time::Instant::now();

        // Default secondary to SPY if not provided
        let secondary = secondary.unwrap_or("SPY");

        // Calculate correlations for different timeframes
        let correlation_1d = self.calculate_correlation(primary, secondary, 1).await?;
        let correlation_7d = self.calculate_correlation(primary, secondary, 7).await?;
        let correlation_30d = self.calculate_correlation(primary, secondary, 30).await?;

        // Calculate BTC dominance if primary is crypto
        let btc_dominance = if self.is_crypto(primary) {
            Some(self.calculate_btc_dominance(30).await?)
        } else {
            None
        };

        // Calculate SPY correlation if not already calculated
        let spy_correlation = if secondary != "SPY" {
            Some(self.calculate_correlation(primary, "SPY", 30).await?)
        } else {
            Some(correlation_30d)
        };

        // Determine global market regime using both short + long horizon
        let global_regime = self
            .determine_global_regime(correlation_1d, correlation_7d, correlation_30d, btc_dominance)
            .await?;

        // Determine local context (per-ticker decoupling analysis)
        let local_context = self
            .determine_local_context(correlation_1d, correlation_7d, correlation_30d)
            .await?;

        let response = CorrelationAnalysisResponse {
            primary_symbol: primary.to_string(),
            secondary_symbol: secondary.to_string(),
            correlation_1d,
            correlation_7d,
            correlation_30d,
            btc_dominance,
            spy_correlation,
            global_regime,
            local_context,
            timestamp: Utc::now(),
        };

        tracing::info!(
            "Correlation analysis completed for {} vs {} in {:?}",
            primary,
            secondary,
            start.elapsed()
        );
        Ok(response)
    }

    /// Production-style correlation calculation:
    /// - Filter history to [now - days, now]
    /// - Aggregate to daily closes
    /// - Compute log returns
    /// - Compute Pearson correlation over returns
    async fn calculate_correlation(
        &self,
        symbol1: &str,
        symbol2: &str,
        days: i32,
    ) -> Result<f64> {
        let history = self.price_history.read().await;
        let now = Utc::now();
        let cutoff = now - Duration::days(days.into());

        let series1 = history
            .get(symbol1)
            .with_context(|| format!("no price history for symbol {}", symbol1))?;
        let series2 = history
            .get(symbol2)
            .with_context(|| format!("no price history for symbol {}", symbol2))?;

        // Filter to window
        let series1: Vec<_> = series1
            .iter()
            .filter(|(ts, _)| *ts >= cutoff && *ts <= now)
            .cloned()
            .collect();

        let series2: Vec<_> = series2
            .iter()
            .filter(|(ts, _)| *ts >= cutoff && *ts <= now)
            .cloned()
            .collect();

        if series1.len() < 2 || series2.len() < 2 {
            bail!(
                "not enough data for correlation between {} and {} for {} days",
                symbol1,
                symbol2,
                days
            );
        }

        // Roll up to daily closes (last price per calendar day)
        let daily1 = Self::to_daily_closes(&series1)?;
        let daily2 = Self::to_daily_closes(&series2)?;

        // Find common dates
        let mut common_dates: Vec<NaiveDate> = daily1
            .keys()
            .filter(|d| daily2.contains_key(d))
            .cloned()
            .collect();
        common_dates.sort();

        if common_dates.len() < 3 {
            bail!(
                "not enough overlapping daily data for {} and {} over {} days",
                symbol1,
                symbol2,
                days
            );
        }

        // Build aligned price vectors
        let mut prices1 = Vec::with_capacity(common_dates.len());
        let mut prices2 = Vec::with_capacity(common_dates.len());

        for d in &common_dates {
            let p1 = *daily1
                .get(d)
                .expect("date should exist in daily1 (checked above)");
            let p2 = *daily2
                .get(d)
                .expect("date should exist in daily2 (checked above)");
            prices1.push(p1);
            prices2.push(p2);
        }

        // Compute log returns
        let returns1 = Self::log_returns(&prices1)?;
        let returns2 = Self::log_returns(&prices2)?;

        // Need same length; they should be, but guard anyway
        let n = returns1.len().min(returns2.len());
        if n < 2 {
            bail!("not enough return points for correlation");
        }

        let corr = Self::pearson_correlation(&returns1[..n], &returns2[..n])
            .context("failed to compute Pearson correlation")?;

        Ok(corr.max(-1.0).min(1.0))
    }

    /// BTC dominance: BTC market cap / total crypto market cap * 100
    /// Uses latest prices as a proxy (in production, use real market cap data)
    async fn calculate_btc_dominance(&self, days: i32) -> Result<f64> {
        let history = self.price_history.read().await;
        let now = Utc::now();
        let cutoff = now - Duration::days(days.into());

        let btc_series = history
            .get("BTC")
            .with_context(|| "no BTC price history for dominance calc".to_string())?;

        // Latest BTC price in window
        let btc_price = btc_series
            .iter()
            .filter(|(ts, _)| *ts >= cutoff && *ts <= now)
            .max_by_key(|(ts, _)| *ts)
            .map(|(_, p)| *p)
            .context("no BTC price in the selected window")?;

        let btc_price_f = btc_price
            .to_f64()
            .context("failed to convert BTC price to f64")?;

        let mut total_crypto_proxy = 0.0_f64;

        // Treat price as a rough proxy (NOT accurate, but deterministic)
        for (symbol, series) in history.iter() {
            if !self.is_crypto(symbol) {
                continue;
            }
            if symbol == "BTC" {
                continue;
            }
            if let Some((_, p)) = series
                .iter()
                .filter(|(ts, _)| *ts >= cutoff && *ts <= now)
                .max_by_key(|(ts, _)| *ts)
            {
                if let Some(val) = p.to_f64() {
                    total_crypto_proxy += val;
                }
            }
        }

        if total_crypto_proxy <= 0.0 {
            bail!("no other crypto prices available for BTC dominance calculation");
        }

        let total = btc_price_f + total_crypto_proxy;
        let dominance = (btc_price_f / total) * 100.0;
        Ok(dominance)
    }

    /// Classify global market regime using multi-horizon correlations + BTC dominance
    async fn determine_global_regime(
        &self,
        corr_1d: f64,
        corr_7d: f64,
        corr_30d: f64,
        btc_dominance: Option<f64>,
    ) -> Result<GlobalRegime> {
        // For crypto: use BTC dominance + correlations
        if let Some(dom) = btc_dominance {
            // CRYPTO_ALT_SEASON: BTC dominance falling, high correlations (alts + equities moving together)
            if dom < 45.0 && corr_30d > 0.6 && corr_1d > 0.6 && corr_7d > 0.6 {
                Ok(GlobalRegime::CryptoAltSeason)
            }
            // CRYPTO_BTC_DOMINANCE: BTC dominance rising, low correlations (flight to safety)
            else if dom > 55.0 && corr_30d < 0.3 && corr_1d < 0.3 {
                Ok(GlobalRegime::CryptoBtcDominance)
            } else {
                Ok(GlobalRegime::Neutral)
            }
        } else {
            // For equities: use correlation patterns
            // EQUITY_RISK_ON: high correlation on all horizons
            if corr_30d > 0.7 && corr_1d > 0.6 && corr_7d > 0.6 {
                Ok(GlobalRegime::EquityRiskOn)
            }
            // EQUITY_RISK_OFF: low correlation across horizons
            else if corr_30d < 0.3 && corr_1d < 0.3 && corr_7d < 0.3 {
                Ok(GlobalRegime::EquityRiskOff)
            } else {
                Ok(GlobalRegime::Neutral)
            }
        }
    }

    /// Classify local context (per-ticker decoupling analysis)
    /// Detects when a ticker is doing something not explained by broad market risk
    async fn determine_local_context(
        &self,
        corr_1d: f64,
        corr_7d: f64,
        corr_30d: f64,
    ) -> Result<LocalContext> {
        // IDIOSYNCRATIC_BREAKOUT: 30d correlation high but recent correlations drop
        // This suggests the stock is moving on its own catalyst
        if corr_30d > 0.6 && (corr_1d < 0.3 || corr_7d < 0.3) {
            Ok(LocalContext::IdiosyncraticBreakout)
        }
        // CHOPPY_MEAN_REVERT: correlations unstable, mid-range, flipping
        else if corr_30d >= 0.4 && corr_30d <= 0.6 
            && (corr_1d * corr_7d < 0.0 || (corr_1d.abs() < 0.3 && corr_7d.abs() < 0.3)) {
            Ok(LocalContext::ChoppyMeanRevert)
        } else {
            Ok(LocalContext::Normal)
        }
    }

    fn is_crypto(&self, symbol: &str) -> bool {
        matches!(symbol, "BTC" | "ETH" | "ADA" | "SOL" | "DOT" | "MATIC" | "BNB" | "XRP" | "DOGE" | "LINK" | "AVAX" | "ATOM" | "UNI" | "AAVE")
    }

    /// Roll intraday points into daily closes (last price per calendar day).
    fn to_daily_closes(
        series: &[(DateTime<Utc>, Decimal)],
    ) -> Result<BTreeMap<NaiveDate, f64>> {
        let mut daily: BTreeMap<NaiveDate, Decimal> = BTreeMap::new();

        for (ts, price) in series {
            let date = ts.date_naive();
            // Overwrite with latest price in that day
            daily.insert(date, *price);
        }

        let mut out = BTreeMap::new();
        for (d, p) in daily {
            let v = p
                .to_f64()
                .with_context(|| format!("failed to convert price to f64 for date {:?}", d))?;
            out.insert(d, v);
        }

        Ok(out)
    }

    /// Compute log returns from a price series.
    fn log_returns(prices: &[f64]) -> Result<Vec<f64>> {
        if prices.len() < 2 {
            bail!("not enough prices to compute returns");
        }
        let mut returns = Vec::with_capacity(prices.len() - 1);
        for w in prices.windows(2) {
            let p0 = w[0];
            let p1 = w[1];
            if p0 <= 0.0 || p1 <= 0.0 {
                bail!("non-positive price encountered in log return calculation");
            }
            let r = (p1 / p0).ln();
            returns.push(r);
        }
        Ok(returns)
    }

    /// Standard Pearson correlation coefficient.
    fn pearson_correlation(x: &[f64], y: &[f64]) -> Result<f64> {
        let n = x.len();
        if n != y.len() || n < 2 {
            bail!("pearson requires same-length slices with len >= 2");
        }

        let mean = |data: &[f64]| -> f64 {
            let sum: f64 = data.iter().sum();
            sum / (data.len() as f64)
        };

        let mx = mean(x);
        let my = mean(y);

        let mut cov = 0.0;
        let mut var_x = 0.0;
        let mut var_y = 0.0;

        for i in 0..n {
            let dx = x[i] - mx;
            let dy = y[i] - my;
            cov += dx * dy;
            var_x += dx * dx;
            var_y += dy * dy;
        }

        if var_x <= 0.0 || var_y <= 0.0 {
            bail!("zero variance in one of the series (correlation undefined)");
        }

        let corr = cov / (var_x.sqrt() * var_y.sqrt());
        Ok(corr)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::TimeZone;

    #[tokio::test]
    async fn test_correlation_calculation() {
        let engine = CorrelationAnalysisEngine::new();
        
        // Ingest some test data
        let now = Utc::now();
        for i in 0..30 {
            let ts = now - Duration::days(30 - i);
            let price1 = Decimal::from(100 + i);
            let price2 = Decimal::from(200 + i * 2);
            engine.ingest_price("AAPL", ts, price1).await;
            engine.ingest_price("SPY", ts, price2).await;
        }

        let result = engine.calculate_correlation("AAPL", "SPY", 30).await;
        assert!(result.is_ok());
        let corr = result.unwrap();
        // Should be highly correlated (both trending up)
        assert!(corr > 0.9);
    }

    #[tokio::test]
    async fn test_regime_classification() {
        let engine = CorrelationAnalysisEngine::new();
        
        // High correlation -> EquityRiskOn
        let regime = engine.determine_global_regime(0.8, 0.75, 0.8, None).await.unwrap();
        assert_eq!(regime, GlobalRegime::EquityRiskOn);
        
        // Low correlation -> EquityRiskOff
        let regime = engine.determine_global_regime(0.2, 0.25, 0.2, None).await.unwrap();
        assert_eq!(regime, GlobalRegime::EquityRiskOff);
        
        // Crypto alt season
        let regime = engine.determine_global_regime(0.7, 0.65, 0.7, Some(40.0)).await.unwrap();
        assert_eq!(regime, GlobalRegime::CryptoAltSeason);
    }
}
