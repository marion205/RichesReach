"""
Repair Outcome Tracker & Post-Mortem Generator

Closes the feedback loop for the Trust Engine:
1. Checks executed repairs after 7+ days
2. Compares expected vs. actual APY delta
3. Classifies outcomes (beneficial / neutral / underperformed)
4. Generates post-mortem reports with "what we learned"

Part of Trust-First Framework: Gap 2 (Outcome Tracking) + Gap 7 (Post-Mortems)
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg

logger = logging.getLogger(__name__)

# How many days to wait before evaluating a repair outcome
OUTCOME_EVALUATION_DELAY_DAYS = 7

# Outcome classification thresholds
BENEFICIAL_THRESHOLD = 0.5   # actual >= 50% of expected = beneficial
NEUTRAL_RANGE = 0.20         # within 20% of zero = neutral


class RepairOutcomeTracker:
    """
    Evaluates the actual outcomes of executed repairs and generates
    post-mortem reports. Runs as a periodic Celery task (every 12h).
    """

    def check_pending_outcomes(self) -> Dict[str, Any]:
        """
        Find all executed repairs that haven't been evaluated yet
        and are old enough for meaningful comparison.

        Returns:
            dict with: checked, beneficial, neutral, underperformed, errors
        """
        try:
            from .defi_models import DeFiRepairDecision

            cutoff = timezone.now() - timedelta(days=OUTCOME_EVALUATION_DELAY_DAYS)

            # Find repairs that:
            # - Were executed (not just suggested/dismissed)
            # - Haven't been checked yet
            # - Are old enough (7+ days since execution)
            pending = DeFiRepairDecision.objects.filter(
                decision_type='executed',
                outcome_checked_at__isnull=True,
                executed_at__isnull=False,
                executed_at__lte=cutoff,
            ).select_related('from_pool', 'to_pool', 'user')

            stats = {
                'checked': 0,
                'beneficial': 0,
                'neutral': 0,
                'underperformed': 0,
                'errors': 0,
            }

            for decision in pending:
                try:
                    result = self.evaluate_outcome(decision)
                    status = result.get('outcome_status', 'neutral')
                    stats['checked'] += 1
                    stats[status] = stats.get(status, 0) + 1

                except Exception as e:
                    logger.warning(
                        f"Error evaluating outcome for repair {decision.repair_id}: {e}"
                    )
                    stats['errors'] += 1

            logger.info(f"Repair outcome check complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error in repair outcome tracker: {e}", exc_info=True)
            return {'error': str(e)}

    def evaluate_outcome(self, decision) -> Dict[str, Any]:
        """
        Evaluate the actual outcome of an executed repair.

        Compares:
        - Target pool's rolling APY since execution (what happened)
        - Source pool's rolling APY since execution (what would have happened)

        Updates the DeFiRepairDecision record with:
        - actual_apy_delta
        - outcome_status
        - outcome_report (full post-mortem JSON)
        - outcome_checked_at
        """
        from .defi_models import YieldSnapshot

        now = timezone.now()
        executed_at = decision.executed_at

        # Get target pool APY since execution
        target_apy = self._get_avg_apy_since(
            decision.to_pool_id, executed_at
        )

        # Get source pool APY since execution (counterfactual)
        source_apy = self._get_avg_apy_since(
            decision.from_pool_id, executed_at
        )

        # Calculate actual delta
        if target_apy is not None and source_apy is not None:
            actual_apy_delta = (target_apy - source_apy) / 100.0  # Convert to decimal
        else:
            actual_apy_delta = 0.0

        # Classify outcome
        expected = decision.expected_apy_delta or 0.0
        outcome_status = self._classify_outcome(actual_apy_delta, expected)

        # Generate post-mortem report
        outcome_report = self.generate_post_mortem(
            decision=decision,
            target_apy=target_apy,
            source_apy=source_apy,
            actual_apy_delta=actual_apy_delta,
            outcome_status=outcome_status,
        )

        # Update the decision record
        decision.actual_apy_delta = actual_apy_delta
        decision.outcome_status = outcome_status
        decision.outcome_report = outcome_report
        decision.outcome_checked_at = now
        decision.save(update_fields=[
            'actual_apy_delta',
            'outcome_status',
            'outcome_report',
            'outcome_checked_at',
        ])

        logger.info(
            f"Repair outcome evaluated: repair_id={decision.repair_id} "
            f"expected={expected:.4f} actual={actual_apy_delta:.4f} "
            f"status={outcome_status}"
        )

        return {
            'repair_id': decision.repair_id,
            'actual_apy_delta': actual_apy_delta,
            'expected_apy_delta': expected,
            'outcome_status': outcome_status,
            'outcome_report': outcome_report,
        }

    def generate_post_mortem(
        self,
        decision,
        target_apy: Optional[float],
        source_apy: Optional[float],
        actual_apy_delta: float,
        outcome_status: str,
    ) -> Dict[str, Any]:
        """
        Generate a structured post-mortem report.

        Includes:
        - What we expected vs. what happened
        - Before/after metrics
        - Classification + narrative
        - Lessons learned
        """
        expected = decision.expected_apy_delta or 0.0
        days_elapsed = 0
        if decision.executed_at:
            days_elapsed = (timezone.now() - decision.executed_at).days

        # Generate narrative
        from .proof_narrator import get_proof_narrator
        narrator = get_proof_narrator()

        from_vault = ''
        to_vault = ''
        if decision.from_pool:
            protocol = ''
            if decision.from_pool.protocol:
                protocol = decision.from_pool.protocol.name or ''
            from_vault = f"{protocol} {decision.from_pool.symbol}".strip()
        if decision.to_pool:
            protocol = ''
            if decision.to_pool.protocol:
                protocol = decision.to_pool.protocol.name or ''
            to_vault = f"{protocol} {decision.to_pool.symbol}".strip()

        narrative = narrator.narrate_outcome(
            expected_apy_delta=expected,
            actual_apy_delta=actual_apy_delta,
            outcome_status=outcome_status,
            days_since_repair=days_elapsed,
            from_vault=from_vault,
            to_vault=to_vault,
        )

        # Determine what we learned
        lessons = self._derive_lessons(
            outcome_status, expected, actual_apy_delta,
            target_apy, source_apy,
        )

        return {
            'evaluation_date': timezone.now().isoformat(),
            'days_since_repair': days_elapsed,
            'expected_apy_delta': round(expected, 4),
            'actual_apy_delta': round(actual_apy_delta, 4),
            'delta_accuracy': round(actual_apy_delta - expected, 4),
            'target_pool_avg_apy': round(target_apy, 2) if target_apy else None,
            'source_pool_avg_apy': round(source_apy, 2) if source_apy else None,
            'outcome_status': outcome_status,
            'narrative': narrative,
            'lessons_learned': lessons,
            'from_vault': from_vault,
            'to_vault': to_vault,
            'policy_version': decision.policy_version or '',
        }

    def _get_avg_apy_since(
        self, pool_id: Optional[int], since: Any,
    ) -> Optional[float]:
        """Get average APY for a pool since a given datetime."""
        if not pool_id or not since:
            return None

        try:
            from .defi_models import YieldSnapshot

            result = YieldSnapshot.objects.filter(
                pool_id=pool_id,
                timestamp__gte=since,
            ).aggregate(avg_apy=Avg('apy_total'))

            avg = result.get('avg_apy')
            return float(avg) if avg is not None else None

        except Exception as e:
            logger.warning(f"Error getting avg APY for pool {pool_id}: {e}")
            return None

    def _classify_outcome(
        self, actual: float, expected: float,
    ) -> str:
        """
        Classify the repair outcome.

        - beneficial: actual delta >= 50% of expected delta
        - underperformed: actual delta < 0 or far below expected
        - neutral: everything in between
        """
        if expected > 0:
            if actual >= expected * BENEFICIAL_THRESHOLD:
                return 'beneficial'
            elif actual < -abs(expected) * NEUTRAL_RANGE:
                return 'underperformed'
            else:
                return 'neutral'
        else:
            # Expected was 0 or negative (defensive move)
            if actual >= 0:
                return 'beneficial'
            elif actual < -0.01:  # Worse by more than 1%
                return 'underperformed'
            else:
                return 'neutral'

    def _derive_lessons(
        self,
        outcome_status: str,
        expected: float,
        actual: float,
        target_apy: Optional[float],
        source_apy: Optional[float],
    ) -> List[str]:
        """
        Generate "what we learned" from this repair.
        These feed back into system improvement.
        """
        lessons = []

        if outcome_status == 'beneficial':
            lessons.append(
                "Risk-adjusted rotation improved portfolio returns."
            )
            if actual > expected * 1.5:
                lessons.append(
                    "Actual improvement exceeded expectations — "
                    "the target vault outperformed projections."
                )
        elif outcome_status == 'underperformed':
            if actual < 0:
                lessons.append(
                    "The target vault underperformed the source vault. "
                    "APY conditions changed after the rotation."
                )
            lessons.append(
                "Consider longer observation windows before triggering "
                "rotations when APY improvement is marginal."
            )
            if target_apy is not None and source_apy is not None:
                if source_apy > target_apy:
                    lessons.append(
                        "The original vault recovered after the move. "
                        "Short-term APY dips may be temporary."
                    )
        else:  # neutral
            lessons.append(
                "The repair had minimal APY impact. "
                "Risk reduction was the primary benefit."
            )

        return lessons


def check_repair_outcomes() -> Dict[str, Any]:
    """
    Public entry point for the Celery task.
    Evaluates all pending repair outcomes.
    """
    tracker = RepairOutcomeTracker()
    return tracker.check_pending_outcomes()
