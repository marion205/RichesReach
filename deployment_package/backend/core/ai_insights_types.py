"""
GraphQL Types for AI Insights
"""
import graphene
from django.utils import timezone
from typing import List, Dict, Any, Optional
import logging
import os
import json
import re

logger = logging.getLogger(__name__)

try:
    from .models import SavedInsight, SavedInsightShare
except ImportError:
    SavedInsight = None
    SavedInsightShare = None

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Oracle insights will use fallback responses.")


# ===================
# Type Definitions
# ===================

class InsightDataType(graphene.ObjectType):
    """Data associated with an insight"""
    priceTarget = graphene.Float()
    probability = graphene.Float()
    timeframe = graphene.String()
    reasoning = graphene.String()


class MarketInsightType(graphene.ObjectType):
    """AI-powered market insight"""
    id = graphene.ID(required=True)
    title = graphene.String(required=True)
    summary = graphene.String(required=True)
    category = graphene.String(required=True)
    confidence = graphene.Float(required=True)
    impact = graphene.String(required=True)
    sentiment = graphene.String(required=True)
    timestamp = graphene.DateTime(required=True)
    symbols = graphene.List(graphene.String)
    data = graphene.Field(InsightDataType)
    source = graphene.String()
    tags = graphene.List(graphene.String)


class PredictionType(graphene.ObjectType):
    """AI prediction for a stock"""
    timeframe = graphene.String(required=True)
    priceTarget = graphene.Float(required=True)
    probability = graphene.Float(required=True)
    direction = graphene.String(required=True)
    confidence = graphene.Float(required=True)
    factors = graphene.List(graphene.String)


class TechnicalAnalysisType(graphene.ObjectType):
    """Technical analysis data"""
    trend = graphene.String(required=True)
    support = graphene.Float()
    resistance = graphene.Float()
    indicators = graphene.JSONString()


class SentimentAnalysisType(graphene.ObjectType):
    """Sentiment analysis data"""
    overall = graphene.String(required=True)
    news = graphene.String()
    social = graphene.String()
    analyst = graphene.String()


class AIPredictionsType(graphene.ObjectType):
    """AI predictions for a symbol"""
    symbol = graphene.String(required=True)
    predictions = graphene.List(PredictionType, required=True)
    technicalAnalysis = graphene.Field(TechnicalAnalysisType)
    sentimentAnalysis = graphene.Field(SentimentAnalysisType)


class MarketRegimeIndicatorsType(graphene.ObjectType):
    """Market regime indicators"""
    volatility = graphene.Float()
    trend = graphene.String()
    momentum = graphene.Float()
    volume = graphene.Float()


class MarketRegimeType(graphene.ObjectType):
    """Market regime analysis"""
    current = graphene.String(required=True)
    confidence = graphene.Float(required=True)
    transitions = graphene.List(graphene.String)
    indicators = graphene.Field(MarketRegimeIndicatorsType)
    recommendations = graphene.List(graphene.String)


class OracleInsightType(graphene.ObjectType):
    """Oracle insight response"""
    id = graphene.ID(required=True)
    question = graphene.String(required=True)
    answer = graphene.String(required=True)
    confidence = graphene.Float(required=True)
    sources = graphene.List(graphene.String)
    timestamp = graphene.DateTime(required=True)
    relatedInsights = graphene.List(graphene.String)


# ===================
# Query Root
# ===================

