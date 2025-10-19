#!/usr/bin/env python3
"""
SQLite-compatible crypto setup
"""

import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

def create_crypto_tables():
    """Create essential crypto tables for SQLite"""
    
    with connection.cursor() as cursor:
        # Drop tables if they exist
        cursor.execute("DROP TABLE IF EXISTS crypto_currencies;")
        cursor.execute("DROP TABLE IF EXISTS crypto_prices;")
        cursor.execute("DROP TABLE IF EXISTS crypto_portfolios;")
        cursor.execute("DROP TABLE IF EXISTS crypto_holdings;")
        cursor.execute("DROP TABLE IF EXISTS crypto_trades;")
        cursor.execute("DROP TABLE IF EXISTS crypto_ml_predictions;")
        cursor.execute("DROP TABLE IF EXISTS crypto_sbloc_loans;")
        cursor.execute("DROP TABLE IF EXISTS crypto_education_progress;")
        
        # Create cryptocurrencies table
        cursor.execute("""
            CREATE TABLE crypto_currencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(10) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                coingecko_id VARCHAR(50) UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_staking_available BOOLEAN DEFAULT 0,
                min_trade_amount DECIMAL(20,8) DEFAULT 0.0001,
                precision INTEGER DEFAULT 8,
                volatility_tier VARCHAR(20) DEFAULT 'HIGH',
                is_sec_compliant BOOLEAN DEFAULT 0,
                regulatory_status VARCHAR(50) DEFAULT 'UNKNOWN',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create crypto_prices table
        cursor.execute("""
            CREATE TABLE crypto_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cryptocurrency_id INTEGER REFERENCES crypto_currencies(id),
                price_usd DECIMAL(20,8) NOT NULL,
                price_btc DECIMAL(20,8),
                volume_24h DECIMAL(20,2),
                market_cap DECIMAL(20,2),
                price_change_24h DECIMAL(10,4),
                price_change_percentage_24h DECIMAL(10,4),
                rsi_14 DECIMAL(5,2),
                volatility_7d DECIMAL(10,6),
                volatility_30d DECIMAL(10,6),
                momentum_score DECIMAL(5,2),
                sentiment_score DECIMAL(5,2),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create crypto_portfolios table
        cursor.execute("""
            CREATE TABLE crypto_portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES core_user(id),
                total_value_usd DECIMAL(20,2) DEFAULT 0,
                total_cost_basis DECIMAL(20,2) DEFAULT 0,
                total_pnl DECIMAL(20,2) DEFAULT 0,
                total_pnl_percentage DECIMAL(10,4) DEFAULT 0,
                portfolio_volatility DECIMAL(10,6) DEFAULT 0,
                sharpe_ratio DECIMAL(10,4) DEFAULT 0,
                max_drawdown DECIMAL(10,4) DEFAULT 0,
                diversification_score DECIMAL(5,2) DEFAULT 0,
                top_holding_percentage DECIMAL(5,2) DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
        """)
        
        # Create crypto_holdings table
        cursor.execute("""
            CREATE TABLE crypto_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER REFERENCES crypto_portfolios(id),
                cryptocurrency_id INTEGER REFERENCES crypto_currencies(id),
                quantity DECIMAL(20,8) NOT NULL,
                average_cost DECIMAL(20,8) NOT NULL,
                current_price DECIMAL(20,8) NOT NULL,
                current_value DECIMAL(20,2) NOT NULL,
                unrealized_pnl DECIMAL(20,2) NOT NULL,
                unrealized_pnl_percentage DECIMAL(10,4) NOT NULL,
                staked_quantity DECIMAL(20,8) DEFAULT 0,
                staking_rewards DECIMAL(20,8) DEFAULT 0,
                staking_apy DECIMAL(5,2),
                is_collateralized BOOLEAN DEFAULT 0,
                collateral_value DECIMAL(20,2) DEFAULT 0,
                loan_amount DECIMAL(20,2) DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(portfolio_id, cryptocurrency_id)
            )
        """)
        
        # Create crypto_trades table
        cursor.execute("""
            CREATE TABLE crypto_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES core_user(id),
                cryptocurrency_id INTEGER REFERENCES crypto_currencies(id),
                trade_type VARCHAR(20) NOT NULL,
                quantity DECIMAL(20,8) NOT NULL,
                price_per_unit DECIMAL(20,8) NOT NULL,
                total_amount DECIMAL(20,2) NOT NULL,
                fees DECIMAL(20,2) DEFAULT 0,
                order_id VARCHAR(100) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'COMPLETED',
                execution_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_sbloc_funded BOOLEAN DEFAULT 0,
                sbloc_loan_id VARCHAR(100)
            )
        """)
        
        # Create crypto_ml_predictions table
        cursor.execute("""
            CREATE TABLE crypto_ml_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cryptocurrency_id INTEGER REFERENCES crypto_currencies(id),
                prediction_type VARCHAR(20) NOT NULL,
                probability DECIMAL(5,4) NOT NULL,
                confidence_level VARCHAR(20) NOT NULL,
                features_used TEXT DEFAULT '{}',
                model_version VARCHAR(50) DEFAULT 'v1.0',
                prediction_horizon_hours INTEGER DEFAULT 24,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                was_correct BOOLEAN,
                actual_return DECIMAL(10,6)
            )
        """)
        
        # Create crypto_sbloc_loans table
        cursor.execute("""
            CREATE TABLE crypto_sbloc_loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES core_user(id),
                cryptocurrency_id INTEGER REFERENCES crypto_currencies(id),
                collateral_quantity DECIMAL(20,8) NOT NULL,
                collateral_value_at_loan DECIMAL(20,2) NOT NULL,
                loan_amount DECIMAL(20,2) NOT NULL,
                interest_rate DECIMAL(5,4) NOT NULL,
                maintenance_margin DECIMAL(5,4) DEFAULT 0.5,
                liquidation_threshold DECIMAL(5,4) DEFAULT 0.4,
                status VARCHAR(20) DEFAULT 'ACTIVE',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create crypto_education_progress table
        cursor.execute("""
            CREATE TABLE crypto_education_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES core_user(id),
                module_name VARCHAR(100) NOT NULL,
                module_type VARCHAR(20) NOT NULL,
                progress_percentage DECIMAL(5,2) DEFAULT 0,
                is_completed BOOLEAN DEFAULT 0,
                completed_at DATETIME,
                quiz_attempts INTEGER DEFAULT 0,
                best_quiz_score DECIMAL(5,2) DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, module_name)
            )
        """)
        
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
        
        print("✅ Crypto currencies seeded successfully!")

if __name__ == "__main__":
    try:
        create_crypto_tables()
        seed_crypto_currencies()
        print("\n🎉 Crypto system setup complete!")
    except Exception as e:
        print(f"❌ Error setting up crypto system: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
