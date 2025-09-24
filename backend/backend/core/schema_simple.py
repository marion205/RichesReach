# GraphQL schema with signals support
import graphene
import time
import json

class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    name = graphene.String()

class SignalType(graphene.ObjectType):
    id = graphene.ID()
    symbol = graphene.String()
    timeframe = graphene.String()
    triggered_at = graphene.String()
    signal_type = graphene.String()
    entry_price = graphene.Float()
    stop_price = graphene.Float()
    target_price = graphene.Float()
    ml_score = graphene.Float()
    thesis = graphene.String()
    risk_reward_ratio = graphene.Float()
    days_since_triggered = graphene.Int()
    is_liked_by_user = graphene.Boolean()
    user_like_count = graphene.Int()
    features = graphene.String()
    is_active = graphene.Boolean()
    is_validated = graphene.Boolean()
    validation_price = graphene.Float()
    validation_timestamp = graphene.String()
    created_by = graphene.Field(UserType)

class Query(graphene.ObjectType):
    ping = graphene.String()
    signals = graphene.List(
        SignalType,
        symbol=graphene.String(),
        signal_type=graphene.String(),
        min_ml_score=graphene.Float(),
        is_active=graphene.Boolean(),
        limit=graphene.Int()
    )
    
    def resolve_ping(self, info):
        return "pong"
    
    def resolve_signals(self, info, symbol=None, signal_type=None, min_ml_score=None, is_active=None, limit=None):
        # Return mock data that matches the expected structure
        mock_signals = [
            SignalType(
                id="1",
                symbol="AAPL",
                timeframe="1D",
                triggered_at=str(time.time()),
                signal_type="BUY",
                entry_price=150.0,
                stop_price=145.0,
                target_price=160.0,
                ml_score=0.85,
                thesis="Strong technical breakout with volume confirmation",
                risk_reward_ratio=2.0,
                days_since_triggered=1,
                is_liked_by_user=False,
                user_like_count=15,
                features="RSI_OVERSOLD,EMA_CROSSOVER,VOLUME_SURGE",
                is_active=True,
                is_validated=False,
                validation_price=None,
                validation_timestamp=None,
                created_by=UserType(id="1", username="ai_system", name="AI Trading System")
            ),
            SignalType(
                id="2",
                symbol="TSLA",
                timeframe="1D", 
                triggered_at=str(time.time()),
                signal_type="SELL",
                entry_price=250.0,
                stop_price=260.0,
                target_price=230.0,
                ml_score=0.75,
                thesis="Bearish divergence with resistance at key level",
                risk_reward_ratio=2.0,
                days_since_triggered=0,
                is_liked_by_user=True,
                user_like_count=8,
                features="RSI_OVERBOUGHT,MACD_DIVERGENCE,RESISTANCE_BREAK",
                is_active=True,
                is_validated=False,
                validation_price=None,
                validation_timestamp=None,
                created_by=UserType(id="1", username="ai_system", name="AI Trading System")
            )
        ]
        
        # Apply filters
        filtered_signals = mock_signals
        
        if symbol:
            filtered_signals = [s for s in filtered_signals if s.symbol == symbol]
        if signal_type:
            filtered_signals = [s for s in filtered_signals if s.signal_type == signal_type]
        if min_ml_score is not None:
            filtered_signals = [s for s in filtered_signals if s.ml_score >= min_ml_score]
        if is_active is not None:
            filtered_signals = [s for s in filtered_signals if s.is_active == is_active]
        if limit:
            filtered_signals = filtered_signals[:limit]
            
        return filtered_signals

# Authentication types
class TokenPayload(graphene.ObjectType):
    email = graphene.String()
    exp = graphene.Int()
    orig_iat = graphene.Int()

class TokenAuthPayload(graphene.ObjectType):
    token = graphene.String()
    payload = graphene.Field(TokenPayload)

class TokenAuth(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    Output = TokenAuthPayload

    @classmethod
    def mutate(cls, root, info, email, password):
        # Simple authentication for testing
        try:
            if not email or not password:
                return TokenAuthPayload(token=None, payload=None)
            
            # Accept any credentials for testing
            if email and password:
                # Create a simple JWT-like token
                token = f"test-jwt-token-{int(time.time())}"
                payload = TokenPayload(
                    email=email,
                    exp=int(time.time()) + 3600,  # 1 hour from now
                    orig_iat=int(time.time())
                )
                return TokenAuthPayload(token=token, payload=payload)
            else:
                return TokenAuthPayload(token=None, payload=None)
            
        except Exception as e:
            return TokenAuthPayload(token=None, payload=None)

class Mutation(graphene.ObjectType):
    token_auth = TokenAuth.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
