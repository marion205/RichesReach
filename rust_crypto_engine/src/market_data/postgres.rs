// src/market_data/postgres.rs
// Production-grade Postgres/Timescale provider
// Requires sqlx with postgres feature enabled in Cargo.toml

use super::provider::*;
use async_trait::async_trait;
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use std::sync::Arc;

// SQL table structure (Timescale-friendly):
// CREATE TABLE market_quotes (
//   ts        TIMESTAMPTZ NOT NULL,
//   symbol    TEXT        NOT NULL,
//   bid       NUMERIC     NOT NULL,
//   ask       NUMERIC     NOT NULL,
//   PRIMARY KEY (symbol, ts)
// );
// CREATE INDEX market_quotes_symbol_ts_idx ON market_quotes(symbol, ts DESC);
// -- If using Timescale: SELECT create_hypertable('market_quotes', 'ts');

pub struct PostgresProvider {
    // Use conditional compilation to handle sqlx dependency
    #[cfg(feature = "postgres")]
    pool: sqlx::PgPool,
    #[cfg(not(feature = "postgres"))]
    _placeholder: (),
}

impl PostgresProvider {
    #[cfg(feature = "postgres")]
    pub fn new(pool: sqlx::PgPool) -> Self {
        Self { pool }
    }

    #[cfg(not(feature = "postgres"))]
    pub fn new(_pool: ()) -> Self {
        Self { _placeholder: () }
    }
}

#[async_trait]
impl MarketDataProvider for PostgresProvider {
    #[tracing::instrument(skip(self), fields(symbol = %symbol))]
    async fn latest_quote(&self, symbol: &str) -> Result<Quote, ProviderError> {
        #[cfg(feature = "postgres")]
        {
            let row = sqlx::query(
                r#"
                SELECT ts, bid, ask
                FROM market_quotes
                WHERE symbol = $1
                ORDER BY ts DESC
                LIMIT 1
                "#,
            )
            .bind(symbol)
            .fetch_optional(&self.pool)
            .await
            .map_err(|e| ProviderError::Backend(format!("Postgres query failed: {}", e)))?;

            let Some(r) = row else {
                return Err(ProviderError::NotFound(symbol.to_string()));
            };

            // Performance: Clone symbol only once, reuse Arc
            let symbol_arc = Arc::from(symbol);
            Ok(Quote {
                symbol: symbol_arc,
                ts: r.try_get::<DateTime<Utc>, _>("ts")
                    .map_err(|e| ProviderError::Backend(format!("Failed to read ts: {}", e)))?,
                bid: r.try_get::<Decimal, _>("bid")
                    .map_err(|e| ProviderError::Backend(format!("Failed to read bid: {}", e)))?,
                ask: r.try_get::<Decimal, _>("ask")
                    .map_err(|e| ProviderError::Backend(format!("Failed to read ask: {}", e)))?,
            })
        }

        #[cfg(not(feature = "postgres"))]
        {
            Err(ProviderError::Backend(
                "PostgresProvider not available. Enable 'postgres' feature and add sqlx dependency.".to_string()
            ))
        }
    }

    #[tracing::instrument(skip(self), fields(symbol = %symbol, start = %start, end = %end, limit = limit))]
    async fn mid_prices(
        &self,
        symbol: &str,
        start: DateTime<Utc>,
        end: DateTime<Utc>,
        limit: usize,
    ) -> Result<Vec<PricePoint>, ProviderError> {
        #[cfg(feature = "postgres")]
        {
            // Performance: Use index-friendly query with proper bounds
            // Note: LIMIT is applied after ORDER BY, so we get the first N rows in time order
            // Time bounds: [start, end] inclusive (consistent with InMemoryProvider)
            // Compute mid in SQL (NUMERIC division is safe in Postgres)
            let rows = sqlx::query(
                r#"
                SELECT ts, (bid + ask) / 2.0 AS mid
                FROM market_quotes
                WHERE symbol = $1
                  AND ts >= $2
                  AND ts <= $3
                ORDER BY ts ASC
                LIMIT $4
                "#,
            )
            .bind(symbol)
            .bind(start)
            .bind(end)
            .bind(limit.min(100_000) as i64) // Cap limit to prevent excessive memory usage
            .fetch_all(&self.pool)
            .await
            .map_err(|e| ProviderError::Backend(format!("Postgres query failed: {}", e)))?;

            let mut out = Vec::with_capacity(rows.len());
            for r in rows {
                out.push(PricePoint {
                    ts: r.try_get::<DateTime<Utc>, _>("ts")
                        .map_err(|e| ProviderError::Backend(format!("Failed to read ts: {}", e)))?,
                    mid: r.try_get::<Decimal, _>("mid")
                        .map_err(|e| ProviderError::Backend(format!("Failed to read mid: {}", e)))?,
                });
            }
            Ok(out)
        }

        #[cfg(not(feature = "postgres"))]
        {
            Err(ProviderError::Backend(
                "PostgresProvider not available. Enable 'postgres' feature and add sqlx dependency.".to_string()
            ))
        }
    }
}

#[async_trait]
impl MarketDataIngest for PostgresProvider {
    #[tracing::instrument(skip(self), fields(symbol = %quote.symbol, ts = %quote.ts))]
    async fn ingest_quote(&self, quote: Quote) -> Result<(), ProviderError> {
        #[cfg(feature = "postgres")]
        {
            sqlx::query(
                r#"
                INSERT INTO market_quotes (ts, symbol, bid, ask)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (symbol, ts) DO UPDATE
                  SET bid = EXCLUDED.bid,
                      ask = EXCLUDED.ask
                "#,
            )
            .bind(quote.ts)
            .bind(quote.symbol.as_ref())
            .bind(quote.bid)
            .bind(quote.ask)
            .execute(&self.pool)
            .await
            .map_err(|e| ProviderError::Backend(format!("Postgres insert failed: {}", e)))?;

            Ok(())
        }

        #[cfg(not(feature = "postgres"))]
        {
            Err(ProviderError::Backend(
                "PostgresProvider not available. Enable 'postgres' feature and add sqlx dependency.".to_string()
            ))
        }
    }
}
