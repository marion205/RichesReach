"""
Django views for Transparency Dashboard web pages
Public-facing pages for transparency and methodology
"""
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils import timezone
from datetime import timedelta
from .transparency_dashboard import get_transparency_dashboard
from .methodology_page import get_methodology_content, get_methodology_summary
from .models import SignalRecord
import json


@require_http_methods(["GET"])
def transparency_dashboard_view(request):
    """
    Public-facing transparency dashboard web page
    URL: /transparency
    """
    dashboard_service = get_transparency_dashboard()
    
    # Get dashboard data
    limit = int(request.GET.get('limit', 50))
    data = dashboard_service.get_dashboard_data(limit=limit)
    
    # Get performance summary
    days = int(request.GET.get('days', 30))
    performance = dashboard_service.get_performance_summary(days=days)
    
    context = {
        'dashboard': data,
        'performance': performance,
        'selected_period': days,
        'page_title': 'Transparency Dashboard - RichesReach',
        'meta_description': 'Public performance metrics for RichesReach AI trading signals. Real-time win rates, P&L, and signal tracking.',
    }
    
    return render(request, 'transparency/dashboard.html', context)


@require_http_methods(["GET"])
def methodology_view(request):
    """
    Methodology documentation page
    URL: /methodology
    """
    methodology = get_methodology_content()
    summary = get_methodology_summary()
    
    context = {
        'methodology': methodology,
        'summary': summary,
        'page_title': 'Methodology - RichesReach',
        'meta_description': 'How RichesReach calculates trading signals, P&L, and performance metrics. Net-of-costs methodology explained.',
    }
    
    return render(request, 'transparency/methodology.html', context)


@require_http_methods(["GET"])
def signal_detail_view(request, signal_id):
    """
    Individual signal detail page
    URL: /transparency/signal/<signal_id>
    """
    try:
        # Try to find by signal_id first, then by id
        try:
            signal = SignalRecord.objects.get(signal_id=signal_id)
        except SignalRecord.DoesNotExist:
            signal = SignalRecord.objects.get(id=int(signal_id))
        
        context = {
            'signal': signal,
            'page_title': f'Signal {signal.signal_id or signal.id} - RichesReach',
            'meta_description': f'Signal details for {signal.symbol} {signal.action} on {signal.entry_timestamp.strftime("%Y-%m-%d")}',
        }
        
        return render(request, 'transparency/signal_detail.html', context)
    except SignalRecord.DoesNotExist:
        return render(request, 'transparency/404.html', {'message': 'Signal not found'}, status=404)


@require_http_methods(["GET"])
def transparency_api_view(request):
    """
    JSON API endpoint for transparency dashboard data
    URL: /api/transparency
    """
    dashboard_service = get_transparency_dashboard()
    
    limit = int(request.GET.get('limit', 50))
    days = int(request.GET.get('days', 30))
    
    dashboard_data = dashboard_service.get_dashboard_data(limit=limit)
    performance = dashboard_service.get_performance_summary(days=days)
    
    return JsonResponse({
        'dashboard': dashboard_data,
        'performance': performance,
        'timestamp': timezone.now().isoformat()
    })


@require_http_methods(["GET"])
def methodology_api_view(request):
    """
    JSON API endpoint for methodology content
    URL: /api/methodology
    """
    methodology = get_methodology_content()
    summary = get_methodology_summary()
    
    return JsonResponse({
        'methodology': methodology,
        'summary': summary,
        'timestamp': timezone.now().isoformat()
    })

