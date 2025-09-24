# redis_config.py
# Redis configuration for development
# Default Redis settings
REDIS_CONFIG = {
'host': 'localhost',
'port': 6379,
'db': 0,
'password': None,
'decode_responses': True,
'socket_connect_timeout': 5,
'socket_timeout': 5,
}
# Alpha Vantage API settings
ALPHA_VANTAGE_CONFIG = {
'api_key': 'K0A7XYLDNXHNQ1WI',
'base_url': 'https://www.alphavantage.co/query',
'rate_limit_per_minute': 5,
'rate_limit_per_day': 500,
}
# Cache TTL settings (in seconds)
CACHE_TTL = {
'QUOTE_DATA': 300, # 5 minutes
'OVERVIEW_DATA': 3600, # 1 hour
'HISTORICAL_DATA': 86400, # 24 hours
'ANALYSIS_RESULT': 1800, # 30 minutes
}
# Batch processing settings
BATCH_PROCESSING = {
'max_stocks_per_batch': 10,
'batch_delay_seconds': 2,
'max_concurrent_batches': 3,
}
