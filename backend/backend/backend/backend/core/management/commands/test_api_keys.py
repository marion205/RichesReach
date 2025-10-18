"""
Django management command to test API keys
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Test API keys configuration'

    def handle(self, *args, **options):
        self.stdout.write("=== API Keys Test ===")
        
        # Test environment variables
        self.stdout.write(f"FINNHUB_API_KEY from os.getenv: {os.getenv('FINNHUB_API_KEY', 'NOT SET')}")
        self.stdout.write(f"POLYGON_API_KEY from os.getenv: {os.getenv('POLYGON_API_KEY', 'NOT SET')}")
        self.stdout.write(f"ALPHA_VANTAGE_API_KEY from os.getenv: {os.getenv('ALPHA_VANTAGE_API_KEY', 'NOT SET')}")
        
        # Test Django settings
        self.stdout.write(f"FINNHUB_API_KEY from settings: {getattr(settings, 'FINNHUB_API_KEY', 'NOT SET')}")
        self.stdout.write(f"POLYGON_API_KEY from settings: {getattr(settings, 'POLYGON_API_KEY', 'NOT SET')}")
        self.stdout.write(f"ALPHA_VANTAGE_API_KEY from settings: {getattr(settings, 'ALPHA_VANTAGE_API_KEY', 'NOT SET')}")
        
        # Test the views_market module
        try:
            from core.views_market import FINNHUB_API_KEY, POLYGON_API_KEY, ALPHA_VANTAGE_API_KEY
            self.stdout.write(f"FINNHUB_API_KEY from views_market: {FINNHUB_API_KEY}")
            self.stdout.write(f"POLYGON_API_KEY from views_market: {POLYGON_API_KEY}")
            self.stdout.write(f"ALPHA_VANTAGE_API_KEY from views_market: {ALPHA_VANTAGE_API_KEY}")
        except Exception as e:
            self.stdout.write(f"Error importing from views_market: {e}")
