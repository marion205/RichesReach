from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from core.schema import schema
from core.views import stock_viewer, ai_stock_dashboard, industry_stock_page
from django.http import JsonResponse

def test_view(request):
    return JsonResponse({'status': 'ok', 'message': 'Server is working'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False))),
    path('test/', test_view, name='test'),
    path('stocks/', stock_viewer, name='stock_viewer'),
    path('ai-dashboard/', ai_stock_dashboard, name='ai_stock_dashboard'),
    path('defi/', include('defi.urls')),
    path('', industry_stock_page, name='industry_stock_page'),
]