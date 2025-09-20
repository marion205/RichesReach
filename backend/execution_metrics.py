# Execution quality metrics and venue routing
from dataclasses import dataclass
from typing import Optional, Dict, List
from collections import defaultdict
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExecutionEvent:
    symbol: str
    side: str            # "BUY"|"SELL"
    target_qty: float
    decision_ts: float   # epoch seconds (signal time)
    decision_px: float   # reference/arrival price
    venue: str
    fill_qty: float
    avg_fill_px: float
    fees: float
    completed_ts: float
    order_id: Optional[str] = None
    client_id: Optional[str] = None

def implementation_shortfall(ev: ExecutionEvent) -> float:
    """
    IS (bps): signed slippage vs. decision price including fees.
    Positive = worse than reference (higher cost for BUY, lower proceeds for SELL).
    """
    if ev.target_qty <= 0 or ev.fill_qty <= 0:
        return 0.0
    
    signed = 1 if ev.side == "BUY" else -1
    slip = signed * ((ev.avg_fill_px - ev.decision_px) / ev.decision_px)
    total = slip + (ev.fees / (ev.decision_px * ev.fill_qty))
    return float(total * 1e4)  # basis points

def venue_attribution(events: List[ExecutionEvent]) -> Dict[str, Dict[str, float]]:
    """Average IS and other metrics by venue"""
    agg = defaultdict(lambda: {'total_is': 0.0, 'count': 0, 'total_fees': 0.0, 'total_volume': 0.0})
    
    for e in events:
        is_bps = implementation_shortfall(e)
        agg[e.venue]['total_is'] += is_bps
        agg[e.venue]['count'] += 1
        agg[e.venue]['total_fees'] += e.fees
        agg[e.venue]['total_volume'] += e.avg_fill_px * e.fill_qty
    
    result = {}
    for venue, stats in agg.items():
        if stats['count'] > 0:
            result[venue] = {
                'avg_is_bps': stats['total_is'] / stats['count'],
                'total_trades': stats['count'],
                'total_fees': stats['total_fees'],
                'total_volume': stats['total_volume'],
                'avg_fee_bps': (stats['total_fees'] / stats['total_volume'] * 1e4) if stats['total_volume'] > 0 else 0
            }
    
    return result

