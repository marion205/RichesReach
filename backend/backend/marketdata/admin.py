# marketdata/admin.py
from django.contrib import admin
from .models import Equity, DailyBar, Quote, OptionContract, ProviderHealth

@admin.register(Equity)
class EquityAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'exchange', 'sector', 'market_cap', 'updated_at']
    list_filter = ['exchange', 'sector', 'created_at']
    search_fields = ['symbol', 'name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(DailyBar)
class DailyBarAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'date', 'close', 'volume', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['symbol']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'price', 'change_percent', 'volume', 'provider', 'timestamp']
    list_filter = ['provider', 'timestamp']
    search_fields = ['symbol']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

@admin.register(OptionContract)
class OptionContractAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'underlying', 'contract_type', 'strike', 'expiration', 'bid', 'ask', 'provider']
    list_filter = ['contract_type', 'expiration', 'provider', 'updated_at']
    search_fields = ['symbol', 'underlying']
    readonly_fields = ['updated_at']
    date_hierarchy = 'expiration'

@admin.register(ProviderHealth)
class ProviderHealthAdmin(admin.ModelAdmin):
    list_display = ['provider', 'is_healthy', 'failure_count', 'last_success', 'last_failure', 'updated_at']
    list_filter = ['is_healthy', 'provider', 'updated_at']
    readonly_fields = ['updated_at']