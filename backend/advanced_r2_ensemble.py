#!/usr/bin/env python3
"""
Advanced R² Ensemble - Production-grade stacking approach
Based on sophisticated walk-forward validation and meta-learning
"""

import os
import sys
import django
import argparse
import warnings
import logging
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
from sklearn.model_selection import TimeSeriesSplit

warnings.filterwarnings("ignore", category=FutureWarning)

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except Exception:
    HAS_XGB = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- utils --------------------
@dataclass
class Result:
    r2_oos: float
    n_oos: int
    details: Dict[str, float]

def winsor(s: pd.Series, q: float) -> pd.Series:
    if q <= 0: return s
    lo, hi = s.quantile(q), s.quantile(1-q)
    return s.clip(lo, hi)

def rsi(prices: pd.Series, window=14) -> pd.Series:
    d = prices.diff()
    up = d.clip(lower=0).rolling(window).mean()
    dn = (-d.clip(upper=0)).rolling(window).mean()
    rs = up / (dn + 1e-12)
    return 100 - (100 / (1 + rs))

# -------------------- data loader --------------------
def load_prices_from_yfinance(symbols: List[str], days: int = 1000) -> pd.DataFrame:
    """Load prices from yfinance for multiple symbols"""
    import yfinance as yf
    
    all_data = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days}d")
            
            if not hist.empty and len(hist) > 100:
                # Rename columns to lowercase
                hist.columns = [col.lower() for col in hist.columns]
                hist['symbol'] = symbol
                all_data.append(hist)
                logger.info(f"✓ {symbol}: {len(hist)} days")
        except Exception as e:
            logger.error(f"Error loading {symbol}: {e}")
    
    if not all_data:
        raise ValueError("No data loaded for any symbol")
    
    # Combine all data
    combined = pd.concat(all_data, ignore_index=False)
    
    # Get market data (SPY as proxy)
    try:
        spy = yf.Ticker("SPY")
        market_data = spy.history(period=f"{days}d")
        market_data.columns = [f"market_{col.lower()}" for col in market_data.columns]
        
        # Align market data with stock data
        common_dates = combined.index.intersection(market_data.index)
        if len(common_dates) > 50:
            combined = combined.loc[common_dates]
            market_aligned = market_data.loc[common_dates]
            
            # Add market columns
            for col in market_aligned.columns:
                combined[col] = market_aligned[col]
    except Exception as e:
        logger.warning(f"Could not load market data: {e}")
        # Create proxy market data
        combined['market_close'] = combined['close'].rolling(5, min_periods=1).mean()
        combined['market_close'] = combined['market_close'] + np.random.normal(0, combined['close'].std()*0.01, len(combined))
    
    return combined[['close', 'volume', 'market_close']].dropna()

def load_prices(path: str) -> pd.DataFrame:
    """Load prices from CSV file"""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    assert "date" in df and "close" in df and "volume" in df, "CSV needs: date, close, volume [,market_close]"
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    if "market_close" not in df:
        proxy = df["close"].rolling(5, min_periods=1).mean()
        proxy = proxy + np.random.normal(0, df["close"].std()*0.01, len(proxy))
        df["market_close"] = proxy
    return df[["close","volume","market_close"]].dropna()

