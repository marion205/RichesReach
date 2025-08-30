from django.contrib import admin
from django.urls import path
from core.views import graphql_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', graphql_view),
]