"""
Live Day Trading Engine
Real-time pick generation with live market data
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .universe_generator import LiveUniverseGenerator, UniverseSymbol
from .feature_calculator import RealTimeFeatureCalculator, TradingFeatures
from ..broker.adapters.base import Broker
from ..market.providers.base import MarketDataProvider


@dataclass
class DayTradingPick:
    """Live day trading pick with real-time data"""
    symbol: str
    side: str  # "LONG" or "SHORT"
    score: float
    confidence: float
    
    # Real-time features
    features: Dict[str, float]
    
    # Risk management
    risk: Dict[str, float]
    
    # Market context
    market_regime: str
    volatility_regime: str
    
    # Timing
    entry_time: datetime
    time_stop_min: int
    
    # Oracle insights
    oracle_insight: str
    notes: str


@dataclass
class TradingMode:
    """Trading mode configuration"""
    name: str
    max_positions: int
    max_risk_per_trade: float
    min_score_threshold: float
    max_spread_bps: float
    min_volume: int
    volatility_tolerance: str


class LiveDayTradingEngine:
    """Real-time day trading engine with live data"""
    
    def __init__(
        self, 
        universe_generator: LiveUniverseGenerator,
        feature_calculator: RealTimeFeatureCalculator,
        broker: Broker,
        market_data_provider: MarketDataProvider
    ):
        self.universe_generator = universe_generator
        self.feature_calculator = feature_calculator
        self.broker = broker
        self.market_data_provider = market_data_provider
        self.logger = logging.getLogger(__name__)
        
        # Trading modes
        self.modes = {
            "SAFE": TradingMode(
                name="SAFE",
                max_positions=5,
                max_risk_per_trade=0.01,  # 1% per trade
                min_score_threshold=0.7,
                max_spread_bps=5.0,
                min_volume=1_000_000,
                volatility_tolerance="LOW"
            ),
            "AGGRESSIVE": TradingMode(
                name="AGGRESSIVE",
                max_positions=10,
                max_risk_per_trade=0.02,  # 2% per trade
                min_score_threshold=0.6,
                max_spread_bps=10.0,
                min_volume=500_000,
                volatility_tolerance="HIGH"
            )
        }
        
        # Live state
        self.current_picks = {}
        self.last_update = None
        self.market_status = "UNKNOWN"
    
    async def generate_picks(self, mode: str = "SAFE") -> List[DayTradingPick]:
        """Generate live day trading picks"""
        try:
            self.logger.info(f"🎯 Generating {mode} picks with live data...")
            
            # Get trading mode
            trading_mode = self.modes.get(mode, self.modes["SAFE"])
            
            # Generate universe
            universe = await self.universe_generator.generate_universe(mode)
            
            # Calculate features for each symbol
            picks = []
            for symbol_data in universe[:20]:  # Limit to top 20
                symbol = symbol_data.symbol
                
                # Calculate real-time features
                features = await self.feature_calculator.calculate_features(symbol)
                if not features:
                    continue
                
                # Generate pick
                pick = await self._create_pick(symbol, features, trading_mode)
                if pick:
                    picks.append(pick)
            
            # Sort by score and apply limits
            picks.sort(key=lambda x: x.score, reverse=True)
            picks = picks[:trading_mode.max_positions]
            
            # Update state
            self.current_picks[mode] = picks
            self.last_update = datetime.now()
            
            self.logger.info(f"✅ Generated {len(picks)} {mode} picks")
            return picks
            
        except Exception as e:
            self.logger.error(f"❌ Pick generation failed: {e}")
            return []
    
    async def _create_pick(
        self, 
        symbol: str, 
        features: TradingFeatures, 
        mode: TradingMode
    ) -> Optional[DayTradingPick]:
        """Create a trading pick from features"""
        
        # Determine side based on momentum and technicals
        side = self._determine_side(features)
        
        # Calculate composite score
        score = self._calculate_pick_score(features, side)
        
        # Check if meets mode criteria
        if not self._meets_mode_criteria(features, score, mode):
            return None
        
        # Calculate risk parameters
        risk = await self._calculate_risk_parameters(symbol, features, mode)
        
        # Generate Oracle insight
        oracle_insight = await self._generate_oracle_insight(symbol, features, side)
        
        # Create pick
        pick = DayTradingPick(
            symbol=symbol,
            side=side,
            score=score,
            confidence=self._calculate_confidence(features),
            features=self._extract_feature_dict(features),
            risk=risk,
            market_regime=self._determine_market_regime(),
            volatility_regime=features.volatility_regime,
            entry_time=datetime.now(),
            time_stop_min=self._calculate_time_stop(features),
            oracle_insight=oracle_insight,
            notes=self._generate_notes(features, side)
        )
        
        return pick
    
    def _determine_side(self, features: TradingFeatures) -> str:
        """Determine LONG or SHORT side based on features"""
        
        # Momentum-based decision
        momentum_score = (
            features.momentum_15m * 0.5 +
            features.momentum_5m * 0.3 +
            features.momentum_1m * 0.2
        )
        
        # Technical indicators
        technical_score = (
            (features.rsi_14 - 50) / 50 * 0.3 +  # RSI momentum
            features.macd_signal * 0.3 +          # MACD signal
            (features.bollinger_position - 0.5) * 2 * 0.2 +  # Bollinger position
            features.vwap_distance * 0.2         # VWAP distance
        )
        
        # Breakout confirmation
        breakout_score = features.breakout_pct * 0.5
        
        # Composite signal
        total_signal = momentum_score + technical_score + breakout_score
        
        return "LONG" if total_signal > 0 else "SHORT"
    
    def _calculate_pick_score(self, features: TradingFeatures, side: str) -> float:
        """Calculate pick score based on features and side"""
        
        # Base score from features
        base_score = features.composite_score
        
        # Side-specific adjustments
        if side == "LONG":
            # Favor positive momentum and breakouts
            side_score = (
                max(0, features.momentum_15m) * 0.3 +
                max(0, features.breakout_pct) * 0.2 +
                (features.rsi_14 - 30) / 40 * 0.2 +  # RSI > 30
                features.catalyst_score * 0.3
            )
        else:  # SHORT
            # Favor negative momentum and breakdowns
            side_score = (
                max(0, -features.momentum_15m) * 0.3 +
                max(0, -features.breakout_pct) * 0.2 +
                (70 - features.rsi_14) / 40 * 0.2 +  # RSI < 70
                -features.catalyst_score * 0.3
            )
        
        # Volume confirmation
        volume_score = min(features.rvol_10m / 2, 1.0)  # Cap at 2x volume
        
        # Spread penalty
        spread_penalty = max(0, 1 - features.spread_bps / 20)  # Penalty for wide spreads
        
        # Final score
        final_score = (
            base_score * 0.4 +
            side_score * 0.3 +
            volume_score * 0.2 +
            spread_penalty * 0.1
        )
        
        return max(0, min(1, final_score))
    
    def _meets_mode_criteria(
        self, 
        features: TradingFeatures, 
        score: float, 
        mode: TradingMode
    ) -> bool:
        """Check if pick meets mode criteria"""
        
        return (
            score >= mode.min_score_threshold and
            features.spread_bps <= mode.max_spread_bps and
            features.rvol_10m >= 1.2 and  # Minimum volume spike
            features.volatility_regime in ["NORMAL", mode.volatility_tolerance]
        )
    
    async def _calculate_risk_parameters(
        self, 
        symbol: str, 
        features: TradingFeatures, 
        mode: TradingMode
    ) -> Dict[str, float]:
        """Calculate risk management parameters"""
        
        # Get current quote for price
        quotes = await self.market_data_provider.get_quotes([symbol])
        if symbol not in quotes:
            return {}
        
        current_price = quotes[symbol].price
        
        # ATR-based stop loss
        atr_multiplier = 2.0 if mode.name == "SAFE" else 1.5
        stop_distance = features.atr_5m * atr_multiplier
        
        # Position sizing based on risk
        account = await self.broker.get_account()
        risk_amount = account.buying_power * mode.max_risk_per_trade
        
        # Calculate position size
        position_size = int(risk_amount / stop_distance)
        position_size = max(1, min(position_size, 1000))  # Reasonable limits
        
        # Stop loss price
        if features.side == "LONG":
            stop_price = current_price - stop_distance
        else:
            stop_price = current_price + stop_distance
        
        # Take profit targets
        profit_multiplier = 2.0 if mode.name == "SAFE" else 1.5
        if features.side == "LONG":
            target1 = current_price + (stop_distance * profit_multiplier)
            target2 = current_price + (stop_distance * profit_multiplier * 1.5)
        else:
            target1 = current_price - (stop_distance * profit_multiplier)
            target2 = current_price - (stop_distance * profit_multiplier * 1.5)
        
        return {
            "atr_5m": features.atr_5m,
            "size_shares": position_size,
            "stop": stop_price,
            "targets": [target1, target2],
            "time_stop_min": self._calculate_time_stop(features),
            "risk_per_trade": mode.max_risk_per_trade,
            "max_loss": risk_amount
        }
    
    def _calculate_time_stop(self, features: TradingFeatures) -> int:
        """Calculate time-based stop (minutes)"""
        
        # Base time stop on volatility
        if features.volatility_regime == "HIGH":
            return 30  # 30 minutes for high volatility
        elif features.volatility_regime == "LOW":
            return 120  # 2 hours for low volatility
        else:
            return 60  # 1 hour for normal volatility
    
    def _calculate_confidence(self, features: TradingFeatures) -> float:
        """Calculate confidence score for the pick"""
        
        # Factors that increase confidence
        confidence_factors = [
            abs(features.momentum_15m) > 0.02,  # Strong momentum
            features.rvol_10m > 1.5,           # Volume confirmation
            features.spread_bps < 5,           # Tight spreads
            abs(features.breakout_pct) > 0.01, # Clear breakout
            features.catalyst_score > 0.3      # Strong catalyst
        ]
        
        confidence = sum(confidence_factors) / len(confidence_factors)
        return max(0.5, min(0.95, confidence))  # Reasonable bounds
    
    async def _generate_oracle_insight(
        self, 
        symbol: str, 
        features: TradingFeatures, 
        side: str
    ) -> str:
        """Generate Oracle AI insight for the pick"""
        
        # Mock Oracle insight (would integrate with your Oracle system)
        insights = {
            "LONG": [
                f"Oracle: {symbol} showing strong bullish momentum with {features.rvol_10m:.1f}x volume spike",
                f"Oracle: {symbol} breaking above resistance with RSI {features.rsi_14:.1f} - bullish continuation likely",
                f"Oracle: {symbol} catalyst score {features.catalyst_score:.2f} supports long position"
            ],
            "SHORT": [
                f"Oracle: {symbol} showing bearish momentum with {features.rvol_10m:.1f}x volume confirmation",
                f"Oracle: {symbol} breaking below support with RSI {features.rsi_14:.1f} - bearish continuation likely",
                f"Oracle: {symbol} negative catalyst score {features.catalyst_score:.2f} supports short position"
            ]
        }
        
        import random
        return random.choice(insights[side])
    
    def _extract_feature_dict(self, features: TradingFeatures) -> Dict[str, float]:
        """Extract features as dictionary"""
        return {
            "momentum_15m": features.momentum_15m,
            "rvol_10m": features.rvol_10m,
            "vwap_dist": features.vwap_distance,
            "breakout_pct": features.breakout_pct,
            "spread_bps": features.spread_bps,
            "catalyst_score": features.catalyst_score,
            "rsi_14": features.rsi_14,
            "macd_signal": features.macd_signal,
            "bollinger_position": features.bollinger_position,
            "atr_5m": features.atr_5m
        }
    
    def _determine_market_regime(self) -> str:
        """Determine current market regime"""
        # Mock implementation - would use VIX, sector rotation, etc.
        import random
        regimes = ["BULL", "BEAR", "SIDEWAYS", "VOLATILE"]
        return random.choice(regimes)
    
    def _generate_notes(self, features: TradingFeatures, side: str) -> str:
        """Generate trading notes"""
        notes = []
        
        if features.rvol_10m > 2.0:
            notes.append(f"High volume spike: {features.rvol_10m:.1f}x")
        
        if abs(features.breakout_pct) > 0.02:
            notes.append(f"Breakout: {features.breakout_pct:.2%}")
        
        if features.spread_bps < 3:
            notes.append("Tight spreads - good liquidity")
        
        if features.catalyst_score > 0.5:
            notes.append("Strong catalyst support")
        
        return "; ".join(notes) if notes else "Standard day trading setup"
    
    async def get_live_picks(self, mode: str = "SAFE") -> List[DayTradingPick]:
        """Get current live picks"""
        if mode in self.current_picks:
            cache_age = datetime.now() - self.last_update
            if cache_age < timedelta(minutes=2):  # 2-minute cache
                return self.current_picks[mode]
        
        # Generate new picks if cache is stale
        return await self.generate_picks(mode)
    
    async def update_pick_status(self, symbol: str, status: str):
        """Update pick status (for tracking)"""
        # Implementation for tracking pick performance
        pass


# Factory function
async def create_live_trading_engine(
    alpaca_api_key: str,
    alpaca_secret: str,
    polygon_api_key: str
) -> LiveDayTradingEngine:
    """Create live trading engine with all components"""
    
    from ..market.providers.polygon import PolygonProvider
    from ..broker.adapters.alpaca_paper import AlpacaPaperBroker
    
    # Create components
    market_provider = PolygonProvider(api_key=polygon_api_key)
    universe_generator = LiveUniverseGenerator(market_provider)
    feature_calculator = RealTimeFeatureCalculator(market_provider)
    broker = AlpacaPaperBroker(
        api_key_id=alpaca_api_key,
        api_secret_key=alpaca_secret
    )
    
    # Create engine
    engine = LiveDayTradingEngine(
        universe_generator=universe_generator,
        feature_calculator=feature_calculator,
        broker=broker,
        market_data_provider=market_provider
    )
    
    return engine
