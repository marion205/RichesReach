"""
Feast Feature Store Definitions for RichesReach AI
Phase 1: ML Feature Management
"""

from datetime import timedelta
from feast import Entity, Feature, FeatureView, ValueType
from feast.data_source import DataSource
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres import PostgreSQLOfflineStoreConfig
from feast.infra.online_stores.contrib.postgres_online_store.postgres import PostgreSQLOnlineStoreConfig

# Entities
symbol_entity = Entity(
    name="symbol",
    value_type=ValueType.STRING,
    description="Stock or crypto symbol",
)

# Market Data Features
market_data_source = DataSource(
    name="market_data_source",
    query="SELECT * FROM market_data_features",
    timestamp_field="timestamp",
)

market_data_features = FeatureView(
    name="market_data_features",
    entities=[symbol_entity],
    ttl=timedelta(hours=1),
    features=[
        Feature(name="price", dtype=ValueType.FLOAT),
        Feature(name="volume", dtype=ValueType.INT64),
        Feature(name="high", dtype=ValueType.FLOAT),
        Feature(name="low", dtype=ValueType.FLOAT),
        Feature(name="open", dtype=ValueType.FLOAT),
        Feature(name="close", dtype=ValueType.FLOAT),
        Feature(name="change_percent", dtype=ValueType.FLOAT),
    ],
    source=market_data_source,
)

# Technical Indicators Features
technical_indicators_source = DataSource(
    name="technical_indicators_source",
    query="SELECT * FROM technical_indicators_features",
    timestamp_field="timestamp",
)

technical_indicators_features = FeatureView(
    name="technical_indicators_features",
    entities=[symbol_entity],
    ttl=timedelta(hours=6),
    features=[
        Feature(name="sma_20", dtype=ValueType.FLOAT),
        Feature(name="sma_50", dtype=ValueType.FLOAT),
        Feature(name="ema_12", dtype=ValueType.FLOAT),
        Feature(name="ema_26", dtype=ValueType.FLOAT),
        Feature(name="rsi_14", dtype=ValueType.FLOAT),
        Feature(name="macd", dtype=ValueType.FLOAT),
        Feature(name="macd_signal", dtype=ValueType.FLOAT),
        Feature(name="macd_histogram", dtype=ValueType.FLOAT),
        Feature(name="bollinger_upper", dtype=ValueType.FLOAT),
        Feature(name="bollinger_middle", dtype=ValueType.FLOAT),
        Feature(name="bollinger_lower", dtype=ValueType.FLOAT),
        Feature(name="atr_14", dtype=ValueType.FLOAT),
        Feature(name="stochastic_k", dtype=ValueType.FLOAT),
        Feature(name="stochastic_d", dtype=ValueType.FLOAT),
    ],
    source=technical_indicators_source,
)

# Sentiment Features
sentiment_source = DataSource(
    name="sentiment_source",
    query="SELECT * FROM sentiment_features",
    timestamp_field="timestamp",
)

sentiment_features = FeatureView(
    name="sentiment_features",
    entities=[symbol_entity],
    ttl=timedelta(hours=2),
    features=[
        Feature(name="sentiment_score", dtype=ValueType.FLOAT),
        Feature(name="sentiment_confidence", dtype=ValueType.FLOAT),
        Feature(name="news_count", dtype=ValueType.INT64),
        Feature(name="positive_news_count", dtype=ValueType.INT64),
        Feature(name="negative_news_count", dtype=ValueType.INT64),
        Feature(name="social_mentions", dtype=ValueType.INT64),
        Feature(name="social_sentiment", dtype=ValueType.FLOAT),
    ],
    source=sentiment_source,
)

# Fundamental Data Features
fundamental_source = DataSource(
    name="fundamental_source",
    query="SELECT * FROM fundamental_features",
    timestamp_field="timestamp",
)

fundamental_features = FeatureView(
    name="fundamental_features",
    entities=[symbol_entity],
    ttl=timedelta(days=1),
    features=[
        Feature(name="market_cap", dtype=ValueType.FLOAT),
        Feature(name="pe_ratio", dtype=ValueType.FLOAT),
        Feature(name="pb_ratio", dtype=ValueType.FLOAT),
        Feature(name="debt_to_equity", dtype=ValueType.FLOAT),
        Feature(name="roe", dtype=ValueType.FLOAT),
        Feature(name="roa", dtype=ValueType.FLOAT),
        Feature(name="revenue_growth", dtype=ValueType.FLOAT),
        Feature(name="earnings_growth", dtype=ValueType.FLOAT),
        Feature(name="dividend_yield", dtype=ValueType.FLOAT),
        Feature(name="beta", dtype=ValueType.FLOAT),
    ],
    source=fundamental_source,
)

# ML Prediction Features
ml_prediction_source = DataSource(
    name="ml_prediction_source",
    query="SELECT * FROM ml_prediction_features",
    timestamp_field="timestamp",
)

ml_prediction_features = FeatureView(
    name="ml_prediction_features",
    entities=[symbol_entity],
    ttl=timedelta(hours=1),
    features=[
        Feature(name="prediction_score", dtype=ValueType.FLOAT),
        Feature(name="prediction_confidence", dtype=ValueType.FLOAT),
        Feature(name="model_version", dtype=ValueType.STRING),
        Feature(name="prediction_type", dtype=ValueType.STRING),
        Feature(name="risk_score", dtype=ValueType.FLOAT),
        Feature(name="volatility_score", dtype=ValueType.FLOAT),
    ],
    source=ml_prediction_source,
)

# Portfolio Features
portfolio_source = DataSource(
    name="portfolio_source",
    query="SELECT * FROM portfolio_features",
    timestamp_field="timestamp",
)

portfolio_features = FeatureView(
    name="portfolio_features",
    entities=[symbol_entity],
    ttl=timedelta(hours=1),
    features=[
        Feature(name="portfolio_weight", dtype=ValueType.FLOAT),
        Feature(name="unrealized_pnl", dtype=ValueType.FLOAT),
        Feature(name="realized_pnl", dtype=ValueType.FLOAT),
        Feature(name="total_return", dtype=ValueType.FLOAT),
        Feature(name="sharpe_ratio", dtype=ValueType.FLOAT),
        Feature(name="max_drawdown", dtype=ValueType.FLOAT),
        Feature(name="var_95", dtype=ValueType.FLOAT),
    ],
    source=portfolio_source,
)