def calculate_execution_quality(events: List[ExecutionEvent]) -> Dict[str, float]:
    """Calculate overall execution quality metrics"""
    if not events:
        return {}
    
    is_values = [implementation_shortfall(e) for e in events]
    
    # Calculate statistics
    avg_is = sum(is_values) / len(is_values)
    median_is = sorted(is_values)[len(is_values) // 2]
    p95_is = sorted(is_values)[int(len(is_values) * 0.95)]
    p99_is = sorted(is_values)[int(len(is_values) * 0.99)]
    
    # Calculate fill rates
    total_target = sum(e.target_qty for e in events)
    total_filled = sum(e.fill_qty for e in events)
    fill_rate = total_filled / total_target if total_target > 0 else 0
    
    # Calculate timing metrics
    latencies = [e.completed_ts - e.decision_ts for e in events]
    avg_latency = sum(latencies) / len(latencies)
    
    return {
        'avg_is_bps': avg_is,
        'median_is_bps': median_is,
        'p95_is_bps': p95_is,
        'p99_is_bps': p99_is,
        'fill_rate': fill_rate,
        'avg_latency_ms': avg_latency * 1000,
        'total_trades': len(events),
        'total_volume': sum(e.avg_fill_px * e.fill_qty for e in events)
    }

@dataclass
class VenueQuote:
    venue: str
    bid: float
    ask: float
    latency_ms: int
    fee_bps: float
    available_qty: float = 0.0
    timestamp: float = 0.0

def score_quote(q: VenueQuote, side: str, weights: Dict[str, float] = None) -> float:
    """
    Lower is better. Combines price, fee, and latency.
    Tunable weights w_price, w_fee, w_lat.
    """
    if weights is None:
        weights = {'price': 1.0, 'fee': 0.5, 'latency': 0.001, 'qty': 0.1}
    
    # Effective price considering fees
    mid_fee = q.fee_bps * 1e-4
    if side == "BUY":
        px_component = q.ask  # Lower ask better
        fee_component = mid_fee * q.ask
    else:
        px_component = -q.bid  # Higher bid better
        fee_component = mid_fee * q.bid
    
    # Latency component (lower is better)
    lat_component = q.latency_ms
    
    # Quantity component (higher available qty is better)
    qty_component = -q.available_qty  # Negative because lower score is better
    
    return (weights['price'] * px_component + 
            weights['fee'] * fee_component + 
            weights['latency'] * lat_component + 
            weights['qty'] * qty_component)

def best_venue(quotes: List[VenueQuote], side: str, weights: Dict[str, float] = None) -> VenueQuote:
    """Select best venue based on scoring function"""
    if not quotes:
        raise ValueError("No quotes provided")
    
    return min(quotes, key=lambda q: score_quote(q, side, weights))

def create_execution_event(
    symbol: str,
    side: str,
    target_qty: float,
    decision_px: float,
    venue: str,
    fill_qty: float,
    avg_fill_px: float,
    fees: float,
    order_id: Optional[str] = None,
    client_id: Optional[str] = None
) -> ExecutionEvent:
    """Create an execution event with current timestamp"""
    now = time.time()
    return ExecutionEvent(
        symbol=symbol,
        side=side,
        target_qty=target_qty,
        decision_ts=now,
        decision_px=decision_px,
        venue=venue,
        fill_qty=fill_qty,
        avg_fill_px=avg_fill_px,
        fees=fees,
        completed_ts=now,
        order_id=order_id,
        client_id=client_id
    )

class ExecutionTracker:
    """Track execution quality over time"""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events: List[ExecutionEvent] = []
        self.venue_stats = defaultdict(list)
    
    def add_event(self, event: ExecutionEvent):
        """Add execution event to tracker"""
        self.events.append(event)
        self.venue_stats[event.venue].append(event)
        
        # Keep only recent events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
            # Clean up venue stats too
            for venue in self.venue_stats:
                if len(self.venue_stats[venue]) > self.max_events:
                    self.venue_stats[venue] = self.venue_stats[venue][-self.max_events:]
    
    def get_venue_ranking(self) -> List[Dict[str, any]]:
        """Get venues ranked by execution quality"""
        venue_metrics = venue_attribution(self.events)
        
        # Convert to list and sort by avg_is_bps (lower is better)
        ranking = []
        for venue, metrics in venue_metrics.items():
            ranking.append({
                'venue': venue,
                'avg_is_bps': metrics['avg_is_bps'],
                'total_trades': metrics['total_trades'],
                'total_volume': metrics['total_volume'],
                'avg_fee_bps': metrics['avg_fee_bps']
            })
        
        return sorted(ranking, key=lambda x: x['avg_is_bps'])
    
    def get_overall_quality(self) -> Dict[str, float]:
        """Get overall execution quality metrics"""
        return calculate_execution_quality(self.events)
    
    def get_recent_quality(self, hours: int = 24) -> Dict[str, float]:
        """Get execution quality for recent events"""
        cutoff_time = time.time() - (hours * 3600)
        recent_events = [e for e in self.events if e.completed_ts >= cutoff_time]
        return calculate_execution_quality(recent_events)
    
    def reset(self):
        """Reset tracker state"""
        self.events.clear()
        self.venue_stats.clear()

# Example usage
def example_execution_analysis():
    """Example of how to use execution metrics"""
    # Create some sample events
    events = [
        ExecutionEvent("BTC", "BUY", 1.0, 50000.0, "binance", 1.0, 50010.0, 5.0, time.time()),
        ExecutionEvent("BTC", "BUY", 1.0, 50000.0, "coinbase", 1.0, 50005.0, 3.0, time.time()),
        ExecutionEvent("ETH", "SELL", 10.0, 3000.0, "binance", 10.0, 2995.0, 2.0, time.time()),
    ]
    
    # Calculate venue attribution
    venue_stats = venue_attribution(events)
    print("Venue Attribution:", venue_stats)
    
    # Calculate overall quality
    quality = calculate_execution_quality(events)
    print("Execution Quality:", quality)
    
    # Example venue selection
    quotes = [
        VenueQuote("binance", 50000.0, 50010.0, 50, 10.0, 1000.0),
        VenueQuote("coinbase", 50005.0, 50015.0, 100, 5.0, 500.0),
    ]
    
    best = best_venue(quotes, "BUY")
    print("Best venue for BUY:", best.venue)

if __name__ == "__main__":
    example_execution_analysis()
