"""
URL configuration for richesreach project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include core app URLs (banking endpoints)
    path('', include('core.banking_urls')),
]

