-- Migration: Create market_quotes table
-- Compatible with both standard Postgres and TimescaleDB

CREATE TABLE IF NOT EXISTS market_quotes (
    ts        TIMESTAMPTZ NOT NULL,
    symbol    TEXT        NOT NULL,
    bid       NUMERIC     NOT NULL,
    ask       NUMERIC     NOT NULL,
    PRIMARY KEY (symbol, ts),
    -- Ensure valid price data (bid > 0, ask > 0, ask >= bid)
    CHECK (bid > 0 AND ask > 0 AND ask >= bid)
);

-- Index for fast latest quote lookups (symbol + descending timestamp)
CREATE INDEX IF NOT EXISTS market_quotes_symbol_ts_idx 
    ON market_quotes(symbol, ts DESC);

-- Index for time-range queries (useful for mid_prices queries)
CREATE INDEX IF NOT EXISTS market_quotes_ts_idx 
    ON market_quotes(ts);

-- If using TimescaleDB, convert to hypertable:
-- SELECT create_hypertable('market_quotes', 'ts', if_not_exists => true);

-- Optional: Add retention policy (e.g., keep 1 year of data)
-- SELECT add_retention_policy('market_quotes', INTERVAL '1 year');

