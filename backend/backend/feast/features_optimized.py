"""
Optimized Feast Feature Views
==============================
Feature views for ML inference with TTL-based caching.

These features are served from Redis (online) and computed from Postgres (offline).
"""

from feast import (
    Entity,
    FeatureView,
    Field,
    FileSource,
    ValueType,
)
from datetime import timedelta
from typing import Optional
import os


# Entities
user_entity = Entity(
    name="user_id",
    join_keys=["user_id"],
    description="User identifier",
    value_type=ValueType.INT64,
)

ticker_entity = Entity(
    name="ticker",
    join_keys=["ticker"],
    description="Stock ticker symbol",
    value_type=ValueType.STRING,
)


# Market State Features (15 min TTL - fast changing)
market_state_source = FileSource(
    # In production, replace with PostgresSource pointing to your market_data table
    path="s3://richesreach-feast/offline/market_state.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

market_state_features = FeatureView(
    name="market_state",
    entities=[ticker_entity],
    ttl=timedelta(minutes=15),
    schema=[
        Field(name="volatility_14d", dtype=ValueType.FLOAT),
        Field(name="iv_rank", dtype=ValueType.FLOAT),
        Field(name="momentum_21d", dtype=ValueType.FLOAT),
        Field(name="liquidity_score", dtype=ValueType.FLOAT),
        Field(name="volume_ratio", dtype=ValueType.FLOAT),
        Field(name="price_change_pct", dtype=ValueType.FLOAT),
    ],
    online=True,
    source=market_state_source,
    tags={"team": "ml", "domain": "market_data"},
)


# Portfolio State Features (5 min TTL - user-specific)
portfolio_state_source = FileSource(
    path="s3://richesreach-feast/offline/portfolio_state.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

portfolio_state_features = FeatureView(
    name="portfolio_state",
    entities=[user_entity],
    ttl=timedelta(minutes=5),
    schema=[
        Field(name="equity_ratio", dtype=ValueType.FLOAT),
        Field(name="cash_available", dtype=ValueType.FLOAT),
        Field(name="risk_budget", dtype=ValueType.FLOAT),
        Field(name="age_days", dtype=ValueType.INT64),
        Field(name="total_return_pct", dtype=ValueType.FLOAT),
        Field(name="sharpe_ratio", dtype=ValueType.FLOAT),
        Field(name="max_drawdown", dtype=ValueType.FLOAT),
    ],
    online=True,
    source=portfolio_state_source,
    tags={"team": "ml", "domain": "portfolio"},
)


# User Behavior Features (30 min TTL - slower changing)
user_behavior_source = FileSource(
    path="s3://richesreach-feast/offline/user_behavior.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

user_behavior_features = FeatureView(
    name="user_behavior",
    entities=[user_entity],
    ttl=timedelta(minutes=30),
    schema=[
        Field(name="session_count_7d", dtype=ValueType.INT64),
        Field(name="learning_time_minutes", dtype=ValueType.INT64),
        Field(name="trade_frequency", dtype=ValueType.FLOAT),
        Field(name="risk_preference_score", dtype=ValueType.FLOAT),
        Field(name="engagement_score", dtype=ValueType.FLOAT),
    ],
    online=True,
    source=user_behavior_source,
    tags={"team": "ml", "domain": "user"},
)


# Regime Features (10 min TTL - market regime)
regime_source = FileSource(
    path="s3://richesreach-feast/offline/regime.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

regime_features = FeatureView(
    name="market_regime",
    entities=[],  # Global features, no entity key
    ttl=timedelta(minutes=10),
    schema=[
        Field(name="regime_type", dtype=ValueType.STRING),  # BULL, BEAR, SIDEWAYS
        Field(name="regime_confidence", dtype=ValueType.FLOAT),
        Field(name="vix_level", dtype=ValueType.FLOAT),
        Field(name="trend_strength", dtype=ValueType.FLOAT),
        Field(name="volatility_regime", dtype=ValueType.STRING),
    ],
    online=True,
    source=regime_source,
    tags={"team": "ml", "domain": "regime"},
)

