"""
GraphQL Types and Queries for Transparency Dashboard
Public-facing performance metrics and signal tracking.
"""
import graphene
from .transparency_dashboard import get_transparency_dashboard
from typing import Dict, Any


class SignalRecordType(graphene.ObjectType):
    """GraphQL type for signal record"""
    id = graphene.Int()
    symbol = graphene.String()
    action = graphene.String()
    confidence = graphene.Float()
    entry_price = graphene.Float()
    entry_timestamp = graphene.String()
    exit_price = graphene.Float()
    exit_timestamp = graphene.String()
    pnl = graphene.Float()
    pnl_percent = graphene.Float()
    reasoning = graphene.String()
    status = graphene.String()
    user_id = graphene.Int()
    trading_mode = graphene.String()
    signal_id = graphene.String()


class TransparencyStatisticsType(graphene.ObjectType):
    """Statistics for transparency dashboard"""
    total_signals = graphene.Int()
    closed_signals = graphene.Int()
    open_signals = graphene.Int()
    abstained_signals = graphene.Int()
    win_rate = graphene.Float()
    total_wins = graphene.Int()
    total_losses = graphene.Int()
    avg_win = graphene.Float()
    avg_loss = graphene.Float()
    total_pnl = graphene.Float()
    profit_factor = graphene.Float()
    last_updated = graphene.String()


class TransparencyDashboardType(graphene.ObjectType):
    """Transparency dashboard data"""
    signals = graphene.List(SignalRecordType)
    statistics = graphene.Field(TransparencyStatisticsType)


class PerformanceSummaryType(graphene.ObjectType):
    """Performance summary for a time period"""
    period_days = graphene.Int()
    total_signals = graphene.Int()
    win_rate = graphene.Float()
    total_pnl = graphene.Float()
    avg_pnl = graphene.Float()
    sharpe_ratio = graphene.Float()
    max_drawdown = graphene.Float()