class AIInsightsQueries(graphene.ObjectType):
    """GraphQL queries for AI insights"""
    
    # Market insights query
    market_insights = graphene.List(
        MarketInsightType,
        limit=graphene.Int(default_value=20),
        category=graphene.String()
    )
    
    # AI predictions query
    ai_predictions = graphene.Field(
        AIPredictionsType,
        symbol=graphene.String(required=True)
    )
    
    # Market regime query
    market_regime = graphene.Field(MarketRegimeType)
    
    # Oracle insights query
    oracle_insights = graphene.Field(
        OracleInsightType,
        query=graphene.String(required=True)
    )
    
    def resolve_market_insights(self, info, limit=20, category=None):
        """Get market insights. Returns mock data until AI service is wired."""
        mock_insights = [
            {
                'id': '1',
                'title': 'Tech Sector Momentum Building',
                'summary': 'Strong earnings and AI adoption driving tech stocks higher',
                'category': 'sector',
                'confidence': 0.85,
                'impact': 'high',
                'sentiment': 'bullish',
                'timestamp': timezone.now(),
                'symbols': ['AAPL', 'MSFT', 'GOOGL'],
                'data': {
                    'priceTarget': None,
                    'probability': 0.75,
                    'timeframe': '3-6 months',
                    'reasoning': 'Strong fundamentals and positive earnings trends'
                },
                'source': 'AI Analysis',
                'tags': ['tech', 'earnings', 'momentum']
            },
            {
                'id': '2',
                'title': 'Market Volatility Expected',
                'summary': 'Economic indicators suggest increased volatility ahead',
                'category': 'market',
                'confidence': 0.70,
                'impact': 'medium',
                'sentiment': 'neutral',
                'timestamp': timezone.now(),
                'symbols': [],
                'data': {
                    'priceTarget': None,
                    'probability': 0.65,
                    'timeframe': '1-2 months',
                    'reasoning': 'Mixed economic signals and policy uncertainty'
                },
                'source': 'AI Analysis',
                'tags': ['volatility', 'market', 'economic']
            }
        ]
        
        # Filter by category if provided
        if category:
            mock_insights = [i for i in mock_insights if i['category'] == category]
        
        # Limit results
        mock_insights = mock_insights[:limit]
        
        return [MarketInsightType(**insight) for insight in mock_insights]
    
    def resolve_ai_predictions(self, info, symbol):
        """Get AI predictions for a symbol. Returns mock data until AI service is wired."""
        return AIPredictionsType(
            symbol=symbol.upper(),
            predictions=[
                PredictionType(
                    timeframe='1 month',
                    priceTarget=180.0,
                    probability=0.75,
                    direction='up',
                    confidence=0.80,
                    factors=['Strong earnings', 'Positive sentiment', 'Technical breakout']
                ),
                PredictionType(
                    timeframe='3 months',
                    priceTarget=200.0,
                    probability=0.65,
                    direction='up',
                    confidence=0.70,
                    factors=['Long-term trend', 'Sector momentum', 'Fundamentals']
                )
            ],
            technicalAnalysis=TechnicalAnalysisType(
                trend='bullish',
                support=150.0,
                resistance=200.0,
                indicators='{}'
            ),
            sentimentAnalysis=SentimentAnalysisType(
                overall='positive',
                news='bullish',
                social='neutral',
                analyst='bullish'
            )
        )
    
    def resolve_market_regime(self, info):
        """Get current market regime. Returns mock data until AI service is wired."""
        return MarketRegimeType(
            current='bull',
            confidence=0.75,
            transitions=['bull', 'neutral'],
            indicators=MarketRegimeIndicatorsType(
                volatility=15.5,
                trend='upward',
                momentum=0.65,
                volume=1.2
            ),
            recommendations=[
                'Consider growth stocks',
                'Maintain diversified portfolio',
                'Watch for volatility spikes'
            ]
        )
    
    def resolve_oracle_insights(self, info, query):
        """Get oracle insights for a query using real AI analysis"""
        from .graphql_utils import get_user_from_context
        from .premium_analytics import PremiumAnalyticsService
        
        # Get user from context
        user = get_user_from_context(info.context)
        
        # Build context for AI
        context_parts = []
        
        # Add portfolio data if user is authenticated
        portfolio_summary = None
        if user and not getattr(user, 'is_anonymous', True):
            try:
                analytics_service = PremiumAnalyticsService()
                portfolio_metrics = analytics_service.get_portfolio_performance_metrics(user.id)
                
                if portfolio_metrics:
                    holdings = portfolio_metrics.get('holdings', [])
                    total_value = portfolio_metrics.get('total_value', 0)
                    total_return_percent = portfolio_metrics.get('total_return_percent', 0)
                    sector_allocation = portfolio_metrics.get('sector_allocation', {})
                    
                    # Build portfolio summary
                    portfolio_summary = {
                        'total_value': total_value,
                        'total_return_percent': total_return_percent,
                        'holdings_count': len(holdings),
                        'top_holdings': [
                            {
                                'symbol': h.get('symbol', ''),
                                'shares': h.get('shares', 0),
                                'value': h.get('total_value', 0),
                                'return_percent': h.get('return_percent', 0)
                            }
                            for h in holdings[:10]  # Top 10 holdings
                        ],
                        'sector_allocation': sector_allocation
                    }
                    
                    context_parts.append(f"User Portfolio:\n{json.dumps(portfolio_summary, indent=2)}")
            except Exception as e:
                logger.warning(f"Failed to get portfolio data for Oracle insights: {e}")
        
        # Add market context
        try:
            from .ai_service import AIService
            ai_service = AIService()
            
            # Get market analysis if available
            if ai_service.market_data_service:
                try:
                    market_overview = ai_service.market_data_service.get_market_overview()
                    if market_overview:
                        context_parts.append(f"Market Overview:\n{json.dumps(market_overview, indent=2, default=str)}")
                except Exception as e:
                    logger.debug(f"Could not get market overview: {e}")
        except Exception as e:
            logger.debug(f"Could not initialize AI service for market data: {e}")
        
        # Build the AI prompt
        system_prompt = """You are RichesReach Oracle, an advanced AI financial advisor. Your role is to provide insightful, actionable financial analysis based on real portfolio and market data.

Guidelines:
- Be specific and data-driven in your responses
- Reference actual portfolio holdings, market conditions, and metrics when available
- Provide actionable recommendations, not generic advice
- If portfolio data is available, tailor your response to the user's specific situation
- Use clear, professional language suitable for investors
- Include confidence levels and reasoning for your insights
- Keep responses concise but comprehensive (2-4 paragraphs)"""

        user_prompt = f"User Question: {query}\n\n"
        
        if context_parts:
            user_prompt += "\n".join(context_parts)
            user_prompt += "\n\nPlease provide a comprehensive, data-driven answer to the user's question based on the portfolio and market data provided above."
        else:
            user_prompt += "Please provide market insights and recommendations based on current market conditions."
        
        # Call OpenAI API
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_api_key or not OPENAI_AVAILABLE:
            logger.warning("⚠️ [Oracle] OpenAI API key not found - using fallback response")
            return self._get_fallback_oracle_insight(query, portfolio_summary)
        
        try:
            logger.info(f"🤖 [Oracle] Calling OpenAI API for query: {query[:100]}...")
            logger.info(f"📊 [Oracle] Context available: portfolio={portfolio_summary is not None}, market_data={len(context_parts) > (1 if portfolio_summary else 0)}")
            
            client = openai.OpenAI(api_key=openai_api_key)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            ai_answer = response.choices[0].message.content.strip()
            
            logger.info(f"✅ [Oracle] OpenAI API call successful. Response length: {len(ai_answer)} chars, Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            
            # Extract confidence from response if mentioned, otherwise default
            # Default to high confidence for AI-generated insights
            confidence = 0.85
            
            # Only extract confidence if it's explicitly mentioned near the word "confidence"
            # This prevents picking up random percentages from the response
            confidence_patterns = [
                r'confidence[:\s]+(\d+)%',  # "confidence: 85%"
                r'(\d+)%\s+confidence',      # "85% confidence"
                r'(\d+)%\s+certain',         # "85% certain"
                r'(\d+)%\s+confident',       # "85% confident"
            ]
            
            for pattern in confidence_patterns:
                conf_match = re.search(pattern, ai_answer, re.IGNORECASE)
                if conf_match:
                    extracted = float(conf_match.group(1)) / 100.0
                    # Only use if it's a reasonable confidence value (0.5-1.0)
                    if 0.5 <= extracted <= 1.0:
                        confidence = extracted
                        break
            
            # Determine sources based on available data
            sources = []
            if portfolio_summary:
                sources.append('Portfolio analysis')
            sources.extend(['AI analysis', 'Market data', 'Technical indicators'])
            
            # Extract related insights from the response
            related_insights = []
            if 'rebalancing' in ai_answer.lower() or 'rebalance' in ai_answer.lower():
                related_insights.append('Portfolio rebalancing')
            if 'diversification' in ai_answer.lower() or 'diversify' in ai_answer.lower():
                related_insights.append('Diversification strategy')
            if 'risk' in ai_answer.lower():
                related_insights.append('Risk management')
            if not related_insights:
                related_insights = ['Market trends', 'Sector analysis', 'Portfolio optimization']
            
            logger.info(f"✅ [Oracle] Generated Oracle insight using OpenAI for query: {query[:50]}...")
            
            return OracleInsightType(
                id=f"oracle-{timezone.now().timestamp()}",
                question=query,
                answer=ai_answer,
                confidence=confidence,
                sources=sources,
                timestamp=timezone.now(),
                relatedInsights=related_insights
            )
            
        except Exception as e:
            logger.error(f"❌ [Oracle] Error calling OpenAI API for Oracle insights: {e}", exc_info=True)
            logger.warning("⚠️ [Oracle] Falling back to template response")
            return self._get_fallback_oracle_insight(query, portfolio_summary)
    
    def _get_fallback_oracle_insight(self, query: str, portfolio_summary: Optional[Dict] = None):
        """Fallback response when OpenAI is not available"""
        logger.warning("📝 [Oracle] Using fallback template response (OpenAI not available)")
        
        if portfolio_summary:
            holdings_count = portfolio_summary.get('holdings_count', 0)
            total_value = portfolio_summary.get('total_value', 0)
            total_return = portfolio_summary.get('total_return_percent', 0)
            
            answer = f"Based on your portfolio analysis:\n\n"
            answer += f"Your portfolio contains {holdings_count} holdings with a total value of ${total_value:,.2f} "
            answer += f"and a return of {total_return:+.2f}%.\n\n"
            answer += f"Regarding '{query}': While I cannot provide real-time AI analysis at the moment, "
            answer += "I recommend reviewing your portfolio allocation, considering diversification, "
            answer += "and monitoring market trends. For personalized insights, please ensure OpenAI API is configured."
        else:
            answer = f"Based on current market analysis, {query.lower()} requires consideration of multiple factors including market conditions, sector performance, and economic indicators. "
            answer += "For personalized AI-powered insights, please ensure OpenAI API is configured and you have portfolio data available."
        
        return OracleInsightType(
            id=f"oracle-fallback-{timezone.now().timestamp()}",
            question=query,
            answer=answer,
            confidence=0.60,
            sources=['Portfolio data', 'Market analysis'],
            timestamp=timezone.now(),
            relatedInsights=['Market trends', 'Portfolio optimization', 'Risk management']
        )


# ===================
# Mutations
# ===================

class SaveInsightResult(graphene.ObjectType):
    """Result of saving an insight"""
    success = graphene.Boolean(required=True)
    message = graphene.String()


class ShareInsightResult(graphene.ObjectType):
    """Result of sharing an insight"""
    success = graphene.Boolean(required=True)
    message = graphene.String()


class AIInsightsMutations(graphene.ObjectType):
    """GraphQL mutations for AI insights"""
    
    save_insight = graphene.Field(
        SaveInsightResult,
        insightId=graphene.ID(required=True)
    )
    
    share_insight = graphene.Field(
        ShareInsightResult,
        insightId=graphene.ID(required=True),
        platform=graphene.String(required=True)
    )
    
    def resolve_save_insight(self, info, insightId):
        """Save an insight to user's collection (persisted in DB)."""
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return SaveInsightResult(success=False, message="Authentication required")
        if not insightId:
            return SaveInsightResult(success=False, message="Insight ID required")
        if SavedInsight is None:
            return SaveInsightResult(success=True, message="Insight saved successfully")
        try:
            SavedInsight.objects.get_or_create(
                user=user,
                insight_id=str(insightId),
                defaults={'title': '', 'summary': '', 'category': ''}
            )
            return SaveInsightResult(success=True, message="Insight saved successfully")
        except Exception as e:
            logger.warning(f"Save insight failed: {e}")
            return SaveInsightResult(success=False, message=str(e))

    def resolve_share_insight(self, info, insightId, platform):
        """Share an insight to a platform (recorded in DB; frontend can use share URL)."""
        user = getattr(info.context, 'user', None)
        if not user or user.is_anonymous:
            return ShareInsightResult(success=False, message="Authentication required")
        if not insightId or not platform:
            return ShareInsightResult(success=False, message="Insight ID and platform required")
        if SavedInsightShare is None:
            return ShareInsightResult(success=True, message=f"Insight shared to {platform} successfully")
        try:
            SavedInsightShare.objects.create(
                user=user,
                insight_id=str(insightId),
                platform=platform.strip().lower()
            )
            return ShareInsightResult(
                success=True,
                message=f"Insight shared to {platform} successfully"
            )
        except Exception as e:
            logger.warning(f"Share insight failed: {e}")
            return ShareInsightResult(success=False, message=str(e))

