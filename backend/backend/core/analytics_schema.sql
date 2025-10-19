-- Analytics Database Schema - Phase 3
-- Real-time analytics, business intelligence, and predictive analytics

-- Analytics Metrics Table
CREATE TABLE IF NOT EXISTS analytics_metrics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    value DECIMAL(20, 8) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    labels JSONB DEFAULT '{}',
    metric_type VARCHAR(50) NOT NULL DEFAULT 'gauge',
    metadata JSONB DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for analytics_metrics
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_name ON analytics_metrics(name);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_timestamp ON analytics_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_name_timestamp ON analytics_metrics(name, timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_labels ON analytics_metrics USING GIN(labels);

-- Analytics Events Table
CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(255) DEFAULT NULL,
    session_id VARCHAR(255) DEFAULT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    properties JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for analytics_events
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_session_id ON analytics_events(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_properties ON analytics_events USING GIN(properties);

-- Market Data Table
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    volume BIGINT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    change DECIMAL(20, 8) NOT NULL DEFAULT 0,
    change_percent DECIMAL(10, 4) NOT NULL DEFAULT 0,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for market_data
CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_market_data_price ON market_data(price);

-- User Behavior Table
CREATE TABLE IF NOT EXISTS user_behavior (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    page VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    duration DECIMAL(10, 3) NOT NULL DEFAULT 0,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for user_behavior
CREATE INDEX IF NOT EXISTS idx_user_behavior_user_id ON user_behavior(user_id);
CREATE INDEX IF NOT EXISTS idx_user_behavior_session_id ON user_behavior(session_id);
CREATE INDEX IF NOT EXISTS idx_user_behavior_event_type ON user_behavior(event_type);
CREATE INDEX IF NOT EXISTS idx_user_behavior_timestamp ON user_behavior(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_behavior_page ON user_behavior(page);
CREATE INDEX IF NOT EXISTS idx_user_behavior_properties ON user_behavior USING GIN(properties);

-- Business Intelligence Views
CREATE OR REPLACE VIEW bi_revenue_metrics AS
SELECT 
    DATE_TRUNC('day', timestamp) as date,
    SUM(CASE WHEN name = 'total_revenue' THEN value ELSE 0 END) as daily_revenue,
    SUM(CASE WHEN name = 'revenue_growth' THEN value ELSE 0 END) as revenue_growth,
    COUNT(DISTINCT CASE WHEN name = 'revenue_per_user' THEN labels->>'user_id' END) as revenue_users
FROM analytics_metrics 
WHERE name IN ('total_revenue', 'revenue_growth', 'revenue_per_user')
    AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY date DESC;

CREATE OR REPLACE VIEW bi_user_metrics AS
SELECT 
    DATE_TRUNC('day', timestamp) as date,
    SUM(CASE WHEN name = 'total_users' THEN value ELSE 0 END) as total_users,
    SUM(CASE WHEN name = 'active_users' THEN value ELSE 0 END) as active_users,
    SUM(CASE WHEN name = 'new_users' THEN value ELSE 0 END) as new_users,
    SUM(CASE WHEN name = 'user_retention' THEN value ELSE 0 END) as user_retention
FROM analytics_metrics 
WHERE name IN ('total_users', 'active_users', 'new_users', 'user_retention')
    AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY date DESC;

-- Market Analytics Views
CREATE OR REPLACE VIEW market_performance AS
SELECT 
    symbol,
    DATE_TRUNC('hour', timestamp) as hour,
    AVG(price) as avg_price,
    MAX(price) as max_price,
    MIN(price) as min_price,
    SUM(volume) as total_volume,
    AVG(change_percent) as avg_change_percent,
    COUNT(*) as data_points
FROM market_data 
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY symbol, DATE_TRUNC('hour', timestamp)
ORDER BY symbol, hour DESC;

CREATE OR REPLACE VIEW market_trends AS
SELECT 
    symbol,
    DATE_TRUNC('day', timestamp) as date,
    AVG(price) as daily_avg_price,
    MAX(price) as daily_high,
    MIN(price) as daily_low,
    SUM(volume) as daily_volume,
    AVG(change_percent) as daily_change_percent,
    COUNT(*) as data_points
FROM market_data 
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY symbol, DATE_TRUNC('day', timestamp)
ORDER BY symbol, date DESC;

-- User Analytics Views
CREATE OR REPLACE VIEW user_engagement AS
SELECT 
    user_id,
    DATE_TRUNC('day', timestamp) as date,
    COUNT(*) as total_events,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(DISTINCT page) as unique_pages,
    AVG(duration) as avg_session_duration,
    MAX(timestamp) - MIN(timestamp) as total_time_spent
FROM user_behavior 
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY user_id, DATE_TRUNC('day', timestamp)
ORDER BY user_id, date DESC;

CREATE OR REPLACE VIEW user_journey AS
SELECT 
    user_id,
    session_id,
    MIN(timestamp) as session_start,
    MAX(timestamp) as session_end,
    COUNT(*) as total_events,
    COUNT(DISTINCT page) as unique_pages,
    AVG(duration) as avg_event_duration,
    SUM(duration) as total_session_duration,
    array_agg(DISTINCT page ORDER BY timestamp) as page_sequence
FROM user_behavior 
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY user_id, session_id
ORDER BY user_id, session_start DESC;

-- Performance Analytics Views
CREATE OR REPLACE VIEW system_performance AS
SELECT 
    DATE_TRUNC('minute', timestamp) as minute,
    AVG(CASE WHEN name = 'cpu_usage' THEN value END) as avg_cpu_usage,
    AVG(CASE WHEN name = 'memory_usage' THEN value END) as avg_memory_usage,
    AVG(CASE WHEN name = 'disk_usage' THEN value END) as avg_disk_usage,
    AVG(CASE WHEN name = 'network_usage' THEN value END) as avg_network_usage
FROM analytics_metrics 
WHERE name IN ('cpu_usage', 'memory_usage', 'disk_usage', 'network_usage')
    AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('minute', timestamp)
ORDER BY minute DESC;

CREATE OR REPLACE VIEW api_performance AS
SELECT 
    DATE_TRUNC('minute', timestamp) as minute,
    AVG(CASE WHEN name = 'request_rate' THEN value END) as avg_request_rate,
    AVG(CASE WHEN name = 'response_time' THEN value END) as avg_response_time,
    AVG(CASE WHEN name = 'error_rate' THEN value END) as avg_error_rate,
    AVG(CASE WHEN name = 'throughput' THEN value END) as avg_throughput
FROM analytics_metrics 
WHERE name IN ('request_rate', 'response_time', 'error_rate', 'throughput')
    AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('minute', timestamp)
ORDER BY minute DESC;

-- Predictive Analytics Tables
CREATE TABLE IF NOT EXISTS prediction_models (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_data BYTEA NOT NULL,
    scaler_data BYTEA NOT NULL,
    accuracy_score DECIMAL(10, 4) NOT NULL,
    training_data_size INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    model_id INTEGER REFERENCES prediction_models(id),
    current_price DECIMAL(20, 8) NOT NULL,
    predicted_price DECIMAL(20, 8) NOT NULL,
    price_change DECIMAL(20, 8) NOT NULL,
    price_change_percent DECIMAL(10, 4) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL,
    horizon_hours INTEGER NOT NULL,
    prediction_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    anomaly_score DECIMAL(10, 4) NOT NULL,
    threshold DECIMAL(10, 4) NOT NULL,
    data_point JSONB NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for predictive analytics tables
CREATE INDEX IF NOT EXISTS idx_prediction_models_symbol ON prediction_models(symbol);
CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON predictions(symbol);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(prediction_timestamp);
CREATE INDEX IF NOT EXISTS idx_anomalies_symbol ON anomalies(symbol);
CREATE INDEX IF NOT EXISTS idx_anomalies_detected_at ON anomalies(detected_at);

-- User Clustering Tables
CREATE TABLE IF NOT EXISTS user_clusters (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    cluster_id INTEGER NOT NULL,
    cluster_features JSONB NOT NULL,
    cluster_created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cluster_analysis (
    id SERIAL PRIMARY KEY,
    cluster_id INTEGER NOT NULL,
    cluster_size INTEGER NOT NULL,
    cluster_characteristics JSONB NOT NULL,
    analysis_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for user clustering tables
CREATE INDEX IF NOT EXISTS idx_user_clusters_user_id ON user_clusters(user_id);
CREATE INDEX IF NOT EXISTS idx_user_clusters_cluster_id ON user_clusters(cluster_id);
CREATE INDEX IF NOT EXISTS idx_cluster_analysis_cluster_id ON cluster_analysis(cluster_id);

-- Analytics Alerts Table
CREATE TABLE IF NOT EXISTS analytics_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    alert_data JSONB DEFAULT '{}',
    threshold_value DECIMAL(20, 8) DEFAULT NULL,
    actual_value DECIMAL(20, 8) DEFAULT NULL,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255) DEFAULT NULL,
    acknowledged_at TIMESTAMPTZ DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for analytics alerts
CREATE INDEX IF NOT EXISTS idx_analytics_alerts_type ON analytics_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_analytics_alerts_severity ON analytics_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_analytics_alerts_acknowledged ON analytics_alerts(is_acknowledged);
CREATE INDEX IF NOT EXISTS idx_analytics_alerts_created_at ON analytics_alerts(created_at);

-- Analytics Dashboard Configuration Table
CREATE TABLE IF NOT EXISTS dashboard_configs (
    id SERIAL PRIMARY KEY,
    dashboard_type VARCHAR(50) NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for dashboard configs
CREATE INDEX IF NOT EXISTS idx_dashboard_configs_type ON dashboard_configs(dashboard_type);
CREATE INDEX IF NOT EXISTS idx_dashboard_configs_active ON dashboard_configs(is_active);

-- Analytics Retention Policies (for data cleanup)
-- Keep metrics for 90 days
CREATE OR REPLACE FUNCTION cleanup_old_metrics()
RETURNS void AS $$
BEGIN
    DELETE FROM analytics_metrics 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    DELETE FROM analytics_events 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    DELETE FROM market_data 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    DELETE FROM user_behavior 
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    DELETE FROM predictions 
    WHERE prediction_timestamp < NOW() - INTERVAL '30 days';
    
    DELETE FROM anomalies 
    WHERE detected_at < NOW() - INTERVAL '30 days';
    
    DELETE FROM analytics_alerts 
    WHERE created_at < NOW() - INTERVAL '30 days' 
    AND is_acknowledged = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to run cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-analytics', '0 2 * * *', 'SELECT cleanup_old_metrics();');

-- Analytics Materialized Views for Performance
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_analytics_summary AS
SELECT 
    DATE_TRUNC('day', timestamp) as date,
    COUNT(DISTINCT CASE WHEN name LIKE 'revenue%' THEN name END) as revenue_metrics_count,
    COUNT(DISTINCT CASE WHEN name LIKE 'user%' THEN name END) as user_metrics_count,
    COUNT(DISTINCT CASE WHEN name LIKE 'system%' THEN name END) as system_metrics_count,
    AVG(CASE WHEN name = 'total_revenue' THEN value END) as avg_daily_revenue,
    AVG(CASE WHEN name = 'active_users' THEN value END) as avg_daily_active_users,
    AVG(CASE WHEN name = 'cpu_usage' THEN value END) as avg_daily_cpu_usage
FROM analytics_metrics 
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY date DESC;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_mv_daily_analytics_summary_date ON mv_daily_analytics_summary(date);

-- Refresh materialized view function
CREATE OR REPLACE FUNCTION refresh_analytics_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_daily_analytics_summary;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO richesreach_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO richesreach_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO richesreach_user;
