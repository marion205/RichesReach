"""
Point-in-Time Data Service for Institutional Features
Handles data snapshots, corporate actions, and historical accuracy
"""
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from .models import (
    StockPriceSnapshot, CorporateAction, MarketRegime, 
    PortfolioSnapshot, MLModelVersion, AuditLog
)
from .ml_settings import get_pit_config, is_pit_enabled

logger = logging.getLogger(__name__)

class PointInTimeDataService:
    """Service for managing point-in-time data snapshots"""
    
    def __init__(self):
        self.config = get_pit_config()
        self.enabled = is_pit_enabled()
    
    def create_stock_snapshot(
        self, 
        stock_id: int, 
        symbol: str, 
        as_of: date, 
        price_data: Dict[str, Any],
        additional_metrics: Optional[Dict[str, Any]] = None
    ) -> StockPriceSnapshot:
        """Create a point-in-time stock price snapshot"""
        if not self.enabled:
            logger.warning("Point-in-time data is disabled")
            return None
        
        try:
            with transaction.atomic():
                snapshot, created = StockPriceSnapshot.objects.get_or_create(
                    stock_id=stock_id,
                    as_of=as_of,
                    defaults={
                        'symbol': symbol.upper(),
                        'open_price': price_data.get('open'),
                        'high_price': price_data.get('high'),
                        'low_price': price_data.get('low'),
                        'close': price_data.get('close'),
                        'volume': price_data.get('volume'),
                        'adjusted_close': price_data.get('adjusted_close'),
                        'dividend_amount': price_data.get('dividend_amount', 0),
                        'split_coefficient': price_data.get('split_coefficient', 1.0),
                        'source': price_data.get('source', 'api'),
                    }
                )
                
                # Update additional metrics if provided
                if additional_metrics:
                    snapshot.adv_score = additional_metrics.get('adv_score')
                    snapshot.volatility = additional_metrics.get('volatility')
                    snapshot.beta = additional_metrics.get('beta')
                    snapshot.market_cap = additional_metrics.get('market_cap')
                    snapshot.pe_ratio = additional_metrics.get('pe_ratio')
                    snapshot.dividend_yield = additional_metrics.get('dividend_yield')
                    snapshot.save()
                
                logger.info(f"Created stock snapshot: {symbol} @ {as_of}")
                return snapshot
                
        except Exception as e:
            logger.error(f"Error creating stock snapshot: {e}")
            return None
    
    def get_stock_snapshot(
        self, 
        symbol: str, 
        as_of: date
    ) -> Optional[StockPriceSnapshot]:
        """Get stock snapshot for a specific date"""
        try:
            return StockPriceSnapshot.objects.filter(
                symbol=symbol.upper(),
                as_of=as_of
            ).first()
        except Exception as e:
            logger.error(f"Error getting stock snapshot: {e}")
            return None
    
    def get_latest_snapshot_before(
        self, 
        symbol: str, 
        as_of: date
    ) -> Optional[StockPriceSnapshot]:
        """Get latest stock snapshot before a specific date"""
        try:
            return StockPriceSnapshot.objects.filter(
                symbol=symbol.upper(),
                as_of__lte=as_of
            ).order_by('-as_of').first()
        except Exception as e:
            logger.error(f"Error getting latest snapshot: {e}")
            return None
    
    def get_stock_history(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> List[StockPriceSnapshot]:
        """Get stock price history for a date range"""
        try:
            return list(StockPriceSnapshot.objects.filter(
                symbol=symbol.upper(),
                as_of__range=[start_date, end_date]
            ).order_by('as_of'))
        except Exception as e:
            logger.error(f"Error getting stock history: {e}")
            return []
    
    def create_corporate_action(
        self,
        stock_id: int,
        symbol: str,
        action_type: str,
        ex_date: date,
        amount: Optional[float] = None,
        ratio: Optional[float] = None,
        description: str = ""
    ) -> CorporateAction:
        """Create a corporate action record"""
        try:
            with transaction.atomic():
                action = CorporateAction.objects.create(
                    stock_id=stock_id,
                    symbol=symbol.upper(),
                    action_type=action_type,
                    ex_date=ex_date,
                    amount=amount,
                    ratio=ratio,
                    description=description,
                    source='api'
                )
                
                logger.info(f"Created corporate action: {symbol} {action_type} on {ex_date}")
                return action
                
        except Exception as e:
            logger.error(f"Error creating corporate action: {e}")
            return None
    
    def get_corporate_actions(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> List[CorporateAction]:
        """Get corporate actions for a symbol and date range"""
        try:
            return list(CorporateAction.objects.filter(
                symbol=symbol.upper(),
                ex_date__range=[start_date, end_date]
            ).order_by('ex_date'))
        except Exception as e:
            logger.error(f"Error getting corporate actions: {e}")
            return []
    
    def create_market_regime(
        self,
        as_of: date,
        regime: str,
        confidence: float,
        vix_level: Optional[float] = None,
        market_return: Optional[float] = None,
        volatility: Optional[float] = None,
        ml_prediction: Optional[Dict[str, Any]] = None
    ) -> MarketRegime:
        """Create a market regime classification"""
        try:
            with transaction.atomic():
                regime_obj, created = MarketRegime.objects.get_or_create(
                    as_of=as_of,
                    defaults={
                        'regime': regime,
                        'confidence': confidence,
                        'vix_level': vix_level,
                        'market_return': market_return,
                        'volatility': volatility,
                        'ml_prediction': ml_prediction,
                        'model_version': 'v1.0'
                    }
                )
                
                if not created:
                    # Update existing regime
                    regime_obj.regime = regime
                    regime_obj.confidence = confidence
                    regime_obj.vix_level = vix_level
                    regime_obj.market_return = market_return
                    regime_obj.volatility = volatility
                    regime_obj.ml_prediction = ml_prediction
                    regime_obj.save()
                
                logger.info(f"Created market regime: {regime} on {as_of}")
                return regime_obj
                
        except Exception as e:
            logger.error(f"Error creating market regime: {e}")
            return None
    
    def get_market_regime(self, as_of: date) -> Optional[MarketRegime]:
        """Get market regime for a specific date"""
        try:
            return MarketRegime.objects.filter(as_of=as_of).first()
        except Exception as e:
            logger.error(f"Error getting market regime: {e}")
            return None
    
    def create_portfolio_snapshot(
        self,
        user_id: int,
        as_of: date,
        holdings: Dict[str, Any],
        total_value: float,
        performance_metrics: Optional[Dict[str, Any]] = None,
        risk_metrics: Optional[Dict[str, Any]] = None
    ) -> PortfolioSnapshot:
        """Create a portfolio snapshot"""
        try:
            with transaction.atomic():
                snapshot, created = PortfolioSnapshot.objects.get_or_create(
                    user_id=user_id,
                    as_of=as_of,
                    defaults={
                        'holdings': holdings,
                        'total_value': total_value,
                        'cash_balance': holdings.get('cash', 0),
                        'source': 'system'
                    }
                )
                
                # Update performance metrics if provided
                if performance_metrics:
                    snapshot.daily_return = performance_metrics.get('daily_return')
                    snapshot.total_return = performance_metrics.get('total_return')
                    snapshot.volatility = performance_metrics.get('volatility')
                    snapshot.sharpe_ratio = performance_metrics.get('sharpe_ratio')
                    snapshot.max_drawdown = performance_metrics.get('max_drawdown')
                    snapshot.sector_allocation = performance_metrics.get('sector_allocation')
                
                # Update risk metrics if provided
                if risk_metrics:
                    snapshot.var_95 = risk_metrics.get('var_95')
                    snapshot.cvar_95 = risk_metrics.get('cvar_95')
                    snapshot.beta = risk_metrics.get('beta')
                    snapshot.tracking_error = risk_metrics.get('tracking_error')
                
                snapshot.save()
                
                logger.info(f"Created portfolio snapshot for user {user_id} @ {as_of}")
                return snapshot
                
        except Exception as e:
            logger.error(f"Error creating portfolio snapshot: {e}")
            return None
    
    def get_portfolio_snapshot(
        self, 
        user_id: int, 
        as_of: date
    ) -> Optional[PortfolioSnapshot]:
        """Get portfolio snapshot for a specific date"""
        try:
            return PortfolioSnapshot.objects.filter(
                user_id=user_id,
                as_of=as_of
            ).first()
        except Exception as e:
            logger.error(f"Error getting portfolio snapshot: {e}")
            return None
    
    def get_portfolio_history(
        self, 
        user_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[PortfolioSnapshot]:
        """Get portfolio history for a date range"""
        try:
            return list(PortfolioSnapshot.objects.filter(
                user_id=user_id,
                as_of__range=[start_date, end_date]
            ).order_by('as_of'))
        except Exception as e:
            logger.error(f"Error getting portfolio history: {e}")
            return []
    
    def cleanup_old_data(self, retention_days: Optional[int] = None):
        """Clean up old point-in-time data"""
        if not self.enabled:
            return
        
        retention_days = retention_days or self.config.get('RETENTION_DAYS', 90)
        cutoff_date = timezone.now().date() - timedelta(days=retention_days)
        
        try:
            with transaction.atomic():
                # Clean up old stock snapshots
                deleted_snapshots = StockPriceSnapshot.objects.filter(
                    as_of__lt=cutoff_date
                ).delete()[0]
                
                # Clean up old corporate actions
                deleted_actions = CorporateAction.objects.filter(
                    ex_date__lt=cutoff_date
                ).delete()[0]
                
                # Clean up old market regimes
                deleted_regimes = MarketRegime.objects.filter(
                    as_of__lt=cutoff_date
                ).delete()[0]
                
                # Clean up old portfolio snapshots
                deleted_portfolios = PortfolioSnapshot.objects.filter(
                    as_of__lt=cutoff_date
                ).delete()[0]
                
                logger.info(f"Cleaned up old data: {deleted_snapshots} snapshots, "
                          f"{deleted_actions} actions, {deleted_regimes} regimes, "
                          f"{deleted_portfolios} portfolios")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality metrics for monitoring"""
        try:
            today = timezone.now().date()
            
            # Count snapshots by date
            recent_snapshots = StockPriceSnapshot.objects.filter(
                as_of__gte=today - timedelta(days=7)
            ).count()
            
            # Count unique symbols
            unique_symbols = StockPriceSnapshot.objects.values('symbol').distinct().count()
            
            # Count corporate actions
            recent_actions = CorporateAction.objects.filter(
                ex_date__gte=today - timedelta(days=30)
            ).count()
            
            # Count market regimes
            recent_regimes = MarketRegime.objects.filter(
                as_of__gte=today - timedelta(days=30)
            ).count()
            
            return {
                'recent_snapshots_7d': recent_snapshots,
                'unique_symbols': unique_symbols,
                'recent_actions_30d': recent_actions,
                'recent_regimes_30d': recent_regimes,
                'data_freshness': {
                    'latest_snapshot': StockPriceSnapshot.objects.order_by('-as_of').first().as_of if StockPriceSnapshot.objects.exists() else None,
                    'latest_regime': MarketRegime.objects.order_by('-as_of').first().as_of if MarketRegime.objects.exists() else None,
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting data quality metrics: {e}")
            return {}

class AuditService:
    """Service for audit logging"""
    
    @staticmethod
    def log_ml_mutation(
        user_id: int,
        action_type: str,
        request_id: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: str = "",
        model_version: str = "",
        feature_version: str = "",
        optimization_method: str = ""
    ) -> AuditLog:
        """Log an ML mutation for audit purposes"""
        try:
            with transaction.atomic():
                audit_log = AuditLog.objects.create(
                    user_id=user_id,
                    action_type=action_type,
                    request_id=request_id,
                    input_data=input_data,
                    output_data=output_data,
                    execution_time_ms=execution_time_ms,
                    success=success,
                    error_message=error_message,
                    model_version=model_version,
                    feature_version=feature_version,
                    optimization_method=optimization_method
                )
                
                logger.info(f"Audit log created: {action_type} for user {user_id}")
                return audit_log
                
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            return None
    
    @staticmethod
    def get_audit_logs(
        user_id: Optional[int] = None,
        action_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs with optional filtering"""
        try:
            queryset = AuditLog.objects.all()
            
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            if action_type:
                queryset = queryset.filter(action_type=action_type)
            if start_date:
                queryset = queryset.filter(timestamp__date__gte=start_date)
            if end_date:
                queryset = queryset.filter(timestamp__date__lte=end_date)
            
            return list(queryset.order_by('-timestamp')[:limit])
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []

# Global instances
pit_service = PointInTimeDataService()
audit_service = AuditService()