# -------------------- feature engineering --------------------
def build_features(df: pd.DataFrame, freq: str, horizon: int, winsor_q: float) -> pd.DataFrame:
    # resample
    if freq.upper().startswith("W"):
        df = df.resample("W-FRI").last().dropna()

    out = df.copy()
    out["ret"] = np.log(out["close"] / out["close"].shift(1))
    out["mkt_ret"] = np.log(out["market_close"] / out["market_close"].shift(1))

    # core technicals with multiple lookbacks
    looks = [4, 8, 12, 26, 52]  # weekly bars ≈ 1m,2m,3m,6m,1y
    for L in looks:
        out[f"ret_sum_{L}"] = out["ret"].rolling(L).sum()
        out[f"vol_{L}"] = out["ret"].rolling(L).std()
        out[f"mkt_sum_{L}"] = out["mkt_ret"].rolling(L).sum()
        out[f"volratio_{L}"] = out["volume"] / (out["volume"].rolling(L).mean() + 1e-12)

    # momentum/mean-reversion lags
    for lag in [1,2,4,8,12,26]:
        out[f"lag_ret_{lag}"] = out["ret"].shift(lag)

    # RSI / MACD / Bollinger %B
    out["rsi_14"] = rsi(out["close"], 14)
    ema12 = out["close"].ewm(span=12, adjust=False).mean()
    ema26 = out["close"].ewm(span=26, adjust=False).mean()
    out["macd"] = ema12 - ema26
    out["macd_sig"] = out["macd"].ewm(span=9, adjust=False).mean()
    mid20 = out["close"].rolling(20).mean()
    std20 = out["close"].rolling(20).std()
    out["pctB"] = (out["close"] - (mid20 - 2*std20)) / ((mid20 + 2*std20) - (mid20 - 2*std20) + 1e-12)

    # market beta (60 bars)
    cov60 = out["ret"].rolling(60).cov(out["mkt_ret"])
    var60 = out["mkt_ret"].rolling(60).var()
    out["beta_60"] = cov60 / (var60 + 1e-12)

    # distribution shape (rolling skew/kurtosis) – robust proxies
    out["skew_40"] = (out["ret"].rolling(40).apply(lambda x: pd.Series(x).skew(), raw=False))
    out["kurt_40"] = (out["ret"].rolling(40).apply(lambda x: pd.Series(x).kurt(), raw=False))

    # target: H-step ahead sum of returns (weekly horizon recommended)
    H = max(1, int(horizon))
    out["y"] = out["ret"].rolling(H).sum().shift(-H)

    # winsorize tails
    for c in [col for col in out.columns if col != "y"]:
        out[c] = winsor(out[c], winsor_q)
    out["y"] = winsor(out["y"], winsor_q)

    out = out.dropna()

    feat_cols = [c for c in out.columns if c not in ["y"]]
    return out[feat_cols + ["y"]]

# -------------------- model stack --------------------
def make_base_models() -> Dict[str, object]:
    gbr = GradientBoostingRegressor(
        n_estimators=900, learning_rate=0.04, max_depth=3, subsample=0.9, random_state=42
    )
    enet = Pipeline([
        ("scaler", StandardScaler()),
        ("enet", ElasticNet(alpha=7e-4, l1_ratio=0.4, max_iter=15000, random_state=42)),
    ])
    xgb = None
    if HAS_XGB:
        xgb = XGBRegressor(
            n_estimators=2500, learning_rate=0.03, max_depth=4,
            subsample=0.9, colsample_bytree=0.8,
            reg_lambda=3.0, reg_alpha=0.0,
            tree_method="hist", random_state=42
        )
    return {"gbr": gbr, "enet": enet, "xgb": xgb}

def walk_forward_stack(df: pd.DataFrame, n_splits=6, embargo=2, use_xgb=True) -> Result:
    feat_cols = [c for c in df.columns if c != "y"]
    X = df[feat_cols].values
    y = df["y"].values
    n = len(df)

    # chronological splits over the last half of the data
    start_train = int(n * 0.5)
    split_idx = np.linspace(start_train, n, n_splits + 1, dtype=int)
    split_idx[-1] = n

    base_models = make_base_models()
    if not use_xgb or base_models["xgb"] is None:
        del base_models["xgb"]

    # out-of-fold predictions for meta-learner
    meta_pred = np.full(n, np.nan, dtype=float)

    for k in range(n_splits):
        test_start = split_idx[k] + embargo
        test_end   = split_idx[k + 1]
        train_end  = split_idx[k]
        if test_end - test_start < 10:
            continue

        # train/val split inside training period for early stopping
        cut = int(train_end * 0.85)
        Xtr, ytr = X[:cut], y[:cut]
        Xval, yval = X[cut:train_end], y[cut:train_end]

        # fit base models and generate test preds
        preds_stack = []
        for name, model in base_models.items():
            if name == "xgb":
                try:
                    # Try modern XGBoost API
                    model.fit(Xtr, ytr, eval_set=[(Xval, yval)], eval_metric="rmse",
                              verbose=False, early_stopping_rounds=100)
                except TypeError:
                    try:
                        # Try older XGBoost API
                        model.fit(Xtr, ytr, eval_set=[(Xval, yval)],
                                  verbose=False, early_stopping_rounds=100)
                    except TypeError:
                        # Fallback to simple fit
                        model.fit(Xtr, ytr)
            else:
                model.fit(X[:train_end], y[:train_end])
            p = model.predict(X[test_start:test_end])
            preds_stack.append(p)

        # meta learner (ElasticNet) on VAL of base models vs yval, then predict TEST
        # Build OOF for this fold's val
        val_stack = []
        for name, model in base_models.items():
            pv = model.predict(Xval)
            val_stack.append(pv)
        val_stack = np.vstack(val_stack).T  # shape (len(val), n_models)

        meta = ElasticNet(alpha=1e-3, l1_ratio=0.2, max_iter=20000, random_state=17)
        meta.fit(val_stack, yval)

        test_stack = np.vstack(preds_stack).T
        meta_pred[test_start:test_end] = meta.predict(test_stack)

    valid = ~np.isnan(meta_pred)
    r2 = r2_score(y[valid], meta_pred[valid]) if valid.any() else float("nan")
    return Result(r2_oos=float(r2), n_oos=int(valid.sum()),
                  details={"splits": n_splits, "embargo": embargo, "models": list(base_models.keys())})

