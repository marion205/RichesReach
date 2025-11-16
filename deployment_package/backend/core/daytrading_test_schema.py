# daytrading_test_schema.py
# Minimal test schema to isolate dayTradingPicks resolver
# NO IMPORTS from broken files - completely isolated
import graphene
import sys
import os

# Standalone resolver function - no imports from queries.py
def _get_day_trading_picks_from_polygon(limit=20):
    """Standalone function to get picks - uses Polygon API or mock"""
    try:
        from polygon import RESTClient
        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            return _get_mock_picks(limit)
        
        client = RESTClient(api_key)
        snapshots = client.get_snapshot_direction(
            market_type='stocks',
            direction='gainers',
            include_otc=False
        )
        
        picks = []
        for snap in snapshots[:limit]:
            try:
                price = snap.last_trade.price if snap.last_trade else 0
                change_pct = snap.todays_change_percent if hasattr(snap, 'todays_change_percent') else 0
                score = abs(change_pct) * 10
                
                picks.append({
                    'symbol': snap.ticker,
                    'score': round(score, 2),
                    'side': 'LONG',
                    'features': {'momentum15m': change_pct / 100},
                    'risk': {'atr5m': price * 0.02, 'stop': round(price * 0.98, 2)},
                    'notes': f'Top gainer: {change_pct:.2f}% today'
                })
            except Exception:
                continue
        
        return picks if picks else _get_mock_picks(limit)
    except Exception:
        return _get_mock_picks(limit)

def _get_mock_picks(limit=20):
    """Mock picks for testing"""
    return [
        {'symbol': 'AAPL', 'score': 0.9, 'side': 'LONG', 'features': {}, 'risk': {}, 'notes': 'Test pick 1'},
        {'symbol': 'TSLA', 'score': 0.8, 'side': 'SHORT', 'features': {}, 'risk': {}, 'notes': 'Test pick 2'},
        {'symbol': 'NVDA', 'score': 0.85, 'side': 'LONG', 'features': {}, 'risk': {}, 'notes': 'Test pick 3'},
    ][:limit]


class DayTradingPickType(graphene.ObjectType):
    symbol = graphene.String()
    score = graphene.Float()
    side = graphene.String()
    features = graphene.JSONString()
    risk = graphene.JSONString()
    notes = graphene.String()


class DayTradingDataType(graphene.ObjectType):
    asOf = graphene.String()
    mode = graphene.String()
    picks = graphene.List(DayTradingPickType)
    universeSize = graphene.Int()
    qualityThreshold = graphene.Float()


class Query(graphene.ObjectType):
    day_trading_picks = graphene.Field(
        DayTradingDataType,
        mode=graphene.String(required=False, default_value="SAFE"),
        description="Day trading picks test field",
    )

    def resolve_day_trading_picks(self, info, mode="SAFE"):
        print("✅ RESOLVER CALLED: day_trading_picks", mode, file=sys.stderr, flush=True)
        
        try:
            picks = _get_day_trading_picks_from_polygon(limit=20)
            
            # Convert dict picks to DayTradingPickType objects
            pick_objects = []
            for pick_dict in picks:
                pick_objects.append(DayTradingPickType(
                    symbol=pick_dict.get('symbol'),
                    score=pick_dict.get('score', 0.0),
                    side=pick_dict.get('side', 'LONG'),
                    features=pick_dict.get('features', {}),
                    risk=pick_dict.get('risk', {}),
                    notes=pick_dict.get('notes', '')
                ))
            
            print(f"✅ RESOLVER: Returning {len(pick_objects)} picks", file=sys.stderr, flush=True)
            
            from django.utils import timezone
            return DayTradingDataType(
                asOf=timezone.now().isoformat(),
                mode=mode,
                picks=pick_objects,
                universeSize=len(pick_objects),
                qualityThreshold=0.0
            )
        except Exception as e:
            print(f"❌ RESOLVER ERROR: {e}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc()
            # Return empty on error
            from django.utils import timezone
            return DayTradingDataType(
                asOf=timezone.now().isoformat(),
                mode=mode,
                picks=[],
                universeSize=0,
                qualityThreshold=2.5 if mode == "SAFE" else 2.0
            )


schema = graphene.Schema(query=Query)
