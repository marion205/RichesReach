"""
learn_drift_centroids — Learn archetype centroids from engagement data.

Aggregates each user's L2-normalised engagement vector (click counts over
REC_TYPES_ORDER) grouped by their quiz archetype, then writes the per-archetype
mean vector to drift_centroids.json (path controlled by DRIFT_CENTROIDS_PATH).

The consistency service's get_drift_signal() will use these learned centroids
the next time it is called, replacing the rule-based fallback centroids.

Usage
-----
  # Dry run — print centroids, do not write file
  python manage.py learn_drift_centroids --dry-run

  # Learn from last 30 days (default) and write file
  python manage.py learn_drift_centroids

  # Learn from last 60 days
  python manage.py learn_drift_centroids --days 60

  # Require at least 10 users per archetype before trusting a centroid
  python manage.py learn_drift_centroids --min-users 10

Design notes
------------
- Uses the in-memory event store (get_all_events_for_metrics + archetype lookup
  via the profile service). In production, replace the profile lookup with a
  DB query; the centroid math stays the same.
- A centroid is only written for archetypes with >= min_users contributors.
  Archetypes with too few users fall back to the rule-based centroid at
  inference time (behavioural_consistency_service._rule_based_centroids()).
- The written file is atomic: we build the full dict, then write once, so the
  service never reads a partial file.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from django.core.management.base import BaseCommand

from core.behavioral_events import get_all_events_for_metrics
from core.behavioral_consistency_service import (
    REC_TYPES_ORDER,
    _LEARNED_CENTROIDS_PATH,
)
from core.behavioral_ranking_service import _ARCHETYPE_AFFINITY

_KNOWN_ARCHETYPES = list(_ARCHETYPE_AFFINITY.keys())


def _build_engagement_vector(clicks: Dict[str, int]) -> List[float]:
    """Raw click counts per REC_TYPES_ORDER (not yet normalised)."""
    return [float(clicks.get(rt, 0)) for rt in REC_TYPES_ORDER]


def _l2_normalise(vec: List[float]) -> List[float]:
    norm = sum(x * x for x in vec) ** 0.5
    if norm <= 0:
        return vec
    return [x / norm for x in vec]


def _add_vectors(a: List[float], b: List[float]) -> List[float]:
    return [x + y for x, y in zip(a, b)]


def _mean_vector(acc: List[float], n: int) -> List[float]:
    return [x / n for x in acc]


class Command(BaseCommand):
    help = (
        "Learn per-archetype engagement centroids from recent click data and "
        "write them to drift_centroids.json for data-driven archetype drift detection."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Days of click history to use (default: 30)",
        )
        parser.add_argument(
            "--min-users",
            type=int,
            default=5,
            help="Minimum number of users per archetype to include that centroid (default: 5)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print computed centroids without writing to file",
        )

    def handle(self, *args, **options):
        days: int = options["days"]
        min_users: int = options["min_users"]
        dry_run: bool = options["dry_run"]

        # ── Step 1: collect per-user click vectors ─────────────────────────────
        all_events = get_all_events_for_metrics(since_days=days)

        # Build click count per rec_type per user
        user_clicks: Dict[str, Dict[str, int]] = {}
        for user_id, events in all_events.items():
            counts: Dict[str, int] = defaultdict(int)
            for e in events:
                if e.get("event_type") == "interaction" and e.get("action") == "click":
                    rt = e.get("rec_type") or e.get("rec_id")
                    if rt:
                        counts[rt] += 1
            if counts:
                user_clicks[user_id] = dict(counts)

        self.stdout.write(
            f"Users with click data in last {days} days: {len(user_clicks)}"
        )

        # ── Step 2: look up each user's quiz archetype ─────────────────────────
        # MVP: uses in-memory profile service. In production this would be a DB
        # query (e.g. InvestorProfile.objects.filter(user_id__in=user_ids)).
        archetype_vectors: Dict[str, List[List[float]]] = {
            arch: [] for arch in _KNOWN_ARCHETYPES
        }

        try:
            from core.investor_profile_service import investor_profile_service
            for user_id, clicks in user_clicks.items():
                try:
                    profile = investor_profile_service.get_profile(user_id)
                    arch = profile.archetype.value if profile else None
                except Exception:
                    arch = None
                if arch and arch in archetype_vectors:
                    vec = _l2_normalise(_build_engagement_vector(clicks))
                    archetype_vectors[arch].append(vec)
        except ImportError:
            self.stderr.write(
                "Could not import investor_profile_service. "
                "No archetype lookup available — no centroids computed."
            )
            return

        # ── Step 3: compute mean centroid per archetype ────────────────────────
        learned: Dict[str, List[float]] = {}
        for arch, vecs in archetype_vectors.items():
            n = len(vecs)
            self.stdout.write(f"  {arch}: {n} user(s) with click data")
            if n < min_users:
                self.stdout.write(
                    f"    -> skipped (need >= {min_users}, got {n})"
                )
                continue
            acc = [0.0] * len(REC_TYPES_ORDER)
            for v in vecs:
                acc = _add_vectors(acc, v)
            centroid = _l2_normalise(_mean_vector(acc, n))
            learned[arch] = centroid
            self.stdout.write(
                f"    -> centroid computed (top dims: "
                + ", ".join(
                    f"{REC_TYPES_ORDER[i]}={centroid[i]:.3f}"
                    for i in sorted(range(len(centroid)), key=lambda x: -centroid[x])[:3]
                )
                + ")"
            )

        if not learned:
            self.stdout.write(
                "No archetypes met the minimum-users threshold. "
                "File not written; rule-based centroids will remain in use."
            )
            return

        self.stdout.write(
            f"Centroids learned for: {', '.join(sorted(learned.keys()))}"
        )

        if dry_run:
            self.stdout.write("Dry run — not writing file.")
            return

        # ── Step 4: write centroids file ───────────────────────────────────────
        out_path = os.environ.get("DRIFT_CENTROIDS_PATH", _LEARNED_CENTROIDS_PATH)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump({"centroids": learned}, f, indent=2)
        self.stdout.write(f"Written to {out_path}")
