// src/analysis/regime.rs
use crate::market_data::provider::MarketDataProvider;
use crate::utils::stats::{log_returns, pearson, daily_mid_prices, atr};
use anyhow::{Result, bail};
use chrono::{Utc, Duration};
use rust_decimal::prelude::*;
use serde::{Serialize, Deserialize};
use std::sync::Arc;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EquityVolRegime {
    Low,
    Medium,
    High,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum GlobalMarketRegime {
    RiskOn,
    RiskOff,
    Transition,
    ExtremeFear,
    Neutral,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegimeSignals {
    pub spy_btc_corr_30d: f64,
    pub btc_dominance: Option<f64>,
    pub dxy_strength: f64,
    pub equity_volatility: EquityVolRegime,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketRegimeResponse {
    pub regime: GlobalMarketRegime,
    pub confidence: f64,
    pub primary_driver: String,
    pub signals: RegimeSignals,
    pub timestamp: chrono::DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimpleMarketRegime {
    pub headline: String,
    pub one_liner: String,
    pub action: String,
    pub mood: String,
    pub confidence: f64,
    pub timestamp: chrono::DateTime<Utc>,
}

pub struct MarketRegimeEngine {
    provider: Arc<dyn MarketDataProvider>,
}

impl MarketRegimeEngine {
    pub fn new(provider: Arc<dyn MarketDataProvider>) -> Self {
        Self { provider }
    }

    // ──────────────────────────────────────────────────────────────────────
    // MAIN ENTRY POINT (Quant Edition)
    // ──────────────────────────────────────────────────────────────────────
    pub async fn analyze(&self) -> Result<MarketRegimeResponse> {
        let spy_btc_corr = self.corr_30d("SPY", "BTC").await.unwrap_or(0.0);
        let btc_dom = self.btc_dominance(30).await.ok();
        let dxy_strength = self.dxy_strength_index().await.unwrap_or(0.0);
        let vol_regime = self.spy_vol_regime().await?;

        // Compute final regime + explanation
        let (regime, confidence, primary) =
            self.combine(spy_btc_corr, btc_dom, dxy_strength, &vol_regime);

        Ok(MarketRegimeResponse {
            regime,
            confidence,
            primary_driver: primary,
            signals: RegimeSignals {
                spy_btc_corr_30d: spy_btc_corr,
                btc_dominance: btc_dom,
                dxy_strength,
                equity_volatility: vol_regime,
            },
            timestamp: Utc::now(),
        })
    }

    // ──────────────────────────────────────────────────────────────────────
    // JOBS EDITION: Human-readable regime messages
    // ──────────────────────────────────────────────────────────────────────
    pub async fn analyze_simple(&self) -> Result<SimpleMarketRegime> {
        let full = self.analyze().await?;

        let mood = match full.regime {
            GlobalMarketRegime::RiskOn => "Greed",
            GlobalMarketRegime::RiskOff => "Fear",
            GlobalMarketRegime::ExtremeFear => "Panic",
            GlobalMarketRegime::Transition => "Confusion",
            GlobalMarketRegime::Neutral => "Boredom",
        };

        let (headline, one_liner, action) = self.get_legendary_message(&full).unwrap_or_else(|| {
            // Default fallback messages
            match (full.regime.clone(), full.confidence) {
                (GlobalMarketRegime::RiskOn, c) if c > 0.8 => (
                    "Everything risk is ripping higher together",
                    "This is the strongest risk-on regime in months — money is flooding in",
                    "Go aggressive • Buy the dip • Load up on alts • Raise leverage",
                ),
                (GlobalMarketRegime::RiskOn, _) => (
                    "Money is flowing into risk assets like crazy",
                    "Stocks and crypto are moving up together — classic bull market behavior",
                    "Increase exposure • Go long alts • Raise risk budget",
                ),
                (GlobalMarketRegime::RiskOff, c) if c > 0.8 => (
                    "Safe-haven rush is in full force",
                    "Bitcoin dominance spiking, USD surging — traders are running for cover",
                    "Cut risk hard • Move to cash/stablecoins • Short alts",
                ),
                (GlobalMarketRegime::RiskOff, _) => (
                    "Risk assets are bleeding in unison",
                    "Stocks and crypto both getting crushed — defensive mode activated",
                    "Reduce leverage • Rotate to stables • Protect capital",
                ),
                (GlobalMarketRegime::ExtremeFear, _) => (
                    "Markets are in full-blown panic",
                    "This is capitulation territory — fear is at levels seen only at major bottoms",
                    "Prepare shopping list • Start nibbling • This is where legends buy",
                ),
                (GlobalMarketRegime::Transition, _) => (
                    "The market has no idea what it wants",
                    "Mixed signals everywhere — no clear trend yet",
                    "Stay patient • Trade small • Wait for clarity",
                ),
                (GlobalMarketRegime::Neutral, _) => (
                    "Nothing exciting is happening",
                    "Choppy, low-conviction market — range-bound grinding",
                    "Trade lightly • Focus on mean-reversion • Keep powder dry",
                ),
            }
        });

        Ok(SimpleMarketRegime {
            headline: headline.into(),
            one_liner: one_liner.into(),
            action: action.into(),
            mood: mood.into(),
            confidence: full.confidence,
            timestamp: Utc::now(),
        })
    }

    // ──────────────────────────────────────────────────────────────────────
    // LEGENDARY REGIME MESSAGES (10 historically accurate templates)
    // ──────────────────────────────────────────────────────────────────────
    fn get_legendary_message(&self, full: &MarketRegimeResponse) -> Option<(&'static str, &'static str, &'static str)> {
        let corr = full.signals.spy_btc_corr_30d;
        let dom = full.signals.btc_dominance;
        let dxy = full.signals.dxy_strength;

        match (full.regime.clone(), full.confidence, corr, dom) {
            // 1. March 2020 – Pandemic Capitulation
            (GlobalMarketRegime::ExtremeFear, c, _, _) if c > 0.9 => Some((
                "The greatest buying panic of our generation",
                "Markets just capitulated — this is where legends are made",
                "Start buying gradually • Build positions • This is 2009 energy",
            )),

            // 2. Late-cycle Crypto Mania (e.g., 2021)
            (GlobalMarketRegime::RiskOn, c, corr, Some(dom))
                if c > 0.9 && corr > 0.85 && dom < 40.0 => Some((
                    "We are in full-blown alt-season mania",
                    "Every coin is pumping together — classic cycle blow-off",
                    "Take profits • Lock gains • Avoid becoming exit liquidity",
                )),

            // 3. Major Crypto Crash Pattern (e.g., Terra/Luna 2022)
            (GlobalMarketRegime::RiskOff, c, _, Some(dom))
                if c > 0.9 && dom > 62.0 => Some((
                    "Bitcoin dominance just hit escape velocity",
                    "Risk capital is fleeing alts — safety flows in full force",
                    "Move to majors & stables • Cut weak positions",
                )),

            // 4. Global Policy Pivot (e.g., 2019 Powell Pivot)
            (GlobalMarketRegime::RiskOn, c, _, _)
                if c > 0.85 && dxy < -0.25 => Some((
                    "A major policy shift just triggered a market reset",
                    "Strongest risk-on reversal in years",
                    "Buy leaders • Ride momentum • Add on dips",
                )),

            // 5. Oversold Macro Bottom (e.g., Oct 2022 CPI flush)
            (GlobalMarketRegime::ExtremeFear, c, _, _) if c > 0.92 => Some((
                "This fear spike is the strongest since the last crash bottom",
                "We are entering historic capitulation territory",
                "Prepare your buy list • Bottom formation underway",
            )),

            // 6. Post-event Macro Regime Shift (safe alternative)
            (GlobalMarketRegime::RiskOn, c, _, _)
                if c > 0.9 && dxy > 0.2 => Some((
                    "A major macro event just flipped the entire risk landscape",
                    "Stocks, crypto, and commodities are all getting bid",
                    "Go bullish • Ride momentum • Lean into strength",
                )),

            // 7. Stealth Bear Market (e.g., 2022)
            (GlobalMarketRegime::Transition, _, corr, Some(dom))
                if corr < 0.2 && dom > 58.0 => Some((
                    "The market is lying to you",
                    "Everything seems calm but risk assets are quietly bleeding out",
                    "Reduce exposure • Tighten stops • Wait for clarity",
                )),

            // 8. The Quiet Bull Market (e.g., 2023 AI grind)
            (GlobalMarketRegime::RiskOn, c, corr, _)
                if c > 0.7 && corr > 0.75 => Some((
                    "The boring bull market continues",
                    "Slow, steady grind higher — perfect for compounding",
                    "Stay invested • Add on dips • Hold winners",
                )),

            // 9. Cross-Asset Everything Rally
            (GlobalMarketRegime::RiskOn, c, _, Some(dom))
                if c > 0.88 && dom < 43.0 => Some((
                    "A rare everything rally is underway",
                    "Stocks, alts, and bonds are ripping together",
                    "Ride momentum • Don't overthink it • Let it run",
                )),

            // 10. Final Shakeout Before Bull Run
            (GlobalMarketRegime::ExtremeFear, c, _, Some(dom))
                if c > 0.85 && dom > 60.0 => Some((
                    "One final purge before the real bull run",
                    "Weak hands are being shaken out — accumulation zone forming",
                    "Start scaling in • Build core positions • Prepare for upside",
                )),

            _ => None,
        }
    }

    // ──────────────────────────────────────────────────────────────────────
    // SIGNAL #1 — 30D Correlation SPY ↔ BTC
    // ──────────────────────────────────────────────────────────────────────
    async fn corr_30d(&self, a: &str, b: &str) -> Result<f64> {
        let end = Utc::now();
        let start = end - Duration::days(30);

        let h1 = self.provider.get_price_history(a, start, end).await?;
        let h2 = self.provider.get_price_history(b, start, end).await?;

        if h1.len() < 20 || h2.len() < 20 {
            bail!("insufficient data for correlation");
        }

        let c1: Vec<f64> = h1.iter().map(|(_, p)| p.to_f64().unwrap_or(0.0)).collect();
        let c2: Vec<f64> = h2.iter().map(|(_, p)| p.to_f64().unwrap_or(0.0)).collect();

        let r1 = log_returns(&c1)?;
        let r2 = log_returns(&c2)?;

        let n = r1.len().min(r2.len());
        pearson(&r1[..n], &r2[..n])
    }

    // ──────────────────────────────────────────────────────────────────────
    // SIGNAL #2 — BTC Dominance
    // ──────────────────────────────────────────────────────────────────────
    async fn btc_dominance(&self, days: i64) -> Result<f64> {
        let end = Utc::now();
        let start = end - Duration::days(days);

        let btc = self.provider.get_price_history("BTC", start, end).await?;
        if btc.is_empty() { bail!("no BTC data"); }

        let btc_latest = btc.last().unwrap().1.to_f64().unwrap();

        let cryptos = ["ETH","SOL","ADA","XRP","LINK","DOGE","DOT","BNB","MATIC"];

        let mut total = btc_latest;
        for symbol in &cryptos {
            if let Ok(h) = self.provider.get_price_history(symbol, start, end).await {
                if let Some((_, p)) = h.last() {
                    total += p.to_f64().unwrap_or(0.0);
                }
            }
        }

        Ok((btc_latest / total) * 100.0)
    }

    // ──────────────────────────────────────────────────────────────────────
    // SIGNAL #3 — DXY Strength (synthetic)
    // ──────────────────────────────────────────────────────────────────────
    async fn dxy_strength_index(&self) -> Result<f64> {
        let end = Utc::now();
        let start = end - Duration::days(20);

        let eurusd = self.provider.get_fx_history("EURUSD", start, end).await?;
        let usdjpy = self.provider.get_fx_history("USDJPY", start, end).await?;

        let eur = daily_mid_prices(&eurusd)?;
        let jpy = daily_mid_prices(&usdjpy)?;

        let eur_closes: Vec<f64> = eur.iter().map(|(_,_,c)| *c).collect();
        let jpy_closes: Vec<f64> = jpy.iter().map(|(_,_,c)| *c).collect();

        let eur_ret = log_returns(&eur_closes)?;
        let jpy_ret = log_returns(&jpy_closes)?;

        let n = eur_ret.len().min(jpy_ret.len());
        if n < 5 { bail!("insufficient data for DXY"); }

        // DXY ↑ when EURUSD ↓, and USDJPY ↑
        let dxy_proxy: f64 = (0.5 * (-eur_ret[n-1])) + (0.5 * jpy_ret[n-1]);

        Ok(dxy_proxy)
    }

    // ──────────────────────────────────────────────────────────────────────
    // SIGNAL #4 — SPY volatility regime via 14-day ATR normalization
    // ──────────────────────────────────────────────────────────────────────
    async fn spy_vol_regime(&self) -> Result<EquityVolRegime> {
        let end = Utc::now();
        let start = end - Duration::days(20);

        let spy = self.provider.get_price_history("SPY", start, end).await?;
        if spy.is_empty() { bail!("no SPY data"); }

        let fx_formatted: Vec<_> = spy.iter()
            .map(|(ts, p)| (*ts, *p, *p))
            .collect();

        let daily = daily_mid_prices(&fx_formatted)?;
        let a = atr(&daily, 14)?;

        let level = a / daily.last().unwrap().2; // ATR % of price

        Ok(
            if level < 0.01 { EquityVolRegime::Low }
            else if level < 0.02 { EquityVolRegime::Medium }
            else { EquityVolRegime::High }
        )
    }

    // ──────────────────────────────────────────────────────────────────────
    // COMBINATION LOGIC — Fusion of all signals
    // ──────────────────────────────────────────────────────────────────────
    fn combine(
        &self,
        corr: f64,
        btc_dom: Option<f64>,
        dxy_strength: f64,
        vol: &EquityVolRegime
    ) -> (GlobalMarketRegime, f64, String) {

        let mut score = 0.0;
        let mut reasons = vec![];

        // Signal: SPY/BTC correlation
        if corr > 0.6 {
            score += 0.35;
            reasons.push("strong SPY–BTC correlation");
        } else if corr < 0.3 {
            score -= 0.25;
            reasons.push("weak SPY–BTC correlation");
        }

        // Signal: BTC Dominance
        if let Some(dom) = btc_dom {
            if dom < 45.0 {
                score += 0.25;
                reasons.push("falling BTC dominance (alt-season)");
            } else if dom > 55.0 {
                score -= 0.25;
                reasons.push("rising BTC dominance (risk-off crypto)");
            }
        }

        // Signal: DXY
        if dxy_strength < -0.1 {
            score += 0.20;
            reasons.push("weak USD (pro-risk)");
        } else if dxy_strength > 0.1 {
            score -= 0.20;
            reasons.push("strong USD (risk-off)");
        }

        // Signal: Volatility
        match vol {
            EquityVolRegime::Low => {
                score += 0.15;
                reasons.push("low volatility regime");
            },
            EquityVolRegime::Medium => {},
            EquityVolRegime::High => {
                score -= 0.30;
                reasons.push("high volatility (fear)");
            }
        }

        // Final regime decision
        let (regime, conf): (GlobalMarketRegime, f64) =
            if score > 0.6 { (GlobalMarketRegime::RiskOn, score) }
            else if score < -0.6 { (GlobalMarketRegime::RiskOff, -score) }
            else if score < -1.0 { (GlobalMarketRegime::ExtremeFear, -score) }
            else { (GlobalMarketRegime::Transition, score.abs()) };

        let primary = reasons.join(" + ");

        (regime, conf.max(0.05).min(1.0), primary)
    }
}

