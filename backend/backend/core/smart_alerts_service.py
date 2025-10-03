import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.contrib.auth.models import User
from .real_market_data_service import real_market_data_service
from .advanced_analytics_service import advanced_analytics_service
from .advanced_dashboard_service import advanced_dashboard_service
from .performance_attribution_service import performance_attribution_service
from .yodlee_service import yodlee_service
from .alert_config_service import alert_config_service
from .alert_delivery_service import alert_delivery_service
from .ml_anomaly_service import ml_anomaly_service
from .models_smart_alerts import SmartAlert, AlertSuppression, AlertDeliveryHistory

logger = logging.getLogger(__name__)

class SmartAlertsService:
    """Service for intelligent portfolio coaching alerts and insights"""
    
    def __init__(self):
        self.market_service = real_market_data_service
        self.analytics_service = advanced_analytics_service
        self.dashboard_service = advanced_dashboard_service
        self.attribution_service = performance_attribution_service
        self.yodlee_service = yodlee_service
        self.config_service = alert_config_service
        self.delivery_service = alert_delivery_service
        self.ml_anomaly_service = ml_anomaly_service
    
    def generate_smart_alerts(self, user: User, portfolio_id: str = None, 
                            timeframe: str = '1M') -> List[Dict[str, Any]]:
        """Generate comprehensive smart alerts for portfolio coaching"""
        try:
            alerts = []
            
            # Get comprehensive portfolio data
            dashboard_data = self.dashboard_service.get_comprehensive_dashboard_data(
                user=user, portfolio_id=portfolio_id, timeframe=timeframe
            )
            
            if not dashboard_data:
                return self._get_default_alerts()
            
            # Generate different types of alerts
            alerts.extend(self._generate_performance_alerts(dashboard_data, timeframe))
            alerts.extend(self._generate_risk_alerts(dashboard_data, timeframe))
            alerts.extend(self._generate_allocation_alerts(dashboard_data, timeframe))
            alerts.extend(self._generate_attribution_alerts(dashboard_data, timeframe))
            alerts.extend(self._generate_market_regime_alerts(dashboard_data, timeframe))
            alerts.extend(self._generate_rebalancing_alerts(dashboard_data, timeframe))
            alerts.extend(self._generate_opportunity_alerts(dashboard_data, timeframe))
            
            # Yodlee-specific alerts using real portfolio data
            alerts.extend(self._generate_yodlee_portfolio_alerts(user, timeframe))
            alerts.extend(self._generate_yodlee_transaction_alerts(user, timeframe))
            alerts.extend(self._generate_yodlee_cash_flow_alerts(user, timeframe))
            alerts.extend(self._generate_yodlee_holding_alerts(user, timeframe))
            
            # Generate ML-driven anomaly alerts (synchronous for now)
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    ml_anomalies = loop.run_until_complete(
                        self.ml_anomaly_service.detect_anomalies(user, portfolio_id, timeframe)
                    )
                except RuntimeError:
                    ml_anomalies = asyncio.run(
                        self.ml_anomaly_service.detect_anomalies(user, portfolio_id, timeframe)
                    )
                alerts.extend(ml_anomalies)
            except Exception as e:
                logger.error(f"Error generating ML anomalies: {e}")
                # Continue without ML anomalies if they fail
            
            # Filter out suppressed alerts and apply deduplication
            alerts = self._filter_suppressed_alerts(user, alerts, portfolio_id)
            
            # Sort alerts by urgency and priority
            alerts = self._prioritize_alerts(alerts)
            
            # Store alerts in database for tracking
            self._store_alerts_in_db(user, alerts, portfolio_id, timeframe)
            
            return alerts[:10]  # Return top 10 most important alerts
            
        except Exception as e:
            logger.error(f"Error generating smart alerts: {e}")
            return self._get_default_alerts()
    
    def _generate_performance_alerts(self, dashboard_data: Dict, timeframe: str) -> List[Dict[str, Any]]:
        """Generate performance-based coaching alerts"""
        alerts = []
        
        try:
            overview = dashboard_data.get('overview', {})
            benchmark_comparison = dashboard_data.get('benchmark_comparison', {})
            
            # Portfolio vs Benchmark Performance Alert
            portfolio_return = overview.get('total_return_percent', 0)
            benchmark_return = benchmark_comparison.get('primary_benchmark', {}).get('return', 0)
            performance_diff = portfolio_return - benchmark_return
            
            if abs(performance_diff) > 2.0:  # Significant under/outperformance
                if performance_diff < -2.0:
                    alerts.append({
                        'id': f'perf_under_{datetime.now().strftime("%Y%m%d_%H%M")}',
                        'type': 'performance_underperformance',
                        'priority': 'high',
                        'category': 'performance',
                        'title': 'Portfolio Underperforming Benchmark',
                        'message': f'Your portfolio is down {abs(performance_diff):.1f}% vs {benchmark_comparison.get("primary_benchmark", {}).get("name", "benchmark")} this {timeframe.lower()}. Consider reviewing your allocation strategy.',
                        'details': {
                            'portfolio_return': portfolio_return,
                            'benchmark_return': benchmark_return,
                            'underperformance': performance_diff,
                            'timeframe': timeframe
                        },
                        'actionable': True,
                        'suggested_actions': [
                            'Review sector allocation vs benchmark',
                            'Consider rebalancing overweight positions',
                            'Evaluate individual stock selection',
                            'Check if market conditions favor your strategy'
                        ],
                        'coaching_tip': 'Underperformance can be temporary. Focus on your long-term strategy and risk management.',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    alerts.append({
                        'id': f'perf_out_{datetime.now().strftime("%Y%m%d_%H%M")}',
                        'type': 'performance_outperformance',
                        'priority': 'medium',
                        'category': 'performance',
                        'title': 'Portfolio Outperforming Benchmark',
                        'message': f'Great job! Your portfolio is up {performance_diff:.1f}% vs {benchmark_comparison.get("primary_benchmark", {}).get("name", "benchmark")} this {timeframe.lower()}.',
                        'details': {
                            'portfolio_return': portfolio_return,
                            'benchmark_return': benchmark_return,
                            'outperformance': performance_diff,
                            'timeframe': timeframe
                        },
                        'actionable': False,
                        'suggested_actions': [
                            'Consider taking some profits if positions are overvalued',
                            'Review if outperformance is sustainable',
                            'Document what drove the outperformance'
                        ],
                        'coaching_tip': 'Outperformance is great, but ensure it\'s not due to excessive risk-taking.',
                        'timestamp': datetime.now().isoformat()
                    })
            
            # YTD Performance Alert
            ytd_return = overview.get('ytd_return', 0)
            if ytd_return < -10:
                alerts.append({
                    'id': f'ytd_weak_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'ytd_weak_performance',
                    'priority': 'high',
                    'category': 'performance',
                    'title': 'Weak Year-to-Date Performance',
                    'message': f'Your portfolio is down {abs(ytd_return):.1f}% year-to-date. This may indicate a need for strategy adjustment.',
                    'details': {
                        'ytd_return': ytd_return,
                        'threshold': -10
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Review your investment thesis for major holdings',
                        'Consider defensive positioning',
                        'Evaluate if market conditions have changed',
                        'Check for concentration risk'
                    ],
                    'coaching_tip': 'Negative YTD performance requires careful analysis. Don\'t panic, but do review your strategy.',
                    'timestamp': datetime.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating performance alerts: {e}")
            return []
    
    def _generate_risk_alerts(self, dashboard_data: Dict, timeframe: str) -> List[Dict[str, Any]]:
        """Generate risk-based coaching alerts"""
        alerts = []
        
        try:
            overview = dashboard_data.get('overview', {})
            risk_metrics = dashboard_data.get('risk_metrics', {})
            
            # Sharpe Ratio Deterioration Alert
            sharpe_ratio = overview.get('sharpe_ratio', 0)
            if sharpe_ratio < 0.5:  # Poor risk-adjusted returns
                alerts.append({
                    'id': f'sharpe_low_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'risk_sharpe_deterioration',
                    'priority': 'high',
                    'category': 'risk',
                    'title': 'Sharpe Ratio Has Deteriorated',
                    'message': f'Your Sharpe ratio of {sharpe_ratio:.2f} indicates poor risk-adjusted returns. Consider rebalancing to improve risk efficiency.',
                    'details': {
                        'sharpe_ratio': sharpe_ratio,
                        'threshold': 0.5,
                        'interpretation': 'Poor risk-adjusted returns'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Reduce portfolio volatility through diversification',
                        'Consider adding low-volatility assets',
                        'Review high-risk positions',
                        'Implement risk management strategies'
                    ],
                    'coaching_tip': 'A low Sharpe ratio means you\'re taking too much risk for the returns you\'re getting.',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Volatility Alert
            volatility = overview.get('volatility', 0)
            if volatility > 20:  # High volatility
                alerts.append({
                    'id': f'vol_high_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'risk_high_volatility',
                    'priority': 'medium',
                    'category': 'risk',
                    'title': 'Portfolio Volatility is High',
                    'message': f'Your portfolio volatility of {volatility:.1f}% is above typical levels. Consider reducing risk exposure.',
                    'details': {
                        'volatility': volatility,
                        'threshold': 20,
                        'interpretation': 'High volatility'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Add defensive assets (bonds, utilities)',
                        'Reduce position sizes in volatile stocks',
                        'Consider hedging strategies',
                        'Review concentration in high-beta sectors'
                    ],
                    'coaching_tip': 'High volatility can lead to emotional decision-making. Consider your risk tolerance.',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Maximum Drawdown Alert
            max_drawdown = overview.get('max_drawdown', 0)
            if max_drawdown < -15:  # Significant drawdown
                alerts.append({
                    'id': f'dd_high_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'risk_high_drawdown',
                    'priority': 'high',
                    'category': 'risk',
                    'title': 'Maximum Drawdown Exceeded',
                    'message': f'Your maximum drawdown of {abs(max_drawdown):.1f}% exceeds comfortable levels. Review risk management.',
                    'details': {
                        'max_drawdown': max_drawdown,
                        'threshold': -15,
                        'interpretation': 'Significant loss from peak'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Implement stop-loss strategies',
                        'Reduce position sizes',
                        'Add defensive assets',
                        'Consider portfolio insurance'
                    ],
                    'coaching_tip': 'Large drawdowns can take a long time to recover from. Focus on capital preservation.',
                    'timestamp': datetime.now().isoformat()
                })
            
            # VaR Alert
            var_95 = risk_metrics.get('value_at_risk', {}).get('var_95_1d', 0)
            if var_95 < -3:  # High daily VaR
                alerts.append({
                    'id': f'var_high_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'risk_high_var',
                    'priority': 'medium',
                    'category': 'risk',
                    'title': 'High Daily Value at Risk',
                    'message': f'Your 95% VaR of {abs(var_95):.1f}% means you could lose this much in a single day. Consider reducing risk.',
                    'details': {
                        'var_95': var_95,
                        'threshold': -3,
                        'interpretation': 'High daily risk'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Reduce position sizes',
                        'Add uncorrelated assets',
                        'Implement risk controls',
                        'Consider hedging'
                    ],
                    'coaching_tip': 'VaR helps you understand your worst-case daily loss. Make sure you\'re comfortable with it.',
                    'timestamp': datetime.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating risk alerts: {e}")
            return []
    
    def _generate_allocation_alerts(self, dashboard_data: Dict, timeframe: str) -> List[Dict[str, Any]]:
        """Generate allocation-based coaching alerts"""
        alerts = []
        
        try:
            sector_analysis = dashboard_data.get('sector_analysis', {})
            sector_weights = sector_analysis.get('sector_weights', {})
            
            # Technology Overweight Alert
            tech_weight = sector_weights.get('technology', 0)
            if tech_weight > 0.35:  # Overweight in tech
                alerts.append({
                    'id': f'tech_over_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'allocation_tech_overweight',
                    'priority': 'medium',
                    'category': 'allocation',
                    'title': 'Overweight in Technology Sector',
                    'message': f'You\'re overweight in Technology by {((tech_weight - 0.25) * 100):.0f}% vs typical allocation. Consider diversifying.',
                    'details': {
                        'current_weight': tech_weight,
                        'suggested_weight': 0.25,
                        'overweight_amount': tech_weight - 0.25,
                        'sector': 'Technology'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Reduce technology exposure gradually',
                        'Add defensive sectors (utilities, consumer staples)',
                        'Consider value stocks in other sectors',
                        'Review individual tech stock positions'
                    ],
                    'coaching_tip': 'Technology can be volatile. Ensure your allocation matches your risk tolerance.',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Sector Concentration Alert
            top_3_weight = sum(sorted(sector_weights.values(), reverse=True)[:3])
            if top_3_weight > 0.7:  # High concentration
                alerts.append({
                    'id': f'conc_high_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'allocation_high_concentration',
                    'priority': 'medium',
                    'category': 'allocation',
                    'title': 'High Sector Concentration',
                    'message': f'Your top 3 sectors represent {top_3_weight*100:.0f}% of your portfolio. Consider broader diversification.',
                    'details': {
                        'top_3_weight': top_3_weight,
                        'threshold': 0.7,
                        'sectors': list(sector_weights.keys())[:3]
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Add underrepresented sectors',
                        'Consider sector-neutral strategies',
                        'Review sector rotation opportunities',
                        'Implement equal-weight sector allocation'
                    ],
                    'coaching_tip': 'Diversification across sectors reduces risk and smooths returns over time.',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Single Stock Concentration Alert
            # This would require individual stock data
            alerts.append({
                'id': f'stock_conc_{datetime.now().strftime("%Y%m%d_%H%M")}',
                'type': 'allocation_stock_concentration',
                'priority': 'low',
                'category': 'allocation',
                'title': 'Check Individual Stock Concentration',
                'message': 'Review if any single stock represents more than 10% of your portfolio.',
                'details': {
                    'suggested_max_weight': 0.10,
                    'risk': 'Single stock risk'
                },
                'actionable': True,
                'suggested_actions': [
                    'Review largest positions',
                    'Consider position size limits',
                    'Implement concentration controls',
                    'Diversify within sectors'
                ],
                'coaching_tip': 'No single stock should dominate your portfolio. Spread your risk.',
                'timestamp': datetime.now().isoformat()
            })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating allocation alerts: {e}")
            return []
    
    def _generate_attribution_alerts(self, dashboard_data: Dict, timeframe: str) -> List[Dict[str, Any]]:
        """Generate attribution-based coaching alerts"""
        alerts = []
        
        try:
            attribution = dashboard_data.get('attribution', {})
            brinson = attribution.get('brinson_attribution', {})
            
            # Security Selection Performance
            selection_effect = brinson.get('security_selection', 0)
            if selection_effect > 1.0:  # Strong security selection
                alerts.append({
                    'id': f'select_strong_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'attribution_strong_selection',
                    'priority': 'low',
                    'category': 'attribution',
                    'title': 'Strong Security Selection',
                    'message': f'Your security selection added {selection_effect:.1f}% to returns. Great stock picking!',
                    'details': {
                        'selection_effect': selection_effect,
                        'interpretation': 'Strong individual stock selection'
                    },
                    'actionable': False,
                    'suggested_actions': [
                        'Document your selection process',
                        'Consider increasing research time',
                        'Review what drove the outperformance'
                    ],
                    'coaching_tip': 'Strong security selection is a competitive advantage. Keep up the good work!',
                    'timestamp': datetime.now().isoformat()
                })
            elif selection_effect < -0.5:  # Weak security selection
                alerts.append({
                    'id': f'select_weak_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'attribution_weak_selection',
                    'priority': 'medium',
                    'category': 'attribution',
                    'title': 'Weak Security Selection',
                    'message': f'Your security selection detracted {abs(selection_effect):.1f}% from returns. Consider index funds or better research.',
                    'details': {
                        'selection_effect': selection_effect,
                        'interpretation': 'Weak individual stock selection'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Consider low-cost index funds',
                        'Improve research process',
                        'Focus on allocation over selection',
                        'Review underperforming positions'
                    ],
                    'coaching_tip': 'If stock selection consistently underperforms, consider a more passive approach.',
                    'timestamp': datetime.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating attribution alerts: {e}")
            return []
    
    def _generate_market_regime_alerts(self, dashboard_data: Dict, timeframe: str) -> List[Dict[str, Any]]:
        """Generate market regime-based coaching alerts"""
        alerts = []
        
        try:
            market_regime = dashboard_data.get('market_regime', {})
            current_regime = market_regime.get('current_regime', 'normal')
            regime_probability = market_regime.get('regime_probability', 0.5)
            
            if current_regime == 'bear_market' and regime_probability > 0.7:
                alerts.append({
                    'id': f'bear_market_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'market_bear_regime',
                    'priority': 'high',
                    'category': 'market_regime',
                    'title': 'Bear Market Conditions Detected',
                    'message': f'Market indicators suggest bear market conditions ({regime_probability*100:.0f}% probability). Consider defensive positioning.',
                    'details': {
                        'regime': current_regime,
                        'probability': regime_probability,
                        'market_conditions': 'Bear market'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Increase cash allocation',
                        'Add defensive sectors',
                        'Consider hedging strategies',
                        'Review growth stock exposure'
                    ],
                    'coaching_tip': 'Bear markets are temporary but can be painful. Focus on capital preservation.',
                    'timestamp': datetime.now().isoformat()
                })
            elif current_regime == 'bull_market' and regime_probability > 0.8:
                alerts.append({
                    'id': f'bull_market_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'market_bull_regime',
                    'priority': 'low',
                    'category': 'market_regime',
                    'title': 'Strong Bull Market Conditions',
                    'message': f'Market indicators show strong bull market conditions ({regime_probability*100:.0f}% probability). Stay invested but watch for signs of excess.',
                    'details': {
                        'regime': current_regime,
                        'probability': regime_probability,
                        'market_conditions': 'Bull market'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Stay invested in quality growth',
                        'Watch for valuation excesses',
                        'Consider profit-taking on winners',
                        'Maintain diversification'
                    ],
                    'coaching_tip': 'Bull markets can create overconfidence. Stick to your strategy and risk management.',
                    'timestamp': datetime.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating market regime alerts: {e}")
            return []
    
    def _generate_rebalancing_alerts(self, dashboard_data: Dict, timeframe: str) -> List[Dict[str, Any]]:
        """Generate rebalancing coaching alerts"""
        alerts = []
        
        try:
            recommendations = dashboard_data.get('recommendations', [])
            
            for rec in recommendations:
                if rec.get('type') == 'rebalancing':
                    alerts.append({
                        'id': f'rebal_{rec.get("id", "unknown")}',
                        'type': 'rebalancing_opportunity',
                        'priority': rec.get('priority', 'medium'),
                        'category': 'rebalancing',
                        'title': rec.get('title', 'Rebalancing Opportunity'),
                        'message': rec.get('description', 'Consider rebalancing your portfolio'),
                        'details': rec.get('details', {}),
                        'actionable': True,
                        'suggested_actions': [rec.get('recommended_action', 'Review allocation')],
                        'coaching_tip': rec.get('expected_impact', 'Rebalancing can improve risk-adjusted returns'),
                        'confidence': rec.get('confidence', 0.5),
                        'timestamp': datetime.now().isoformat()
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating rebalancing alerts: {e}")
            return []
    
    def _generate_opportunity_alerts(self, dashboard_data: Dict, timeframe: str) -> List[Dict[str, Any]]:
        """Generate opportunity-based coaching alerts"""
        alerts = []
        
        try:
            # This would integrate with market data to identify opportunities
            # For now, provide general coaching alerts
            
            alerts.append({
                'id': f'opp_dca_{datetime.now().strftime("%Y%m%d_%H%M")}',
                'type': 'opportunity_dca',
                'priority': 'low',
                'category': 'opportunity',
                'title': 'Consider Dollar-Cost Averaging',
                'message': 'Market volatility presents opportunities for dollar-cost averaging into quality positions.',
                'details': {
                    'strategy': 'Dollar-cost averaging',
                    'benefit': 'Reduces timing risk'
                },
                'actionable': True,
                'suggested_actions': [
                    'Set up regular investment schedule',
                    'Focus on quality companies',
                    'Ignore short-term market noise',
                    'Maintain long-term perspective'
                ],
                'coaching_tip': 'DCA works best with quality investments over long time horizons.',
                'timestamp': datetime.now().isoformat()
            })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating opportunity alerts: {e}")
            return []
    
    def _prioritize_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize alerts by importance and recency"""
        try:
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            
            # Sort by priority (high to low) and then by timestamp (newest first)
            alerts.sort(key=lambda x: (
                priority_order.get(x.get('priority', 'low'), 1),
                x.get('timestamp', '')
            ), reverse=True)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error prioritizing alerts: {e}")
            return alerts
    
    def _get_default_alerts(self) -> List[Dict[str, Any]]:
        """Return default coaching alerts when calculation fails"""
        return [
            {
                'id': 'default_1',
                'type': 'general_coaching',
                'priority': 'low',
                'category': 'general',
                'title': 'Welcome to Smart Alerts',
                'message': 'Your personalized portfolio coaching alerts will appear here based on your portfolio performance and risk metrics.',
                'details': {},
                'actionable': False,
                'suggested_actions': [],
                'coaching_tip': 'Smart alerts help you make better investment decisions by providing timely insights.',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def get_alert_categories(self) -> List[Dict[str, Any]]:
        """Get available alert categories and their descriptions"""
        return [
            {
                'category': 'performance',
                'name': 'Performance Alerts',
                'description': 'Alerts about portfolio performance vs benchmarks',
                'icon': 'trending-up',
                'color': '#10B981'
            },
            {
                'category': 'risk',
                'name': 'Risk Management',
                'description': 'Alerts about risk metrics and portfolio safety',
                'icon': 'shield',
                'color': '#EF4444'
            },
            {
                'category': 'allocation',
                'name': 'Asset Allocation',
                'description': 'Alerts about portfolio diversification and concentration',
                'icon': 'pie-chart',
                'color': '#3B82F6'
            },
            {
                'category': 'attribution',
                'name': 'Performance Attribution',
                'description': 'Alerts about what\'s driving your returns',
                'icon': 'bar-chart-2',
                'color': '#8B5CF6'
            },
            {
                'category': 'market_regime',
                'name': 'Market Conditions',
                'description': 'Alerts about changing market conditions',
                'icon': 'cloud',
                'color': '#F59E0B'
            },
            {
                'category': 'rebalancing',
                'name': 'Rebalancing',
                'description': 'Alerts about rebalancing opportunities',
                'icon': 'refresh-cw',
                'color': '#06B6D4'
            },
            {
                'category': 'opportunity',
                'name': 'Opportunities',
                'description': 'Alerts about investment opportunities',
                'icon': 'lightbulb',
                'color': '#84CC16'
            }
        ]
    
    def get_user_alert_preferences(self, user: User) -> Dict[str, Any]:
        """Get user's alert preferences and settings"""
        # This would integrate with user preferences storage
        return {
                'enabled_categories': ['performance', 'risk', 'allocation', 'rebalancing'],
                'priority_threshold': 'medium',  # Only show medium and high priority alerts
                'frequency': 'daily',  # How often to check for new alerts
                'delivery_method': 'in_app',  # in_app, email, push
                'quiet_hours': {
                    'enabled': True,
                    'start': '22:00',
                    'end': '08:00'
                },
                'custom_thresholds': {
                    'performance_threshold': 2.0,  # Alert if under/outperforming by this %
                    'volatility_threshold': 20.0,  # Alert if volatility exceeds this %
                    'drawdown_threshold': -15.0,  # Alert if drawdown exceeds this %
                    'sector_concentration_threshold': 0.35  # Alert if any sector exceeds this weight
                }
            }
    
    def _generate_yodlee_portfolio_alerts(self, user: User, timeframe: str) -> List[Dict[str, Any]]:
        """Generate alerts based on real Yodlee portfolio data"""
        alerts = []
        
        try:
            # Get real portfolio data from Yodlee
            portfolio_data = self.yodlee_service.get_user_portfolio_summary(user)
            if not portfolio_data:
                return alerts
            
            # Portfolio Value Change Alert
            current_value = portfolio_data.get('total_value', 0)
            previous_value = portfolio_data.get('previous_value', 0)
            if previous_value > 0:
                value_change_pct = ((current_value - previous_value) / previous_value) * 100
                
                if abs(value_change_pct) > 5.0:  # Significant change
                    if value_change_pct < -5.0:
                        alerts.append({
                            'id': f'yodlee_portfolio_down_{datetime.now().strftime("%Y%m%d_%H%M")}',
                            'type': 'yodlee_portfolio_decline',
                            'priority': 'high',
                            'category': 'portfolio',
                            'title': 'Portfolio Value Declined Significantly',
                            'message': f'Your portfolio value decreased by {abs(value_change_pct):.1f}% to ${current_value:,.0f}. This may indicate market volatility or position changes.',
                            'details': {
                                'current_value': current_value,
                                'previous_value': previous_value,
                                'change_percent': value_change_pct,
                                'data_source': 'yodlee'
                            },
                            'actionable': True,
                            'suggested_actions': [
                                'Review recent transactions',
                                'Check for large position changes',
                                'Consider market conditions',
                                'Review individual holdings performance'
                            ],
                            'coaching_tip': 'Portfolio declines can be temporary. Focus on your long-term strategy and risk management.',
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        alerts.append({
                            'id': f'yodlee_portfolio_up_{datetime.now().strftime("%Y%m%d_%H%M")}',
                            'type': 'yodlee_portfolio_growth',
                            'priority': 'low',
                            'category': 'portfolio',
                            'title': 'Portfolio Value Increased Significantly',
                            'message': f'Great news! Your portfolio value increased by {value_change_pct:.1f}% to ${current_value:,.0f}.',
                            'details': {
                                'current_value': current_value,
                                'previous_value': previous_value,
                                'change_percent': value_change_pct,
                                'data_source': 'yodlee'
                            },
                            'actionable': False,
                            'suggested_actions': [
                                'Consider taking some profits if positions are overvalued',
                                'Review if growth is sustainable',
                                'Document what drove the growth'
                            ],
                            'coaching_tip': 'Portfolio growth is great, but ensure it\'s not due to excessive risk-taking.',
                            'timestamp': datetime.now().isoformat()
                        })
            
            # Cash Position Alert
            cash_balance = portfolio_data.get('cash_balance', 0)
            total_value = portfolio_data.get('total_value', 0)
            if total_value > 0:
                cash_percentage = (cash_balance / total_value) * 100
                
                if cash_percentage > 20:  # High cash position
                    alerts.append({
                        'id': f'yodlee_high_cash_{datetime.now().strftime("%Y%m%d_%H%M")}',
                        'type': 'yodlee_high_cash_position',
                        'priority': 'medium',
                        'category': 'allocation',
                        'title': 'High Cash Position Detected',
                        'message': f'You have {cash_percentage:.1f}% of your portfolio in cash (${cash_balance:,.0f}). Consider investing excess cash for better returns.',
                        'details': {
                            'cash_balance': cash_balance,
                            'total_value': total_value,
                            'cash_percentage': cash_percentage,
                            'data_source': 'yodlee'
                        },
                        'actionable': True,
                        'suggested_actions': [
                            'Consider dollar-cost averaging into quality investments',
                            'Review your investment strategy',
                            'Set up automatic investments',
                            'Consider high-yield savings or short-term bonds'
                        ],
                        'coaching_tip': 'Cash provides safety but typically underperforms over time. Find the right balance for your risk tolerance.',
                        'timestamp': datetime.now().isoformat()
                    })
                elif cash_percentage < 2:  # Low cash position
                    alerts.append({
                        'id': f'yodlee_low_cash_{datetime.now().strftime("%Y%m%d_%H%M")}',
                        'type': 'yodlee_low_cash_position',
                        'priority': 'medium',
                        'category': 'allocation',
                        'title': 'Low Cash Position',
                        'message': f'You have only {cash_percentage:.1f}% in cash (${cash_balance:,.0f}). Consider maintaining an emergency fund.',
                        'details': {
                            'cash_balance': cash_balance,
                            'total_value': total_value,
                            'cash_percentage': cash_percentage,
                            'data_source': 'yodlee'
                        },
                        'actionable': True,
                        'suggested_actions': [
                            'Build emergency fund (3-6 months expenses)',
                            'Consider liquidating some positions',
                            'Set up automatic savings',
                            'Review liquidity needs'
                        ],
                        'coaching_tip': 'An emergency fund provides financial security and prevents forced selling during market downturns.',
                        'timestamp': datetime.now().isoformat()
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating Yodlee portfolio alerts: {e}")
            return []
    
    def _generate_yodlee_transaction_alerts(self, user: User, timeframe: str) -> List[Dict[str, Any]]:
        """Generate alerts based on Yodlee transaction data"""
        alerts = []
        
        try:
            # Get recent transactions from Yodlee
            transactions = self.yodlee_service.get_recent_transactions(user, days=30)
            if not transactions:
                return alerts
            
            # Large Transaction Alert
            large_transactions = [t for t in transactions if abs(t.get('amount', 0)) > 10000]
            if large_transactions:
                for transaction in large_transactions[:3]:  # Limit to top 3
                    alerts.append({
                        'id': f'yodlee_large_txn_{transaction.get("id", "unknown")}',
                        'type': 'yodlee_large_transaction',
                        'priority': 'medium',
                        'category': 'transaction',
                        'title': 'Large Transaction Detected',
                        'message': f'Large transaction of ${abs(transaction.get("amount", 0)):,.0f} on {transaction.get("date", "unknown date")}. Review if this aligns with your strategy.',
                        'details': {
                            'amount': transaction.get('amount', 0),
                            'date': transaction.get('date'),
                            'description': transaction.get('description', ''),
                            'account': transaction.get('account_name', ''),
                            'data_source': 'yodlee'
                        },
                        'actionable': True,
                        'suggested_actions': [
                            'Verify transaction details',
                            'Review if it aligns with your strategy',
                            'Consider tax implications',
                            'Document the reasoning'
                        ],
                        'coaching_tip': 'Large transactions can significantly impact your portfolio. Always review them carefully.',
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Frequent Trading Alert
            trading_frequency = len([t for t in transactions if t.get('category') in ['buy', 'sell']])
            if trading_frequency > 10:  # More than 10 trades in 30 days
                alerts.append({
                    'id': f'yodlee_frequent_trading_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'yodlee_frequent_trading',
                    'priority': 'medium',
                    'category': 'behavior',
                    'title': 'Frequent Trading Detected',
                    'message': f'You\'ve made {trading_frequency} trades in the last 30 days. Frequent trading can increase costs and reduce returns.',
                    'details': {
                        'trading_count': trading_frequency,
                        'period_days': 30,
                        'data_source': 'yodlee'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Review your trading strategy',
                        'Consider longer holding periods',
                        'Calculate trading costs impact',
                        'Focus on quality over quantity'
                    ],
                    'coaching_tip': 'Frequent trading often leads to higher costs and lower returns. Consider a more patient approach.',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Unusual Spending Pattern Alert
            spending_by_category = {}
            for transaction in transactions:
                if transaction.get('amount', 0) < 0:  # Outgoing money
                    category = transaction.get('category', 'other')
                    spending_by_category[category] = spending_by_category.get(category, 0) + abs(transaction.get('amount', 0))
            
            # Check for unusual spending in any category
            total_spending = sum(spending_by_category.values())
            if total_spending > 0:
                for category, amount in spending_by_category.items():
                    category_percentage = (amount / total_spending) * 100
                    if category_percentage > 40:  # More than 40% in one category
                        alerts.append({
                            'id': f'yodlee_spending_pattern_{category}_{datetime.now().strftime("%Y%m%d_%H%M")}',
                            'type': 'yodlee_spending_pattern',
                            'priority': 'low',
                            'category': 'spending',
                            'title': 'Unusual Spending Pattern',
                            'message': f'{category_percentage:.1f}% of your spending is in {category} (${amount:,.0f}). Review if this aligns with your budget.',
                            'details': {
                                'category': category,
                                'amount': amount,
                                'percentage': category_percentage,
                                'total_spending': total_spending,
                                'data_source': 'yodlee'
                            },
                            'actionable': True,
                            'suggested_actions': [
                                'Review your budget allocation',
                                'Consider if spending is necessary',
                                'Look for cost-saving opportunities',
                                'Track spending trends over time'
                            ],
                            'coaching_tip': 'Understanding your spending patterns helps with better financial planning and investment decisions.',
                            'timestamp': datetime.now().isoformat()
                        })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating Yodlee transaction alerts: {e}")
            return []
    
    def _generate_yodlee_cash_flow_alerts(self, user: User, timeframe: str) -> List[Dict[str, Any]]:
        """Generate alerts based on Yodlee cash flow data"""
        alerts = []
        
        try:
            # Get cash flow data from Yodlee
            cash_flow = self.yodlee_service.get_cash_flow_summary(user, days=30)
            if not cash_flow:
                return alerts
            
            # Negative Cash Flow Alert
            net_cash_flow = cash_flow.get('net_cash_flow', 0)
            if net_cash_flow < 0:
                alerts.append({
                    'id': f'yodlee_negative_cashflow_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'yodlee_negative_cashflow',
                    'priority': 'high',
                    'category': 'cashflow',
                    'title': 'Negative Cash Flow Detected',
                    'message': f'Your cash flow is negative by ${abs(net_cash_flow):,.0f} this month. This may impact your ability to invest or meet expenses.',
                    'details': {
                        'net_cash_flow': net_cash_flow,
                        'income': cash_flow.get('income', 0),
                        'expenses': cash_flow.get('expenses', 0),
                        'data_source': 'yodlee'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Review and reduce unnecessary expenses',
                        'Look for additional income sources',
                        'Consider liquidating some investments',
                        'Create a budget to track spending'
                    ],
                    'coaching_tip': 'Negative cash flow can lead to debt accumulation. Address this promptly to maintain financial health.',
                    'timestamp': datetime.now().isoformat()
                })
            
            # High Expense Ratio Alert
            income = cash_flow.get('income', 0)
            expenses = cash_flow.get('expenses', 0)
            if income > 0:
                expense_ratio = (expenses / income) * 100
                if expense_ratio > 90:  # More than 90% of income spent
                    alerts.append({
                        'id': f'yodlee_high_expense_ratio_{datetime.now().strftime("%Y%m%d_%H%M")}',
                        'type': 'yodlee_high_expense_ratio',
                        'priority': 'medium',
                        'category': 'cashflow',
                        'title': 'High Expense Ratio',
                        'message': f'You\'re spending {expense_ratio:.1f}% of your income (${expenses:,.0f} of ${income:,.0f}). Consider reducing expenses to increase savings.',
                        'details': {
                            'expense_ratio': expense_ratio,
                            'income': income,
                            'expenses': expenses,
                            'data_source': 'yodlee'
                        },
                        'actionable': True,
                        'suggested_actions': [
                            'Create a detailed budget',
                            'Identify and cut unnecessary expenses',
                            'Look for ways to increase income',
                            'Set savings goals'
                        ],
                        'coaching_tip': 'Aim to save at least 20% of your income for long-term financial security.',
                        'timestamp': datetime.now().isoformat()
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating Yodlee cash flow alerts: {e}")
            return []
    
    def _generate_yodlee_holding_alerts(self, user: User, timeframe: str) -> List[Dict[str, Any]]:
        """Generate alerts based on Yodlee holding data"""
        alerts = []
        
        try:
            # Get holdings data from Yodlee
            holdings = self.yodlee_service.get_user_holdings(user)
            if not holdings:
                return alerts
            
            # Single Stock Concentration Alert
            total_value = sum(h.get('current_value', 0) for h in holdings)
            if total_value > 0:
                for holding in holdings:
                    holding_value = holding.get('current_value', 0)
                    holding_percentage = (holding_value / total_value) * 100
                    
                    if holding_percentage > 15:  # More than 15% in single stock
                        alerts.append({
                            'id': f'yodlee_concentration_{holding.get("symbol", "unknown")}_{datetime.now().strftime("%Y%m%d_%H%M")}',
                            'type': 'yodlee_stock_concentration',
                            'priority': 'medium',
                            'category': 'concentration',
                            'title': 'High Stock Concentration',
                            'message': f'{holding.get("symbol", "Unknown")} represents {holding_percentage:.1f}% of your portfolio (${holding_value:,.0f}). Consider diversifying.',
                            'details': {
                                'symbol': holding.get('symbol', ''),
                                'company_name': holding.get('company_name', ''),
                                'current_value': holding_value,
                                'percentage': holding_percentage,
                                'total_portfolio_value': total_value,
                                'data_source': 'yodlee'
                            },
                            'actionable': True,
                            'suggested_actions': [
                                'Consider reducing position size',
                                'Add more diversified holdings',
                                'Review risk tolerance',
                                'Consider index funds for diversification'
                            ],
                            'coaching_tip': 'No single stock should dominate your portfolio. Diversification reduces risk.',
                            'timestamp': datetime.now().isoformat()
                        })
            
            # Sector Concentration Alert
            sector_holdings = {}
            for holding in holdings:
                sector = holding.get('sector', 'Unknown')
                value = holding.get('current_value', 0)
                sector_holdings[sector] = sector_holdings.get(sector, 0) + value
            
            for sector, value in sector_holdings.items():
                sector_percentage = (value / total_value) * 100
                if sector_percentage > 40:  # More than 40% in one sector
                    alerts.append({
                        'id': f'yodlee_sector_concentration_{sector}_{datetime.now().strftime("%Y%m%d_%H%M")}',
                        'type': 'yodlee_sector_concentration',
                        'priority': 'medium',
                        'category': 'concentration',
                        'title': 'High Sector Concentration',
                        'message': f'You\'re {sector_percentage:.1f}% invested in {sector} sector (${value:,.0f}). Consider diversifying across sectors.',
                        'details': {
                            'sector': sector,
                            'value': value,
                            'percentage': sector_percentage,
                            'total_portfolio_value': total_value,
                            'data_source': 'yodlee'
                        },
                        'actionable': True,
                        'suggested_actions': [
                            'Reduce exposure to this sector',
                            'Add holdings in other sectors',
                            'Consider sector-neutral strategies',
                            'Review sector rotation opportunities'
                        ],
                        'coaching_tip': 'Sector concentration increases risk. Diversify across multiple sectors for better risk management.',
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Low Diversification Alert
            num_holdings = len(holdings)
            if num_holdings < 10 and total_value > 50000:  # Less than 10 holdings with significant value
                alerts.append({
                    'id': f'yodlee_low_diversification_{datetime.now().strftime("%Y%m%d_%H%M")}',
                    'type': 'yodlee_low_diversification',
                    'priority': 'medium',
                    'category': 'diversification',
                    'title': 'Low Portfolio Diversification',
                    'message': f'You have only {num_holdings} holdings in your portfolio. Consider adding more positions for better diversification.',
                    'details': {
                        'num_holdings': num_holdings,
                        'total_value': total_value,
                        'data_source': 'yodlee'
                    },
                    'actionable': True,
                    'suggested_actions': [
                        'Add more individual stocks',
                        'Consider index funds or ETFs',
                        'Diversify across sectors and geographies',
                        'Review your investment strategy'
                    ],
                    'coaching_tip': 'Diversification is key to reducing risk. Aim for at least 15-20 different holdings.',
                    'timestamp': datetime.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating Yodlee holding alerts: {e}")
            return []
    
    def _filter_suppressed_alerts(self, user: User, alerts: List[Dict[str, Any]], 
                                portfolio_id: str = None) -> List[Dict[str, Any]]:
        """Filter out suppressed alerts based on cooldown periods and user preferences"""
        try:
            filtered_alerts = []
            
            for alert in alerts:
                alert_type = alert.get('type', '')
                
                # Check if alert type is enabled for user
                if not self.config_service.is_alert_enabled(user, alert_type):
                    continue
                
                # Check if alert is suppressed
                if self._is_alert_suppressed(user, alert_type, portfolio_id):
                    continue
                
                # Check delivery preferences
                category = alert.get('category', 'general')
                priority_level = self._map_priority_to_urgency(alert.get('priority', 'medium'))
                
                if not self.config_service.should_deliver_alert(user, category, priority_level):
                    continue
                
                filtered_alerts.append(alert)
            
            return filtered_alerts
            
        except Exception as e:
            logger.error(f"Error filtering suppressed alerts: {e}")
            return alerts
    
    def _is_alert_suppressed(self, user: User, alert_type: str, portfolio_id: str = None) -> bool:
        """Check if an alert type is currently suppressed for a user"""
        try:
            suppression = AlertSuppression.objects.filter(
                user=user,
                alert_type=alert_type,
                portfolio_id=portfolio_id
            ).first()
            
            if suppression and suppression.is_suppressed():
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking alert suppression: {e}")
            return False
    
    def _map_priority_to_urgency(self, priority: str) -> str:
        """Map priority level to urgency level"""
        mapping = {
            'high': 'critical',
            'medium': 'important', 
            'low': 'informational'
        }
        return mapping.get(priority, 'informational')
    
    def _store_alerts_in_db(self, user: User, alerts: List[Dict[str, Any]], 
                           portfolio_id: str = None, timeframe: str = '1M') -> None:
        """Store generated alerts in database for tracking and delivery"""
        try:
            for alert_data in alerts:
                alert_id = alert_data.get('id', f"{alert_data.get('type', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
                # Check if alert already exists
                existing_alert = SmartAlert.objects.filter(
                    user=user,
                    alert_id=alert_id
                ).first()
                
                if existing_alert:
                    continue  # Skip if already exists
                
                # Create new alert
                alert = SmartAlert.objects.create(
                    user=user,
                    alert_id=alert_id,
                    alert_type=alert_data.get('type', ''),
                    urgency_level=self._map_priority_to_urgency(alert_data.get('priority', 'medium')),
                    priority=alert_data.get('priority', 'medium'),
                    category=alert_data.get('category', 'general'),
                    title=alert_data.get('title', ''),
                    message=alert_data.get('message', ''),
                    coaching_tip=alert_data.get('coaching_tip', ''),
                    trigger_reason=alert_data.get('trigger_reason', ''),
                    details=alert_data.get('details', {}),
                    suggested_actions=alert_data.get('suggested_actions', []),
                    actionable=alert_data.get('actionable', True),
                    portfolio_id=portfolio_id,
                    timeframe=timeframe,
                    data_source=alert_data.get('details', {}).get('data_source', 'calculated'),
                    expires_at=datetime.now() + timedelta(days=30)  # Alerts expire after 30 days
                )
                
                # Update suppression record
                self._update_alert_suppression(user, alert_data.get('type', ''), portfolio_id)
                
                # Deliver alert via preferred channels (synchronous for now)
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(
                            self.delivery_service.deliver_alert(alert)
                        )
                    except RuntimeError:
                        asyncio.run(
                            self.delivery_service.deliver_alert(alert)
                        )
                except Exception as e:
                    logger.error(f"Error delivering alert: {e}")
                    # Continue even if delivery fails
                
        except Exception as e:
            logger.error(f"Error storing alerts in database: {e}")
    
    def _update_alert_suppression(self, user: User, alert_type: str, portfolio_id: str = None) -> None:
        """Update alert suppression record to prevent spam"""
        try:
            cooldown_hours = self.config_service.get_cooldown_period(user, alert_type)
            suppression_until = datetime.now() + timedelta(hours=cooldown_hours)
            
            suppression, created = AlertSuppression.objects.get_or_create(
                user=user,
                alert_type=alert_type,
                portfolio_id=portfolio_id,
                defaults={
                    'last_triggered_at': datetime.now(),
                    'suppression_until': suppression_until,
                    'trigger_count': 1,
                    'suppression_reason': 'cooldown_period'
                }
            )
            
            if not created:
                # Update existing suppression
                suppression.last_triggered_at = datetime.now()
                suppression.suppression_until = suppression_until
                suppression.trigger_count += 1
                suppression.save()
                
        except Exception as e:
            logger.error(f"Error updating alert suppression: {e}")
    
    def _add_trigger_reason(self, alert: Dict[str, Any], current_value: Any, 
                           threshold: Any, metric_name: str) -> Dict[str, Any]:
        """Add contextual trigger reason to alert"""
        try:
            if isinstance(current_value, (int, float)) and isinstance(threshold, (int, float)):
                if current_value > threshold:
                    trigger_reason = f"{metric_name} is {current_value:.2f}, above your threshold of {threshold:.2f}"
                else:
                    trigger_reason = f"{metric_name} is {current_value:.2f}, below your threshold of {threshold:.2f}"
            else:
                trigger_reason = f"{metric_name} triggered alert condition"
            
            alert['trigger_reason'] = trigger_reason
            return alert
            
        except Exception as e:
            logger.error(f"Error adding trigger reason: {e}")
            alert['trigger_reason'] = "Alert condition met"
            return alert
    
    def _enhance_alert_with_context(self, alert: Dict[str, Any], user: User, 
                                   alert_type: str) -> Dict[str, Any]:
        """Enhance alert with user-specific context and urgency level"""
        try:
            # Get user thresholds for context
            thresholds = self.config_service.get_user_thresholds(user, alert_type)
            
            # Add urgency level based on severity
            urgency_level = self._determine_urgency_level(alert, thresholds)
            alert['urgency_level'] = urgency_level
            
            # Add contextual trigger reason if not present
            if 'trigger_reason' not in alert:
                alert['trigger_reason'] = self._generate_trigger_reason(alert, thresholds)
            
            # Add expiration time
            alert['expires_at'] = (datetime.now() + timedelta(days=30)).isoformat()
            
            return alert
            
        except Exception as e:
            logger.error(f"Error enhancing alert with context: {e}")
            return alert
    
    def _determine_urgency_level(self, alert: Dict[str, Any], thresholds: Dict[str, Any]) -> str:
        """Determine urgency level based on alert severity and thresholds"""
        try:
            priority = alert.get('priority', 'medium')
            alert_type = alert.get('type', '')
            details = alert.get('details', {})
            
            # Critical alerts - immediate action required
            critical_types = [
                'yodlee_negative_cashflow',
                'risk_high_drawdown',
                'yodlee_portfolio_decline'
            ]
            
            if alert_type in critical_types or priority == 'high':
                return 'critical'
            
            # Important alerts - review soon
            important_types = [
                'risk_sharpe_deterioration',
                'risk_high_volatility',
                'allocation_tech_overweight',
                'yodlee_high_cash_position',
                'yodlee_low_cash_position'
            ]
            
            if alert_type in important_types or priority == 'medium':
                return 'important'
            
            # Informational alerts - coaching/FYI
            return 'informational'
            
        except Exception as e:
            logger.error(f"Error determining urgency level: {e}")
            return 'informational'
    
    def _generate_trigger_reason(self, alert: Dict[str, Any], thresholds: Dict[str, Any]) -> str:
        """Generate contextual trigger reason for alert"""
        try:
            alert_type = alert.get('type', '')
            details = alert.get('details', {})
            
            # Generate specific trigger reasons based on alert type
            if 'performance' in alert_type:
                change_pct = details.get('change_percent', 0)
                threshold = thresholds.get('performance_diff_threshold', 2.0)
                return f"Portfolio performance difference of {abs(change_pct):.1f}% exceeds threshold of {threshold:.1f}%"
            
            elif 'sharpe' in alert_type:
                sharpe_ratio = details.get('sharpe_ratio', 0)
                threshold = thresholds.get('sharpe_min_threshold', 0.5)
                return f"Sharpe ratio of {sharpe_ratio:.2f} is below threshold of {threshold:.2f}"
            
            elif 'volatility' in alert_type:
                volatility = details.get('volatility', 0)
                threshold = thresholds.get('volatility_max_threshold', 20.0)
                return f"Volatility of {volatility:.1f}% exceeds threshold of {threshold:.1f}%"
            
            elif 'drawdown' in alert_type:
                drawdown = details.get('max_drawdown', 0)
                threshold = thresholds.get('drawdown_max_threshold', -15.0)
                return f"Maximum drawdown of {abs(drawdown):.1f}% exceeds threshold of {abs(threshold):.1f}%"
            
            elif 'tech_overweight' in alert_type:
                tech_weight = details.get('current_weight', 0)
                threshold = thresholds.get('tech_weight_max_threshold', 0.35)
                return f"Technology allocation of {tech_weight:.1%} exceeds threshold of {threshold:.1%}"
            
            elif 'cash' in alert_type:
                cash_pct = details.get('cash_percentage', 0)
                if 'high' in alert_type:
                    threshold = thresholds.get('cash_max_threshold', 0.20)
                    return f"Cash position of {cash_pct:.1f}% exceeds threshold of {threshold:.1%}"
                else:
                    threshold = thresholds.get('cash_min_threshold', 0.02)
                    return f"Cash position of {cash_pct:.1f}% is below threshold of {threshold:.1%}"
            
            else:
                return "Alert condition met based on your portfolio analysis"
                
        except Exception as e:
            logger.error(f"Error generating trigger reason: {e}")
            return "Alert condition met"

# Global instance
smart_alerts_service = SmartAlertsService()
