#!/usr/bin/env python3
"""
Production Monitoring Demo for Live Market Intelligence
Showcase continuous performance tracking, alerting, and optimization
"""

import asyncio
import time
import random
import logging
from datetime import datetime, timedelta
from core.production_monitoring import monitoring_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionMonitoringDemo:
    """Demo class for production monitoring features"""
    
    def __init__(self):
        self.demo_duration = 300  # 5 minutes
        self.metrics_interval = 10  # seconds
        self.is_running = False
        
        # Demo data
        self.endpoints = [
            "/api/recommendations",
            "/api/portfolio/optimize",
            "/api/stocks/analyze",
            "/api/market/regime",
            "/api/user/profile"
        ]
        
        self.models = [
            "market_regime_predictor",
            "portfolio_optimizer",
            "stock_scorer",
            "risk_analyzer",
            "sentiment_analyzer"
        ]
        
        self.data_sources = [
            "alpha_vantage",
            "finnhub",
            "yahoo_finance",
            "news_api",
            "twitter_api"
        ]
    
    async def simulate_api_traffic(self):
        """Simulate realistic API traffic patterns"""
        logger.info("Simulating API traffic...")
        
        while self.is_running:
            try:
                # Simulate multiple concurrent requests
                for _ in range(random.randint(1, 5)):
                    endpoint = random.choice(self.endpoints)
                    
                    # Simulate realistic response times
                    if "optimize" in endpoint:
                        response_time = random.uniform(800, 2000)  # Slower for complex operations
                    elif "analyze" in endpoint:
                        response_time = random.uniform(300, 800)   # Medium for analysis
                    else:
                        response_time = random.uniform(100, 400)  # Fast for simple operations
                    
                    # Simulate occasional errors
                    status_code = 200 if random.random() > 0.05 else random.choice([400, 500, 503])
                    
                    # Record API performance
                    monitoring_service.record_api_performance(
                        endpoint=endpoint,
                        response_time=response_time,
                        status_code=status_code,
                        user_id=f"user_{random.randint(1000, 9999)}"
                    )
                    
                    logger.info(f"API: {endpoint} - {response_time:.1f}ms - {status_code}")
                
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"ERROR: API simulation error: {e}")
    
    async def simulate_ml_model_performance(self):
        """Simulate ML model performance metrics"""
        logger.info("🤖 Simulating ML model performance...")
        
        while self.is_running:
            try:
                for model in self.models:
                    # Simulate realistic accuracy patterns
                    base_accuracy = 0.85
                    if "regime" in model:
                        base_accuracy = 0.78  # Market regime is harder to predict
                    elif "optimizer" in model:
                        base_accuracy = 0.92  # Portfolio optimization is more reliable
                    
                    # Add some variation
                    accuracy = base_accuracy + random.uniform(-0.05, 0.05)
                    accuracy = max(0.6, min(0.98, accuracy))  # Keep in reasonable range
                    
                    # Simulate prediction time based on model complexity
                    if "analyzer" in model:
                        prediction_time = random.uniform(50, 150)
                    elif "optimizer" in model:
                        prediction_time = random.uniform(200, 500)
                    else:
                        prediction_time = random.uniform(20, 80)
                    
                    # Simulate data quality
                    data_quality = random.uniform(0.7, 0.95)
                    
                    # Record model performance
                    monitoring_service.record_model_performance(
                        model_name=model,
                        accuracy=accuracy,
                        prediction_time=prediction_time,
                        data_quality=data_quality
                    )
                    
                    logger.info(f"🤖 Model: {model} - Accuracy: {accuracy:.3f} - Time: {prediction_time:.1f}ms")
                
                await asyncio.sleep(random.uniform(5, 10))
                
            except Exception as e:
                logger.error(f"ERROR: ML simulation error: {e}")
    
    async def simulate_market_data_quality(self):
        """Simulate market data quality metrics"""
        logger.info("📈 Simulating market data quality...")
        
        while self.is_running:
            try:
                for source in self.data_sources:
                    # Simulate data freshness (seconds since last update)
                    if "news" in source or "twitter" in source:
                        freshness = random.uniform(10, 60)  # Social data is more frequent
                    else:
                        freshness = random.uniform(30, 300)  # Market data varies
                    
                    # Simulate data completeness
                    completeness = random.uniform(0.8, 0.98)
                    
                    # Simulate data accuracy
                    if "alpha_vantage" in source:
                        accuracy = random.uniform(0.9, 0.98)  # High quality
                    elif "finnhub" in source:
                        accuracy = random.uniform(0.85, 0.95)  # Good quality
                    else:
                        accuracy = random.uniform(0.75, 0.9)   # Variable quality
                    
                    # Record data quality metrics
                    monitoring_service.record_market_data_quality(
                        data_source=source,
                        freshness=freshness,
                        completeness=completeness,
                        accuracy=accuracy
                    )
                    
                    logger.info(f"📈 Data: {source} - Fresh: {freshness:.1f}s - Complete: {completeness:.3f} - Accurate: {accuracy:.3f}")
                
                await asyncio.sleep(random.uniform(8, 15))
                
            except Exception as e:
                logger.error(f"ERROR: Data quality simulation error: {e}")
    
    async def simulate_system_health(self):
        """Simulate system health metrics"""
        logger.info("💻 Simulating system health...")
        
        while self.is_running:
            try:
                # Simulate realistic system metrics
                cpu_usage = random.uniform(30, 85)
                memory_usage = random.uniform(45, 90)
                disk_usage = random.uniform(20, 75)
                active_connections = random.randint(50, 200)
                
                # Record system health
                monitoring_service.record_system_health(
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    disk_usage=disk_usage,
                    active_connections=active_connections
                )
                
                logger.info(f"💻 System - CPU: {cpu_usage:.1f}% - Memory: {memory_usage:.1f}% - Disk: {disk_usage:.1f}% - Connections: {active_connections}")
                
                await asyncio.sleep(random.uniform(15, 25))
                
            except Exception as e:
                logger.error(f"ERROR: System health simulation error: {e}")
    
    async def simulate_anomalies(self):
        """Simulate occasional anomalies to test alerting"""
        logger.info("Simulating anomalies...")
        
        while self.is_running:
            try:
                # Wait for a while before introducing anomalies
                await asyncio.sleep(60)
                
                if not self.is_running:
                    break
                
                # Simulate high latency anomaly
                logger.warning("Simulating high latency anomaly...")
                for _ in range(5):
                    monitoring_service.record_api_performance(
                        endpoint="/api/portfolio/optimize",
                        response_time=random.uniform(1500, 3000),
                        status_code=200
                    )
                    await asyncio.sleep(2)
                
                # Simulate low accuracy anomaly
                logger.warning("Simulating low accuracy anomaly...")
                for _ in range(3):
                    monitoring_service.record_model_performance(
                        model_name="market_regime_predictor",
                        accuracy=random.uniform(0.6, 0.75),
                        prediction_time=random.uniform(100, 200),
                        data_quality=random.uniform(0.8, 0.9)
                    )
                    await asyncio.sleep(3)
                
                # Simulate data quality degradation
                logger.warning("Simulating data quality degradation...")
                for _ in range(4):
                    monitoring_service.record_market_data_quality(
                        data_source="alpha_vantage",
                        freshness=random.uniform(400, 600),
                        completeness=random.uniform(0.6, 0.8),
                        accuracy=random.uniform(0.7, 0.85)
                    )
                    await asyncio.sleep(2)
                
                logger.info("SUCCESS: Anomalies simulated, returning to normal operation...")
                
            except Exception as e:
                logger.error(f"ERROR: Anomaly simulation error: {e}")
    
    async def display_metrics_dashboard(self):
        """Display real-time metrics dashboard"""
        logger.info("Starting metrics dashboard...")
        
        while self.is_running:
            try:
                # Clear screen (works on Unix-like systems)
                print("\033[2J\033[H")
                
                # Display header
                print("RICHESREACH AI - PRODUCTION MONITORING DASHBOARD")
                print("=" * 80)
                print(f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏱️  Demo Duration: {self.demo_duration}s | Interval: {self.metrics_interval}s")
                print("=" * 80)
                
                # Get performance summaries
                api_summary = monitoring_service.get_performance_summary("APIResponseTime", hours=1)
                model_summary = monitoring_service.get_performance_summary("ModelAccuracy", hours=1)
                data_summary = monitoring_service.get_performance_summary("OverallDataQuality", hours=1)
                system_summary = monitoring_service.get_performance_summary("CPUUsage", hours=1)
                
                # Display API Performance
                print("\nAPI PERFORMANCE (Last Hour)")
                print("-" * 40)
                if "error" not in api_summary:
                    stats = api_summary["statistics"]
                    print(f"   Response Time: {stats['average']:.1f}ms (min: {stats['min']:.1f}, max: {stats['max']:.1f})")
                    print(f"   Total Requests: {api_summary['total_metrics']}")
                else:
                    print("   No API metrics available")
                
                # Display ML Model Performance
                print("\n🤖 ML MODEL PERFORMANCE (Last Hour)")
                print("-" * 40)
                if "error" not in model_summary:
                    stats = model_summary["statistics"]
                    print(f"   Accuracy: {stats['average']:.3f} (min: {stats['min']:.3f}, max: {stats['max']:.3f})")
                    print(f"   Total Predictions: {model_summary['total_metrics']}")
                else:
                    print("   No model metrics available")
                
                # Display Data Quality
                print("\n📈 DATA QUALITY (Last Hour)")
                print("-" * 40)
                if "error" not in data_summary:
                    stats = data_summary["statistics"]
                    print(f"   Quality Score: {stats['average']:.3f} (min: {stats['min']:.3f}, max: {stats['max']:.3f})")
                    print(f"   Total Measurements: {data_summary['total_metrics']}")
                else:
                    print("   No data quality metrics available")
                
                # Display System Health
                print("\n💻 SYSTEM HEALTH (Last Hour)")
                print("-" * 40)
                if "error" not in system_summary:
                    stats = system_summary["statistics"]
                    print(f"   CPU Usage: {stats['average']:.1f}% (min: {stats['min']:.1f}, max: {stats['max']:.1f})")
                    print(f"   Total Measurements: {system_summary['total_metrics']}")
                else:
                    print("   No system metrics available")
                
                # Display Active Alerts
                active_alerts = monitoring_service.get_active_alerts()
                print(f"\nACTIVE ALERTS: {len(active_alerts)}")
                print("-" * 40)
                if active_alerts:
                    for alert in active_alerts[-3:]:  # Show last 3 alerts
                        print(f"   {alert.severity.upper()}: {alert.message}")
                        print(f"   Time: {alert.timestamp.strftime('%H:%M:%S')}")
                        print()
                else:
                    print("   No active alerts")
                
                # Display footer
                print("=" * 80)
                print("Press Ctrl+C to stop the demo")
                print("Check CloudWatch for detailed metrics (if AWS configured)")
                
                await asyncio.sleep(self.metrics_interval)
                
            except Exception as e:
                logger.error(f"ERROR: Dashboard error: {e}")
                await asyncio.sleep(self.metrics_interval)
    
    async def run_demo(self):
        """Run the complete production monitoring demo"""
        logger.info("Starting Production Monitoring Demo...")
        logger.info("=" * 60)
        
        try:
            # Start monitoring service
            monitoring_service.start_monitoring()
            
            # Start all simulation tasks
            self.is_running = True
            
            tasks = [
                self.simulate_api_traffic(),
                self.simulate_ml_model_performance(),
                self.simulate_market_data_quality(),
                self.simulate_system_health(),
                self.simulate_anomalies(),
                self.display_metrics_dashboard()
            ]
            
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Demo stopped by user")
        except Exception as e:
            logger.error(f"ERROR: Demo error: {e}")
        finally:
            # Cleanup
            self.is_running = False
            monitoring_service.stop_monitoring()
            logger.info("SUCCESS: Demo completed, monitoring service stopped")
    
    def run_sync(self):
        """Run the demo synchronously"""
        asyncio.run(self.run_demo())

def main():
    """Main demo function"""
    print("PRODUCTION MONITORING DEMO FOR LIVE MARKET INTELLIGENCE")
    print("=" * 80)
    print("This demo showcases:")
    print("   Real-time performance monitoring")
    print("   Intelligent alerting system")
    print("   ML model performance tracking")
    print("   Data quality monitoring")
    print("   System health tracking")
    print("   CloudWatch integration")
    print("=" * 80)
    
    # Create and run demo
    demo = ProductionMonitoringDemo()
    
    try:
        demo.run_sync()
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"\nERROR: Demo failed: {e}")

if __name__ == "__main__":
    main()
