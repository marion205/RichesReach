"""
Banking URL patterns - Yodlee integration endpoints
"""
from django.urls import path
from .banking_views import (
    StartFastlinkView,
    YodleeCallbackView,
    AccountsView,
    TransactionsView,
    RefreshAccountView,
    DeleteBankLinkView,
    WebhookView,
)

app_name = 'banking'

urlpatterns = [
    path('api/yodlee/fastlink/start', StartFastlinkView.as_view(), name='fastlink_start'),
    path('api/yodlee/fastlink/callback', YodleeCallbackView.as_view(), name='fastlink_callback'),
    path('api/yodlee/accounts', AccountsView.as_view(), name='accounts'),
    path('api/yodlee/transactions', TransactionsView.as_view(), name='transactions'),
    path('api/yodlee/refresh', RefreshAccountView.as_view(), name='refresh'),
    path('api/yodlee/bank-link/<int:bank_link_id>', DeleteBankLinkView.as_view(), name='delete_bank_link'),
    path('api/yodlee/webhook', WebhookView.as_view(), name='webhook'),
]

