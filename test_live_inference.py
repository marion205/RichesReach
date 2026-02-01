#!/usr/bin/env python3
"""
Test Live Inference with Ensemble
Quick test script to verify ensemble predictor integration.
"""
import os
import sys
import django
import asyncio

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.live_hybrid_inference import get_live_inference


async def test_live_inference():
    """Test live inference with ensemble"""
    print("🧪 Testing Live Inference with Ensemble")
    print("=" * 60)
    
    # Get inference instance (ensemble enabled by default)
    inference = get_live_inference(use_ensemble=True)
    
    print(f"\n✅ Inference initialized")
    print(f"   Ensemble enabled: {inference.use_ensemble}")
    print(f"   Confidence threshold: {inference.confidence_threshold}")
    
    # Test symbols
    symbols = ['SPY', 'AAPL', 'MSFT']
    
    print(f"\n📊 Generating signals for {len(symbols)} symbols...")
    print(f"   Symbols: {', '.join(symbols)}")
    
    results = []
    for symbol in symbols:
        print(f"\n🔍 Testing {symbol}...")
        try:
            signal = await inference.generate_live_signal(symbol, use_alpaca=True)
            
            results.append(signal)
            
            print(f"   ✅ Action: {signal.get('action', 'N/A')}")
            print(f"   📈 Confidence: {signal.get('confidence', 0):.2%}")
            print(f"   🤖 Model Type: {signal.get('model_type', 'unknown')}")
            
            # Show reasoning
            reasoning = signal.get('reasoning', '')
            if reasoning:
                print(f"   💭 Reasoning: {reasoning[:100]}...")
            
            # Show alternative data if available
            alt_data = signal.get('enhanced_alt_data', {})
            if alt_data:
                print(f"   📊 Alternative Data:")
                if alt_data.get('social_sentiment') is not None:
                    print(f"      Social Sentiment: {alt_data['social_sentiment']:+.2f}")
                if alt_data.get('unusual_volume_pct') is not None and alt_data['unusual_volume_pct'] > 0:
                    print(f"      Unusual Options Volume: {alt_data['unusual_volume_pct']:.1%}")
                if alt_data.get('call_bias') is not None:
                    print(f"      Call Bias: {alt_data['call_bias']:.2f}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({'symbol': symbol, 'error': str(e)})
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    successful = [r for r in results if 'action' in r]
    print(f"\n✅ Successful: {len(successful)}/{len(symbols)}")
    
    if successful:
        import numpy as np
        confidences = [r['confidence'] for r in successful if 'confidence' in r]
        if confidences:
            avg_confidence = np.mean(confidences)
            print(f"📈 Average Confidence: {avg_confidence:.2%}")
        
        ensemble_count = sum(1 for r in successful if r.get('model_type') == 'ensemble')
        xgb_count = sum(1 for r in successful if r.get('model_type') == 'xgboost')
        print(f"🤖 Ensemble Used: {ensemble_count}")
        print(f"🤖 XGBoost Used: {xgb_count}")
        
        # Actions breakdown
        actions = {}
        for r in successful:
            action = r.get('action', 'UNKNOWN')
            actions[action] = actions.get(action, 0) + 1
        
        print(f"\n📋 Actions:")
        for action, count in actions.items():
            print(f"   {action}: {count}")
    
    print("\n✅ Test complete!")


if __name__ == '__main__':
    asyncio.run(test_live_inference())

