// src/market_data/factory.rs
use crate::market_data::{
    cached::CachedProvider,
    in_memory::InMemoryProvider,
    postgres::PostgresProvider,
    provider::{MarketDataIngest, MarketDataProvider},
};
use chrono::Duration;
use std::{env, sync::Arc};

pub struct ProviderBundle {
    pub read: Arc<dyn MarketDataProvider>,
    pub ingest: Arc<dyn MarketDataIngest>,
}

pub async fn build_provider_bundle() -> anyhow::Result<ProviderBundle> {
    let backend = env::var("MARKET_DATA_BACKEND").unwrap_or_else(|_| "in_memory".to_string());
    let cache_ttl_secs: i64 = env::var("MARKET_DATA_CACHE_TTL_SECONDS")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(0);

    match backend.as_str() {
        "in_memory" => {
            let p = Arc::new(InMemoryProvider::new());
            let read: Arc<dyn MarketDataProvider> = if cache_ttl_secs > 0 {
                Arc::new(CachedProvider::new(p.clone(), Duration::seconds(cache_ttl_secs)))
            } else {
                p.clone()
            };
            Ok(ProviderBundle {
                read,
                ingest: p,
            })
        }

        "postgres" => {
            // Fail fast if DATABASE_URL is missing
            let database_url = env::var("DATABASE_URL")
                .map_err(|_| anyhow::anyhow!("MARKET_DATA_BACKEND=postgres requires DATABASE_URL env var"))?;
            
            // Note: sqlx is optional - if not available, return error
            #[cfg(feature = "postgres")]
            {
                // Connect to Postgres (sqlx handles connection pooling)
                let pool = sqlx::PgPool::connect(&database_url).await
                    .map_err(|e| anyhow::anyhow!("Failed to connect to Postgres: {}", e))?;
                
                // Validate connection with a simple query (cheap, deterministic probe)
                sqlx::query("SELECT 1")
                    .execute(&pool)
                    .await
                    .map_err(|e| anyhow::anyhow!("Postgres health check failed: {}", e))?;
                
                tracing::info!("Postgres provider connected and validated");
                
                // Only wrap read handle with cache (not ingest) - correct design
                let p = Arc::new(PostgresProvider::new(pool));
                let read: Arc<dyn MarketDataProvider> = if cache_ttl_secs > 0 {
                    Arc::new(CachedProvider::new(p.clone(), Duration::seconds(cache_ttl_secs)))
                } else {
                    p.clone()
                };
                Ok(ProviderBundle {
                    read,
                    ingest: p,
                })
            }
            
            #[cfg(not(feature = "postgres"))]
            {
                anyhow::bail!("Postgres backend requires sqlx feature. Add to Cargo.toml: sqlx = {{ version = \"0.7\", features = [\"runtime-tokio\", \"postgres\", \"chrono\", \"rust_decimal\", \"macros\"] }}")
            }
        }

        other => anyhow::bail!("Unknown MARKET_DATA_BACKEND={other}. Valid options: in_memory, postgres"),
    }
}

