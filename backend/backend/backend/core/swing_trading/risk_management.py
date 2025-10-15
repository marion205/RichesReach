"""
Risk Management and Position Sizing for Swing Trading
Professional risk management with Kelly Criterion, portfolio heat maps, and dynamic stops
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal
import logging
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Professional risk management system for swing trading
    """
    
    def __init__(self):
        self.max_portfolio_risk = 0.02  # 2% max portfolio risk per trade
        self.max_position_size = 0.1    # 10% max position size
        self.correlation_threshold = 0.7  # Max correlation between positions
        self.max_drawdown = 0.15        # 15% max drawdown limit
        
    def calculate_position_size(self, 
                              account_equity: float,
                              entry_price: float,
                              stop_price: float,
                              risk_per_trade: float = 0.01,
                              max_position_pct: float = 0.1) -> Dict[str, Any]:
        """
        Calculate optimal position size using multiple methods
        
        Args:
            account_equity: Total account equity
            entry_price: Entry price for the trade
            stop_price: Stop loss price
            risk_per_trade: Risk per trade as percentage (default 1%)
            max_position_pct: Maximum position size as percentage of equity
            
        Returns:
            Dictionary with position sizing calculations
        """
        try:
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_price)
            
            if risk_per_share <= 0:
                return {
                    'shares': 0,
                    'dollar_risk': 0,
                    'position_value': 0,
                    'position_pct': 0,
                    'method': 'invalid_stop',
                    'error': 'Invalid stop price'
                }
            
            # Method 1: Fixed Risk Percentage
            dollars_at_risk = account_equity * risk_per_trade
            shares_fixed_risk = int(dollars_at_risk / risk_per_share)
            
            # Method 2: Maximum Position Size
            max_position_value = account_equity * max_position_pct
            shares_max_position = int(max_position_value / entry_price)
            
            # Method 3: Kelly Criterion (if win rate and avg win/loss provided)
            # This would require historical performance data
            
            # Choose the most conservative approach
            shares = min(shares_fixed_risk, shares_max_position)
            
            # Calculate final metrics
            position_value = shares * entry_price
            position_pct = position_value / account_equity
            dollar_risk = shares * risk_per_share
            
            return {
                'shares': shares,
                'dollar_risk': dollar_risk,
                'position_value': position_value,
                'position_pct': position_pct,
                'risk_per_trade_pct': (dollar_risk / account_equity) * 100,
                'method': 'conservative',
                'risk_per_share': risk_per_share,
                'max_shares_fixed_risk': shares_fixed_risk,
                'max_shares_position': shares_max_position
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {
                'shares': 0,
                'dollar_risk': 0,
                'position_value': 0,
                'position_pct': 0,
                'method': 'error',
                'error': str(e)
            }
    
    def calculate_kelly_position_size(self, 
                                    account_equity: float,
                                    win_rate: float,
                                    avg_win: float,
                                    avg_loss: float,
                                    entry_price: float,
                                    stop_price: float) -> Dict[str, Any]:
        """
        Calculate position size using Kelly Criterion
        
        Args:
            account_equity: Total account equity
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade percentage
            avg_loss: Average losing trade percentage
            entry_price: Entry price
            stop_price: Stop loss price
            
        Returns:
            Dictionary with Kelly-based position sizing
        """
        try:
            if win_rate <= 0 or win_rate >= 1 or avg_win <= 0 or avg_loss <= 0:
                return {
                    'kelly_fraction': 0,
                    'shares': 0,
                    'position_value': 0,
                    'position_pct': 0,
                    'method': 'kelly_invalid',
                    'error': 'Invalid Kelly parameters'
                }
            
            # Kelly Criterion: f = (bp - q) / b
            # where b = odds (avg_win/avg_loss), p = win_rate, q = loss_rate
            b = avg_win / avg_loss
            p = win_rate
            q = 1 - win_rate
            
            kelly_fraction = (b * p - q) / b
            
            # Apply safety factor (typically 0.25-0.5 of Kelly)
            safety_factor = 0.25
            adjusted_kelly = kelly_fraction * safety_factor
            
            # Cap at maximum position size
            max_kelly = 0.1  # 10% max
            final_kelly = min(adjusted_kelly, max_kelly)
            
            # Calculate position size
            position_value = account_equity * final_kelly
            shares = int(position_value / entry_price)
            
            return {
                'kelly_fraction': kelly_fraction,
                'adjusted_kelly': adjusted_kelly,
                'final_kelly': final_kelly,
                'shares': shares,
                'position_value': position_value,
                'position_pct': final_kelly * 100,
                'method': 'kelly_criterion',
                'safety_factor': safety_factor
            }
            
        except Exception as e:
            logger.error(f"Error calculating Kelly position size: {e}")
            return {
                'kelly_fraction': 0,
                'shares': 0,
                'position_value': 0,
                'position_pct': 0,
                'method': 'kelly_error',
                'error': str(e)
            }
    
    def calculate_dynamic_stop_loss(self, 
                                  entry_price: float,
                                  atr: float,
                                  atr_multiplier: float = 1.5,
                                  support_level: Optional[float] = None,
                                  resistance_level: Optional[float] = None,
                                  signal_type: str = 'long') -> Dict[str, Any]:
        """
        Calculate dynamic stop loss using multiple methods
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            atr_multiplier: ATR multiplier for stop distance
            support_level: Support level price
            resistance_level: Resistance level price
            signal_type: 'long' or 'short'
            
        Returns:
            Dictionary with stop loss calculations
        """
        try:
            # Method 1: ATR-based stop
            atr_stop_distance = atr * atr_multiplier
            
            if signal_type == 'long':
                atr_stop = entry_price - atr_stop_distance
            else:
                atr_stop = entry_price + atr_stop_distance
            
            # Method 2: Support/Resistance based stop
            sr_stop = None
            if signal_type == 'long' and support_level:
                sr_stop = support_level * 0.99  # 1% below support
            elif signal_type == 'short' and resistance_level:
                sr_stop = resistance_level * 1.01  # 1% above resistance
            
            # Method 3: Percentage-based stop
            percentage_stop = 0.05  # 5% stop
            if signal_type == 'long':
                pct_stop = entry_price * (1 - percentage_stop)
            else:
                pct_stop = entry_price * (1 + percentage_stop)
            
            # Choose the most conservative stop (closest to entry for long, farthest for short)
            if signal_type == 'long':
                stops = [atr_stop, sr_stop, pct_stop]
                stops = [s for s in stops if s is not None]
                final_stop = max(stops) if stops else atr_stop
            else:
                stops = [atr_stop, sr_stop, pct_stop]
                stops = [s for s in stops if s is not None]
                final_stop = min(stops) if stops else atr_stop
            
            # Calculate risk metrics
            stop_distance = abs(entry_price - final_stop)
            risk_percentage = (stop_distance / entry_price) * 100
            
            return {
                'stop_price': final_stop,
                'stop_distance': stop_distance,
                'risk_percentage': risk_percentage,
                'atr_stop': atr_stop,
                'sr_stop': sr_stop,
                'pct_stop': pct_stop,
                'method': 'dynamic',
                'atr_multiplier': atr_multiplier
            }
            
        except Exception as e:
            logger.error(f"Error calculating dynamic stop loss: {e}")
            return {
                'stop_price': entry_price * 0.95,  # Default 5% stop
                'stop_distance': entry_price * 0.05,
                'risk_percentage': 5.0,
                'method': 'default',
                'error': str(e)
            }
    
    def calculate_target_price(self, 
                             entry_price: float,
                             stop_price: float,
                             risk_reward_ratio: float = 2.0,
                             atr: Optional[float] = None,
                             resistance_level: Optional[float] = None,
                             support_level: Optional[float] = None,
                             signal_type: str = 'long') -> Dict[str, Any]:
        """
        Calculate target price using multiple methods
        
        Args:
            entry_price: Entry price
            stop_price: Stop loss price
            risk_reward_ratio: Desired risk/reward ratio
            atr: Average True Range
            resistance_level: Resistance level price
            support_level: Support level price
            signal_type: 'long' or 'short'
            
        Returns:
            Dictionary with target price calculations
        """
        try:
            risk_distance = abs(entry_price - stop_price)
            
            # Method 1: Risk/Reward ratio based
            reward_distance = risk_distance * risk_reward_ratio
            
            if signal_type == 'long':
                rr_target = entry_price + reward_distance
            else:
                rr_target = entry_price - reward_distance
            
            # Method 2: ATR-based target
            atr_target = None
            if atr:
                atr_target_distance = atr * 2.0  # 2x ATR target
                if signal_type == 'long':
                    atr_target = entry_price + atr_target_distance
                else:
                    atr_target = entry_price - atr_target_distance
            
            # Method 3: Support/Resistance based target
            sr_target = None
            if signal_type == 'long' and resistance_level:
                sr_target = resistance_level * 0.99  # Just below resistance
            elif signal_type == 'short' and support_level:
                sr_target = support_level * 1.01  # Just above support
            
            # Choose the most conservative target
            targets = [rr_target, atr_target, sr_target]
            targets = [t for t in targets if t is not None]
            
            if signal_type == 'long':
                final_target = min(targets) if targets else rr_target
            else:
                final_target = max(targets) if targets else rr_target
            
            # Calculate actual risk/reward ratio
            actual_reward = abs(final_target - entry_price)
            actual_rr = actual_reward / risk_distance if risk_distance > 0 else 0
            
            return {
                'target_price': final_target,
                'reward_distance': actual_reward,
                'risk_reward_ratio': actual_rr,
                'rr_target': rr_target,
                'atr_target': atr_target,
                'sr_target': sr_target,
                'method': 'dynamic'
            }
            
        except Exception as e:
            logger.error(f"Error calculating target price: {e}")
            return {
                'target_price': entry_price * 1.1,  # Default 10% target
                'reward_distance': entry_price * 0.1,
                'risk_reward_ratio': 2.0,
                'method': 'default',
                'error': str(e)
            }
    
    def calculate_portfolio_heat(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate portfolio heat and risk metrics
        
        Args:
            positions: List of position dictionaries with symbol, value, risk, etc.
            
        Returns:
            Dictionary with portfolio heat analysis
        """
        try:
            if not positions:
                return {
                    'total_risk': 0,
                    'total_value': 0,
                    'heat_percentage': 0,
                    'sector_exposure': {},
                    'correlation_risk': 0,
                    'recommendations': []
                }
            
            total_value = sum(pos.get('position_value', 0) for pos in positions)
            total_risk = sum(pos.get('dollar_risk', 0) for pos in positions)
            
            # Calculate sector exposure (simplified)
            sector_exposure = {}
            for pos in positions:
                sector = pos.get('sector', 'Unknown')
                sector_value = pos.get('position_value', 0)
                if sector in sector_exposure:
                    sector_exposure[sector] += sector_value
                else:
                    sector_exposure[sector] = sector_value
            
            # Convert to percentages
            for sector in sector_exposure:
                sector_exposure[sector] = (sector_exposure[sector] / total_value) * 100
            
            # Calculate correlation risk (simplified)
            symbols = [pos.get('symbol', '') for pos in positions]
            correlation_risk = len(set(symbols)) / len(symbols) if symbols else 0
            
            # Generate recommendations
            recommendations = []
            
            if total_risk / total_value > 0.05:  # More than 5% portfolio risk
                recommendations.append("Consider reducing position sizes - portfolio risk is high")
            
            max_sector_exposure = max(sector_exposure.values()) if sector_exposure else 0
            if max_sector_exposure > 30:  # More than 30% in one sector
                recommendations.append("Consider diversifying - high sector concentration")
            
            if correlation_risk < 0.7:  # Low diversification
                recommendations.append("Consider adding uncorrelated positions")
            
            return {
                'total_risk': total_risk,
                'total_value': total_value,
                'heat_percentage': (total_risk / total_value) * 100 if total_value > 0 else 0,
                'sector_exposure': sector_exposure,
                'correlation_risk': correlation_risk,
                'recommendations': recommendations,
                'position_count': len(positions)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio heat: {e}")
            return {
                'total_risk': 0,
                'total_value': 0,
                'heat_percentage': 0,
                'sector_exposure': {},
                'correlation_risk': 0,
                'recommendations': [f"Error calculating portfolio heat: {str(e)}"]
            }
    
    def validate_trade_risk(self, 
                          account_equity: float,
                          position_value: float,
                          dollar_risk: float,
                          existing_positions: List[Dict[str, Any]],
                          symbol: str) -> Dict[str, Any]:
        """
        Validate trade against risk management rules
        
        Args:
            account_equity: Total account equity
            position_value: Proposed position value
            dollar_risk: Proposed dollar risk
            existing_positions: List of existing positions
            symbol: Symbol being traded
            
        Returns:
            Dictionary with validation results
        """
        try:
            violations = []
            warnings = []
            
            # Check position size limit
            position_pct = (position_value / account_equity) * 100
            if position_pct > self.max_position_size * 100:
                violations.append(f"Position size {position_pct:.1f}% exceeds limit {self.max_position_size * 100:.1f}%")
            
            # Check portfolio risk limit
            total_existing_risk = sum(pos.get('dollar_risk', 0) for pos in existing_positions)
            total_risk = total_existing_risk + dollar_risk
            portfolio_risk_pct = (total_risk / account_equity) * 100
            
            if portfolio_risk_pct > self.max_portfolio_risk * 100:
                violations.append(f"Portfolio risk {portfolio_risk_pct:.1f}% exceeds limit {self.max_portfolio_risk * 100:.1f}%")
            
            # Check for duplicate positions
            existing_symbols = [pos.get('symbol', '') for pos in existing_positions]
            if symbol in existing_symbols:
                warnings.append(f"Already have position in {symbol}")
            
            # Check correlation risk
            if len(existing_positions) > 0:
                # Simplified correlation check - in practice, you'd use actual correlation data
                if len(existing_positions) > 5:
                    warnings.append("High number of positions - consider consolidation")
            
            # Check drawdown limit
            # This would require account history data
            
            is_valid = len(violations) == 0
            
            return {
                'is_valid': is_valid,
                'violations': violations,
                'warnings': warnings,
                'position_pct': position_pct,
                'portfolio_risk_pct': portfolio_risk_pct,
                'total_positions': len(existing_positions) + 1
            }
            
        except Exception as e:
            logger.error(f"Error validating trade risk: {e}")
            return {
                'is_valid': False,
                'violations': [f"Error validating trade: {str(e)}"],
                'warnings': [],
                'position_pct': 0,
                'portfolio_risk_pct': 0,
                'total_positions': 0
            }
    
    def generate_risk_report(self, 
                           account_equity: float,
                           positions: List[Dict[str, Any]],
                           recent_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive risk report
        
        Args:
            account_equity: Total account equity
            positions: Current positions
            recent_trades: Recent trade history
            
        Returns:
            Dictionary with comprehensive risk analysis
        """
        try:
            # Calculate portfolio heat
            portfolio_heat = self.calculate_portfolio_heat(positions)
            
            # Calculate performance metrics
            if recent_trades:
                total_trades = len(recent_trades)
                winning_trades = sum(1 for trade in recent_trades if trade.get('pnl', 0) > 0)
                win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
                
                total_pnl = sum(trade.get('pnl', 0) for trade in recent_trades)
                avg_win = sum(trade.get('pnl', 0) for trade in recent_trades if trade.get('pnl', 0) > 0) / max(winning_trades, 1)
                avg_loss = sum(trade.get('pnl', 0) for trade in recent_trades if trade.get('pnl', 0) < 0) / max(total_trades - winning_trades, 1)
            else:
                total_trades = 0
                win_rate = 0
                total_pnl = 0
                avg_win = 0
                avg_loss = 0
            
            # Risk score calculation
            risk_score = 0
            
            # Portfolio heat component
            if portfolio_heat['heat_percentage'] > 10:
                risk_score += 30
            elif portfolio_heat['heat_percentage'] > 5:
                risk_score += 15
            
            # Position concentration component
            if len(positions) > 10:
                risk_score += 20
            elif len(positions) > 5:
                risk_score += 10
            
            # Performance component
            if win_rate < 40:
                risk_score += 25
            elif win_rate < 50:
                risk_score += 15
            
            # Generate recommendations
            recommendations = []
            
            if risk_score > 70:
                recommendations.append("HIGH RISK: Consider reducing position sizes and taking profits")
            elif risk_score > 50:
                recommendations.append("MODERATE RISK: Monitor positions closely")
            else:
                recommendations.append("LOW RISK: Portfolio appears well-managed")
            
            if portfolio_heat['heat_percentage'] > 5:
                recommendations.append("Reduce portfolio heat by closing some positions")
            
            if win_rate < 50 and total_trades > 10:
                recommendations.append("Consider reviewing trading strategy - win rate below 50%")
            
            return {
                'risk_score': min(100, risk_score),
                'portfolio_heat': portfolio_heat,
                'performance_metrics': {
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0
                },
                'recommendations': recommendations,
                'account_equity': account_equity,
                'position_count': len(positions),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            return {
                'risk_score': 100,
                'portfolio_heat': {'heat_percentage': 0},
                'performance_metrics': {},
                'recommendations': [f"Error generating report: {str(e)}"],
                'account_equity': account_equity,
                'position_count': 0,
                'generated_at': datetime.now().isoformat()
            }


def calculate_risk_reward_ratio(entry_price: float, stop_price: float, target_price: float) -> float:
    """
    Calculate risk/reward ratio for a trade
    
    Args:
        entry_price: Entry price
        stop_price: Stop loss price
        target_price: Target price
        
    Returns:
        Risk/reward ratio
    """
    try:
        risk = abs(entry_price - stop_price)
        reward = abs(target_price - entry_price)
        
        if risk <= 0:
            return 0.0
        
        return reward / risk
        
    except Exception as e:
        logger.error(f"Error calculating risk/reward ratio: {e}")
        return 0.0


def calculate_max_drawdown(equity_curve: List[float]) -> Dict[str, float]:
    """
    Calculate maximum drawdown from equity curve
    
    Args:
        equity_curve: List of equity values over time
        
    Returns:
        Dictionary with drawdown metrics
    """
    try:
        if not equity_curve or len(equity_curve) < 2:
            return {'max_drawdown': 0.0, 'max_drawdown_pct': 0.0}
        
        peak = equity_curve[0]
        max_dd = 0.0
        max_dd_pct = 0.0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            
            drawdown = peak - equity
            drawdown_pct = (drawdown / peak) * 100
            
            if drawdown > max_dd:
                max_dd = drawdown
                max_dd_pct = drawdown_pct
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd_pct
        }
        
    except Exception as e:
        logger.error(f"Error calculating max drawdown: {e}")
        return {'max_drawdown': 0.0, 'max_drawdown_pct': 0.0}