class TransparencyQueries(graphene.ObjectType):
    """GraphQL queries for transparency dashboard"""
    
    transparency_dashboard = graphene.Field(
        TransparencyDashboardType,
        limit=graphene.Int(default_value=50),
        description="Get transparency dashboard with last N signals and statistics"
    )
    
    transparency_signals = graphene.List(
        SignalRecordType,
        limit=graphene.Int(default_value=50),
        status=graphene.String(),
        symbol=graphene.String(),
        description="Get transparency signals (optionally filtered)"
    )
    
    transparency_performance = graphene.Field(
        PerformanceSummaryType,
        days=graphene.Int(default_value=30),
        description="Get performance summary for last N days"
    )
    
    transparency_csv_export = graphene.String(
        limit=graphene.Int(default_value=100),
        days=graphene.Int(),
        status=graphene.String(),
        description="Get CSV export URL for signals (returns download link)"
    )
    
    def resolve_transparency_dashboard(self, info, limit: int = 50) -> Dict[str, Any]:
        """Resolve transparency dashboard data"""
        dashboard_service = get_transparency_dashboard()
        data = dashboard_service.get_dashboard_data(limit=limit)
        
        # Convert to GraphQL types
        signals = [
            SignalRecordType(
                id=s['id'],
                symbol=s['symbol'],
                action=s['action'],
                confidence=s['confidence'],
                entry_price=s['entry_price'],
                entry_timestamp=s['entry_timestamp'],
                exit_price=s['exit_price'],
                exit_timestamp=s['exit_timestamp'],
                pnl=s['pnl'],
                pnl_percent=s['pnl_percent'],
                reasoning=s['reasoning'],
                status=s['status'],
                user_id=s.get('user_id'),
                trading_mode=s.get('trading_mode', 'PAPER'),
                signal_id=s.get('signal_id', '')
            )
            for s in data['signals']
        ]
        
        stats = TransparencyStatisticsType(
            total_signals=data['statistics']['total_signals'],
            closed_signals=data['statistics']['closed_signals'],
            open_signals=data['statistics']['open_signals'],
            abstained_signals=data['statistics']['abstained_signals'],
            win_rate=data['statistics']['win_rate'],
            total_wins=data['statistics']['total_wins'],
            total_losses=data['statistics']['total_losses'],
            avg_win=data['statistics']['avg_win'],
            avg_loss=data['statistics']['avg_loss'],
            total_pnl=data['statistics']['total_pnl'],
            profit_factor=data['statistics']['profit_factor'],
            last_updated=data['statistics']['last_updated']
        )
        
        return TransparencyDashboardType(
            signals=signals,
            statistics=stats
        )
    
    def resolve_transparency_signals(
        self,
        info,
        limit: int = 50,
        status: str = None,
        symbol: str = None
    ):
        """Resolve transparency signals with optional filters"""
        dashboard_service = get_transparency_dashboard()
        data = dashboard_service.get_dashboard_data(limit=limit * 2)  # Get more to filter
        
        # Filter signals
        signals = data['signals']
        if status:
            signals = [s for s in signals if s['status'] == status.upper()]
        if symbol:
            signals = [s for s in signals if s['symbol'].upper() == symbol.upper()]
        
        # Limit results
        signals = signals[:limit]
        
        return [
            SignalRecordType(
                id=s['id'],
                symbol=s['symbol'],
                action=s['action'],
                confidence=s['confidence'],
                entry_price=s['entry_price'],
                entry_timestamp=s['entry_timestamp'],
                exit_price=s['exit_price'],
                exit_timestamp=s['exit_timestamp'],
                pnl=s['pnl'],
                pnl_percent=s['pnl_percent'],
                reasoning=s['reasoning'],
                status=s['status'],
                user_id=s.get('user_id'),
                trading_mode=s.get('trading_mode', 'PAPER'),
                signal_id=s.get('signal_id', '')
            )
            for s in signals
        ]
    
    def resolve_transparency_performance(self, info, days: int = 30) -> PerformanceSummaryType:
        """Resolve performance summary"""
        dashboard_service = get_transparency_dashboard()
        summary = dashboard_service.get_performance_summary(days=days)
        
        return PerformanceSummaryType(
            period_days=summary['period_days'],
            total_signals=summary['total_signals'],
            win_rate=summary['win_rate'],
            total_pnl=summary['total_pnl'],
            avg_pnl=summary['avg_pnl'],
            sharpe_ratio=summary['sharpe_ratio'],
            max_drawdown=summary['max_drawdown']
        )
    
    def resolve_transparency_csv_export(self, info, limit: int = 100, days: int = None, status: str = None) -> str:
        """Resolve CSV export - returns download URL"""
        import os
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta
        from core.models import SignalRecord
        import csv
        
        # Build query
        queryset = SignalRecord.objects.all()
        
        if days:
            cutoff_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(entry_timestamp__gte=cutoff_date)
        
        if status and status.upper() != 'ALL':
            queryset = queryset.filter(status=status.upper())
        
        queryset = queryset.order_by('-entry_timestamp')[:limit]
        signals = list(queryset)
        
        if not signals:
            return ""
        
        # Generate CSV in media directory
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        os.makedirs(media_root, exist_ok=True)
        
        filename = f"signals_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(media_root, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'signal_id', 'symbol', 'action', 'confidence',
                'entry_price', 'entry_timestamp', 'exit_price', 'exit_timestamp',
                'pnl', 'pnl_percent', 'status', 'reasoning', 'user_id', 'trading_mode'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for signal in signals:
                writer.writerow({
                    'signal_id': signal.signal_id or signal.id,
                    'symbol': signal.symbol,
                    'action': signal.action,
                    'confidence': signal.confidence,
                    'entry_price': signal.entry_price or '',
                    'entry_timestamp': signal.entry_timestamp.isoformat() if signal.entry_timestamp else '',
                    'exit_price': signal.exit_price or '',
                    'exit_timestamp': signal.exit_timestamp.isoformat() if signal.exit_timestamp else '',
                    'pnl': signal.pnl or '',
                    'pnl_percent': signal.pnl_percent or '',
                    'status': signal.status,
                    'reasoning': signal.reasoning or '',
                    'user_id': signal.user_id or '',
                    'trading_mode': signal.trading_mode or 'PAPER',
                })
        
        # Return URL path
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        return f"{media_url}{filename}"

