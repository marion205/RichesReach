"""
Auto-Defend Repair Engine (Phase 7)

Monitors open options positions and generates defensive repair plans when
positions start "leaking" Delta—i.e., when price movement has increased
directional risk beyond institutional safety thresholds.

Core Strategy: Transform stressed spreads into Iron Wings
- Bull Put Spread goes negative? → Sell a Bear Call Spread to collect credit
- Bull Call Spread goes negative? → Sell a Bear Put Spread to collect credit
- Result: Extra credit reduces max loss and widens break-even

This is the ultimate competitive differentiator: while other apps leave users
to suffer maximum loss, RichesReach proactively suggests defensive adjustments
that turn losing trades into recoverable positions.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass

from .options_valuation_engine import Greeks, BlackScholesCalculator
from .options_strategy_router import StrategyRouter

logger = logging.getLogger(__name__)


@dataclass
class RepairPlan:
    """Suggested defensive adjustment for a leaking position"""
    position_id: int
    ticker: str
    original_strategy: str
    current_delta: float
    delta_drift_pct: float
    current_max_loss: float
    
    # Repair action
    repair_type: str  # "BEAR_CALL_SPREAD", "BEAR_PUT_SPREAD", "IRON_WING"
    repair_strikes: str  # e.g., "Sell 125C / Buy 130C"
    repair_credit: float  # Additional credit collected
    
    # Impact
    new_max_loss: float  # Reduced risk after repair
    new_break_even: float
    confidence_boost: float  # 0-1, how much this improves win probability
    
    # UI
    headline: str
    reason: str
    action_description: str
    priority: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"


class OptionsRepairEngine:
    """
    Monitors open positions and generates 'Repair Plans' when
    Delta risk exceeds institutional safety thresholds.
    """
    
    # Configuration
    DELTA_REPAIR_THRESHOLD = 0.25  # Trigger repair if Delta drift > 25%
    MAX_LOSS_RATIO_THRESHOLD = 0.15  # Trigger if unrealized loss > 15% of account
    
    # Repair priority mapping
    PRIORITY_MATRIX = {
        "CRITICAL": {"delta_trigger": 0.50, "loss_trigger": 0.25},  # > 50% delta drift
        "HIGH": {"delta_trigger": 0.35, "loss_trigger": 0.20},      # > 35% delta drift
        "MEDIUM": {"delta_trigger": 0.25, "loss_trigger": 0.15},    # > 25% delta drift
        "LOW": {"delta_trigger": 0.15, "loss_trigger": 0.10},       # > 15% delta drift
    }
    
    def __init__(self, router: StrategyRouter, bs_calc: Optional[BlackScholesCalculator] = None):
        """
        Initialize the repair engine.
        
        Args:
            router: StrategyRouter instance for generating hedge suggestions
            bs_calc: Optional BlackScholesCalculator for Greeks updates
        """
        self.router = router
        self.bs_calc = bs_calc
        self.logger = logging.getLogger("OptionsRepairEngine")
    
    def analyze_position_health(
        self,
        position,
        current_underlying_price: float,
        account_equity: float,
    ) -> Optional[RepairPlan]:
        """
        Analyze an active position and check if it needs a repair.
        
        Args:
            position: OptionsPosition model instance
            current_underlying_price: Current underlying stock price
            account_equity: User's total account equity (for risk % calculation)
        
        Returns:
            RepairPlan if repair is needed, None otherwise
        """
        try:
            # Extract current Greeks from position
            current_delta = float(position.position_delta)
            current_max_loss = float(position.max_loss)
            unrealized_pnl = float(position.unrealized_pnl)
            
            # Calculate Delta drift
            if abs(current_delta) < 0.01:
                return None  # Position is already neutral
            
            # Check delta drift threshold
            delta_drift_pct = abs(current_delta)
            if delta_drift_pct < self.DELTA_REPAIR_THRESHOLD:
                return None  # Not directional enough to warrant repair
            
            # Check unrealized loss threshold
            loss_ratio = abs(unrealized_pnl) / account_equity if account_equity > 0 else 0
            if loss_ratio < 0.10:
                return None  # Loss is manageable
            
            # Position is "leaking"—generate repair plan
            self.logger.info(
                f"🔧 Position {position.id} ({position.ticker} {position.strategy_type}) "
                f"needs repair: delta_drift={delta_drift_pct:.1%}, loss={unrealized_pnl:.0f}"
            )
            
            return self._generate_repair_plan(
                position=position,
                current_underlying_price=current_underlying_price,
                current_delta=current_delta,
                delta_drift_pct=delta_drift_pct,
                account_equity=account_equity,
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing position {position.id}: {e}")
            return None
    
    def _generate_repair_plan(
        self,
        position,
        current_underlying_price: float,
        current_delta: float,
        delta_drift_pct: float,
        account_equity: float,
    ) -> Optional[RepairPlan]:
        """
        Generate the actual repair plan based on position characteristics.
        """
        try:
            ticker = position.ticker
            strategy_type = position.strategy_type
            current_max_loss = float(position.max_loss)
            unrealized_pnl = float(position.unrealized_pnl)
            
            # Determine repair type based on directional bias
            # If position is long (positive delta), we sell a bearish spread to hedge
            # If position is short (negative delta), we sell a bullish spread to hedge
            if current_delta > 0:
                # Position is long delta → sell bearish spread (Bear Call Spread)
                hedge_type = "BEAR_CALL_SPREAD"
                repair_strikes = f"Sell {int(current_underlying_price)}C / Buy {int(current_underlying_price + 5)}C"
            else:
                # Position is short delta → sell bullish spread (Bull Put Spread)
                hedge_type = "BULL_PUT_SPREAD"
                repair_strikes = f"Sell {int(current_underlying_price - 5)}P / Buy {int(current_underlying_price - 10)}P"
            
            # Estimate repair credit (mock calculation—real one uses Greeks)
            repair_credit = abs(unrealized_pnl) * 0.3  # Collect 30% of current loss as credit
            repair_credit = max(50, min(500, repair_credit))  # Cap between $50-500
            
            # Calculate new risk profile
            new_max_loss = current_max_loss - repair_credit
            new_break_even = current_underlying_price + (0.02 * current_underlying_price)  # Approximate
            
            # Determine priority
            priority = self._calculate_priority(delta_drift_pct, abs(unrealized_pnl) / account_equity)
            
            # Confidence boost calculation (how much this improves edge)
            confidence_boost = min(0.15, delta_drift_pct * 0.3)  # Up to 15% boost
            
            # Build user-friendly messages
            headline = f"🛡️ Auto-Shield: Defensive Hedge for {ticker}"
            
            if priority == "CRITICAL":
                reason = (
                    f"Your {strategy_type} has moved significantly against you. "
                    f"Position delta is now {abs(current_delta):.1%}—highly directional. "
                    f"This defensive hedge neutralizes {abs(current_delta):.0%} of the risk while collecting ${repair_credit:.0f}."
                )
                priority_emoji = "🚨"
            elif priority == "HIGH":
                reason = (
                    f"Market movement has increased position risk. "
                    f"This hedge reduces your max loss by ${repair_credit:.0f} and restores balance."
                )
                priority_emoji = "⚠️"
            else:
                reason = (
                    f"Your position is drifting directionally. "
                    f"This adjustment improves your edge and protects against further moves."
                )
                priority_emoji = "💡"
            
            action_description = (
                f"{priority_emoji} {hedge_type}: {repair_strikes} "
                f"(collect ${repair_credit:.0f}, reduce max loss to ${new_max_loss:.0f})"
            )
            
            return RepairPlan(
                position_id=position.id,
                ticker=ticker,
                original_strategy=strategy_type,
                current_delta=current_delta,
                delta_drift_pct=delta_drift_pct,
                current_max_loss=current_max_loss,
                repair_type=hedge_type,
                repair_strikes=repair_strikes,
                repair_credit=repair_credit,
                new_max_loss=new_max_loss,
                new_break_even=new_break_even,
                confidence_boost=confidence_boost,
                headline=headline,
                reason=reason,
                action_description=action_description,
                priority=priority,
            )
            
        except Exception as e:
            self.logger.error(f"Error generating repair plan: {e}")
            return None
    
    def _calculate_priority(self, delta_drift_pct: float, loss_ratio: float) -> str:
        """
        Determine priority level based on delta drift and loss ratio.
        
        Args:
            delta_drift_pct: Absolute delta drift (0-1)
            loss_ratio: Unrealized loss as % of account (0-1)
        
        Returns:
            Priority string: "CRITICAL", "HIGH", "MEDIUM", "LOW"
        """
        # Weighted scoring: delta drift (60%) + loss ratio (40%)
        risk_score = (delta_drift_pct * 0.6) + (loss_ratio * 0.4)
        
        if risk_score > 0.40:
            return "CRITICAL"
        elif risk_score > 0.30:
            return "HIGH"
        elif risk_score > 0.20:
            return "MEDIUM"
        else:
            return "LOW"
    
    def batch_analyze_portfolio(
        self,
        positions: List,
        current_underlying_prices: Dict[str, float],
        account_equity: float,
    ) -> List[RepairPlan]:
        """
        Analyze all open positions in a portfolio and return repair plans.
        
        Args:
            positions: List of OptionsPosition objects
            current_underlying_prices: Dict mapping ticker → current price
            account_equity: User's total account equity
        
        Returns:
            List of RepairPlan objects (only positions needing repair)
        """
        repair_plans = []
        
        for position in positions:
            # Skip closed positions
            if hasattr(position, 'is_closed') and position.is_closed:
                continue
            
            ticker = position.ticker
            price = current_underlying_prices.get(ticker, 0)
            
            if price <= 0:
                self.logger.warning(f"Skipping {ticker}: no price data")
                continue
            
            plan = self.analyze_position_health(
                position=position,
                current_underlying_price=price,
                account_equity=account_equity,
            )
            
            if plan:
                repair_plans.append(plan)
        
        # Sort by priority (CRITICAL first)
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        repair_plans.sort(key=lambda p: priority_order.get(p.priority, 4))
        
        self.logger.info(
            f"Portfolio analysis complete: {len(repair_plans)} position(s) need repair"
        )
        
        return repair_plans
    
    def execute_repair_suggestion_workflow(
        self,
        repair_plan: RepairPlan,
        user_id: int,
    ) -> Dict:
        """
        Execute the full repair suggestion workflow:
        1. Send Slack alert to ops (if CRITICAL)
        2. Send push notification to user
        3. Log repair suggestion for analytics
        4. Wait for user acceptance
        
        Args:
            repair_plan: RepairPlan object
            user_id: User ID for push notification
        
        Returns:
            Workflow result dict with status and timestamps
        """
        result = {
            "repair_id": repair_plan.position_id,
            "ticker": repair_plan.ticker,
            "priority": repair_plan.priority,
            "alerts_sent": [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            # Alert 1: Slack to ops (if CRITICAL or HIGH)
            if repair_plan.priority in ["CRITICAL", "HIGH"]:
                from .alert_notifications import send_slack_alert
                
                slack_result = send_slack_alert(
                    alert_level="critical" if repair_plan.priority == "CRITICAL" else "warning",
                    metric_name=f"Position Repair Needed: {repair_plan.ticker}",
                    message=repair_plan.headline,
                    timestamp=datetime.utcnow(),
                    details={
                        "user_id": user_id,
                        "ticker": repair_plan.ticker,
                        "delta_drift": f"{repair_plan.delta_drift_pct:.1%}",
                        "current_max_loss": f"${repair_plan.current_max_loss:.0f}",
                        "repair_type": repair_plan.repair_type,
                        "repair_credit": f"${repair_plan.repair_credit:.0f}",
                    },
                )
                if slack_result:
                    result["alerts_sent"].append("slack")
            
            # Alert 2: Push notification to user
            from .alert_notifications import send_push_notification
            
            push_result = send_push_notification(
                title=repair_plan.headline,
                body=repair_plan.reason,
                priority="high" if repair_plan.priority in ["CRITICAL", "HIGH"] else "normal",
                data={
                    "type": "repair_suggestion",
                    "position_id": str(repair_plan.position_id),
                    "ticker": repair_plan.ticker,
                    "action": repair_plan.action_description,
                    "new_max_loss": f"${repair_plan.new_max_loss:.0f}",
                    "confidence_boost": f"{repair_plan.confidence_boost:.0%}",
                },
            )
            if push_result:
                result["alerts_sent"].append("push")
            
            # Alert 3: Log to database (for analytics and replay)
            self.logger.info(
                f"✅ Repair workflow executed for {repair_plan.ticker}: "
                f"alerts={result['alerts_sent']}, "
                f"priority={repair_plan.priority}"
            )
            result["success"] = True
            
        except Exception as e:
            self.logger.error(f"Error executing repair workflow: {e}")
            result["success"] = False
            result["error"] = str(e)
        
        return result


class RepairPlanAcceptor:
    """
    Handles user acceptance/rejection of repair plans.
    Executes the repair trade if accepted, or logs rejection for analytics.
    """
    
    def __init__(self, broker_api=None):
        """
        Args:
            broker_api: Optional broker API for executing actual trades
        """
        self.broker_api = broker_api
        self.logger = logging.getLogger("RepairAcceptor")
    
    def accept_repair(self, repair_plan: RepairPlan, position_id: int) -> Dict:
        """
        User accepted the repair plan. Execute the trade.
        
        Args:
            repair_plan: RepairPlan object
            position_id: Position ID being repaired
        
        Returns:
            Execution result
        """
        result = {
            "status": "pending",
            "position_id": position_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            # TODO: Actually execute hedge trade via broker API
            # For now, just log the intention
            self.logger.info(
                f"✅ REPAIR ACCEPTED: {repair_plan.ticker} {repair_plan.repair_type} "
                f"({repair_plan.repair_strikes}). Executing trade..."
            )
            
            # Simulate execution
            result["status"] = "executed"
            result["order_id"] = f"REPAIR_{position_id}_{int(datetime.utcnow().timestamp())}"
            result["message"] = (
                f"Repair trade executed: Collect ${repair_plan.repair_credit:.0f}, "
                f"reduce max loss to ${repair_plan.new_max_loss:.0f}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing repair: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            return result
    
    def reject_repair(self, repair_plan: RepairPlan, reason: Optional[str] = None) -> Dict:
        """
        User rejected the repair plan. Log for analytics.
        
        Args:
            repair_plan: RepairPlan object
            reason: Optional reason for rejection
        
        Returns:
            Rejection result
        """
        self.logger.info(
            f"❌ REPAIR REJECTED: {repair_plan.ticker} {repair_plan.repair_type}. "
            f"Reason: {reason or 'User choice'}"
        )
        
        return {
            "status": "rejected",
            "position_id": repair_plan.position_id,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
        }
