"""
Feedback loop: compute CTR (rule vs ML) from shadow data and optionally update ranking weights.
Run daily via cron or Celery beat. Requires shadow impressions and interactions with position_rule/position_ml.
"""

from django.core.management.base import BaseCommand

from core.behavioral_events import (
    get_shadow_impressions_for_metrics,
    get_all_events_for_metrics,
)
from core.ranking_config import get_ranking_weights, set_ranking_weights, invalidate_weights_cache


class Command(BaseCommand):
    help = "Compute rule vs ML CTR from shadow data and optionally update ranking weights."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14, help="Days of data to use")
        parser.add_argument("--dry-run", action="store_true", help="Only compute metrics, do not write weights")
        parser.add_argument("--update-weights", action="store_true", help="Update weights file from metrics")

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        update_weights = options["update_weights"]

        shadows = get_shadow_impressions_for_metrics(since_days=days)
        all_events = get_all_events_for_metrics(since_days=days)

        # Flatten to all interactions with position_rule / position_ml
        clicks_rule = {1: 0, 2: 0, 3: 0}
        clicks_ml = {1: 0, 2: 0, 3: 0}
        for user_id, events in all_events.items():
            for e in events:
                if e.get("event_type") != "interaction" or e.get("action") != "click":
                    continue
                pr = e.get("position_rule")
                pm = e.get("position_ml")
                if pr in (1, 2, 3):
                    clicks_rule[pr] += 1
                if pm in (1, 2, 3):
                    clicks_ml[pm] += 1

        n_shadows = len(shadows)
        if n_shadows == 0:
            self.stdout.write("No shadow impressions in the last %s days." % days)
            return

        imp_rule_1 = imp_rule_2 = imp_rule_3 = n_shadows
        imp_ml_1 = imp_ml_2 = imp_ml_3 = n_shadows

        ctr_rule_1 = clicks_rule[1] / imp_rule_1 if imp_rule_1 else 0
        ctr_rule_2 = clicks_rule[2] / imp_rule_2 if imp_rule_2 else 0
        ctr_rule_3 = clicks_rule[3] / imp_rule_3 if imp_rule_3 else 0
        ctr_ml_1 = clicks_ml[1] / imp_ml_1 if imp_ml_1 else 0
        ctr_ml_2 = clicks_ml[2] / imp_ml_2 if imp_ml_2 else 0
        ctr_ml_3 = clicks_ml[3] / imp_ml_3 if imp_ml_3 else 0

        total_clicks_rule = clicks_rule[1] + clicks_rule[2] + clicks_rule[3]
        total_clicks_ml = clicks_ml[1] + clicks_ml[2] + clicks_ml[3]
        total_impressions = n_shadows * 3
        ctr_rule_avg = total_clicks_rule / total_impressions if total_impressions else 0
        ctr_ml_avg = total_clicks_ml / total_impressions if total_impressions else 0

        self.stdout.write(
            "Shadow metrics (last %s days): impressions=%s" % (days, n_shadows)
        )
        self.stdout.write(
            "  Rule CTR pos1=%.3f pos2=%.3f pos3=%.3f avg=%.3f"
            % (ctr_rule_1, ctr_rule_2, ctr_rule_3, ctr_rule_avg)
        )
        self.stdout.write(
            "  ML   CTR pos1=%.3f pos2=%.3f pos3=%.3f avg=%.3f"
            % (ctr_ml_1, ctr_ml_2, ctr_ml_3, ctr_ml_avg)
        )
        if ctr_rule_avg > 0:
            lift = (ctr_ml_avg - ctr_rule_avg) / ctr_rule_avg
            self.stdout.write("  ML lift vs rule: %.1f%%" % (lift * 100))

        if not update_weights or dry_run:
            return

        current = get_ranking_weights()
        # Simple update: if ML beats rule by >5%, nudge weights toward slightly more archetype (personalization)
        if ctr_rule_avg > 0 and (ctr_ml_avg - ctr_rule_avg) / ctr_rule_avg > 0.05:
            new_weights = {
                "recency": current.get("recency", 0.4),
                "archetype": min(0.45, current.get("archetype", 0.3) + 0.05),
                "popularity": max(0.1, current.get("popularity", 0.2) - 0.02),
                "urgency": current.get("urgency", 0.1),
            }
            s = sum(new_weights.values())
            new_weights = {k: round(v / s, 2) for k, v in new_weights.items()}
            set_ranking_weights(new_weights)
            invalidate_weights_cache()
            self.stdout.write("Updated weights: %s" % new_weights)
        else:
            self.stdout.write("No weight update (insufficient lift).")
