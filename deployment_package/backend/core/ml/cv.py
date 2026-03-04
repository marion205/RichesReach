"""
cv.py
=====
Walk-forward cross-validation with embargo for time-series financial data.

Why not sklearn's TimeSeriesSplit directly?
-------------------------------------------
sklearn's TimeSeriesSplit handles the ordering, but it doesn't enforce an
*embargo* — a gap between the end of the training set and the start of the
test set.

Without an embargo, the last `horizon` rows of the training set have
forward-return labels that overlap with the test set's feature dates.
For a 20-day forward return this means the last 20 training rows "know"
prices that appear in the first 20 test rows → leakage.

The embargo removes those rows from training, eliminating the overlap.

Scheme: expanding window
------------------------
Each successive fold expands the training set rather than sliding a fixed
window.  This makes better use of older data and mimics how a real
quant would retrain — never discarding validated history.

    Fold 1: Train [0..T1-embargo]            → Test [T1..T2]
    Fold 2: Train [0..T2-embargo]            → Test [T2..T3]
    ...

Usage
-----
    from ml.cv import walk_forward_splits
    for train_idx, test_idx in walk_forward_splits(len(X), n_splits=4, embargo_periods=20):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        ...
"""

from __future__ import annotations

import logging
from typing import Iterator

import numpy as np
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger(__name__)

# Minimum training rows required before a fold is usable
_MIN_TRAIN_ROWS = 100


def walk_forward_splits(
    n: int,
    n_splits: int = 4,
    embargo_periods: int = 20,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """
    Generate (train_indices, test_indices) pairs for walk-forward CV.

    Parameters
    ----------
    n : int
        Total number of observations (rows in X and y).
    n_splits : int
        Number of folds.  More folds → better estimate of OOS performance,
        but each fold's test set is smaller.  4–5 is typical.
    embargo_periods : int
        Number of rows to drop from the *end* of each training fold.
        Should equal the target horizon (e.g. 20 for a 20-day forward return)
        to ensure no target-period overlap between train and test.

    Yields
    ------
    (train_idx, test_idx) : tuple[np.ndarray, np.ndarray]
        Integer positional indices (suitable for .iloc[]).
        Guaranteed: max(train_idx) + embargo_periods < min(test_idx)
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)

    for fold, (train_idx, test_idx) in enumerate(tscv.split(range(n))):
        # Apply embargo: drop the last `embargo_periods` rows from training.
        # These rows have forward-return labels that overlap with test dates.
        embargoed_train = train_idx[:-embargo_periods] if len(train_idx) > embargo_periods else train_idx

        if len(embargoed_train) < _MIN_TRAIN_ROWS:
            logger.warning(
                "Fold %d: only %d training rows after embargo — skipping (need %d)",
                fold + 1, len(embargoed_train), _MIN_TRAIN_ROWS,
            )
            continue

        # Sanity check: ensure no overlap
        assert embargoed_train[-1] < test_idx[0], (
            f"Fold {fold+1}: embargo insufficient — train[-1]={embargoed_train[-1]} "
            f">= test[0]={test_idx[0]}"
        )

        logger.debug(
            "Fold %d: train rows %d→%d (%d rows), test rows %d→%d (%d rows)",
            fold + 1,
            embargoed_train[0], embargoed_train[-1], len(embargoed_train),
            test_idx[0], test_idx[-1], len(test_idx),
        )

        yield embargoed_train, test_idx
