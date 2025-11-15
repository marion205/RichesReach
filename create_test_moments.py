#!/usr/bin/env python3
"""
Quick script to create test StockMoment data for testing the Key Moments feature.
This can be run directly or imported into Django shell.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.models import StockMoment, MomentCategory

def create_test_moments():
    """Create test stock moments for popular stocks"""
    
    # Test symbols
    symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'NVDA']
    
    # Sample moments data
    moments_data = [
        {
            'category': MomentCategory.NEWS,
            'title': 'Product Launch Announcement',
            'quick_summary': 'Company announced new product line',
            'deep_summary': 'The company held a major product launch event, introducing new features that analysts believe will drive revenue growth. Market reaction was positive with increased trading volume.',
            'importance_score': 0.85,
            'impact_1d': 2.5,
            'impact_7d': 5.2,
        },
        {
            'category': MomentCategory.EARNINGS,
            'title': 'Q3 Earnings Beat Expectations',
            'quick_summary': 'Earnings exceeded analyst estimates',
            'deep_summary': 'The company reported quarterly earnings that beat analyst expectations by 8%. Revenue growth was strong across all segments, particularly in the core business unit.',
            'importance_score': 0.90,
            'impact_1d': 4.1,
            'impact_7d': 7.3,
        },
        {
            'category': MomentCategory.INSIDER,
            'title': 'CEO Purchased Shares',
            'quick_summary': 'Insider buying activity detected',
            'deep_summary': 'The CEO purchased $2M worth of company shares in an open market transaction. This is typically seen as a bullish signal by investors.',
            'importance_score': 0.75,
            'impact_1d': 1.8,
            'impact_7d': 3.5,
        },
        {
            'category': MomentCategory.MACRO,
            'title': 'Fed Interest Rate Decision',
            'quick_summary': 'Federal Reserve policy update',
            'deep_summary': 'The Federal Reserve announced its interest rate decision, which impacts the broader market. Technology stocks showed mixed reactions to the news.',
            'importance_score': 0.70,
            'impact_1d': -1.2,
            'impact_7d': 2.1,
        },
        {
            'category': MomentCategory.SENTIMENT,
            'title': 'Analyst Upgrade',
            'quick_summary': 'Major bank upgraded stock rating',
            'deep_summary': 'A major investment bank upgraded the stock from "Hold" to "Buy" with a price target increase. The upgrade cited strong fundamentals and growth prospects.',
            'importance_score': 0.80,
            'impact_1d': 2.3,
            'impact_7d': 4.6,
        },
    ]
    
    created_count = 0
    
    for symbol in symbols:
        # Create moments at different timestamps (last 30 days)
        base_time = timezone.now()
        
        for i, moment_data in enumerate(moments_data):
            # Spread moments over the last 30 days
            days_ago = (len(moments_data) - i) * 6  # Every 6 days
            timestamp = base_time - timedelta(days=days_ago)
            
            # Check if moment already exists
            existing = StockMoment.objects.filter(
                symbol=symbol,
                timestamp__date=timestamp.date(),
                title=moment_data['title']
            ).first()
            
            if existing:
                print(f"⚠️  Moment already exists for {symbol} on {timestamp.date()}")
                continue
            
            moment = StockMoment.objects.create(
                symbol=symbol,
                timestamp=timestamp,
                category=moment_data['category'],
                title=moment_data['title'],
                quick_summary=moment_data['quick_summary'],
                deep_summary=moment_data['deep_summary'],
                importance_score=moment_data['importance_score'],
                impact_1d=moment_data.get('impact_1d'),
                impact_7d=moment_data.get('impact_7d'),
                source_links=[
                    f'https://example.com/news/{symbol.lower()}-{i+1}',
                    f'https://example.com/analysis/{symbol.lower()}-{i+1}',
                ]
            )
            
            created_count += 1
            print(f"✅ Created moment for {symbol}: {moment_data['title']} ({timestamp.date()})")
    
    print(f"\n🎉 Created {created_count} test moments!")
    print(f"\n📊 Total moments in database: {StockMoment.objects.count()}")
    print(f"\n💡 You can now test the Key Moments feature in the app!")

if __name__ == '__main__':
    try:
        create_test_moments()
    except Exception as e:
        print(f"❌ Error creating test moments: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

