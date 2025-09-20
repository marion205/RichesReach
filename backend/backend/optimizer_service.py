# file: optimizer_service.py
# run: uvicorn optimizer_service:app --host 0.0.0.0 --port 8088
from typing import List, Dict, Optional
from math import sqrt
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Try CVXPY; fallback to greedy
try:
    import cvxpy as cp
    HAVE_CVXPY = True
except Exception:
    HAVE_CVXPY = False

app = FastAPI(title="Personalized Quant Optimizer", version="0.1.0")

# ---------- Schemas ----------
class Ticker(BaseModel):
    symbol: str
    score: float = Field(..., description="Personalized score (factor+AI blend)")
    sector: str = "Other"
    vol: Optional[float] = Field(None, description="Annualized stdev as decimal, e.g. 0.20")

class Policy(BaseModel):
    volTarget: Optional[float] = Field(None, description="Annualized volatility target (e.g., 0.13)")
    nameCap: float = Field(0.06, description="Max weight per name")
    sectorCap: float = Field(0.30, description="Max weight per sector")
    turnoverBudget: Optional[float] = Field(None, description="||w - w_prev||_1 <= budget")
    sectorOverrides: Optional[Dict[str, float]] = None  # e.g. {"Technology":0.25}

class OptimizeRequest(BaseModel):
    tickers: List[Ticker]
    policy: Policy
    prevWeights: Optional[Dict[str, float]] = None  # map symbol->weight
    # Optional covariance override: upper triangular packed list by row or dense? Keep simple: none.

class NameWeight(BaseModel):
    symbol: str
    weight: float

class OptimizeResponse(BaseModel):
    status: str
    weights: List[NameWeight]
    portfolioVol: float
    objective: float
    diagnostics: Dict[str, float]
    sectorWeights: Dict[str, float]

# ---------- Helpers ----------
def build_cov(tickers: List[Ticker]) -> np.ndarray:
    """
    Diagonal vol with simple sector correlation structure:
    same-sector rho=0.6, cross-sector rho=0.2 (heuristic).
    """
    n = len(tickers)
    vols = np.array([t.vol if (t.vol and t.vol > 0) else 0.20 for t in tickers])  # default 20%
    D = np.diag(vols)
    corr = np.full((n, n), 0.2)
    sectors = [t.sector or "Other" for t in tickers]
    for i in range(n):
        corr[i, i] = 1.0
        for j in range(i+1, n):
            if sectors[i] == sectors[j]:
                corr[i, j] = corr[j, i] = 0.6
    Sigma = D @ corr @ D
    return Sigma

def greedy_allocate(scores, sectors, name_cap, sector_cap):
    """Fallback if CVXPY is unavailable. Score-sorted, cap-aware, fills to 100%."""
    n = len(scores)
    order = np.argsort(-scores)
    w = np.zeros(n)
    sector_tot = {}
    remain = 1.0
    for idx in order:
        s = sectors[idx]
        cap_s = sector_cap
        cap_s = cap_s  # could allow overrides upstream
        take = min(name_cap, remain, cap_s - sector_tot.get(s, 0.0))
        if take > 1e-9:
            w[idx] = take
            sector_tot[s] = sector_tot.get(s, 0.0) + take
            remain -= take
        if remain <= 1e-9:
            break
    # If not fully invested (caps too tight), spread residual
    if remain > 1e-6:
        for idx in order:
            room = name_cap - w[idx]
            if room <= 0: continue
            s = sectors[idx]; sroom = sector_cap - sector_tot.get(s,0.0)
            add = min(room, sroom, remain)
            if add > 1e-9:
                w[idx] += add
                sector_tot[s] = sector_tot.get(s,0.0) + add
                remain -= add
                if remain <= 1e-9:
                    break
    return w

