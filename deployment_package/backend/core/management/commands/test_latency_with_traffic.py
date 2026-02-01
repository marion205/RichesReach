"""
Test Latency with Real Traffic
Generate test signals and measure actual latency performance.
"""
from django.core.management.base import BaseCommand
from core.optimized_live_inference import get_optimized_inference
from core.speed_optimization_service import get_speed_optimization_service
import asyncio
import time
import statistics


class Command(BaseCommand):
    help = 'Test latency with real traffic by generating test signals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            nargs='+',
            default=['AAPL', 'MSFT', 'GOOGL'],
            help='Symbols to test (default: AAPL MSFT GOOGL)'
        )
        parser.add_argument(
            '--iterations',
            type=int,
            default=10,
            help='Number of test iterations (default: 10)'
        )
        parser.add_argument(
            '--parallel',
            action='store_true',
            help='Run tests in parallel (batch mode)'
        )

    def handle(self, *args, **options):
        symbols = options['symbols']
        iterations = options['iterations']
        parallel = options['parallel']
        
        self.stdout.write("🚀 Latency Testing with Real Traffic")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Symbols: {', '.join(symbols)}")
        self.stdout.write(f"Iterations: {iterations}")
        self.stdout.write(f"Mode: {'Parallel (batch)' if parallel else 'Sequential'}")
        self.stdout.write("")
        
        # Get services
        inference = get_optimized_inference()
        speed_service = get_speed_optimization_service()
        
        # Run tests
        if parallel:
            results = asyncio.run(self._test_parallel(inference, speed_service, symbols, iterations))
        else:
            results = asyncio.run(self._test_sequential(inference, speed_service, symbols, iterations))
        
        # Analyze results
        self._analyze_results(results, speed_service)
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Latency testing complete!"))

    async def _test_sequential(self, inference, speed_service, symbols, iterations):
        """Run sequential tests"""
        results = []
        
        for i in range(iterations):
            self.stdout.write(f"\n📊 Iteration {i+1}/{iterations}")
            
            for symbol in symbols:
                start_time = time.time()
                try:
                    signal = await inference.generate_live_signal_optimized(symbol)
                    latency = (time.time() - start_time) * 1000
                    
                    # Record latency
                    speed_service.record_latency(latency, operation="inference")
                    
                    results.append({
                        'symbol': symbol,
                        'latency_ms': latency,
                        'action': signal.get('action', 'UNKNOWN'),
                        'confidence': signal.get('confidence', 0.0),
                        'success': True,
                        'breakdown': signal.get('latency_breakdown', {})
                    })
                    
                    self.stdout.write(
                        f"   {symbol}: {latency:.1f}ms "
                        f"({signal.get('action', 'UNKNOWN')}, "
                        f"confidence: {signal.get('confidence', 0.0):.2%})"
                    )
                except Exception as e:
                    latency = (time.time() - start_time) * 1000
                    results.append({
                        'symbol': symbol,
                        'latency_ms': latency,
                        'action': 'ERROR',
                        'confidence': 0.0,
                        'success': False,
                        'error': str(e)
                    })
                    self.stdout.write(
                        self.style.ERROR(f"   {symbol}: ERROR - {e}")
                    )
            
            # Small delay between iterations
            await asyncio.sleep(0.5)
        
        return results

    async def _test_parallel(self, inference, speed_service, symbols, iterations):
        """Run parallel (batch) tests"""
        results = []
        
        for i in range(iterations):
            self.stdout.write(f"\n📊 Batch Iteration {i+1}/{iterations}")
            
            start_time = time.time()
            try:
                signals = await inference.generate_signals_batch_optimized(symbols)
                batch_latency = (time.time() - start_time) * 1000
                
                for signal in signals:
                    latency = signal.get('latency_ms', batch_latency / len(signals))
                    speed_service.record_latency(latency, operation="inference")
                    
                    results.append({
                        'symbol': signal.get('symbol', 'UNKNOWN'),
                        'latency_ms': latency,
                        'action': signal.get('action', 'UNKNOWN'),
                        'confidence': signal.get('confidence', 0.0),
                        'success': True,
                        'breakdown': signal.get('latency_breakdown', {})
                    })
                
                avg_latency = batch_latency / len(signals)
                self.stdout.write(
                    f"   Batch: {batch_latency:.1f}ms total "
                    f"({avg_latency:.1f}ms avg per symbol, {len(signals)} signals)"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   Batch ERROR: {e}")
                )
            
            await asyncio.sleep(0.5)
        
        return results

    def _analyze_results(self, results, speed_service):
        """Analyze and display results"""
        if not results:
            self.stdout.write(self.style.WARNING("⚠️  No results to analyze"))
            return
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        if not successful:
            self.stdout.write(self.style.ERROR("❌ All tests failed!"))
            return
        
        latencies = [r['latency_ms'] for r in successful]
        
        self.stdout.write("\n📈 Latency Statistics:")
        self.stdout.write(f"   Total Tests: {len(results)}")
        self.stdout.write(f"   Successful: {len(successful)}")
        self.stdout.write(f"   Failed: {len(failed)}")
        self.stdout.write("")
        self.stdout.write(f"   Average: {statistics.mean(latencies):.1f}ms")
        self.stdout.write(f"   Median: {statistics.median(latencies):.1f}ms")
        self.stdout.write(f"   Min: {min(latencies):.1f}ms")
        self.stdout.write(f"   Max: {max(latencies):.1f}ms")
        
        if len(latencies) > 1:
            self.stdout.write(f"   Std Dev: {statistics.stdev(latencies):.1f}ms")
            self.stdout.write(f"   P95: {self._percentile(latencies, 95):.1f}ms")
            self.stdout.write(f"   P99: {self._percentile(latencies, 99):.1f}ms")
        
        # Check against target
        target_ms = 500.0
        below_target = [l for l in latencies if l < target_ms]
        below_target_pct = (len(below_target) / len(latencies)) * 100
        
        self.stdout.write("")
        self.stdout.write(f"   Target: <{target_ms}ms")
        self.stdout.write(f"   Below Target: {len(below_target)}/{len(latencies)} ({below_target_pct:.1f}%)")
        
        if below_target_pct >= 90:
            self.stdout.write(self.style.SUCCESS("   ✅ EXCELLENT: Meeting target!"))
        elif below_target_pct >= 50:
            self.stdout.write(self.style.WARNING("   ⚠️  GOOD: Most requests meet target"))
        else:
            self.stdout.write(self.style.ERROR("   ❌ NEEDS IMPROVEMENT: Less than 50% meet target"))
        
        # Breakdown analysis (if available)
        if successful and 'breakdown' in successful[0] and successful[0]['breakdown']:
            self.stdout.write("\n⏱️  Latency Breakdown (avg):")
            breakdown_keys = successful[0]['breakdown'].keys()
            for key in breakdown_keys:
                values = [
                    r['breakdown'].get(key, 0) 
                    for r in successful 
                    if r.get('breakdown') and key in r['breakdown']
                ]
                if values:
                    avg = statistics.mean(values)
                    self.stdout.write(f"   {key}: {avg:.1f}ms")
        
        # Get aggregated stats from service
        service_stats = speed_service.get_latency_stats()
        if service_stats.get('count', 0) > 0:
            self.stdout.write("\n📊 Service Aggregated Stats:")
            self.stdout.write(f"   Total Recorded: {service_stats['count']}")
            self.stdout.write(f"   Avg: {service_stats['avg_ms']:.1f}ms")
            self.stdout.write(f"   Below Target: {service_stats['below_target']:.1f}%")

    def _percentile(self, data, percentile):
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

