# schema.py
import graphene
from graphene import ObjectType, Field, List, Float, String, Int, Decimal as GDecimal
from settings import settings
from typing import Optional
from models import AIRecommendations, BuyRecommendation as BRModel, PortfolioAnalysis as PAModel, ExpectedImpact as EIModel, Risk as RiskModel, AssetAllocation as AAModel, RiskAssessment as RAModel, MarketOutlook as MOModel
from policy import policy_from_profile, passes_emergency_floor
from quant.factors import compute_factors, blend_signal
from quant.risk import shrink_cov, ex_ante_vol, factor_exposures, stress_scenarios
from quant.optimizer import mean_variance_tc
from clients.market import market
from decimal import Decimal
import pandas as pd
import numpy as np

# Graphene types
class GBuyAllocation(graphene.ObjectType):
    symbol = graphene.String()
    percentage = GDecimal()
    reasoning = graphene.String()

class GBuyRecommendation(graphene.ObjectType):
    symbol = graphene.String()
    companyName = graphene.String()
    recommendation = graphene.String()
    confidence = GDecimal()
    reasoning = graphene.String()
    targetPrice = GDecimal()
    currentPrice = GDecimal()
    expectedReturn = GDecimal()     # decimal units, e.g. 0.06
    allocation = graphene.List(GBuyAllocation)
    whyThisSize = graphene.String()
    factorContrib = graphene.JSONString()  # {"momentum": 0.8, "value": 0.3, ...}
    tcPreview = GDecimal()                 # est transaction cost percent for this name

class GRisk(graphene.ObjectType):
    volatilityEstimate = GDecimal()
    maxDrawdownPct = GDecimal()

class GExpectedImpact(graphene.ObjectType):
    evPct = GDecimal()  # decimal units
    evAbs = GDecimal()
    per10k = GDecimal()

class GAssetAllocation(graphene.ObjectType):
    stocks = GDecimal()
    bonds = GDecimal()
    cash = GDecimal()

class GPortfolioAnalysis(graphene.ObjectType):
    totalValue = GDecimal()
    numHoldings = Int()
    sectorBreakdown = graphene.JSONString()
    riskScore = GDecimal()
    diversificationScore = GDecimal()
    expectedImpact = Field(GExpectedImpact)
    risk = Field(GRisk)
    assetAllocation = Field(GAssetAllocation)

class GRiskAssessment(graphene.ObjectType):
    overallRisk = String()
    volatilityEstimate = GDecimal()
    recommendations = graphene.List(String)

class GMarketOutlook(graphene.ObjectType):
    overallSentiment = String()
    confidence = GDecimal()
    keyFactors = graphene.List(String)

class GAIRecommendations(graphene.ObjectType):
    portfolioAnalysis = Field(GPortfolioAnalysis)
    buyRecommendations = graphene.List(GBuyRecommendation)
    sellRecommendations = graphene.List(graphene.JSONString)
    rebalanceSuggestions = graphene.List(graphene.JSONString)
    riskAssessment = Field(GRiskAssessment)
    marketOutlook = Field(GMarketOutlook)
    schemaVersion = String()