# ---------- Core ----------
@app.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    if not req.tickers:
        raise HTTPException(400, "No tickers provided")
    n = len(req.tickers)
    symbols = [t.symbol for t in req.tickers]
    sectors = [t.sector or "Other" for t in req.tickers]
    scores = np.array([float(t.score) for t in req.tickers])
    Sigma = build_cov(req.tickers)

    # risk aversion: if volTarget provided, solve both a target and penalized version
    # we'll default lambda from target so OSQP behaves nicely, but keep a variance cap too
    volTarget = req.policy.volTarget
    nameCap = float(req.policy.nameCap)
    sectorCapDefault = float(req.policy.sectorCap)
    sectorOverrides = req.policy.sectorOverrides or {}
    sectorCaps = [sectorOverrides.get(sectors[i], sectorCapDefault) for i in range(n)]

    prev_map = req.prevWeights or {}
    w_prev = np.array([prev_map.get(sym, 0.0) for sym in symbols])
    turnoverBudget = req.policy.turnoverBudget

    # Build sector matrix A so A @ w = sector weights
    unique_sectors = sorted(set(sectors))
    A = np.zeros((len(unique_sectors), n))
    for i, s in enumerate(unique_sectors):
        A[i, [j for j in range(n) if sectors[j] == s]] = 1.0

    if HAVE_CVXPY:
        w = cp.Variable(n, nonneg=True)
        # objective: minimize  -score^T w + λ · wᵀΣw
        # derive λ from volTarget if provided; else pick a mild risk penalization
        # quick calibration: set λ so that at w = 1/N, variance term ~ score term scale
        base_lambda = 1.0
        if volTarget:
            base_lambda = 0.5 / max(1e-6, volTarget**2)  # smaller target => larger penalty

        obj = -scores @ w + base_lambda * cp.quad_form(w, Sigma)

        constraints = [
            cp.sum(w) == 1.0,
            w <= nameCap
        ]
        # sector caps
        for i, s in enumerate(unique_sectors):
            cap = sectorOverrides.get(s, sectorCapDefault)
            if cap is not None:
                constraints.append(A[i] @ w <= cap)
        # variance cap if target provided
        if volTarget:
            constraints.append(cp.quad_form(w, Sigma) <= volTarget**2 + 1e-8)
        # turnover budget
        if turnoverBudget is not None:
            constraints.append(cp.norm1(w - w_prev) <= float(turnoverBudget))

        prob = cp.Problem(cp.Minimize(obj), constraints)
        try:
            prob.solve(solver=cp.OSQP, verbose=False)
            if w.value is None:
                # try ECOS as backup
                prob.solve(solver=cp.ECOS, verbose=False)
        except Exception as e:
            # fall through to greedy
            pass

        if w.value is not None:
            w_opt = np.maximum(0.0, np.array(w.value).reshape(-1))
            w_opt = w_opt / max(1e-9, w_opt.sum())
        else:
            w_opt = greedy_allocate(scores, sectors, nameCap, sectorCapDefault)
    else:
        w_opt = greedy_allocate(scores, sectors, nameCap, sectorCapDefault)

    port_var = float(w_opt @ Sigma @ w_opt)
    port_vol = sqrt(max(0.0, port_var))
    sector_w = A @ w_opt
    sector_weights = {unique_sectors[i]: float(sector_w[i]) for i in range(len(unique_sectors))}
    obj_val = float(-scores @ w_opt + (0.0 if not HAVE_CVXPY else 0))  # informational

    return OptimizeResponse(
        status="ok",
        weights=[NameWeight(symbol=symbols[i], weight=float(w_opt[i])) for i in range(n)],
        portfolioVol=port_vol,
        objective=obj_val,
        diagnostics={
            "n": float(n),
            "cvxpy": float(1 if HAVE_CVXPY else 0),
            "variance": float(port_var),
        },
        sectorWeights=sector_weights
    )

@app.get("/health")
def health():
    return {"status": "ok", "cvxpy_available": HAVE_CVXPY}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)
