// src/utils/stats.rs
use chrono::{DateTime, NaiveDate, Utc};
use rust_decimal::Decimal;
use rust_decimal::prelude::*;
use anyhow::{Result, bail, Context};
use std::collections::BTreeMap;

/// Convert irregular timestamps into daily OHLC
/// Supports both legacy tuple format and new PricePoint format
pub fn daily_mid_prices(
    fx_history: &[(DateTime<Utc>, Decimal, Decimal)]
) -> Result<Vec<(f64, f64, f64)>> {
    let mut daily: BTreeMap<NaiveDate, (f64, f64, f64)> = BTreeMap::new();

    for (ts, bid, ask) in fx_history {
        let date = ts.date_naive();
        let mid = (*bid + *ask) / Decimal::TWO;
        let mid_f = mid.to_f64().unwrap_or(0.0);

        let entry = daily.entry(date).or_insert((mid_f, mid_f, mid_f));
        entry.0 = entry.0.max(mid_f); // high
        entry.1 = entry.1.min(mid_f); // low
        entry.2 = mid_f;             // close
    }

    Ok(daily.into_values().collect())
}

/// Convert PricePoint series into daily OHLC
pub fn daily_mid_prices_from_points(
    points: &[crate::market_data::PricePoint]
) -> Result<Vec<(f64, f64, f64)>> {
    let mut daily: BTreeMap<NaiveDate, (f64, f64, f64)> = BTreeMap::new();

    for point in points {
        let date = point.ts.date_naive();
        let mid_f = point.mid.to_f64().unwrap_or(0.0);

        let entry = daily.entry(date).or_insert((mid_f, mid_f, mid_f));
        entry.0 = entry.0.max(mid_f); // high
        entry.1 = entry.1.min(mid_f); // low
        entry.2 = mid_f;             // close
    }

    Ok(daily.into_values().collect())
}

/// Convert price history to daily closes
pub fn to_daily_closes(
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

/// Compute log returns from closes
pub fn log_returns(prices: &[f64]) -> Result<Vec<f64>> {
    if prices.len() < 2 {
        bail!("need >=2 prices");
    }

    Ok(prices.windows(2).map(|w| {
        if w[0] <= 0.0 || w[1] <= 0.0 {
            0.0 // Return 0 for invalid prices
        } else {
            (w[1] / w[0]).ln()
        }
    }).collect())
}

/// Pearson correlation
pub fn pearson(x: &[f64], y: &[f64]) -> Result<f64> {
    let n = x.len();
    if n < 2 || n != y.len() {
        bail!("invalid pearson dimensions");
    }

    let mx = x.iter().sum::<f64>() / n as f64;
    let my = y.iter().sum::<f64>() / n as f64;

    let mut cov = 0.0;
    let mut vx = 0.0;
    let mut vy = 0.0;

    for i in 0..n {
        let dx = x[i] - mx;
        let dy = y[i] - my;
        cov += dx * dy;
        vx += dx * dx;
        vy += dy * dy;
    }

    if vx == 0.0 || vy == 0.0 {
        bail!("zero variance");
    }

    Ok(cov / (vx.sqrt() * vy.sqrt()))
}

/// ATR: Average True Range (14-period default)
pub fn atr(daily: &[(f64, f64, f64)], period: usize) -> Result<f64> {
    if daily.len() < period + 1 {
        bail!("not enough data for ATR");
    }

    let mut trs = Vec::new();
    let mut prev_close = None;

    for (high, low, close) in daily {
        let tr: f64 = if let Some(pc) = prev_close {
            let hl: f64 = *high - *low;
            let diff_high: f64 = *high - pc;
            let diff_low: f64 = *low - pc;
            let hc: f64 = diff_high.abs();
            let lc: f64 = diff_low.abs();
            hl.max(hc).max(lc)
        } else {
            *high - *low
        };
        prev_close = Some(*close);
        trs.push(tr);
    }

    Ok(trs[trs.len() - period..].iter().sum::<f64>() / period as f64)
}

