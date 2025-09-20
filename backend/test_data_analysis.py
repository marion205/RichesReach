#!/usr/bin/env python3
"""
Data analysis test to examine what the existing systems are returning
"""
import requests
import json
from typing import Dict, Any

BACKEND_URL = "http://localhost:8000"
GRAPHQL_ENDPOINT = f"{BACKEND_URL}/graphql/"

def make_request(query: str, variables: Dict = None) -> Dict:
    """Make a GraphQL request"""
    payload = {"query": query, "variables": variables or {}}
    response = requests.post(GRAPHQL_ENDPOINT, json=payload, timeout=30)
    return response.json()

def analyze_ai_recommendations():
    """Analyze the AI recommendations data"""
    print("🔍 ANALYZING AI RECOMMENDATIONS")
    print("=" * 50)
    
    query = """
    query GetAIRecommendations {
        aiRecommendations {
            portfolioAnalysis {
                totalValue
                numHoldings
                sectorBreakdown
                riskScore
                diversificationScore
            }
            buyRecommendations {
                symbol
                companyName
                recommendation
                confidence
                reasoning
                targetPrice
                currentPrice
                expectedReturn
            }
            sellRecommendations {
                symbol
                reasoning
            }
            rebalanceSuggestions {
                action
                currentAllocation
                suggestedAllocation
                reasoning
                priority
            }
            riskAssessment {
                overallRisk
                volatilityEstimate
                recommendations
            }
            marketOutlook {
                overallSentiment
                confidence
                keyFactors
            }
        }
    }
    """
    
    result = make_request(query)
    
    if "data" in result and "aiRecommendations" in result["data"]:
        ai_data = result["data"]["aiRecommendations"]
        
        print("✅ AI Recommendations Data Found")
        print(f"Portfolio Analysis:")
        portfolio = ai_data.get("portfolioAnalysis", {})
        print(f"  • Total Value: ${portfolio.get('totalValue', 0):,.2f}")
        print(f"  • Number of Holdings: {portfolio.get('numHoldings', 0)}")
        print(f"  • Risk Score: {portfolio.get('riskScore', 0)}")
        print(f"  • Diversification Score: {portfolio.get('diversificationScore', 0)}")
        print(f"  • Sector Breakdown: {portfolio.get('sectorBreakdown', {})}")
        
        print(f"\nBuy Recommendations ({len(ai_data.get('buyRecommendations', []))}):")
        for i, rec in enumerate(ai_data.get('buyRecommendations', [])[:5]):
            print(f"  {i+1}. {rec.get('symbol')} - {rec.get('companyName')}")
            print(f"     Confidence: {rec.get('confidence', 0):.2f}")
            print(f"     Expected Return: {rec.get('expectedReturn', 0):.2f}")
            print(f"     Reasoning: {rec.get('reasoning', 'N/A')[:50]}...")
        
        print(f"\nRisk Assessment:")
        risk = ai_data.get("riskAssessment", {})
        print(f"  • Overall Risk: {risk.get('overallRisk', 'N/A')}")
        print(f"  • Volatility Estimate: {risk.get('volatilityEstimate', 0)}")
        print(f"  • Recommendations: {risk.get('recommendations', [])}")
        
        print(f"\nMarket Outlook:")
        outlook = ai_data.get("marketOutlook", {})
        print(f"  • Sentiment: {outlook.get('overallSentiment', 'N/A')}")
        print(f"  • Confidence: {outlook.get('confidence', 0)}")
        print(f"  • Key Factors: {outlook.get('keyFactors', [])}")
        
    else:
        print("❌ No AI recommendations data found")
        if "errors" in result:
            print("Errors:", result["errors"])

def analyze_stocks_data():
    """Analyze the stocks data"""
    print("\n🔍 ANALYZING STOCKS DATA")
    print("=" * 50)
    
    # Test with AAPL
    query = """
    query GetStocks($search: String) {
        stocks(search: $search) {
            id
            symbol
            companyName
            sector
            marketCap
            peRatio
            dividendYield
            beginnerFriendlyScore
        }
    }
    """
    
    result = make_request(query, {"search": "AAPL"})
    
    if "data" in result and "stocks" in result["data"]:
        stocks = result["data"]["stocks"]
        print(f"✅ Found {len(stocks)} stocks for AAPL search")
        
        for stock in stocks:
            print(f"Stock: {stock.get('symbol')} - {stock.get('companyName')}")
            print(f"  • Sector: {stock.get('sector', 'N/A')}")
            print(f"  • Market Cap: ${stock.get('marketCap', 0):,.0f}")
            print(f"  • P/E Ratio: {stock.get('peRatio', 0)}")
            print(f"  • Dividend Yield: {stock.get('dividendYield', 0)}%")
            print(f"  • Beginner Score: {stock.get('beginnerFriendlyScore', 0)}")
    else:
        print("❌ No stocks data found")
        if "errors" in result:
            print("Errors:", result["errors"])

def analyze_beginner_friendly():
    """Analyze beginner friendly stocks"""
    print("\n🔍 ANALYZING BEGINNER FRIENDLY STOCKS")
    print("=" * 50)
    
    query = """
    query GetBeginnerFriendlyStocks {
        beginnerFriendlyStocks {
            id
            symbol
            companyName
            sector
            marketCap
            peRatio
            dividendYield
            beginnerFriendlyScore
        }
    }
    """
    
    result = make_request(query)
    
    if "data" in result and "beginnerFriendlyStocks" in result["data"]:
        stocks = result["data"]["beginnerFriendlyStocks"]
        print(f"✅ Found {len(stocks)} beginner friendly stocks")
        
        for stock in stocks:
            print(f"Stock: {stock.get('symbol')} - {stock.get('companyName')}")
            print(f"  • Sector: {stock.get('sector', 'N/A')}")
            print(f"  • Market Cap: ${stock.get('marketCap', 0):,.0f}")
            print(f"  • P/E Ratio: {stock.get('peRatio', 0)}")
            print(f"  • Dividend Yield: {stock.get('dividendYield', 0)}%")
            print(f"  • Beginner Score: {stock.get('beginnerFriendlyScore', 0)}")
            print()
    else:
        print("❌ No beginner friendly stocks data found")
        if "errors" in result:
            print("Errors:", result["errors"])

def test_ml_mutation_errors():
    """Test ML mutation error messages"""
    print("\n🔍 TESTING ML MUTATION ERRORS")
    print("=" * 50)
    
    query = """
    mutation GenerateMLPortfolioRecommendation {
        generateMlPortfolioRecommendation {
            success
            message
            recommendation {
                id
                riskProfile
            }
        }
    }
    """
    
    result = make_request(query)
    
    print("ML Mutation Response:")
    print(json.dumps(result, indent=2))
    
    if "data" in result:
        ml_data = result["data"].get("generateMlPortfolioRecommendation", {})
        print(f"\nSuccess: {ml_data.get('success', False)}")
        print(f"Message: {ml_data.get('message', 'No message')}")
    else:
        print("No data in response")

def main():
    """Run all analyses"""
    print("🧪 DATA ANALYSIS TEST SUITE")
    print("Analyzing existing system data and new ML mutation responses")
    print(f"Backend URL: {BACKEND_URL}")
    
    analyze_ai_recommendations()
    analyze_stocks_data()
    analyze_beginner_friendly()
    test_ml_mutation_errors()
    
    print("\n🎉 Data analysis completed!")

if __name__ == "__main__":
    main()
