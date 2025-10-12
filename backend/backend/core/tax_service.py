#!/usr/bin/env python3
"""
Tax Service for RichesReach
Real tax calculations using actual portfolio data and market prices
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Sum, Q
from django.contrib.auth import get_user_model
from .models import User, Portfolio, PortfolioPosition, Stock, PortfolioSnapshot
from .crypto_models import CryptoPortfolio, CryptoHolding, CryptoTrade
from .market_data_service import MarketDataService
from .real_market_data_service import RealMarketDataService

logger = logging.getLogger(__name__)
User = get_user_model()

class TaxService:
    """Service for real tax calculations and optimizations"""
    
    def __init__(self):
        self.market_data_service = MarketDataService()
        self.real_market_service = RealMarketDataService()
        
        # 2024 Tax brackets (single filer)
        self.tax_brackets_2024 = [
            {"min": 0, "max": 11000, "rate": 0.10},
            {"min": 11000, "max": 44725, "rate": 0.12},
            {"min": 44725, "max": 95375, "rate": 0.22},
            {"min": 95375, "max": 182050, "rate": 0.24},
            {"min": 182050, "max": 231250, "rate": 0.32},
            {"min": 231250, "max": 578125, "rate": 0.35},
            {"min": 578125, "max": float('inf'), "rate": 0.37},
        ]
        
        # Long-term capital gains rates (2024)
        self.long_term_cg_rates = [
            {"min": 0, "max": 47025, "rate": 0.00},  # 0% for income up to $47,025
            {"min": 47025, "max": 518900, "rate": 0.15},  # 15% for income $47,025 - $518,900
            {"min": 518900, "max": float('inf'), "rate": 0.20},  # 20% for income above $518,900
        ]
    
    def get_user_portfolio_data(self, user: User) -> Dict[str, Any]:
        """Get real portfolio data for a user"""
        try:
            # Get stock portfolio
            portfolios = Portfolio.objects.filter(user=user)
            stock_positions = []
            total_stock_value = Decimal('0')
            
            for portfolio in portfolios:
                positions = PortfolioPosition.objects.filter(portfolio=portfolio)
                for position in positions:
                    # Get current market price
                    current_price = self._get_current_price(position.stock.symbol)
                    if current_price:
                        current_value = position.shares * Decimal(str(current_price))
                        cost_basis = position.shares * position.average_price
                        unrealized_gain = current_value - cost_basis
                        
                        stock_positions.append({
                            "symbol": position.stock.symbol,
                            "shares": float(position.shares),
                            "cost_basis": float(cost_basis),
                            "current_price": current_price,
                            "current_value": float(current_value),
                            "unrealized_gain": float(unrealized_gain),
                            "unrealized_gain_pct": float((unrealized_gain / cost_basis) * 100) if cost_basis > 0 else 0,
                            "holding_period": self._calculate_holding_period(position.added_at),
                            "is_long_term": self._is_long_term_holding(position.added_at)
                        })
                        total_stock_value += current_value
            
            # Get crypto portfolio
            crypto_positions = []
            total_crypto_value = Decimal('0')
            
            try:
                crypto_portfolio = CryptoPortfolio.objects.get(user=user)
                holdings = CryptoHolding.objects.filter(portfolio=crypto_portfolio)
                
                for holding in holdings:
                    crypto_positions.append({
                        "symbol": holding.cryptocurrency.symbol,
                        "quantity": float(holding.quantity),
                        "cost_basis": float(holding.average_cost * holding.quantity),
                        "current_price": float(holding.current_price),
                        "current_value": float(holding.current_value),
                        "unrealized_gain": float(holding.unrealized_pnl),
                        "unrealized_gain_pct": float(holding.unrealized_pnl_percentage),
                        "holding_period": self._calculate_crypto_holding_period(holding),
                        "is_long_term": self._is_long_term_crypto_holding(holding)
                    })
                    total_crypto_value += Decimal(str(holding.current_value))
            except CryptoPortfolio.DoesNotExist:
                pass
            
            # Get realized gains/losses from trades
            realized_gains = self._get_realized_gains(user)
            
            return {
                "user_id": user.id,
                "stock_positions": stock_positions,
                "crypto_positions": crypto_positions,
                "total_stock_value": float(total_stock_value),
                "total_crypto_value": float(total_crypto_value),
                "total_portfolio_value": float(total_stock_value + total_crypto_value),
                "realized_gains": realized_gains,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio data for user {user.id}: {e}")
            return {"error": str(e)}
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol"""
        try:
            # Try real market data first
            quote_data = self.market_data_service.get_quote(symbol)
            if quote_data and hasattr(quote_data, 'price'):
                return float(quote_data.price)
            
            # Fallback to real market service
            real_data = self.real_market_service.get_benchmark_data(symbol, "1d")
            if real_data and 'price' in real_data:
                return float(real_data['price'])
            
            # Final fallback to stored price in Stock model
            try:
                stock = Stock.objects.get(symbol__iexact=symbol)
                if stock.current_price:
                    logger.info(f"Using stored price for {symbol}: ${stock.current_price}")
                    return float(stock.current_price)
            except Stock.DoesNotExist:
                pass
            
            logger.warning(f"Could not get current price for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def _calculate_holding_period(self, purchase_date) -> int:
        """Calculate holding period in days"""
        from django.utils import timezone
        now = timezone.now()
        if purchase_date.tzinfo is None:
            purchase_date = timezone.make_aware(purchase_date)
        return (now - purchase_date).days
    
    def _is_long_term_holding(self, purchase_date) -> bool:
        """Check if holding qualifies for long-term capital gains"""
        return self._calculate_holding_period(purchase_date) >= 365
    
    def _calculate_crypto_holding_period(self, holding: CryptoHolding) -> int:
        """Calculate crypto holding period in days"""
        from django.utils import timezone
        now = timezone.now()
        created_at = holding.created_at
        if created_at.tzinfo is None:
            created_at = timezone.make_aware(created_at)
        return (now - created_at).days
    
    def _is_long_term_crypto_holding(self, holding: CryptoHolding) -> bool:
        """Check if crypto holding qualifies for long-term capital gains"""
        return self._calculate_crypto_holding_period(holding) >= 365
    
    def _get_realized_gains(self, user: User) -> Dict[str, float]:
        """Get realized gains/losses from trades"""
        try:
            # Get crypto trades
            crypto_trades = CryptoTrade.objects.filter(user=user, trade_type='SELL')
            
            total_realized_gains = Decimal('0')
            long_term_gains = Decimal('0')
            short_term_gains = Decimal('0')
            
            for trade in crypto_trades:
                # Calculate realized gain/loss
                # This is simplified - in reality you'd need to track cost basis per lot
                try:
                    holding = CryptoHolding.objects.get(
                        portfolio__user=user,
                        cryptocurrency=trade.cryptocurrency
                    )
                    cost_basis = holding.average_cost * trade.quantity
                    proceeds = trade.price_per_unit * trade.quantity
                    realized_gain = proceeds - cost_basis
                    
                    total_realized_gains += realized_gain
                    
                    # Determine if long-term or short-term
                    if self._is_long_term_crypto_holding(holding):
                        long_term_gains += realized_gain
                    else:
                        short_term_gains += realized_gain
                        
                except CryptoHolding.DoesNotExist:
                    continue
            
            return {
                "total_realized_gains": float(total_realized_gains),
                "long_term_gains": float(long_term_gains),
                "short_term_gains": float(short_term_gains)
            }
            
        except Exception as e:
            logger.error(f"Error calculating realized gains: {e}")
            return {"total_realized_gains": 0.0, "long_term_gains": 0.0, "short_term_gains": 0.0}
    
    def calculate_tax_bracket(self, taxable_income: float) -> Dict[str, Any]:
        """Calculate tax bracket for given income"""
        for bracket in self.tax_brackets_2024:
            if bracket["min"] <= taxable_income <= bracket["max"]:
                return {
                    "bracket": bracket,
                    "marginal_rate": bracket["rate"],
                    "effective_rate": self._calculate_effective_rate(taxable_income),
                    "next_bracket_threshold": bracket["max"] if bracket["max"] != float('inf') else None,
                    "room_for_gains": max(0, bracket["max"] - taxable_income) if bracket["max"] != float('inf') else float('inf')
                }
        
        # Fallback to highest bracket
        return {
            "bracket": self.tax_brackets_2024[-1],
            "marginal_rate": 0.37,
            "effective_rate": self._calculate_effective_rate(taxable_income),
            "next_bracket_threshold": None,
            "room_for_gains": float('inf')
        }
    
    def _calculate_effective_rate(self, taxable_income: float) -> float:
        """Calculate effective tax rate"""
        total_tax = 0
        remaining_income = taxable_income
        
        for bracket in self.tax_brackets_2024:
            if remaining_income <= 0:
                break
            
            bracket_income = min(remaining_income, bracket["max"] - bracket["min"])
            total_tax += bracket_income * bracket["rate"]
            remaining_income -= bracket_income
        
        return total_tax / taxable_income if taxable_income > 0 else 0
    
    def calculate_capital_gains_tax(self, gains: float, is_long_term: bool, taxable_income: float) -> Dict[str, Any]:
        """Calculate capital gains tax"""
        if is_long_term:
            # Long-term capital gains rates
            for bracket in self.long_term_cg_rates:
                if bracket["min"] <= taxable_income <= bracket["max"]:
                    tax_rate = bracket["rate"]
                    break
            else:
                tax_rate = 0.20  # Highest long-term rate
        else:
            # Short-term capital gains use ordinary income rates
            tax_bracket = self.calculate_tax_bracket(taxable_income)
            tax_rate = tax_bracket["marginal_rate"]
        
        tax_amount = gains * tax_rate
        
        return {
            "gains": gains,
            "is_long_term": is_long_term,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "after_tax_gains": gains - tax_amount
        }
    
    def get_tax_loss_harvesting_opportunities(self, user: User) -> List[Dict[str, Any]]:
        """Find tax loss harvesting opportunities"""
        portfolio_data = self.get_user_portfolio_data(user)
        if "error" in portfolio_data:
            return []
        
        opportunities = []
        
        # Check stock positions
        for position in portfolio_data.get("stock_positions", []):
            if position["unrealized_gain"] < 0:  # Loss position
                # Calculate potential tax savings
                tax_bracket = self.calculate_tax_bracket(85000)  # Default income
                potential_savings = abs(position["unrealized_gain"]) * tax_bracket["marginal_rate"]
                
                opportunities.append({
                    "symbol": position["symbol"],
                    "type": "STOCK",
                    "unrealized_loss": position["unrealized_gain"],
                    "shares": position["shares"],
                    "current_price": position["current_price"],
                    "cost_basis": position["cost_basis"],
                    "potential_tax_savings": potential_savings,
                    "priority": "HIGH" if abs(position["unrealized_gain"]) > 1000 else "MEDIUM",
                    "reason": f"Realize ${abs(position['unrealized_gain']):,.2f} loss for tax savings",
                    "action": "SELL"
                })
        
        # Check crypto positions
        for position in portfolio_data.get("crypto_positions", []):
            if position["unrealized_gain"] < 0:  # Loss position
                tax_bracket = self.calculate_tax_bracket(85000)  # Default income
                potential_savings = abs(position["unrealized_gain"]) * tax_bracket["marginal_rate"]
                
                opportunities.append({
                    "symbol": position["symbol"],
                    "type": "CRYPTO",
                    "unrealized_loss": position["unrealized_gain"],
                    "quantity": position["quantity"],
                    "current_price": position["current_price"],
                    "cost_basis": position["cost_basis"],
                    "potential_tax_savings": potential_savings,
                    "priority": "HIGH" if abs(position["unrealized_gain"]) > 1000 else "MEDIUM",
                    "reason": f"Realize ${abs(position['unrealized_gain']):,.2f} loss for tax savings",
                    "action": "SELL"
                })
        
        # Sort by potential tax savings
        opportunities.sort(key=lambda x: x["potential_tax_savings"], reverse=True)
        
        return opportunities
    
    def get_tax_efficient_rebalancing(self, user: User, target_allocation: Dict[str, float]) -> Dict[str, Any]:
        """Get tax-efficient rebalancing recommendations"""
        portfolio_data = self.get_user_portfolio_data(user)
        if "error" in portfolio_data:
            return {"error": portfolio_data["error"]}
        
        total_value = portfolio_data["total_portfolio_value"]
        current_allocation = self._calculate_current_allocation(portfolio_data)
        
        rebalancing_actions = []
        
        # Calculate rebalancing needs
        for asset_class, target_pct in target_allocation.items():
            current_pct = current_allocation.get(asset_class, 0)
            target_value = total_value * target_pct
            current_value = total_value * current_pct
            
            difference = target_value - current_value
            
            if abs(difference) > total_value * 0.05:  # 5% threshold
                if difference > 0:
                    # Need to buy more
                    rebalancing_actions.append({
                        "action": "BUY",
                        "asset_class": asset_class,
                        "amount": difference,
                        "current_allocation": current_pct,
                        "target_allocation": target_pct,
                        "priority": "MEDIUM"
                    })
                else:
                    # Need to sell
                    # Find positions with lowest tax impact
                    sell_candidates = self._find_sell_candidates(portfolio_data, asset_class, abs(difference))
                    rebalancing_actions.extend(sell_candidates)
        
        return {
            "current_allocation": current_allocation,
            "target_allocation": target_allocation,
            "rebalancing_actions": rebalancing_actions,
            "total_portfolio_value": total_value,
            "tax_impact": self._calculate_rebalancing_tax_impact(rebalancing_actions)
        }
    
    def _calculate_current_allocation(self, portfolio_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate current portfolio allocation"""
        total_value = portfolio_data["total_portfolio_value"]
        if total_value == 0:
            return {}
        
        # Simplified allocation calculation
        # In reality, you'd categorize each position by asset class
        stock_value = portfolio_data["total_stock_value"]
        crypto_value = portfolio_data["total_crypto_value"]
        
        return {
            "stocks": stock_value / total_value,
            "crypto": crypto_value / total_value,
            "cash": 0.0  # Would need to track cash positions
        }
    
    def _find_sell_candidates(self, portfolio_data: Dict[str, Any], asset_class: str, amount_needed: float) -> List[Dict[str, Any]]:
        """Find best positions to sell for rebalancing"""
        candidates = []
        
        if asset_class == "stocks":
            positions = portfolio_data.get("stock_positions", [])
        elif asset_class == "crypto":
            positions = portfolio_data.get("crypto_positions", [])
        else:
            return candidates
        
        # Sort by tax efficiency (prefer losses, then long-term gains, then short-term gains)
        sorted_positions = sorted(positions, key=lambda x: (
            x["unrealized_gain"] < 0,  # Losses first
            x["is_long_term"],  # Long-term gains before short-term
            -x["unrealized_gain"]  # Then by gain amount (ascending)
        ))
        
        remaining_amount = amount_needed
        for position in sorted_positions:
            if remaining_amount <= 0:
                break
            
            position_value = position["current_value"]
            sell_amount = min(remaining_amount, position_value)
            sell_pct = sell_amount / position_value
            
            candidates.append({
                "action": "SELL",
                "symbol": position["symbol"],
                "type": asset_class.upper(),
                "amount": sell_amount,
                "percentage": sell_pct,
                "unrealized_gain": position["unrealized_gain"] * sell_pct,
                "is_long_term": position["is_long_term"],
                "tax_impact": self._calculate_position_tax_impact(position, sell_pct),
                "priority": "LOW" if position["unrealized_gain"] < 0 else "MEDIUM"
            })
            
            remaining_amount -= sell_amount
        
        return candidates
    
    def _calculate_position_tax_impact(self, position: Dict[str, Any], sell_percentage: float) -> Dict[str, Any]:
        """Calculate tax impact of selling a position"""
        gain_amount = position["unrealized_gain"] * sell_percentage
        tax_bracket = self.calculate_tax_bracket(85000)  # Default income
        
        if position["is_long_term"]:
            # Long-term capital gains
            if gain_amount > 0:
                tax_rate = 0.15  # Simplified long-term rate
            else:
                tax_rate = 0  # No tax on losses
        else:
            # Short-term capital gains (ordinary income)
            tax_rate = tax_bracket["marginal_rate"]
        
        tax_amount = gain_amount * tax_rate
        
        return {
            "gain_amount": gain_amount,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "after_tax_amount": gain_amount - tax_amount
        }
    
    def _calculate_rebalancing_tax_impact(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate total tax impact of rebalancing actions"""
        total_gains = 0
        total_taxes = 0
        
        for action in actions:
            if action["action"] == "SELL" and "tax_impact" in action:
                total_gains += action["tax_impact"]["gain_amount"]
                total_taxes += action["tax_impact"]["tax_amount"]
        
        return {
            "total_gains": total_gains,
            "total_taxes": total_taxes,
            "net_impact": total_gains - total_taxes,
            "tax_efficiency": 1 - (total_taxes / total_gains) if total_gains > 0 else 1
        }