# -------------------- main --------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, help="CSV with columns: date, close, volume [,market_close]")
    ap.add_argument("--symbols", type=str, nargs="+", default=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'KO', 'JPM'], 
                    help="Stock symbols to analyze (if no CSV provided)")
    ap.add_argument("--freq", type=str, default="W", help="D or W (weekly recommended)")
    ap.add_argument("--horizon", type=int, default=4, help="Forward steps to predict (on W: ~1 month)")
    ap.add_argument("--winsor", type=float, default=0.02, help="Tail clip quantile (e.g., 0.02 = 2%)")
    ap.add_argument("--splits", type=int, default=6)
    ap.add_argument("--embargo", type=int, default=2)
    ap.add_argument("--no_xgb", action="store_true", help="Disable XGBoost if installed")
    args = ap.parse_args()

    print("\n" + "="*70)
    print("ADVANCED R² ENSEMBLE - PRODUCTION-GRADE STACKING")
    print("="*70)
    
    # Load data
    if args.data:
        df = load_prices(args.data)
        print(f"📊 Loaded data from CSV: {len(df)} rows")
    else:
        df = load_prices_from_yfinance(args.symbols)
        print(f"📊 Loaded data from yfinance: {len(df)} rows for {len(args.symbols)} symbols")
    
    # Build features
    print(f"🔧 Building features...")
    feats = build_features(df, freq=args.freq, horizon=args.horizon, winsor_q=args.winsor)
    print(f"   Features: {len(feats.columns)-1}")
    print(f"   Samples: {len(feats)}")
    
    # Run ensemble
    print(f"🚀 Running advanced ensemble...")
    res = walk_forward_stack(feats, n_splits=args.splits, embargo=args.embargo, use_xgb=(not args.no_xgb))

    print(f"\n📊 RESULTS:")
    print(f"  OOS R²: {res.r2_oos:.4f}")
    print(f"  OOS Samples: {res.n_oos}")
    print(f"  Models: {res.details['models']}")
    print(f"  Splits: {res.details['splits']}")
    print(f"  Embargo: {res.details['embargo']}")
    
    # Performance analysis
    if res.r2_oos > 0.035:
        print(f"\n🎉 EXCELLENT: R² > 0.035 achieved!")
    elif res.r2_oos > 0.02:
        print(f"\n✅ VERY GOOD: R² > 0.02 achieved!")
    elif res.r2_oos > 0.01:
        print(f"\n📈 GOOD: R² > 0.01 achieved!")
    elif res.r2_oos > 0:
        print(f"\n📈 POSITIVE: R² > 0 achieved!")
    else:
        print(f"\n⚠️  Still needs improvement")
    
    # Improvement hints
    if res.r2_oos < 0.035:
        print(f"\n💡 HINTS TO PUSH TOWARD 0.035+:")
        print("- Use weekly (--freq W) and try --horizon 6..8")
        print("- Increase --winsor to 0.03 on very noisy names")
        print("- Ensure XGBoost is installed (pip install xgboost)")
        print("- Try more splits (--splits 8) to stabilize the meta learner")
        print("- Add more symbols for better generalization")

if __name__ == "__main__":
    main()
