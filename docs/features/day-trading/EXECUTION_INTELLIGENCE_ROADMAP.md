# Execution Intelligence Roadmap

## Goal
Build retail execution IQ that's miles ahead of "market buy at open".

## What We're Building

### Phase 1: Smart Order Suggestions (Weeks 1-3)

#### 1.1 Execution Advisor Service
**File**: `deployment_package/backend/core/execution_advisor.py`

```python
class ExecutionAdvisor:
    """
    Generates smart order suggestions for each signal.
    Helps users avoid common retail execution mistakes.
    """
    
    def suggest_order(self, signal: Dict, current_price: float, vwap: float) -> Dict:
        """
        Returns smart order suggestions:
        {
            'order_type': 'LIMIT',  # vs MARKET, STOP_LIMIT
            'price_band': [150.10, 150.20],  # Suggested limit range
            'time_in_force': 'DAY',  # vs IOC, FOK
            'entry_strategy': 'Wait for VWAP pullback',  # Human-readable
            'bracket_legs': {
                'stop': 147.50,
                'target1': 153.00,
                'target2': 156.00
            },
            'rationale': 'Current price is 0.3% above VWAP. Wait for pullback.'
        }
        """
        pass
    
    def should_wait_for_pullback(self, price: float, vwap: float) -> bool:
        """Determine if user should wait for better entry"""
        vwap_dist = (price - vwap) / vwap
        return vwap_dist > 0.002  # > 0.2% above VWAP
```

#### 1.2 Order Type Logic
```python
def _determine_order_type(signal, spread_bps, volatility):
    """Choose best order type based on market conditions"""
    if spread_bps < 10 and volatility < 0.02:
        return 'LIMIT'  # Tight spread, low vol = use limit
    elif spread_bps > 50:
        return 'STOP_LIMIT'  # Wide spread = use stop-limit
    else:
        return 'LIMIT'  # Default to limit
```

#### 1.3 Price Band Calculation
```python
def _calculate_price_band(entry_price, vwap, spread_bps):
    """Calculate suggested limit price range"""
    # Don't pay more than mid + 0.1% for SAFE
    # Don't pay more than mid + 0.2% for AGGRESSIVE
    max_premium = 0.001 if mode == "SAFE" else 0.002
    
    upper_bound = entry_price * (1 + max_premium)
    lower_bound = max(entry_price * 0.999, vwap * 0.998)  # Don't go below VWAP - 0.2%
    
    return [lower_bound, upper_bound]
```

### Phase 2: Broker Integration (Weeks 4-7)

#### 2.1 Alpaca Adapter
**File**: `deployment_package/backend/core/broker_integration/alpaca_adapter.py`

```python
class AlpacaOrderAdapter:
    """
    Generates Alpaca order JSON from signals.
    Pre-fills everything so user just swipes to confirm.
    """
    
    def create_order_from_signal(self, signal: Dict, user: User) -> Dict:
        """
        Generate Alpaca order JSON:
        {
            'symbol': 'AAPL',
            'qty': 10,
            'side': 'buy',
            'type': 'limit',
            'limit_price': 150.15,
            'time_in_force': 'day',
            'bracket': {
                'stop_loss': {'stop_price': 147.50},
                'take_profit': {'limit_price': 153.00}
            }
        }
        """
        pass
    
    def submit_order(self, order: Dict, user_token: str) -> Dict:
        """Submit to Alpaca API"""
        pass
```

#### 2.2 Frontend Integration
**Mobile**: "Swipe to Trade" button
1. Shows suggested order details
2. User swipes to confirm
3. Order pre-filled in broker UI
4. User just clicks "Submit"

**GraphQL Mutation**:
```graphql
mutation CreateOrderFromSignal($signalId: ID!) {
  createOrderFromSignal(signalId: $signalId) {
    orderId
    orderDetails {
      symbol
      qty
      side
      type
      limitPrice
      bracket {
        stopLoss
        takeProfit
      }
    }
    brokerUrl  # Deep link to broker app
  }
}
```

### Phase 3: Execution Quality Tracking (Weeks 8-10)

#### 3.1 Execution Quality Tracker
**File**: `deployment_package/backend/core/execution_quality_tracker.py`

```python
class ExecutionQualityTracker:
    """
    Tracks actual fills vs signal recommendations.
    Provides execution coaching to improve user performance.
    """
    
    def analyze_fill(self, signal: DayTradingSignal, actual_fill: Dict) -> Dict:
        """
        Compare actual fill to signal:
        {
            'slippage': 0.15,  # $0.15 per share
            'slippage_pct': 0.10,  # 0.10%
            'vwap_slippage': 0.05,  # vs VWAP
            'chased_price': True,  # User paid more than suggested
            'quality_score': 7.5,  # 0-10
            'improvement_tip': 'Using limit orders would have saved $0.10/share'
        }
        """
        pass
    
    def generate_coaching_tips(self, user: User) -> List[str]:
        """
        Surface execution improvement tips:
        - "Your average slippage is 0.35%. Using limits would cut it to 0.15%."
        - "You're chasing price 40% of the time. Wait for pullbacks."
        - "Your fills are 0.2% worse than VWAP. Use bracket orders."
        """
        pass
```

#### 3.2 User Execution Dashboard
**GraphQL Query**:
```graphql
query GetExecutionQuality($userId: ID!) {
  executionQuality(userId: $userId) {
    averageSlippage
    averageSlippagePercent
    vwapSlippage
    chasePricePercent
    qualityScore
    improvementTips
    recentFills {
      symbol
      signalPrice
      fillPrice
      slippage
      qualityScore
    }
  }
}
```

## Success Metrics

- ✅ Order suggestions reduce slippage by 50%+
- ✅ Broker integration reduces user errors by 80%+
- ✅ Execution quality tracking shows measurable improvement
- ✅ Users report better fill quality

## Implementation Timeline

- **Weeks 1-3**: Smart order suggestions
- **Weeks 4-7**: Alpaca broker integration
- **Weeks 8-10**: Execution quality tracking
- **Week 11**: Frontend integration
- **Week 12**: User dashboard

## Expected Impact

- **Slippage Reduction**: 50%+ improvement
- **User Errors**: 80%+ reduction in order mistakes
- **Fill Quality**: Better entry prices, fewer bad fills
- **User Education**: Teaches professional execution habits

