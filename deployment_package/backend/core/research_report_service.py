"""
Automated Research Report Generation Service
Creates comprehensive research reports for stocks with PDF export
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from .models import Stock
from .enhanced_stock_service import EnhancedStockService
from .premium_analytics import PremiumAnalyticsService
from .consumer_strength_service import ConsumerStrengthService
from .spending_habits_service import SpendingHabitsService
import json

logger = logging.getLogger(__name__)


class ResearchReportService:
    """Service for generating automated research reports"""
    
    CACHE_TTL = 3600  # 1 hour
    
    def __init__(self):
        self.stock_service = EnhancedStockService()
        self.analytics_service = PremiumAnalyticsService()
        try:
            self.consumer_strength_service = ConsumerStrengthService()
        except Exception as e:
            logger.warning(f"ConsumerStrengthService not available: {e}")
            self.consumer_strength_service = None
    
    def generate_stock_report(
        self,
        symbol: str,
        user_id: Optional[int] = None,
        report_type: str = 'comprehensive'  # 'quick', 'comprehensive', 'deep_dive'
    ) -> Dict[str, Any]:
        """
        Generate comprehensive research report for a stock
        
        Returns:
        {
            'symbol': str,
            'company_name': str,
            'generated_at': datetime,
            'report_type': str,
            'executive_summary': str,
            'sections': {
                'overview': {...},
                'financials': {...},
                'technical_analysis': {...},
                'fundamental_analysis': {...},
                'ai_insights': {...},
                'consumer_strength': {...},
                'risk_assessment': {...},
                'recommendation': {...},
            },
            'key_metrics': {...},
            'charts_data': {...},
        }
        """
        cache_key = f"research_report:{symbol}:{report_type}:{user_id or 'anon'}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            # Use defer() to avoid loading current_price field that doesn't exist in DB
            stock = Stock.objects.defer('current_price').get(symbol=symbol.upper())
            
            # Fetch real-time data from APIs
            import asyncio
            import os
            import requests
            
            # Get current price and other real-time data
            current_price = None
            pe_ratio = None
            market_cap = None
            volatility = None
            sector = stock.sector or 'Unknown'
            
            # Try to get real-time price (async method)
            try:
                price_data = asyncio.run(self.stock_service.get_real_time_price(symbol))
                if price_data:
                    current_price = price_data.get('price')
            except Exception as e:
                logger.warning(f"Could not get real-time price for {symbol}: {e}")
            
            # Fetch comprehensive financial data from Alpha Vantage OVERVIEW
            alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY') or os.getenv('ALPHA_VANTAGE_KEY')
            if alpha_vantage_key:
                try:
                    av_url = "https://www.alphavantage.co/query"
                    av_params = {
                        'function': 'OVERVIEW',
                        'symbol': symbol.upper(),
                        'apikey': alpha_vantage_key
                    }
                    av_response = requests.get(av_url, params=av_params, timeout=10)
                    if av_response.ok:
                        av_data = av_response.json()
                        if av_data and 'Note' not in av_data and 'Information' not in av_data:
                            # Extract real data
                            if av_data.get('PERatio'):
                                pe_ratio = float(av_data['PERatio'])
                            if av_data.get('MarketCapitalization'):
                                market_cap = float(av_data['MarketCapitalization'])
                            if av_data.get('Sector') and av_data['Sector'] != 'None':
                                sector = av_data['Sector']
                            if not current_price and av_data.get('52WeekHigh') and av_data.get('52WeekLow'):
                                # Estimate current price from 52-week range
                                high = float(av_data['52WeekHigh'])
                                low = float(av_data['52WeekLow'])
                                current_price = (high + low) / 2
                            logger.info(f"✅ Fetched real financial data from Alpha Vantage for {symbol}")
                except Exception as e:
                    logger.warning(f"Could not fetch Alpha Vantage data for {symbol}: {e}")
            
            # Calculate volatility if we have price data
            if current_price:
                try:
                    # Use Finnhub to get recent price history for volatility calculation
                    finnhub_key = os.getenv('FINNHUB_API_KEY')
                    if finnhub_key:
                        finnhub_url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={finnhub_key}"
                        finnhub_response = requests.get(finnhub_url, timeout=5)
                        if finnhub_response.ok:
                            finnhub_data = finnhub_response.json()
                            if finnhub_data.get('h') and finnhub_data.get('l'):
                                high = finnhub_data['h']
                                low = finnhub_data['l']
                                # Calculate daily volatility as percentage
                                if current_price > 0:
                                    daily_range = (high - low) / current_price
                                    volatility = daily_range * 100  # Convert to percentage
                except Exception as e:
                    logger.warning(f"Could not calculate volatility for {symbol}: {e}")
            
            # Get spending analysis if user is authenticated
            spending_analysis = None
            if user_id:
                spending_service = SpendingHabitsService()
                spending_analysis = spending_service.analyze_spending_habits(user_id, months=3)
            
            # Get Consumer Strength Score
            consumer_strength = None
            if self.consumer_strength_service:
                try:
                    consumer_strength = self.consumer_strength_service.calculate_consumer_strength(
                        symbol, spending_analysis, user_id
                    )
                except Exception as e:
                    logger.warning(f"Could not calculate consumer strength: {e}")
                    consumer_strength = {'overall_score': 50.0, 'signals': {}}
            else:
                consumer_strength = {'overall_score': 50.0, 'signals': {}}
            
            # Get AI recommendations
            ai_recommendations = None
            stock_rec = None
            if user_id:
                try:
                    ai_recommendations = self.analytics_service.get_ai_recommendations(user_id)
                    # Find this stock in recommendations
                    buy_recs = ai_recommendations.get('buy_recommendations', [])
                    stock_rec = next((r for r in buy_recs if r.get('symbol') == symbol), None)
                except Exception as e:
                    logger.warning(f"Could not get AI recommendations: {e}")
                    stock_rec = None
            
            # Build report sections with real data
            report = {
                'symbol': symbol,
                'company_name': stock.company_name,
                'generated_at': timezone.now().isoformat(),
                'report_type': report_type,
                'executive_summary': self._generate_executive_summary(
                    stock, current_price, consumer_strength, stock_rec, sector
                ),
                'sections': {
                    'overview': self._generate_overview_section(stock, current_price, sector),
                    'financials': self._generate_financials_section(stock, pe_ratio, market_cap, volatility),
                    'technical_analysis': self._generate_technical_section(stock, current_price, volatility),
                    'fundamental_analysis': self._generate_fundamental_section(stock, pe_ratio, market_cap, sector),
                    'ai_insights': self._generate_ai_insights_section(consumer_strength, stock_rec),
                    'consumer_strength': self._generate_consumer_strength_section(consumer_strength),
                    'risk_assessment': self._generate_risk_section(stock, volatility),
                    'recommendation': self._generate_recommendation_section(
                        stock, consumer_strength, stock_rec
                    ),
                },
                'key_metrics': self._extract_key_metrics(stock, current_price, consumer_strength, pe_ratio, volatility, sector),
                'charts_data': self._prepare_charts_data(symbol, consumer_strength),
            }
            
            cache.set(cache_key, report, self.CACHE_TTL)
            return report
            
        except Stock.DoesNotExist:
            # Try to create the stock if it doesn't exist using raw SQL to avoid current_price field
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO core_stock (symbol, company_name, sector, beginner_friendly_score, last_updated)
                        VALUES (%s, %s, %s, %s, NOW())
                        ON CONFLICT (symbol) DO NOTHING
                    """, [symbol.upper(), symbol, '', 5.0])
                logger.info(f"Created stock record for {symbol} using raw SQL")
                # Retry generating the report
                return self.generate_stock_report(symbol, user_id, report_type)
            except Exception as e:
                logger.error(f"Error creating stock {symbol}: {e}")
                # Return a minimal report even if stock doesn't exist
                return {
                    'symbol': symbol.upper(),
                    'company_name': symbol,
                    'generated_at': timezone.now().isoformat(),
                    'report_type': report_type,
                    'executive_summary': f'Research report for {symbol}. Stock data not available in database.',
                    'sections': {
                        'overview': {'symbol': symbol, 'company_name': symbol},
                        'financials': {},
                        'technical_analysis': {},
                        'fundamental_analysis': {},
                        'ai_insights': {},
                        'consumer_strength': {'overall_score': 50.0},
                        'risk_assessment': {},
                        'recommendation': {},
                    },
                    'key_metrics': {},
                    'charts_data': {},
                    'error': f'Stock {symbol} not found in database',
                }
        except Exception as e:
            logger.error(f"Error generating research report for {symbol}: {e}", exc_info=True)
            return {
                'error': str(e),
                'symbol': symbol,
            }
    
    def _generate_executive_summary(
        self,
        stock: Stock,
        current_price: Optional[float],
        consumer_strength: Dict[str, Any],
        stock_rec: Optional[Dict[str, Any]],
        sector: str = None
    ) -> str:
        """Generate executive summary"""
        price_str = f"${current_price:.2f}" if current_price else "N/A"
        score = consumer_strength.get('overall_score', 50.0)
        sector_str = sector or stock.sector or 'Unknown'
        
        summary = f"{stock.company_name} ({stock.symbol}) is currently trading at {price_str}. "
        
        if score >= 70:
            summary += "The stock shows strong consumer strength signals with a score of {:.1f}/100. ".format(score)
        elif score >= 50:
            summary += "The stock shows moderate consumer strength with a score of {:.1f}/100. ".format(score)
        else:
            summary += "The stock shows weak consumer strength signals with a score of {:.1f}/100. ".format(score)
        
        if stock_rec:
            confidence = stock_rec.get('confidence', 0) * 100
            if confidence >= 70:
                summary += f"Our AI model recommends BUY with {confidence:.0f}% confidence. "
            elif confidence >= 50:
                summary += f"Our AI model suggests a cautious BUY with {confidence:.0f}% confidence. "
        
        summary += f"The company operates in the {sector_str} sector."
        
        return summary
    
    def _generate_overview_section(
        self,
        stock: Stock,
        current_price: Optional[float],
        sector: str = None
    ) -> Dict[str, Any]:
        """Generate overview section"""
        sector_str = sector or stock.sector or 'Unknown'
        return {
            'company_name': stock.company_name,
            'symbol': stock.symbol,
            'sector': sector_str,
            'current_price': current_price,
            'market_cap': float(stock.market_cap) if stock.market_cap else None,
            'description': f"{stock.company_name} is a company in the {sector_str} sector.",
        }
    
    def _generate_financials_section(
        self,
        stock: Stock,
        pe_ratio: Optional[float] = None,
        market_cap: Optional[float] = None,
        volatility: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generate financials section with real data"""
        return {
            'pe_ratio': pe_ratio or (float(stock.pe_ratio) if stock.pe_ratio else None),
            'dividend_yield': float(stock.dividend_yield) if stock.dividend_yield else None,
            'debt_ratio': float(stock.debt_ratio) if stock.debt_ratio else None,
            'volatility': volatility or (float(stock.volatility) if stock.volatility else None),
            'market_cap': market_cap or (float(stock.market_cap) if stock.market_cap else None),
            'beginner_friendly_score': stock.beginner_friendly_score,
        }
    
    def _generate_technical_section(
        self,
        stock: Stock,
        current_price: Optional[float],
        volatility: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generate technical analysis section"""
        return {
            'current_price': current_price,
            'volatility': volatility or (float(stock.volatility) if stock.volatility else None),
            'trend': 'Neutral',  # Would calculate from price history
            'support_levels': [],
            'resistance_levels': [],
            'indicators': {
                'rsi': None,  # Would calculate
                'macd': None,  # Would calculate
                'moving_averages': {},
            }
        }
    
    def _generate_fundamental_section(
        self,
        stock: Stock,
        pe_ratio: Optional[float] = None,
        market_cap: Optional[float] = None,
        sector: str = None
    ) -> Dict[str, Any]:
        """Generate fundamental analysis section with real data"""
        sector_str = sector or stock.sector
        return {
            'valuation': {
                'pe_ratio': pe_ratio or (float(stock.pe_ratio) if stock.pe_ratio else None),
                'market_cap': market_cap or (float(stock.market_cap) if stock.market_cap else None),
            },
            'profitability': {
                'dividend_yield': float(stock.dividend_yield) if stock.dividend_yield else None,
            },
            'financial_health': {
                'debt_ratio': float(stock.debt_ratio) if stock.debt_ratio else None,
            },
            'growth_potential': {
                'sector': sector_str,
                'market_cap_category': self._categorize_market_cap(market_cap or stock.market_cap),
            }
        }
    
    def _generate_ai_insights_section(
        self,
        consumer_strength: Dict[str, Any],
        stock_rec: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI insights section"""
        insights = {
            'consumer_strength_score': consumer_strength.get('overall_score', 50.0),
            'spending_score': consumer_strength.get('spending_score', 50.0),
            'options_score': consumer_strength.get('options_score', 50.0),
            'earnings_score': consumer_strength.get('earnings_score', 50.0),
            'insider_score': consumer_strength.get('insider_score', 50.0),
            'spending_growth': consumer_strength.get('spending_growth', 0.0),
            'sector_score': consumer_strength.get('sector_score', 50.0),
        }
        
        if stock_rec:
            insights['recommendation'] = {
                'action': stock_rec.get('recommendation', 'HOLD'),
                'confidence': stock_rec.get('confidence', 0.5) * 100,
                'target_price': stock_rec.get('target_price'),
                'expected_return': stock_rec.get('expected_return', 0) * 100,
                'reasoning': stock_rec.get('reasoning', ''),
            }
        
        return insights
    
    def _generate_consumer_strength_section(
        self,
        consumer_strength: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate consumer strength section"""
        return {
            'overall_score': consumer_strength.get('overall_score', 50.0),
            'components': consumer_strength.get('components', {}),
            'historical_trend': consumer_strength.get('historical_trend', 'stable'),
            'sector_score': consumer_strength.get('sector_score', 50.0),
            'interpretation': self._interpret_consumer_strength(consumer_strength),
        }
    
    def _generate_risk_section(
        self,
        stock: Stock,
        volatility: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generate risk assessment section"""
        vol = volatility or (float(stock.volatility) if stock.volatility else 20.0)
        beginner_score = stock.beginner_friendly_score or 50
        
        risk_level = 'High'
        if vol < 18 and beginner_score >= 70:
            risk_level = 'Low'
        elif vol < 30 and beginner_score >= 50:
            risk_level = 'Medium'
        
        return {
            'overall_risk': risk_level,
            'volatility': vol,
            'beginner_friendly': beginner_score,
            'sector_risk': stock.sector or 'Unknown',
            'recommendations': self._generate_risk_recommendations(risk_level, vol),
        }
    
    def _generate_recommendation_section(
        self,
        stock: Stock,
        consumer_strength: Dict[str, Any],
        stock_rec: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate recommendation section"""
        score = consumer_strength.get('overall_score', 50.0)
        
        if stock_rec:
            action = stock_rec.get('recommendation', 'HOLD')
            confidence = stock_rec.get('confidence', 0.5) * 100
            target_price = stock_rec.get('target_price')
            reasoning = stock_rec.get('reasoning', '')
        else:
            # Generate recommendation from consumer strength
            if score >= 70:
                action = 'BUY'
                confidence = 75.0
            elif score >= 50:
                action = 'HOLD'
                confidence = 50.0
            else:
                action = 'SELL'
                confidence = 40.0
            
            target_price = None
            reasoning = f"Based on Consumer Strength Score of {score:.1f}/100"
        
        return {
            'action': action,
            'confidence': confidence,
            'target_price': target_price,
            'reasoning': reasoning,
            'time_horizon': '3-6 months',
            'risk_level': self._generate_risk_section(stock)['overall_risk'],
        }
    
    def _extract_key_metrics(
        self,
        stock: Stock,
        current_price: Optional[float],
        consumer_strength: Dict[str, Any],
        pe_ratio: Optional[float] = None,
        volatility: Optional[float] = None,
        sector: str = None
    ) -> Dict[str, Any]:
        """Extract key metrics for quick reference with real data"""
        return {
            'price': current_price,
            'market_cap': float(stock.market_cap) if stock.market_cap else None,
            'pe_ratio': pe_ratio or (float(stock.pe_ratio) if stock.pe_ratio else None),
            'consumer_strength': consumer_strength.get('overall_score', 50.0),
            'volatility': volatility or (float(stock.volatility) if stock.volatility else None),
            'sector': sector or stock.sector,
        }
    
    def _prepare_charts_data(
        self,
        symbol: str,
        consumer_strength: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare data for charts"""
        return {
            'consumer_strength_breakdown': {
                'spending': consumer_strength.get('spending_score', 50.0),
                'options': consumer_strength.get('options_score', 50.0),
                'earnings': consumer_strength.get('earnings_score', 50.0),
                'insider': consumer_strength.get('insider_score', 50.0),
            },
            'historical_trend': consumer_strength.get('historical_trend', 'stable'),
        }
    
    def _categorize_market_cap(self, market_cap: Optional[float]) -> str:
        """Categorize market cap"""
        if not market_cap:
            return 'Unknown'
        if market_cap >= 200_000_000_000:
            return 'Mega Cap'
        elif market_cap >= 10_000_000_000:
            return 'Large Cap'
        elif market_cap >= 2_000_000_000:
            return 'Mid Cap'
        elif market_cap >= 300_000_000:
            return 'Small Cap'
        else:
            return 'Micro Cap'
    
    def _interpret_consumer_strength(self, consumer_strength: Dict[str, Any]) -> str:
        """Interpret consumer strength score"""
        score = consumer_strength.get('overall_score', 50.0)
        spending_growth = consumer_strength.get('spending_growth', 0.0)
        
        if score >= 70:
            interpretation = f"Strong consumer signals (Score: {score:.1f}/100). "
            if spending_growth > 0:
                interpretation += f"Consumer spending is growing at {spending_growth:.1f}%, indicating strong demand."
            return interpretation
        elif score >= 50:
            interpretation = f"Moderate consumer signals (Score: {score:.1f}/100). "
            return interpretation
        else:
            interpretation = f"Weak consumer signals (Score: {score:.1f}/100). "
            return interpretation
    
    def _generate_risk_recommendations(self, risk_level: str, volatility: float) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if risk_level == 'High':
            recommendations.append("Consider position sizing to limit exposure")
            recommendations.append("Use stop-loss orders to manage downside risk")
            recommendations.append("Monitor volatility closely")
        elif risk_level == 'Medium':
            recommendations.append("Diversify across multiple positions")
            recommendations.append("Consider dollar-cost averaging")
        else:
            recommendations.append("Suitable for conservative investors")
            recommendations.append("Consider as a core holding")
        
        if volatility > 30:
            recommendations.append("High volatility detected - use appropriate position sizing")
        
        return recommendations
    
    def generate_pdf_report(
        self,
        symbol: str,
        user_id: Optional[int] = None,
        report_type: str = 'comprehensive'
    ) -> bytes:
        """
        Generate PDF version of research report
        
        Returns PDF bytes (would use reportlab or similar)
        """
        # TODO: Implement PDF generation using reportlab
        # For now, return empty bytes
        report = self.generate_stock_report(symbol, user_id, report_type)
        
        # In production, would use reportlab to create PDF
        # from reportlab.lib.pagesizes import letter
        # from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        # ...
        
        return b''  # Placeholder
    
    def send_report_email(
        self,
        symbol: str,
        user_email: str,
        user_id: Optional[int] = None,
        report_type: str = 'comprehensive'
    ) -> bool:
        """
        Generate and email research report
        
        Returns True if successful
        """
        try:
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            report = self.generate_stock_report(symbol, user_id, report_type)
            pdf_bytes = self.generate_pdf_report(symbol, user_id, report_type)
            
            if not report or 'error' in report:
                logger.error(f"Cannot send email - report generation failed for {symbol}")
                return False
            
            # Create email
            subject = f"Research Report: {report['company_name']} ({symbol})"
            body = f"""
Dear Investor,

Please find attached the research report for {report['company_name']} ({symbol}).

{report['executive_summary']}

Key Highlights:
- Consumer Strength Score: {report['key_metrics'].get('consumer_strength', 0):.1f}/100
- Current Price: ${report['key_metrics'].get('price', 'N/A')}
- Recommendation: {report['sections']['recommendation']['action']}

This report was generated on {report['generated_at']}.

Best regards,
RichesReach Research Team
            """
            
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@richesreach.com'),
                to=[user_email],
            )
            
            # Attach PDF if available
            if pdf_bytes:
                email.attach(
                    filename=f"{symbol}_research_report.pdf",
                    content=pdf_bytes,
                    mimetype='application/pdf'
                )
            
            # Send email
            email.send()
            
            logger.info(f"Research report email sent to {user_email} for {symbol}")
            return True
            
        except ImportError:
            logger.warning("Django email not configured - cannot send email")
            return False
        except Exception as e:
            logger.error(f"Error sending research report email: {e}", exc_info=True)
            return False

