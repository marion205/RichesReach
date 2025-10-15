# models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from decimal import Decimal

class BuyAllocation(BaseModel):
    symbol: str
    percentage: Decimal = Field(..., ge=0, le=100)
    reasoning: Optional[str] = None

class BuyRecommendation(BaseModel):
    symbol: str
    companyName: str
    recommendation: str
    confidence: Decimal = Field(..., ge=0, le=1)
    reasoning: Optional[str]
    targetPrice: Optional[Decimal]
    currentPrice: Optional[Decimal]
    expectedReturn: Optional[Decimal]  # DECIMAL in **decimal units**, e.g. 0.06 = 6%
    allocation: List[BuyAllocation] = []

class Risk(BaseModel):
    volatilityEstimate: Optional[Decimal]  # % as **number in percent units** (e.g. 12.8)
    maxDrawdownPct: Optional[Decimal]      # % as **number in percent units** (e.g. 32.0)

class ExpectedImpact(BaseModel):
    evPct: Optional[Decimal]   # **decimal units**, e.g. 0.042 = 4.2%
    evAbs: Optional[Decimal]
    per10k: Optional[Decimal]

class AssetAllocation(BaseModel):
    stocks: Optional[Decimal]
    bonds: Optional[Decimal]
    cash: Optional[Decimal]

class PortfolioAnalysis(BaseModel):
    totalValue: Optional[Decimal]
    numHoldings: Optional[int]
    sectorBreakdown: Optional[Dict[str, Decimal]]
    riskScore: Optional[Decimal]
    diversificationScore: Optional[Decimal]
    expectedImpact: Optional[ExpectedImpact]
    risk: Optional[Risk]
    assetAllocation: Optional[AssetAllocation]

class RiskAssessment(BaseModel):
    overallRisk: Optional[str]
    volatilityEstimate: Optional[Decimal]
    recommendations: Optional[List[str]]

class MarketOutlook(BaseModel):
    overallSentiment: Optional[str]
    confidence: Optional[Decimal]
    keyFactors: Optional[List[str]]

class AIRecommendations(BaseModel):
    portfolioAnalysis: Optional[PortfolioAnalysis]
    buyRecommendations: List[BuyRecommendation] = []
    sellRecommendations: Optional[List[Dict]]
    rebalanceSuggestions: Optional[List[Dict]]
    riskAssessment: Optional[RiskAssessment]
    marketOutlook: Optional[MarketOutlook]
    schemaVersion: str