class Query(ObjectType):
    aiRecommendations = Field(GAIRecommendations)

    async def resolve_aiRecommendations(root, info):
        # 1) Fetch user profile from context (already authenticated, Graphene typical pattern)
        user = info.context["user"]
        profile = user["incomeProfile"]  # ensure you attach this in FastAPI middleware
        liquid_cash = user.get("liquidCashUSD", Decimal("0"))
        profile = {
            **profile,
            "liquidCashUSD": liquid_cash,
            "monthlyContributionUSD": user.get("monthlyContributionUSD", Decimal("0"))
        }

        policy = policy_from_profile(profile)
        if not passes_emergency_floor(profile):
            # No equity buys if cash floor unmet
            return GAIRecommendations(
                portfolioAnalysis=GPortfolioAnalysis(
                    totalValue=Decimal("0"),
                    numHoldings=0,
                    expectedImpact=GExpectedImpact(evPct=Decimal("0"), evAbs=Decimal("0"), per10k=Decimal("0")),
                    risk=GRisk(volatilityEstimate=Decimal("0"), maxDrawdownPct=Decimal("0")),
                ),
                buyRecommendations=[],
                riskAssessment=GRiskAssessment(
                    overallRisk="HIGH",
                    volatilityEstimate=Decimal("0"),
                    recommendations=["Build emergency cash first; equities paused by policy."]
                ),
                marketOutlook=GMarketOutlook(overallSentiment="NEUTRAL", confidence=Decimal("0.5")),
                schemaVersion=settings.SCHEMA_VERSION
            )

        # 2) Universe (avoid microcaps / high-IV if policy says so)
        symbols = ["AAPL","MSFT","GOOGL","AMZN","META","NVDA","JPM","PG","JNJ","XLF","XLV","VTI"]
        # TODO: filter by market cap, iv, etc. from stored fundamentals
        # 3) Data pull with caching
        quotes = {}
        for s in symbols:
            q = await market.finnhub_quote(s)
            quotes[s] = q["value"]["c"]

        prices_now = pd.Series(quotes).fillna(0)
        total_value = Decimal("10000")  # get from portfolio or broker link
        prev_weights = pd.Series(np.zeros(len(symbols)), index=symbols)
        prev_weights["VTI"] = 1.0  # example existing holding as cash proxy alternative

        # 4) Factors + blended signal
        # For demo, fake fundamentals; in prod, keep in Redis with TTL
        df = pd.DataFrame(index=symbols, data={
            "mcap": np.random.lognormal(11, 1, len(symbols))*1e6,
            "pe": np.random.uniform(10, 40, len(symbols)),
            "pb": np.random.uniform(1, 10, len(symbols)),
            "roe": np.random.uniform(0.05, 0.25, len(symbols)),
            "gross_margin": np.random.uniform(0.2, 0.6, len(symbols)),
            "vol_60d": np.random.uniform(0.15, 0.6, len(symbols)),
            "ret_12m": np.random.uniform(-0.2, 0.6, len(symbols)),
            "ret_1m": np.random.uniform(-0.1, 0.2, len(symbols)),
        })
        factors = compute_factors(df)
        weights_map = {"momentum":0.35, "value":0.25, "quality":0.2, "size":0.1, "low_vol":0.1}
        signal = blend_signal(factors, weights_map)

        # 5) Expected returns: map signal → ER (linear mapping)
        mu = (0.05 + 0.10 * (signal - signal.mean())/ (signal.std()+1e-9)).clip(-0.05, 0.25)  # annualized decimals

        # 6) Risk (covariance, shrinkage)
        # In prod: build from daily returns history; here stub with diagonal vol
        rets = pd.DataFrame(np.random.normal(0, 0.02, (252, len(symbols))), columns=symbols)
        cov = shrink_cov(rets)

        # 7) Transaction costs (spread + slippage)
        tc_perc = pd.Series(0.001, index=symbols)  # 10 bps baseline
        tc_perc.loc[["NVDA","JPM"]] = 0.0007      # liquid names cheaper

        # 8) Sector map (stub)
        sector = pd.Series({
            "AAPL":"Tech","MSFT":"Tech","GOOGL":"Tech","AMZN":"ConsDisc","META":"Tech","NVDA":"Tech",
            "JPM":"Financials","PG":"Consumer","JNJ":"Healthcare","XLF":"Financials","XLV":"Healthcare","VTI":"ETF"
        })

        # 9) Optimizer with policy constraints
        w_star = mean_variance_tc(
            mu=mu,
            cov=cov,
            prev_weights=prev_weights.reindex(mu.index).fillna(0),
            sector=sector.reindex(mu.index).fillna("Other"),
            tc_perc=tc_perc.reindex(mu.index).fillna(0.002),
            max_name=float(policy["max_single_name_pct"]),
            max_sector=float(policy["sector_cap_pct"]),
            turnover_budget=float(policy["turnover_budget_pct"]),
            cash_min=0.02,
        )

        # 10) Explainability surfaces
        exposures = factor_exposures(w_star, factors)
        vol_est = ex_ante_vol(w_star.values, cov)

        # 11) Build buy list (only positive deltas from prev to target)
        delta = (w_star - prev_weights).sort_values(ascending=False)
        picks = []
        for sym, add_w in delta.items():
            if add_w <= 1e-4: continue
            rec = BRModel(
                symbol=sym,
                companyName=sym,  # replace from profile2
                recommendation="BUY",
                confidence=Decimal("0.7"),
                reasoning="Blend of momentum/value/quality with cost-aware sizing.",
                targetPrice=None,
                currentPrice=Decimal(str(prices_now[sym] or 0)),
                expectedReturn=Decimal(str(float(mu[sym]))),  # decimal units
                allocation=[{"symbol": sym, "percentage": Decimal(str(round(float(add_w*100), 1))) }]
            )
            picks.append(rec)

        # 12) Expected Impact (portfolio-level)
        port_ev = float((w_star.values * mu.values).sum())   # decimal
        per10k = Decimal(str(round(10000.0 * port_ev, 2)))
        evPct = Decimal(str(round(port_ev, 6)))
        evAbs = Decimal(str(round(float(total_value) * port_ev, 2)))

        # 13) Graph output
        g_picks = []
        for br in picks:
            # factor contribs for this name
            contrib = factors.loc[br.symbol, ["momentum","value","quality","size","low_vol"]].round(2).to_dict()
            tc = float(tc_perc.get(br.symbol, 0.001))
            g_picks.append(GBuyRecommendation(
                symbol=br.symbol,
                companyName=br.companyName,
                recommendation=br.recommendation,
                confidence=br.confidence,
                reasoning=br.reasoning,
                targetPrice=br.targetPrice,
                currentPrice=br.currentPrice,
                expectedReturn=br.expectedReturn,
                allocation=[GBuyAllocation(**a) for a in br.allocation],
                whyThisSize=f"Signal {round(float(signal[br.symbol]),2)}σ, TC {int(tc*10000)} bps, name cap {int(float(policy['max_single_name_pct'])*100)}%, turnover budget {int(float(policy['turnover_budget_pct'])*100)}%.",
                factorContrib=contrib,
                tcPreview=Decimal(str(tc))
            ))

        analysis = GPortfolioAnalysis(
            totalValue=total_value,
            numHoldings=len(symbols),
            sectorBreakdown={s: float(w_star[sector==s].sum()*100) for s in sector.unique()},
            riskScore=Decimal("0.0"),
            diversificationScore=Decimal("0.0"),
            expectedImpact=GExpectedImpact(evPct=evPct, evAbs=evAbs, per10k=per10k),
            risk=GRisk(volatilityEstimate=Decimal(str(round(vol_est*100,1))), maxDrawdownPct=None),
            assetAllocation=GAssetAllocation(stocks=Decimal(str(round(float(w_star.drop("VTI", errors="ignore").sum()*100),1))), bonds=None, cash=Decimal("0")) # example
        )

        return GAIRecommendations(
            portfolioAnalysis=analysis,
            buyRecommendations=g_picks,
            sellRecommendations=[],
            rebalanceSuggestions=[],
            riskAssessment=GRiskAssessment(
                overallRisk="MODERATE", volatilityEstimate=Decimal(str(round(vol_est*100,1))),
                recommendations=["Diversify by sector", "Respect turnover budget"]
            ),
            marketOutlook=GMarketOutlook(overallSentiment="BULLISH", confidence=Decimal("0.65"), keyFactors=["Earnings","Liquidity"]),
            schemaVersion=settings.SCHEMA_VERSION
        )

schema = graphene.Schema(query=Query)
