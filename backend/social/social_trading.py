"""
Social Trading System for RichesReach
Provides comprehensive social trading features including following traders,
copy trading, leaderboards, and social interactions.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import random
import math

class SocialTradingEngine:
    """Main social trading engine with comprehensive features"""
    
    def __init__(self):
        self.traders_db = {}
        self.follows_db = {}
        self.trades_db = {}
        self.leaderboards_db = {}
        self.social_interactions_db = {}
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock data for testing"""
        # Mock traders
        traders = [
            {
                "id": "trader_001",
                "username": "CryptoKing",
                "display_name": "Crypto King",
                "avatar": "https://example.com/avatar1.jpg",
                "bio": "Professional crypto trader with 5+ years experience",
                "followers_count": 1250,
                "following_count": 45,
                "total_trades": 342,
                "win_rate": 0.68,
                "total_return": 0.45,
                "risk_score": 0.7,
                "verified": True,
                "join_date": "2022-01-15",
                "preferred_assets": ["BTC", "ETH", "AAPL", "TSLA"],
                "trading_style": "swing_trading",
                "avg_trade_size": 5000,
                "max_drawdown": 0.12,
                "sharpe_ratio": 1.8
            },
            {
                "id": "trader_002", 
                "username": "DayTraderPro",
                "display_name": "Day Trader Pro",
                "avatar": "https://example.com/avatar2.jpg",
                "bio": "Day trading specialist focusing on momentum plays",
                "followers_count": 890,
                "following_count": 23,
                "total_trades": 156,
                "win_rate": 0.72,
                "total_return": 0.38,
                "risk_score": 0.8,
                "verified": True,
                "join_date": "2022-03-20",
                "preferred_assets": ["SPY", "QQQ", "NVDA", "AMD"],
                "trading_style": "day_trading",
                "avg_trade_size": 2500,
                "max_drawdown": 0.08,
                "sharpe_ratio": 2.1
            },
            {
                "id": "trader_003",
                "username": "OptionsGuru",
                "display_name": "Options Guru",
                "avatar": "https://example.com/avatar3.jpg",
                "bio": "Options trading expert with focus on volatility strategies",
                "followers_count": 2100,
                "following_count": 67,
                "total_trades": 89,
                "win_rate": 0.75,
                "total_return": 0.52,
                "risk_score": 0.6,
                "verified": True,
                "join_date": "2021-11-10",
                "preferred_assets": ["SPY", "QQQ", "AAPL", "MSFT"],
                "trading_style": "options_trading",
                "avg_trade_size": 3000,
                "max_drawdown": 0.15,
                "sharpe_ratio": 1.6
            }
        ]
        
        for trader in traders:
            self.traders_db[trader["id"]] = trader
        
        # Mock follows
        self.follows_db["user_001"] = ["trader_001", "trader_002"]
        self.follows_db["user_002"] = ["trader_001", "trader_003"]
        self.follows_db["user_003"] = ["trader_002", "trader_003"]
        
        # Mock trades
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "BTC", "ETH"]
        for i in range(50):
            trader_id = random.choice(list(self.traders_db.keys()))
            symbol = random.choice(symbols)
            side = random.choice(["BUY", "SELL"])
            quantity = random.randint(10, 1000)
            price = random.uniform(50, 500)
            
            trade = {
                "id": f"trade_{i:03d}",
                "trader_id": trader_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": round(price, 2),
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "status": "filled",
                "copy_trades": random.randint(0, 50),
                "likes": random.randint(0, 25),
                "comments": random.randint(0, 10),
                "pnl": round(random.uniform(-1000, 2000), 2),
                "tags": random.sample(["momentum", "breakout", "reversal", "earnings", "news"], random.randint(1, 3))
            }
            self.trades_db[trade["id"]] = trade
    
    def get_trader_profile(self, trader_id: str) -> Dict[str, Any]:
        """Get detailed trader profile"""
        if trader_id not in self.traders_db:
            return {"error": "Trader not found"}
        
        trader = self.traders_db[trader_id]
        
        # Get recent trades
        recent_trades = [
            trade for trade in self.trades_db.values()
            if trade["trader_id"] == trader_id
        ][-10:]  # Last 10 trades
        
        # Calculate additional metrics
        all_trades = [trade for trade in self.trades_db.values() if trade["trader_id"] == trader_id]
        total_pnl = sum(trade["pnl"] for trade in all_trades)
        avg_pnl = total_pnl / len(all_trades) if all_trades else 0
        
        return {
            **trader,
            "recent_trades": recent_trades,
            "total_pnl": round(total_pnl, 2),
            "avg_pnl": round(avg_pnl, 2),
            "monthly_return": round(random.uniform(0.05, 0.25), 3),
            "yearly_return": round(random.uniform(0.15, 0.45), 3),
            "best_trade": round(max(trade["pnl"] for trade in all_trades), 2) if all_trades else 0,
            "worst_trade": round(min(trade["pnl"] for trade in all_trades), 2) if all_trades else 0,
            "copied_by": random.randint(50, 200),
            "social_score": random.uniform(85, 98)
        }
    
    def get_leaderboard(self, period: str = "monthly", category: str = "returns") -> List[Dict[str, Any]]:
        """Get trading leaderboard"""
        leaderboard = []
        
        for trader_id, trader in self.traders_db.items():
            # Calculate performance metrics
            all_trades = [trade for trade in self.trades_db.values() if trade["trader_id"] == trader_id]
            
            if period == "monthly":
                period_trades = [trade for trade in all_trades 
                               if datetime.fromisoformat(trade["timestamp"]) > datetime.now() - timedelta(days=30)]
            elif period == "weekly":
                period_trades = [trade for trade in all_trades 
                               if datetime.fromisoformat(trade["timestamp"]) > datetime.now() - timedelta(days=7)]
            else:  # all_time
                period_trades = all_trades
            
            if not period_trades:
                continue
            
            period_return = sum(trade["pnl"] for trade in period_trades)
            win_rate = sum(1 for trade in period_trades if trade["pnl"] > 0) / len(period_trades)
            
            leaderboard.append({
                "trader_id": trader_id,
                "username": trader["username"],
                "display_name": trader["display_name"],
                "avatar": trader["avatar"],
                "verified": trader["verified"],
                "period_return": round(period_return, 2),
                "win_rate": round(win_rate, 3),
                "total_trades": len(period_trades),
                "followers_count": trader["followers_count"],
                "copied_by": random.randint(20, 150),
                "social_score": random.uniform(80, 95)
            })
        
        # Sort by category
        if category == "returns":
            leaderboard.sort(key=lambda x: x["period_return"], reverse=True)
        elif category == "win_rate":
            leaderboard.sort(key=lambda x: x["win_rate"], reverse=True)
        elif category == "followers":
            leaderboard.sort(key=lambda x: x["followers_count"], reverse=True)
        elif category == "social_score":
            leaderboard.sort(key=lambda x: x["social_score"], reverse=True)
        
        # Add rankings
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        return leaderboard[:20]  # Top 20
    
    def get_following_feed(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get feed of trades from followed traders"""
        if user_id not in self.follows_db:
            return []
        
        followed_traders = self.follows_db[user_id]
        
        # Get recent trades from followed traders
        feed_trades = []
        for trade in self.trades_db.values():
            if trade["trader_id"] in followed_traders:
                trader_info = self.traders_db[trade["trader_id"]]
                feed_trades.append({
                    **trade,
                    "trader_username": trader_info["username"],
                    "trader_display_name": trader_info["display_name"],
                    "trader_avatar": trader_info["avatar"],
                    "trader_verified": trader_info["verified"],
                    "trader_followers": trader_info["followers_count"]
                })
        
        # Sort by timestamp (most recent first)
        feed_trades.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return feed_trades[:limit]
    
    def follow_trader(self, user_id: str, trader_id: str) -> Dict[str, Any]:
        """Follow a trader"""
        if trader_id not in self.traders_db:
            return {"success": False, "error": "Trader not found"}
        
        if user_id not in self.follows_db:
            self.follows_db[user_id] = []
        
        if trader_id not in self.follows_db[user_id]:
            self.follows_db[user_id].append(trader_id)
            self.traders_db[trader_id]["followers_count"] += 1
        
        return {
            "success": True,
            "message": f"Now following {self.traders_db[trader_id]['username']}",
            "followers_count": self.traders_db[trader_id]["followers_count"]
        }
    
    def unfollow_trader(self, user_id: str, trader_id: str) -> Dict[str, Any]:
        """Unfollow a trader"""
        if user_id in self.follows_db and trader_id in self.follows_db[user_id]:
            self.follows_db[user_id].remove(trader_id)
            self.traders_db[trader_id]["followers_count"] = max(0, self.traders_db[trader_id]["followers_count"] - 1)
        
        return {
            "success": True,
            "message": f"Unfollowed {self.traders_db[trader_id]['username']}",
            "followers_count": self.traders_db[trader_id]["followers_count"]
        }
    
    def copy_trade(self, user_id: str, trade_id: str, copy_amount: float) -> Dict[str, Any]:
        """Copy a trade from another trader"""
        if trade_id not in self.trades_db:
            return {"success": False, "error": "Trade not found"}
        
        original_trade = self.trades_db[trade_id]
        
        # Calculate copy trade parameters
        original_value = original_trade["quantity"] * original_trade["price"]
        copy_quantity = int(copy_amount / original_trade["price"])
        
        # Create copy trade
        copy_trade = {
            "id": f"copy_{trade_id}_{user_id}",
            "user_id": user_id,
            "original_trade_id": trade_id,
            "original_trader_id": original_trade["trader_id"],
            "symbol": original_trade["symbol"],
            "side": original_trade["side"],
            "quantity": copy_quantity,
            "price": original_trade["price"],
            "copy_amount": copy_amount,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "tags": original_trade["tags"]
        }
        
        # Update original trade copy count
        self.trades_db[trade_id]["copy_trades"] += 1
        
        return {
            "success": True,
            "message": f"Copied trade from {self.traders_db[original_trade['trader_id']]['username']}",
            "copy_trade": copy_trade,
            "original_trade": original_trade
        }
    
    def get_trader_search(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for traders"""
        results = []
        
        for trader_id, trader in self.traders_db.items():
            # Simple text search
            if (query.lower() in trader["username"].lower() or 
                query.lower() in trader["display_name"].lower() or
                query.lower() in trader["bio"].lower()):
                
                # Apply filters
                if filters:
                    if "min_followers" in filters and trader["followers_count"] < filters["min_followers"]:
                        continue
                    if "min_win_rate" in filters and trader["win_rate"] < filters["min_win_rate"]:
                        continue
                    if "verified_only" in filters and filters["verified_only"] and not trader["verified"]:
                        continue
                    if "trading_style" in filters and trader["trading_style"] != filters["trading_style"]:
                        continue
                
                results.append(trader)
        
        # Sort by followers count
        results.sort(key=lambda x: x["followers_count"], reverse=True)
        
        return results
    
    def get_social_interactions(self, trade_id: str) -> Dict[str, Any]:
        """Get social interactions for a trade"""
        if trade_id not in self.trades_db:
            return {"error": "Trade not found"}
        
        trade = self.trades_db[trade_id]
        
        # Mock social interactions
        interactions = {
            "likes": trade["likes"],
            "comments": trade["comments"],
            "shares": random.randint(0, 15),
            "bookmarks": random.randint(0, 8),
            "copy_trades": trade["copy_trades"],
            "recent_comments": [
                {
                    "id": f"comment_{i}",
                    "user_id": f"user_{random.randint(1, 10):03d}",
                    "username": f"Trader{i}",
                    "comment": random.choice([
                        "Great trade! Following your strategy.",
                        "Nice call on this one!",
                        "Thanks for sharing your analysis.",
                        "This is exactly what I was looking for.",
                        "Amazing timing on this trade!"
                    ]),
                    "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                    "likes": random.randint(0, 5)
                }
                for i in range(min(trade["comments"], 5))
            ]
        }
        
        return interactions
    
    def like_trade(self, user_id: str, trade_id: str) -> Dict[str, Any]:
        """Like a trade"""
        if trade_id not in self.trades_db:
            return {"success": False, "error": "Trade not found"}
        
        self.trades_db[trade_id]["likes"] += 1
        
        return {
            "success": True,
            "message": "Trade liked",
            "likes_count": self.trades_db[trade_id]["likes"]
        }
    
    def comment_on_trade(self, user_id: str, trade_id: str, comment: str) -> Dict[str, Any]:
        """Add comment to a trade"""
        if trade_id not in self.trades_db:
            return {"success": False, "error": "Trade not found"}
        
        self.trades_db[trade_id]["comments"] += 1
        
        new_comment = {
            "id": f"comment_{random.randint(1000, 9999)}",
            "user_id": user_id,
            "username": f"User{user_id[-3:]}",
            "comment": comment,
            "timestamp": datetime.now().isoformat(),
            "likes": 0
        }
        
        return {
            "success": True,
            "message": "Comment added",
            "comment": new_comment,
            "comments_count": self.trades_db[trade_id]["comments"]
        }
    
    def get_trader_stats(self, trader_id: str) -> Dict[str, Any]:
        """Get comprehensive trader statistics"""
        if trader_id not in self.traders_db:
            return {"error": "Trader not found"}
        
        trader = self.traders_db[trader_id]
        all_trades = [trade for trade in self.trades_db.values() if trade["trader_id"] == trader_id]
        
        if not all_trades:
            return {"error": "No trades found"}
        
        # Calculate comprehensive stats
        total_pnl = sum(trade["pnl"] for trade in all_trades)
        winning_trades = [trade for trade in all_trades if trade["pnl"] > 0]
        losing_trades = [trade for trade in all_trades if trade["pnl"] < 0]
        
        avg_win = sum(trade["pnl"] for trade in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(trade["pnl"] for trade in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Calculate drawdown
        cumulative_pnl = []
        running_total = 0
        for trade in sorted(all_trades, key=lambda x: x["timestamp"]):
            running_total += trade["pnl"]
            cumulative_pnl.append(running_total)
        
        peak = max(cumulative_pnl) if cumulative_pnl else 0
        current = cumulative_pnl[-1] if cumulative_pnl else 0
        max_drawdown = (peak - current) / peak if peak > 0 else 0
        
        return {
            "trader_id": trader_id,
            "username": trader["username"],
            "total_trades": len(all_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(all_trades),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else float('inf'),
            "max_drawdown": round(max_drawdown, 3),
            "sharpe_ratio": trader["sharpe_ratio"],
            "followers_count": trader["followers_count"],
            "total_copies": sum(trade["copy_trades"] for trade in all_trades),
            "avg_trade_size": trader["avg_trade_size"],
            "preferred_assets": trader["preferred_assets"],
            "trading_style": trader["trading_style"],
            "verified": trader["verified"],
            "social_score": random.uniform(85, 98)
        }
