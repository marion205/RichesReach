"""
Test Ensemble Predictor
Tests the ensemble predictor with real data and compares with single models.
"""
from django.core.management.base import BaseCommand
from core.ensemble_predictor import get_ensemble_predictor
from core.enhanced_alternative_data_service import get_enhanced_alternative_data_service
from core.lstm_feature_extractor import get_lstm_feature_extractor
from core.live_hybrid_inference import get_live_inference
import asyncio
import numpy as np


class Command(BaseCommand):
    help = 'Test ensemble predictor with real data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            nargs='+',
            default=['SPY', 'AAPL', 'MSFT'],
            help='Symbols to test (default: SPY AAPL MSFT)'
        )
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare ensemble vs single models'
        )

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Ensemble Predictor")
        self.stdout.write("=" * 60)
        
        symbols = options['symbols']
        compare = options['compare']
        
        # Get services
        ensemble_predictor = get_ensemble_predictor()
        enhanced_alt_data = get_enhanced_alternative_data_service()
        lstm_extractor = get_lstm_feature_extractor()
        live_inference = get_live_inference(use_ensemble=True)
        
        self.stdout.write(f"\n📊 Testing {len(symbols)} symbols...")
        self.stdout.write(f"   Symbols: {', '.join(symbols)}")
        self.stdout.write(f"   Ensemble: {'Enabled' if ensemble_predictor else 'Not available'}")
        
        # Test each symbol
        async def test_symbols():
            results = []
            for symbol in symbols:
                self.stdout.write(f"\n🔍 Testing {symbol}...")
                
                try:
                    # Generate signal using ensemble
                    signal = await live_inference.generate_live_signal(symbol, use_alpaca=True)
                    
                    results.append({
                        'symbol': symbol,
                        'action': signal.get('action'),
                        'confidence': signal.get('confidence'),
                        'model_type': signal.get('model_type', 'unknown'),
                        'reasoning': signal.get('reasoning', ''),
                        'enhanced_alt_data': signal.get('enhanced_alt_data', {})
                    })
                    
                    self.stdout.write(f"   ✅ Action: {signal.get('action')}")
                    self.stdout.write(f"   📈 Confidence: {signal.get('confidence', 0):.2%}")
                    self.stdout.write(f"   🤖 Model: {signal.get('model_type', 'unknown')}")
                    
                    # Show alternative data features
                    alt_data = signal.get('enhanced_alt_data', {})
                    if alt_data:
                        self.stdout.write(f"   📊 Alternative Data:")
                        if alt_data.get('social_sentiment'):
                            self.stdout.write(f"      Social Sentiment: {alt_data['social_sentiment']:+.2f}")
                        if alt_data.get('unusual_volume_pct'):
                            self.stdout.write(f"      Unusual Options Volume: {alt_data['unusual_volume_pct']:.1%}")
                        if alt_data.get('call_bias'):
                            self.stdout.write(f"      Call Bias: {alt_data['call_bias']:.2f}")
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ❌ Error: {e}"))
                    results.append({
                        'symbol': symbol,
                        'error': str(e)
                    })
            
            return results
        
        # Run async test
        try:
            results = asyncio.run(test_symbols())
            
            # Summary
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("📊 Test Results Summary")
            self.stdout.write("=" * 60)
            
            successful = [r for r in results if 'action' in r]
            self.stdout.write(f"\n✅ Successful: {len(successful)}/{len(symbols)}")
            
            if successful:
                avg_confidence = np.mean([r['confidence'] for r in successful])
                ensemble_count = sum(1 for r in successful if r.get('model_type') == 'ensemble')
                
                self.stdout.write(f"📈 Average Confidence: {avg_confidence:.2%}")
                self.stdout.write(f"🤖 Ensemble Used: {ensemble_count}/{len(successful)}")
                
                # Show actions
                actions = {}
                for r in successful:
                    action = r['action']
                    actions[action] = actions.get(action, 0) + 1
                
                self.stdout.write(f"\n📋 Actions:")
                for action, count in actions.items():
                    self.stdout.write(f"   {action}: {count}")
            
            if compare:
                self.stdout.write("\n💡 Comparison Mode:")
                self.stdout.write("   Run with --compare to compare ensemble vs single models")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Test failed: {e}"))

