from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from graphene_django.views import GraphQLView
import os
import json

# GraphQL view
graphql_view = csrf_exempt(GraphQLView.as_view(graphiql=True))

def stock_viewer(request):
    """Simple view to serve the stock viewer HTML page"""
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'stock_viewer.html')
    with open(html_file_path, 'r') as f:
        html_content = f.read()
    return HttpResponse(html_content)

def ai_stock_dashboard(request):
    """AI-powered stock dashboard with ML recommendations"""
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'ai_stock_dashboard.html')
    with open(html_file_path, 'r') as f:
        html_content = f.read()
    return HttpResponse(html_content)

def industry_stock_page(request):
    """Industry-standard AI/ML stock analysis platform"""
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'industry_standard_stock_page.html')
    with open(html_file_path, 'r') as f:
        html_content = f.read()
    return HttpResponse(html_content)