# marketdata/apps.py
from django.apps import AppConfig

class MarketdataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marketdata'
    verbose_name = 'Market Data'
    
    def ready(self):
        """Initialize the app when Django starts"""
        try:
            import marketdata.signals  # Import signals if they exist
        except ImportError:
            pass  # Signals module is optional