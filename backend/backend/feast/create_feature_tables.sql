-- Feast Feature Store Database Tables
-- Phase 1: ML Feature Management

-- Market Data Features Table
CREATE TABLE IF NOT EXISTS market_data_features (
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    price DECIMAL(10,2),
    volume BIGINT,
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    open DECIMAL(10,2),
    close DECIMAL(10,2),
    change_percent DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timestamp)
);

-- Technical Indicators Features Table
CREATE TABLE IF NOT EXISTS technical_indicators_features (
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    sma_20 DECIMAL(10,2),
    sma_50 DECIMAL(10,2),
    ema_12 DECIMAL(10,2),
    ema_26 DECIMAL(10,2),
    rsi_14 DECIMAL(5,2),
    macd DECIMAL(10,4),
    macd_signal DECIMAL(10,4),
    macd_histogram DECIMAL(10,4),
    bollinger_upper DECIMAL(10,2),
    bollinger_middle DECIMAL(10,2),
    bollinger_lower DECIMAL(10,2),
    atr_14 DECIMAL(10,4),
    stochastic_k DECIMAL(5,2),
    stochastic_d DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timestamp)
);

-- Sentiment Features Table
CREATE TABLE IF NOT EXISTS sentiment_features (
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    sentiment_score DECIMAL(3,2),
    sentiment_confidence DECIMAL(3,2),
    news_count INTEGER,
    positive_news_count INTEGER,
    negative_news_count INTEGER,
    social_mentions INTEGER,
    social_sentiment DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timestamp)
);

-- Fundamental Data Features Table
CREATE TABLE IF NOT EXISTS fundamental_features (
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    market_cap BIGINT,
    pe_ratio DECIMAL(8,2),
    pb_ratio DECIMAL(8,2),
    debt_to_equity DECIMAL(8,4),
    roe DECIMAL(8,4),
    roa DECIMAL(8,4),
    revenue_growth DECIMAL(8,4),
    earnings_growth DECIMAL(8,4),
    dividend_yield DECIMAL(5,4),
    beta DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timestamp)
);

-- ML Prediction Features Table
CREATE TABLE IF NOT EXISTS ml_prediction_features (
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    prediction_score DECIMAL(8,4),
    prediction_confidence DECIMAL(3,2),
    model_version VARCHAR(50),
    prediction_type VARCHAR(50),
    risk_score DECIMAL(3,2),
    volatility_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timestamp)
);

-- Portfolio Features Table
CREATE TABLE IF NOT EXISTS portfolio_features (
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    portfolio_weight DECIMAL(5,4),
    unrealized_pnl DECIMAL(12,2),
    realized_pnl DECIMAL(12,2),
    total_return DECIMAL(8,4),
    sharpe_ratio DECIMAL(6,4),
    max_drawdown DECIMAL(6,4),
    var_95 DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timestamp)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data_features(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_technical_symbol_timestamp ON technical_indicators_features(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_symbol_timestamp ON sentiment_features(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_fundamental_symbol_timestamp ON fundamental_features(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ml_prediction_symbol_timestamp ON ml_prediction_features(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_symbol_timestamp ON portfolio_features(symbol, timestamp DESC);

-- Create views for easier querying
CREATE OR REPLACE VIEW latest_market_features AS
SELECT DISTINCT ON (symbol) 
    symbol, timestamp, price, volume, change_percent
FROM market_data_features 
ORDER BY symbol, timestamp DESC;

CREATE OR REPLACE VIEW latest_technical_features AS
SELECT DISTINCT ON (symbol) 
    symbol, timestamp, sma_20, rsi_14, macd, bollinger_upper, bollinger_lower
FROM technical_indicators_features 
ORDER BY symbol, timestamp DESC;

CREATE OR REPLACE VIEW latest_sentiment_features AS
SELECT DISTINCT ON (symbol) 
    symbol, timestamp, sentiment_score, sentiment_confidence, news_count
FROM sentiment_features 
ORDER BY symbol, timestamp DESC;

-- Insert sample data for testing
INSERT INTO market_data_features (symbol, timestamp, price, volume, change_percent) VALUES
('AAPL', NOW(), 175.50, 50000000, 1.25),
('MSFT', NOW(), 350.25, 30000000, 0.85),
('GOOGL', NOW(), 2800.75, 15000000, -0.45)
ON CONFLICT (symbol, timestamp) DO NOTHING;

INSERT INTO technical_indicators_features (symbol, timestamp, sma_20, rsi_14, macd) VALUES
('AAPL', NOW(), 174.20, 65.5, 0.85),
('MSFT', NOW(), 348.90, 58.2, 1.25),
('GOOGL', NOW(), 2795.30, 45.8, -0.35)
ON CONFLICT (symbol, timestamp) DO NOTHING;

INSERT INTO sentiment_features (symbol, timestamp, sentiment_score, sentiment_confidence, news_count) VALUES
('AAPL', NOW(), 0.65, 0.85, 15),
('MSFT', NOW(), 0.72, 0.90, 12),
('GOOGL', NOW(), 0.45, 0.75, 8)
ON CONFLICT (symbol, timestamp) DO NOTHING;
