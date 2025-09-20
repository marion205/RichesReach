from django.contrib import admin
from django.urls import path
from core.views import graphql_view, stock_viewer, ai_stock_dashboard, industry_stock_page
from django.http import JsonResponse

def test_view(request):
    return JsonResponse({'status': 'ok', 'message': 'Server is working'})

urlpatterns = [
path('admin/', admin.site.urls),
path('graphql/', graphql_view),
path('test/', test_view, name='test'),
path('stocks/', stock_viewer, name='stock_viewer'),
path('ai-dashboard/', ai_stock_dashboard, name='ai_stock_dashboard'),
path('', industry_stock_page, name='industry_stock_page'),
]