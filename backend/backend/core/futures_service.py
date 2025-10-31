"""
Futures Service - Paper Trading with Realistic Mock Data
Phase 1: Enhanced mock scenarios
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


# Micro futures contracts
FUTURES_CONTRACTS = {
    "MES": {
        "name": "Micro E-mini S&P 500",
        "multiplier": 5,  # $5 per point
        "tick_size": 0.25,
        "margin": 50.0,  # Initial margin per contract
    },
    "MNQ": {
        "name": "Micro E-mini Nasdaq-100",
        "multiplier": 2,  # $2 per point
        "tick_size": 0.25,
        "margin": 60.0,
    },
    "MYM": {
        "name": "Micro E-mini Dow Jones",
        "multiplier": 0.5,  # $0.50 per point
        "tick_size": 1.0,
        "margin": 50.0,
    },
    "M2K": {
        "name": "Micro Russell 2000",
        "multiplier": 5,  # $5 per point
        "tick_size": 0.1,
        "margin": 50.0,
    },
}


class FuturesPaperAccount:
    """Paper trading account - tracks positions and P&L"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.balance = initial_balance
        self.positions: Dict[str, Dict] = {}
        self.order_history: List[Dict] = []
        self.total_pnl = 0.0
    
    def add_position(self, symbol: str, side: str, quantity: int, entry_price: float):
        """Add a new position"""
        if symbol in self.positions:
            # Update existing position
            pos = self.positions[symbol]
            if pos["side"] == side:
                # Same side - average in
                total_qty = pos["quantity"] + quantity
                total_cost = (pos["quantity"] * pos["entry_price"]) + (quantity * entry_price)
                pos["quantity"] = total_qty
                pos["entry_price"] = total_cost / total_qty
            else:
                # Opposite side - reduce or close
                if quantity >= pos["quantity"]:
                    # Closing position
                    del self.positions[symbol]
                else:
                    pos["quantity"] -= quantity
        else:
            # New position
            self.positions[symbol] = {
                "side": side,
                "quantity": quantity,
                "entry_price": entry_price,
                "entry_time": datetime.now(),
            }
    
    def get_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """Get all positions with current P&L"""
        result = []
        for symbol, pos in self.positions.items():
            current_price = current_prices.get(symbol, pos["entry_price"])
            contract = FUTURES_CONTRACTS.get(symbol[:3], FUTURES_CONTRACTS["MES"])
            
            # Calculate P&L
            price_diff = current_price - pos["entry_price"] if pos["side"] == "BUY" else pos["entry_price"] - current_price
            pnl = price_diff * contract["multiplier"] * pos["quantity"]
            
            result.append({
                "symbol": symbol,
                "side": pos["side"],
                "quantity": pos["quantity"],
                "entry_price": pos["entry_price"],
                "current_price": current_price,
                "pnl": pnl,
                "pnl_percent": (pnl / (pos["entry_price"] * contract["multiplier"] * pos["quantity"])) * 100 if pos["quantity"] > 0 else 0,
            })
        return result


class FuturesRecommendationEngine:
    """Generates realistic futures recommendations based on market conditions"""
    
    def __init__(self):
        self.market_regime = "calm"  # calm, choppy, storm
        self.vix_level = 15.0  # Volatility index
    
    def get_recommendations(self, user_id: Optional[int] = None) -> List[Dict]:
        """Generate recommendations based on current market conditions"""
        recommendations = []
        
        # Determine market regime (simplified)
        hour = datetime.now().hour
        if 9 <= hour <= 16:  # Market hours
            self.market_regime = random.choice(["calm", "choppy"])
            self.vix_level = random.uniform(12.0, 20.0)
        else:
            self.market_regime = "calm"
            self.vix_level = random.uniform(10.0, 15.0)
        
        # Generate 2-3 recommendations
        contracts = ["MES", "MNQ", "MYM"]
        selected = random.sample(contracts, min(2, len(contracts)))
        
        for symbol_base in selected:
            contract = FUTURES_CONTRACTS[symbol_base]
            symbol = f"{symbol_base}Z5"  # Dec 2025
            
            # Determine action based on regime
            if self.market_regime == "calm":
                action = "Buy"
                why_now = f"Calm market. Hedge portfolio with micro contract—max loss ${contract['margin']}."
                probability = random.uniform(65, 75)
                max_gain = contract["margin"] * random.uniform(4, 6)
            elif self.market_regime == "choppy":
                action = random.choice(["Buy", "Sell"])
                why_now = f"Choppy market. Small position for exposure—max loss ${contract['margin']}."
                probability = random.uniform(55, 65)
                max_gain = contract["margin"] * random.uniform(3, 5)
            else:  # storm
                action = "Sell"  # Hedge
                why_now = f"Storm conditions. Hedge portfolio—max loss ${contract['margin']}."
                probability = random.uniform(60, 70)
                max_gain = contract["margin"] * random.uniform(2, 4)
            
            recommendations.append({
                "symbol": symbol,
                "name": contract["name"],
                "why_now": why_now,
                "max_loss": contract["margin"],
                "max_gain": round(max_gain, 2),
                "probability": round(probability, 1),
                "action": action,
            })
        
        return recommendations


# Global paper account (in production, would be per-user)
_paper_accounts: Dict[int, FuturesPaperAccount] = {}


def get_paper_account(user_id: int) -> FuturesPaperAccount:
    """Get or create paper trading account for user"""
    if user_id not in _paper_accounts:
        _paper_accounts[user_id] = FuturesPaperAccount()
    return _paper_accounts[user_id]


def get_recommendation_engine() -> FuturesRecommendationEngine:
    """Get recommendation engine instance"""
    return FuturesRecommendationEngine()

