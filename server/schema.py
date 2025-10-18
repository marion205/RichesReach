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

# Rust Stock Analysis Types
class GTechnicalIndicators(graphene.ObjectType):
    rsi = GDecimal()
    macd = GDecimal()
    macdSignal = GDecimal()
    macdHistogram = GDecimal()
    sma20 = GDecimal()
    sma50 = GDecimal()
    ema12 = GDecimal()
    ema26 = GDecimal()
    bollingerUpper = GDecimal()
    bollingerLower = GDecimal()
    bollingerMiddle = GDecimal()

class GFundamentalAnalysis(graphene.ObjectType):
    valuationScore = GDecimal()
    growthScore = GDecimal()
    stabilityScore = GDecimal()
    dividendScore = GDecimal()
    debtScore = GDecimal()

class GRustStockAnalysis(graphene.ObjectType):
    symbol = String()
    beginnerFriendlyScore = GDecimal()
    riskLevel = String()
    recommendation = String()
    technicalIndicators = Field(GTechnicalIndicators)
    fundamentalAnalysis = Field(GFundamentalAnalysis)
    reasoning = String()

class Query(ObjectType):
    aiRecommendations = Field(GAIRecommendations)
    rustStockAnalysis = Field(GRustStockAnalysis, symbol=String(required=True))

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

    async def resolve_rustStockAnalysis(root, info, symbol):
        """Resolve rust stock analysis for a given symbol"""
        try:
            # Get current price from market data
            quote_data = await market.finnhub_quote(symbol)
            current_price = quote_data.get("value", {}).get("c", 100.0) if quote_data else 100.0
            
            # Generate mock technical indicators
            import random
            technical_indicators = GTechnicalIndicators(
                rsi=Decimal(str(round(random.uniform(30, 70), 2))),
                macd=Decimal(str(round(random.uniform(-2, 2), 4))),
                macdSignal=Decimal(str(round(random.uniform(-1.5, 1.5), 4))),
                macdHistogram=Decimal(str(round(random.uniform(-0.5, 0.5), 4))),
                sma20=Decimal(str(round(current_price * random.uniform(0.95, 1.05), 2))),
                sma50=Decimal(str(round(current_price * random.uniform(0.90, 1.10), 2))),
                ema12=Decimal(str(round(current_price * random.uniform(0.96, 1.04), 2))),
                ema26=Decimal(str(round(current_price * random.uniform(0.92, 1.08), 2))),
                bollingerUpper=Decimal(str(round(current_price * 1.02, 2))),
                bollingerLower=Decimal(str(round(current_price * 0.98, 2))),
                bollingerMiddle=Decimal(str(round(current_price, 2)))
            )
            
            # Generate mock fundamental analysis
            fundamental_analysis = GFundamentalAnalysis(
                valuationScore=Decimal(str(round(random.uniform(0.3, 0.9), 2))),
                growthScore=Decimal(str(round(random.uniform(0.2, 0.8), 2))),
                stabilityScore=Decimal(str(round(random.uniform(0.4, 0.9), 2))),
                dividendScore=Decimal(str(round(random.uniform(0.1, 0.7), 2))),
                debtScore=Decimal(str(round(random.uniform(0.2, 0.8), 2)))
            )
            
            # Determine recommendation based on scores
            avg_score = (float(technical_indicators.rsi) / 100 + 
                        float(fundamental_analysis.valuationScore) + 
                        float(fundamental_analysis.growthScore)) / 3
            
            if avg_score > 0.7:
                recommendation = "STRONG_BUY"
                risk_level = "LOW"
                reasoning = f"{symbol} shows strong technical and fundamental indicators with excellent growth potential."
            elif avg_score > 0.5:
                recommendation = "BUY"
                risk_level = "MODERATE"
                reasoning = f"{symbol} presents a good investment opportunity with balanced risk-reward profile."
            elif avg_score > 0.3:
                recommendation = "HOLD"
                risk_level = "MODERATE"
                reasoning = f"{symbol} shows mixed signals, consider holding current position."
            else:
                recommendation = "SELL"
                risk_level = "HIGH"
                reasoning = f"{symbol} shows concerning technical and fundamental indicators."
            
            return GRustStockAnalysis(
                symbol=symbol,
                beginnerFriendlyScore=Decimal(str(round(random.uniform(0.4, 0.9), 2))),
                riskLevel=risk_level,
                recommendation=recommendation,
                technicalIndicators=technical_indicators,
                fundamentalAnalysis=fundamental_analysis,
                reasoning=reasoning
            )
            
        except Exception as e:
            print(f"Error in rustStockAnalysis resolver: {e}")
            # Return a default analysis
            return GRustStockAnalysis(
                symbol=symbol,
                beginnerFriendlyScore=Decimal("0.5"),
                riskLevel="MODERATE",
                recommendation="HOLD",
                technicalIndicators=GTechnicalIndicators(
                    rsi=Decimal("50.0"),
                    macd=Decimal("0.0"),
                    macdSignal=Decimal("0.0"),
                    macdHistogram=Decimal("0.0"),
                    sma20=Decimal("100.0"),
                    sma50=Decimal("100.0"),
                    ema12=Decimal("100.0"),
                    ema26=Decimal("100.0"),
                    bollingerUpper=Decimal("102.0"),
                    bollingerLower=Decimal("98.0"),
                    bollingerMiddle=Decimal("100.0")
                ),
                fundamentalAnalysis=GFundamentalAnalysis(
                    valuationScore=Decimal("0.5"),
                    growthScore=Decimal("0.5"),
                    stabilityScore=Decimal("0.5"),
                    dividendScore=Decimal("0.5"),
                    debtScore=Decimal("0.5")
                ),
                reasoning=f"Analysis for {symbol} is currently unavailable. Please try again later."
            )

schema = graphene.Schema(query=Query)
