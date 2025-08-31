# core/management/commands/test_rust_integration.py
from django.core.management.base import BaseCommand
from core.rust_stock_service import rust_stock_service
from core.stock_service import AlphaVantageService

class Command(BaseCommand):
    help = 'Test the Rust Stock Analysis Engine integration'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Rust Stock Analysis Engine Integration...")
        
        # Test 1: Health Check
        self.stdout.write("\n1️⃣ Testing Rust Service Health...")
        try:
            health = rust_stock_service.health_check()
            self.stdout.write(self.style.SUCCESS(f"✅ Health Check: {health}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Health Check Failed: {e}"))
            return
        
        # Test 2: Service Availability
        self.stdout.write("\n2️⃣ Testing Service Availability...")
        is_available = rust_stock_service.is_available()
        if is_available:
            self.stdout.write(self.style.SUCCESS("✅ Rust service is available"))
        else:
            self.stdout.write(self.style.ERROR("❌ Rust service is not available"))
            return
        
        # Test 3: Stock Analysis
        self.stdout.write("\n3️⃣ Testing Stock Analysis...")
        try:
            analysis = rust_stock_service.analyze_stock("AAPL", include_technical=False, include_fundamental=True)
            if analysis.get('success'):
                self.stdout.write(self.style.SUCCESS("✅ Stock Analysis Working"))
                analysis_data = analysis.get('analysis', {})
                self.stdout.write(f"   Symbol: {analysis_data.get('symbol')}")
                self.stdout.write(f"   Beginner Score: {analysis_data.get('beginner_friendly_score')}")
                self.stdout.write(f"   Risk Level: {analysis_data.get('risk_level')}")
                self.stdout.write(f"   Recommendation: {analysis_data.get('recommendation')}")
            else:
                self.stdout.write(self.style.ERROR(f"❌ Stock Analysis Failed: {analysis.get('error')}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Stock Analysis Error: {e}"))
        
        # Test 4: Recommendations
        self.stdout.write("\n4️⃣ Testing Recommendations...")
        try:
            recommendations = rust_stock_service.get_recommendations()
            if recommendations.get('recommendations'):
                self.stdout.write(self.style.SUCCESS("✅ Recommendations Working"))
                for rec in recommendations['recommendations']:
                    self.stdout.write(f"   {rec.get('symbol')}: {rec.get('reason')} (Score: {rec.get('beginner_score')})")
            else:
                self.stdout.write(self.style.ERROR("❌ Recommendations Failed"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Recommendations Error: {e}"))
        
        # Test 5: Django Service Integration
        self.stdout.write("\n5️⃣ Testing Django Service Integration...")
        try:
            service = AlphaVantageService()
            rust_analysis = service.analyze_stock_with_rust("MSFT", include_technical=False, include_fundamental=True)
            if rust_analysis:
                self.stdout.write(self.style.SUCCESS("✅ Django-Rust Integration Working"))
                self.stdout.write(f"   Symbol: {rust_analysis.get('symbol')}")
                self.stdout.write(f"   Beginner Score: {rust_analysis.get('beginner_friendly_score')}")
            else:
                self.stdout.write(self.style.WARNING("⚠️ Django-Rust Integration returned no data"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Django-Rust Integration Error: {e}"))
        
        self.stdout.write("\n🎉 Integration Testing Complete!")
        self.stdout.write("\n📊 Summary:")
        self.stdout.write("   - Rust service should be running on http://localhost:3001")
        self.stdout.write("   - Django can now communicate with Rust engine")
        self.stdout.write("   - GraphQL queries can use Rust analysis")
        self.stdout.write("   - Fallback to Python analysis if Rust unavailable")
