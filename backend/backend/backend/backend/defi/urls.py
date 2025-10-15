from django.urls import path
from .views import validate_transaction, aave_user_data
from .views_health import health
from .views_prices import prices

urlpatterns = [
    path('validate-transaction/', validate_transaction),
    path('aave-user-data/', aave_user_data),
    path('health/', health),
    path('prices/', prices),
]
