import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .real_market_data_service import real_market_data_service
from .advanced_analytics_service import advanced_analytics_service
from .custom_benchmark_service import custom_benchmark_service
from .smart_alerts_service import smart_alerts_service

logger = logging.getLogger(__name__)

class RealTimeDataConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time market data and portfolio updates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.subscribed_symbols = set()
        self.subscribed_portfolios = set()
        self.subscribed_benchmarks = set()
        self.update_interval = 5  # seconds
        self.is_running = False
        self.update_task = None
        self.alerts_service = smart_alerts_service
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return
        
        self.room_group_name = f"user_{self.user.id}_realtime"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected for user {self.user.id}")
        
        # Start update task
        self.is_running = True
        self.update_task = asyncio.create_task(self.periodic_update())
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnected for user {self.user.id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_symbols':
                await self.handle_subscribe_symbols(data.get('symbols', []))
            elif message_type == 'subscribe_portfolio':
                await self.handle_subscribe_portfolio(data.get('portfolio_id'))
            elif message_type == 'subscribe_benchmark':
                await self.handle_subscribe_benchmark(data.get('benchmark_id'))
            elif message_type == 'unsubscribe_symbols':
                await self.handle_unsubscribe_symbols(data.get('symbols', []))
            elif message_type == 'unsubscribe_portfolio':
                await self.handle_unsubscribe_portfolio(data.get('portfolio_id'))
            elif message_type == 'unsubscribe_benchmark':
                await self.handle_unsubscribe_benchmark(data.get('benchmark_id'))
            elif message_type == 'get_analytics':
                await self.handle_get_analytics(data.get('portfolio_data'), data.get('benchmark_data'))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def handle_subscribe_symbols(self, symbols: List[str]):
        """Subscribe to real-time updates for specific symbols"""
        self.subscribed_symbols.update(symbols)
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'subscribed_symbols': list(self.subscribed_symbols)
        }))
        logger.info(f"User {self.user.id} subscribed to symbols: {symbols}")
    
    async def handle_subscribe_portfolio(self, portfolio_id: str):
        """Subscribe to real-time updates for a portfolio"""
        self.subscribed_portfolios.add(portfolio_id)
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'subscribed_portfolios': list(self.subscribed_portfolios)
        }))
        logger.info(f"User {self.user.id} subscribed to portfolio: {portfolio_id}")
    
    async def handle_subscribe_benchmark(self, benchmark_id: str):
        """Subscribe to real-time updates for a benchmark"""
        self.subscribed_benchmarks.add(benchmark_id)
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'subscribed_benchmarks': list(self.subscribed_benchmarks)
        }))
        logger.info(f"User {self.user.id} subscribed to benchmark: {benchmark_id}")
    
    async def handle_unsubscribe_symbols(self, symbols: List[str]):
        """Unsubscribe from real-time updates for specific symbols"""
        self.subscribed_symbols.difference_update(symbols)
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'subscribed_symbols': list(self.subscribed_symbols)
        }))
    
    async def handle_unsubscribe_portfolio(self, portfolio_id: str):
        """Unsubscribe from real-time updates for a portfolio"""
        self.subscribed_portfolios.discard(portfolio_id)
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'subscribed_portfolios': list(self.subscribed_portfolios)
        }))
    
    async def handle_unsubscribe_benchmark(self, benchmark_id: str):
        """Unsubscribe from real-time updates for a benchmark"""
        self.subscribed_benchmarks.discard(benchmark_id)
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'subscribed_benchmarks': list(self.subscribed_benchmarks)
        }))
    
    async def handle_get_analytics(self, portfolio_data: Dict, benchmark_data: Dict):
        """Calculate and return advanced analytics"""
        try:
            analytics = await self.calculate_analytics_async(portfolio_data, benchmark_data)
            await self.send(text_data=json.dumps({
                'type': 'analytics_update',
                'analytics': analytics,
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error calculating analytics: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to calculate analytics'
            }))
    
    async def periodic_update(self):
        """Periodic update task for real-time data"""
        while self.is_running:
            try:
                await asyncio.sleep(self.update_interval)
                
                if not self.is_running:
                    break
                
                # Update subscribed symbols
                if self.subscribed_symbols:
                    await self.update_symbol_data()
                
                # Update subscribed portfolios
                if self.subscribed_portfolios:
                    await self.update_portfolio_data()
                
                # Update subscribed benchmarks
                if self.subscribed_benchmarks:
                    await self.update_benchmark_data()
                
                # Check for new smart alerts
                await self.check_smart_alerts()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic update: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    async def update_symbol_data(self):
        """Update real-time data for subscribed symbols"""
        try:
            symbol_data = {}
            for symbol in self.subscribed_symbols:
                # Get latest data (1D timeframe for real-time updates)
                data = await self.get_symbol_data_async(symbol, '1D')
                if data:
                    symbol_data[symbol] = {
                        'current_price': data.get('endValue', 0),
                        'change': data.get('totalReturn', 0),
                        'change_percent': data.get('totalReturnPercent', 0),
                        'volume': data.get('dataPoints', [{}])[-1].get('volume', 0) if data.get('dataPoints') else 0,
                        'timestamp': datetime.now().isoformat()
                    }
            
            if symbol_data:
                await self.send(text_data=json.dumps({
                    'type': 'symbol_update',
                    'data': symbol_data,
                    'timestamp': datetime.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"Error updating symbol data: {e}")
    
    async def update_portfolio_data(self):
        """Update real-time data for subscribed portfolios"""
        try:
            portfolio_data = {}
            for portfolio_id in self.subscribed_portfolios:
                # Get portfolio performance data
                data = await self.get_portfolio_data_async(portfolio_id)
                if data:
                    portfolio_data[portfolio_id] = {
                        'total_value': data.get('totalValue', 0),
                        'total_return': data.get('totalReturn', 0),
                        'total_return_percent': data.get('totalReturnPercent', 0),
                        'day_change': data.get('dayChange', 0),
                        'day_change_percent': data.get('dayChangePercent', 0),
                        'timestamp': datetime.now().isoformat()
                    }
            
            if portfolio_data:
                await self.send(text_data=json.dumps({
                    'type': 'portfolio_update',
                    'data': portfolio_data,
                    'timestamp': datetime.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"Error updating portfolio data: {e}")
    
    async def update_benchmark_data(self):
        """Update real-time data for subscribed benchmarks"""
        try:
            benchmark_data = {}
            for benchmark_id in self.subscribed_benchmarks:
                # Get benchmark performance data
                data = await self.get_benchmark_data_async(benchmark_id)
                if data:
                    benchmark_data[benchmark_id] = {
                        'current_value': data.get('endValue', 0),
                        'total_return': data.get('totalReturn', 0),
                        'total_return_percent': data.get('totalReturnPercent', 0),
                        'volatility': data.get('volatility', 0),
                        'sharpe_ratio': data.get('sharpeRatio', 0),
                        'timestamp': datetime.now().isoformat()
                    }
            
            if benchmark_data:
                await self.send(text_data=json.dumps({
                    'type': 'benchmark_update',
                    'data': benchmark_data,
                    'timestamp': datetime.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"Error updating benchmark data: {e}")
    
    @database_sync_to_async
    def get_symbol_data_async(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Get symbol data asynchronously"""
        try:
            return real_market_data_service.get_benchmark_data(symbol, timeframe)
        except Exception as e:
            logger.error(f"Error getting symbol data for {symbol}: {e}")
            return None
    
    @database_sync_to_async
    def get_portfolio_data_async(self, portfolio_id: str) -> Optional[Dict]:
        """Get portfolio data asynchronously"""
        try:
            # This would integrate with your portfolio service
            # For now, return mock data
            return {
                'totalValue': 100000,
                'totalReturn': 5000,
                'totalReturnPercent': 5.0,
                'dayChange': 250,
                'dayChangePercent': 0.25
            }
        except Exception as e:
            logger.error(f"Error getting portfolio data for {portfolio_id}: {e}")
            return None
    
    @database_sync_to_async
    def get_benchmark_data_async(self, benchmark_id: str) -> Optional[Dict]:
        """Get benchmark data asynchronously"""
        try:
            if benchmark_id.startswith('CUSTOM_'):
                custom_id = benchmark_id.replace('CUSTOM_', '')
                return custom_benchmark_service.get_custom_benchmark_data(int(custom_id), self.user, '1D')
            else:
                return real_market_data_service.get_benchmark_data(benchmark_id, '1D')
        except Exception as e:
            logger.error(f"Error getting benchmark data for {benchmark_id}: {e}")
            return None
    
    @database_sync_to_async
    def calculate_analytics_async(self, portfolio_data: Dict, benchmark_data: Dict) -> Dict:
        """Calculate analytics asynchronously"""
        try:
            return advanced_analytics_service.calculate_comprehensive_metrics(portfolio_data, benchmark_data)
        except Exception as e:
            logger.error(f"Error calculating analytics: {e}")
            return {}

class RiskAlertConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time risk monitoring and alerts"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.risk_thresholds = {}
        self.monitoring_task = None
        self.is_running = False
    
    async def connect(self):
        """Handle WebSocket connection for risk monitoring"""
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return
        
        self.room_group_name = f"user_{self.user.id}_risk_alerts"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Risk monitoring WebSocket connected for user {self.user.id}")
        
        # Start risk monitoring task
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self.risk_monitoring_loop())
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"Risk monitoring WebSocket disconnected for user {self.user.id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages for risk monitoring"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'set_risk_thresholds':
                await self.handle_set_risk_thresholds(data.get('thresholds', {}))
            elif message_type == 'get_risk_status':
                await self.handle_get_risk_status()
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error handling risk monitoring message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def handle_set_risk_thresholds(self, thresholds: Dict):
        """Set risk monitoring thresholds"""
        self.risk_thresholds = thresholds
        await self.send(text_data=json.dumps({
            'type': 'thresholds_updated',
            'thresholds': self.risk_thresholds
        }))
        logger.info(f"Risk thresholds updated for user {self.user.id}: {thresholds}")
    
    async def handle_get_risk_status(self):
        """Get current risk status"""
        try:
            risk_status = await self.calculate_risk_status_async()
            await self.send(text_data=json.dumps({
                'type': 'risk_status',
                'status': risk_status,
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error getting risk status: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to get risk status'
            }))
    
    async def risk_monitoring_loop(self):
        """Main risk monitoring loop"""
        while self.is_running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                if not self.is_running:
                    break
                
                # Calculate current risk metrics
                risk_status = await self.calculate_risk_status_async()
                
                # Check for threshold breaches
                alerts = await self.check_risk_alerts_async(risk_status)
                
                if alerts:
                    await self.send(text_data=json.dumps({
                        'type': 'risk_alert',
                        'alerts': alerts,
                        'timestamp': datetime.now().isoformat()
                    }))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in risk monitoring loop: {e}")
                await asyncio.sleep(1)
    
    @database_sync_to_async
    def calculate_risk_status_async(self) -> Dict:
        """Calculate current risk status asynchronously"""
        try:
            # This would integrate with your portfolio and risk calculation services
            # For now, return mock risk data
            return {
                'portfolio_var_95': -2.5,
                'portfolio_var_99': -4.1,
                'max_drawdown': -8.3,
                'volatility': 15.2,
                'beta': 1.1,
                'sharpe_ratio': 0.85,
                'correlation_to_market': 0.78,
                'concentration_risk': 0.35,
                'liquidity_risk': 0.12,
                'overall_risk_score': 6.5  # 1-10 scale
            }
        except Exception as e:
            logger.error(f"Error calculating risk status: {e}")
            return {}
    
    @database_sync_to_async
    def check_risk_alerts_async(self, risk_status: Dict) -> List[Dict]:
        """Check for risk threshold breaches and generate alerts"""
        try:
            alerts = []
            
            # Check VaR thresholds
            if 'var_95_threshold' in self.risk_thresholds:
                if risk_status.get('portfolio_var_95', 0) < -self.risk_thresholds['var_95_threshold']:
                    alerts.append({
                        'type': 'var_breach',
                        'level': 'warning',
                        'message': f"95% VaR exceeded threshold: {risk_status.get('portfolio_var_95', 0):.2f}%",
                        'metric': 'portfolio_var_95',
                        'value': risk_status.get('portfolio_var_95', 0),
                        'threshold': -self.risk_thresholds['var_95_threshold']
                    })
            
            # Check volatility threshold
            if 'volatility_threshold' in self.risk_thresholds:
                if risk_status.get('volatility', 0) > self.risk_thresholds['volatility_threshold']:
                    alerts.append({
                        'type': 'volatility_breach',
                        'level': 'warning',
                        'message': f"Volatility exceeded threshold: {risk_status.get('volatility', 0):.2f}%",
                        'metric': 'volatility',
                        'value': risk_status.get('volatility', 0),
                        'threshold': self.risk_thresholds['volatility_threshold']
                    })
            
            # Check drawdown threshold
            if 'drawdown_threshold' in self.risk_thresholds:
                if risk_status.get('max_drawdown', 0) < -self.risk_thresholds['drawdown_threshold']:
                    alerts.append({
                        'type': 'drawdown_breach',
                        'level': 'critical',
                        'message': f"Maximum drawdown exceeded threshold: {risk_status.get('max_drawdown', 0):.2f}%",
                        'metric': 'max_drawdown',
                        'value': risk_status.get('max_drawdown', 0),
                        'threshold': -self.risk_thresholds['drawdown_threshold']
                    })
            
            # Check overall risk score
            if 'risk_score_threshold' in self.risk_thresholds:
                if risk_status.get('overall_risk_score', 0) > self.risk_thresholds['risk_score_threshold']:
                    alerts.append({
                        'type': 'risk_score_breach',
                        'level': 'warning',
                        'message': f"Overall risk score exceeded threshold: {risk_status.get('overall_risk_score', 0):.1f}",
                        'metric': 'overall_risk_score',
                        'value': risk_status.get('overall_risk_score', 0),
                        'threshold': self.risk_thresholds['risk_score_threshold']
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking risk alerts: {e}")
            return []
    
    async def check_smart_alerts(self):
        """Check for new smart alerts and send them via WebSocket"""
        try:
            # Get smart alerts for the user
            alerts = await self.get_smart_alerts_async()
            
            if alerts:
                # Send alerts to the user
                await self.send(text_data=json.dumps({
                    'type': 'smart_alerts',
                    'alerts': alerts,
                    'timestamp': datetime.now().isoformat()
                }))
                
                logger.info(f"Sent {len(alerts)} smart alerts to user {self.user.id}")
                
        except Exception as e:
            logger.error(f"Error checking smart alerts: {e}")
    
    @database_sync_to_async
    def get_smart_alerts_async(self):
        """Get smart alerts for the user (async wrapper)"""
        try:
            # Get alerts for the first subscribed portfolio or default
            portfolio_id = list(self.subscribed_portfolios)[0] if self.subscribed_portfolios else None
            
            alerts = self.alerts_service.generate_smart_alerts(
                user=self.user,
                portfolio_id=portfolio_id,
                timeframe='1M'
            )
            
            # Filter alerts by priority and recent timestamp
            recent_alerts = []
            cutoff_time = datetime.now() - timedelta(hours=1)  # Only alerts from last hour
            
            for alert in alerts:
                alert_time = datetime.fromisoformat(alert.get('timestamp', ''))
                if alert_time > cutoff_time and alert.get('priority') in ['high', 'medium']:
                    recent_alerts.append(alert)
            
            return recent_alerts[:5]  # Limit to 5 most recent alerts
            
        except Exception as e:
            logger.error(f"Error getting smart alerts: {e}")
            return []