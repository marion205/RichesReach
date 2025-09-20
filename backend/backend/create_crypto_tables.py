#!/usr/bin/env python3
"""
Create crypto tables directly using SQL
This bypasses Django migrations for now to get the crypto system working
"""

import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

def create_crypto_tables():
    """Create crypto tables using raw SQL"""
    
    with connection.cursor() as cursor:
        # Create cryptocurrencies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_currencies (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                coingecko_id VARCHAR(50) UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_staking_available BOOLEAN DEFAULT FALSE,
                min_trade_amount DECIMAL(20,8) DEFAULT 0.0001,
                precision INTEGER DEFAULT 8,
                volatility_tier VARCHAR(20) DEFAULT 'HIGH',
                is_sec_compliant BOOLEAN DEFAULT FALSE,
                regulatory_status VARCHAR(50) DEFAULT 'UNKNOWN',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create crypto_prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_prices (
                id SERIAL PRIMARY KEY,
                cryptocurrency_id INTEGER REFERENCES crypto_currencies(id) ON DELETE CASCADE,
                price_usd DECIMAL(20,8) NOT NULL,
                price_btc DECIMAL(20,8),
                volume_24h DECIMAL(20,2),
                market_cap DECIMAL(20,2),
                price_change_24h DECIMAL(10,4),
                price_change_percentage_24h DECIMAL(10,4),
                rsi_14 DECIMAL(5,2),
                macd DECIMAL(10,6),
                bollinger_upper DECIMAL(20,8),
                bollinger_lower DECIMAL(20,8),
                volatility_7d DECIMAL(10,6),
                volatility_30d DECIMAL(10,6),
                momentum_score DECIMAL(5,2),
                sentiment_score DECIMAL(5,2),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Create crypto_portfolios table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_portfolios (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES core_user(id) ON DELETE CASCADE,
                total_value_usd DECIMAL(20,2) DEFAULT 0,
                total_cost_basis DECIMAL(20,2) DEFAULT 0,
                total_pnl DECIMAL(20,2) DEFAULT 0,
                total_pnl_percentage DECIMAL(10,4) DEFAULT 0,
                portfolio_volatility DECIMAL(10,6) DEFAULT 0,
                sharpe_ratio DECIMAL(10,4) DEFAULT 0,
                max_drawdown DECIMAL(10,4) DEFAULT 0,
                diversification_score DECIMAL(5,2) DEFAULT 0,
                top_holding_percentage DECIMAL(5,2) DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(user_id)
            );
        """)
        
        # Create crypto_holdings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_holdings (
                id BIGSERIAL PRIMARY KEY,
                portfolio_id BIGINT REFERENCES crypto_portfolios(id) ON DELETE CASCADE,
                cryptocurrency_id BIGINT REFERENCES crypto_currencies(id) ON DELETE CASCADE,
                quantity DECIMAL(20,8) NOT NULL,
                average_cost DECIMAL(20,8) NOT NULL,
                current_price DECIMAL(20,8) NOT NULL,
                current_value DECIMAL(20,2) NOT NULL,
                unrealized_pnl DECIMAL(20,2) NOT NULL,
                unrealized_pnl_percentage DECIMAL(10,4) NOT NULL,
                staked_quantity DECIMAL(20,8) DEFAULT 0,
                staking_rewards DECIMAL(20,8) DEFAULT 0,
                staking_apy DECIMAL(5,2),
                is_collateralized BOOLEAN DEFAULT FALSE,
                collateral_value DECIMAL(20,2) DEFAULT 0,
                loan_amount DECIMAL(20,2) DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(portfolio_id, cryptocurrency_id)
            );
        """)
        
        # Create crypto_trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_trades (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES core_user(id) ON DELETE CASCADE,
                cryptocurrency_id BIGINT REFERENCES crypto_currencies(id) ON DELETE CASCADE,
                trade_type VARCHAR(20) NOT NULL,
                quantity DECIMAL(20,8) NOT NULL,
                price_per_unit DECIMAL(20,8) NOT NULL,
                total_amount DECIMAL(20,2) NOT NULL,
                fees DECIMAL(20,2) DEFAULT 0,
                order_id VARCHAR(100) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'COMPLETED',
                execution_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                is_sbloc_funded BOOLEAN DEFAULT FALSE,
                sbloc_loan_id VARCHAR(100)
            );
        """)
        
        # Create crypto_ml_predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_ml_predictions (
                id BIGSERIAL PRIMARY KEY,
                cryptocurrency_id BIGINT REFERENCES crypto_currencies(id) ON DELETE CASCADE,
                prediction_type VARCHAR(20) NOT NULL,
                probability DECIMAL(5,4) NOT NULL,
                confidence_level VARCHAR(20) NOT NULL,
                features_used JSONB DEFAULT '{}',
                model_version VARCHAR(50) DEFAULT 'v1.0',
                prediction_horizon_hours INTEGER DEFAULT 24,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                was_correct BOOLEAN,
                actual_return DECIMAL(10,6)
            );
        """)
        
        # Create crypto_sbloc_loans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_sbloc_loans (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES core_user(id) ON DELETE CASCADE,
                cryptocurrency_id BIGINT REFERENCES crypto_currencies(id) ON DELETE CASCADE,
                collateral_quantity DECIMAL(20,8) NOT NULL,
                collateral_value_at_loan DECIMAL(20,2) NOT NULL,
                loan_amount DECIMAL(20,2) NOT NULL,
                interest_rate DECIMAL(5,4) NOT NULL,
                maintenance_margin DECIMAL(5,4) DEFAULT 0.5,
                liquidation_threshold DECIMAL(5,4) DEFAULT 0.4,
                status VARCHAR(20) DEFAULT 'ACTIVE',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Create crypto_education_progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_education_progress (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES core_user(id) ON DELETE CASCADE,
                module_name VARCHAR(100) NOT NULL,
                module_type VARCHAR(20) NOT NULL,
                progress_percentage DECIMAL(5,2) DEFAULT 0,
                is_completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP WITH TIME ZONE,
                quiz_attempts INTEGER DEFAULT 0,
                best_quiz_score DECIMAL(5,2) DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(user_id, module_name)
            );
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crypto_prices_crypto_timestamp ON crypto_prices(cryptocurrency_id, timestamp DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crypto_prices_timestamp ON crypto_prices(timestamp DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crypto_holdings_portfolio_crypto ON crypto_holdings(portfolio_id, cryptocurrency_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crypto_trades_user_execution ON crypto_trades(user_id, execution_time DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crypto_trades_crypto_execution ON crypto_trades(cryptocurrency_id, execution_time DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crypto_ml_predictions_crypto_created ON crypto_ml_predictions(cryptocurrency_id, created_at DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crypto_ml_predictions_type_created ON crypto_ml_predictions(prediction_type, created_at DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crypto_ml_predictions_expires ON crypto_ml_predictions(expires_at);")
        
        print("✅ Crypto tables created successfully!")

def seed_crypto_currencies():
    """Seed initial cryptocurrency data"""
    
    crypto_data = [
        ('BTC', 'Bitcoin', 'bitcoin', False, 0.0001, 8, 'HIGH', False, 'UNKNOWN'),
        ('ETH', 'Ethereum', 'ethereum', True, 0.001, 6, 'HIGH', False, 'UNKNOWN'),
        ('SOL', 'Solana', 'solana', True, 0.01, 4, 'EXTREME', False, 'UNKNOWN'),
        ('ADA', 'Cardano', 'cardano', True, 1.0, 2, 'HIGH', False, 'UNKNOWN'),
        ('DOT', 'Polkadot', 'polkadot', True, 0.1, 3, 'HIGH', False, 'UNKNOWN'),
        ('MATIC', 'Polygon', 'matic-network', True, 1.0, 2, 'HIGH', False, 'UNKNOWN'),
        ('AVAX', 'Avalanche', 'avalanche-2', True, 0.1, 3, 'HIGH', False, 'UNKNOWN'),
        ('LINK', 'Chainlink', 'chainlink', True, 0.1, 3, 'HIGH', False, 'UNKNOWN'),
        ('UNI', 'Uniswap', 'uniswap', True, 0.1, 3, 'HIGH', False, 'UNKNOWN'),
        ('LTC', 'Litecoin', 'litecoin', False, 0.01, 4, 'MEDIUM', False, 'UNKNOWN'),
        ('BCH', 'Bitcoin Cash', 'bitcoin-cash', False, 0.01, 4, 'HIGH', False, 'UNKNOWN'),
        ('XRP', 'XRP', 'ripple', False, 1.0, 2, 'HIGH', False, 'UNKNOWN'),
        ('ATOM', 'Cosmos', 'cosmos', True, 0.1, 3, 'HIGH', False, 'UNKNOWN'),
        ('NEAR', 'NEAR Protocol', 'near', True, 0.1, 3, 'EXTREME', False, 'UNKNOWN'),
        ('ALGO', 'Algorand', 'algorand', True, 1.0, 2, 'HIGH', False, 'UNKNOWN'),
        ('FTM', 'Fantom', 'fantom', True, 1.0, 2, 'EXTREME', False, 'UNKNOWN'),
        ('MANA', 'Decentraland', 'decentraland', False, 1.0, 2, 'EXTREME', False, 'UNKNOWN'),
        ('SAND', 'The Sandbox', 'the-sandbox', False, 1.0, 2, 'EXTREME', False, 'UNKNOWN'),
        ('USDC', 'USD Coin', 'usd-coin', True, 1.0, 2, 'LOW', True, 'STABLE_COIN'),
        ('USDT', 'Tether', 'tether', False, 1.0, 2, 'LOW', False, 'STABLE_COIN')
    ]
    
    with connection.cursor() as cursor:
        for data in crypto_data:
            cursor.execute("""
                INSERT INTO crypto_currencies 
                (symbol, name, coingecko_id, is_staking_available, min_trade_amount, precision, volatility_tier, is_sec_compliant, regulatory_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO NOTHING
            """, data)
        
        print("✅ Crypto currencies seeded successfully!")

if __name__ == "__main__":
    try:
        create_crypto_tables()
        seed_crypto_currencies()
        print("\n🎉 Crypto system setup complete!")
    except Exception as e:
        print(f"❌ Error setting up crypto system: {e}")
        sys.exit(1)
