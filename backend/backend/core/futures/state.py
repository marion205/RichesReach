"""
Order State Machine
==================
Simple state machine for order lifecycle management.
"""

from enum import Enum
from typing import Set, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OrderState(Enum):
    """Order state enumeration"""
    NEW = "NEW"
    SUBMITTED = "SUBMITTED"
    PARTIAL = "PARTIAL_FILL"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


# Valid state transitions
VALID_TRANSITIONS: dict[OrderState, Set[OrderState]] = {
    OrderState.NEW: {OrderState.SUBMITTED, OrderState.CANCELED, OrderState.REJECTED},
    OrderState.SUBMITTED: {
        OrderState.PARTIAL,
        OrderState.FILLED,
        OrderState.CANCELED,
        OrderState.REJECTED,
        OrderState.EXPIRED,
    },
    OrderState.PARTIAL: {
        OrderState.FILLED,
        OrderState.CANCELED,
        OrderState.REJECTED,
        OrderState.EXPIRED,
    },
}


def can_transition(src: OrderState, dst: OrderState) -> bool:
    """
    Check if state transition is valid.
    
    Args:
        src: Current state
        dst: Target state
        
    Returns:
        True if transition is allowed
    """
    valid_destinations = VALID_TRANSITIONS.get(src, set())
    return dst in valid_destinations


class OrderStateMachine:
    """Manages order state transitions"""
    
    def __init__(self, order_id: str, initial_state: OrderState = OrderState.NEW):
        self.order_id = order_id
        self.state = initial_state
        self.history: list[tuple[datetime, OrderState, Optional[str]]] = []
        self._record_transition(initial_state, "Initial state")
    
    def transition(self, new_state: OrderState, reason: Optional[str] = None) -> bool:
        """
        Attempt to transition to new state.
        
        Args:
            new_state: Target state
            reason: Optional reason for transition
            
        Returns:
            True if transition succeeded
        """
        if not can_transition(self.state, new_state):
            logger.warning(
                f"Invalid transition for {self.order_id}: {self.state.value} -> {new_state.value}"
            )
            return False
        
        old_state = self.state
        self.state = new_state
        self._record_transition(new_state, reason)
        
        logger.info(f"Order {self.order_id}: {old_state.value} -> {new_state.value} ({reason})")
        return True
    
    def _record_transition(self, state: OrderState, reason: Optional[str]):
        """Record state transition in history"""
        self.history.append((datetime.now(), state, reason))
    
    def is_final(self) -> bool:
        """Check if order is in final state (no more transitions)"""
        return self.state in {
            OrderState.FILLED,
            OrderState.CANCELED,
            OrderState.REJECTED,
            OrderState.EXPIRED,
        }
    
    def get_history(self) -> list[dict]:
        """Get transition history"""
        return [
            {
                "timestamp": ts.isoformat(),
                "state": state.value,
                "reason": reason,
            }
            for ts, state, reason in self.history
        ]

