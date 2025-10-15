#!/usr/bin/env python3
"""
Create swing trading tables directly and mark migrations as applied
This bypasses the migration issues and creates the tables we need
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

def create_swing_trading_tables():
    """Create swing trading tables directly"""
    
    with connection.cursor() as cursor:
        print("Creating swing trading tables...")
        
        # Create OHLCV table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS core_ohlcv (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(10) NOT NULL,
                timestamp DATETIME NOT NULL,
                timeframe VARCHAR(5) NOT NULL DEFAULT '1d',
                open_price DECIMAL(10,2) NOT NULL,
                high_price DECIMAL(10,2) NOT NULL,
                low_price DECIMAL(10,2) NOT NULL,
                close_price DECIMAL(10,2) NOT NULL,
                volume BIGINT NOT NULL,
                ema_12 DECIMAL(10,2),
                ema_26 DECIMAL(10,2),
                rsi_14 DECIMAL(5,2),
                atr_14 DECIMAL(10,2),
                volume_sma_20 BIGINT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                UNIQUE(symbol, timestamp, timeframe)
            )
        """)
        print("✅ Created core_ohlcv table")
        
        # Create Signal table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS core_signal (
                id VARCHAR(36) PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                timeframe VARCHAR(5) NOT NULL,
                triggered_at DATETIME NOT NULL,
                kind VARCHAR(50) NOT NULL,
                features TEXT NOT NULL,
                ml_score DECIMAL(3,2) NOT NULL,
                thesis TEXT,
                entry_price DECIMAL(10,2),
                stop_price DECIMAL(10,2),
                target_price DECIMAL(10,2),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_by_id INTEGER,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (created_by_id) REFERENCES core_user (id)
            )
        """)
        print("✅ Created core_signal table")
        
        # Create SignalLike table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS core_signallike (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id VARCHAR(36) NOT NULL,
                user_id INTEGER NOT NULL,
                created_at DATETIME NOT NULL,
                UNIQUE(signal_id, user_id),
                FOREIGN KEY (signal_id) REFERENCES core_signal (id),
                FOREIGN KEY (user_id) REFERENCES core_user (id)
            )
        """)
        print("✅ Created core_signallike table")
        
        # Create SignalComment table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS core_signalcomment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id VARCHAR(36) NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (signal_id) REFERENCES core_signal (id),
                FOREIGN KEY (user_id) REFERENCES core_user (id)
            )
        """)
        print("✅ Created core_signalcomment table")
        
        # Create TraderScore table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS core_traderscore (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                accuracy DECIMAL(5,2) NOT NULL,
                total_signals INTEGER NOT NULL,
                winning_signals INTEGER NOT NULL,
                avg_return DECIMAL(5,2) NOT NULL,
                sharpe_ratio DECIMAL(5,2) NOT NULL,
                max_drawdown DECIMAL(5,2) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                UNIQUE(user_id),
                FOREIGN KEY (user_id) REFERENCES core_user (id)
            )
        """)
        print("✅ Created core_traderscore table")
        
        # Create BacktestStrategy table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS core_backteststrategy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                strategy_type VARCHAR(50) NOT NULL,
                parameters TEXT NOT NULL,
                total_return DECIMAL(5,2),
                win_rate DECIMAL(5,2),
                max_drawdown DECIMAL(5,2),
                sharpe_ratio DECIMAL(5,2),
                total_trades INTEGER,
                is_public BOOLEAN NOT NULL DEFAULT 0,
                likes_count INTEGER NOT NULL DEFAULT 0,
                shares_count INTEGER NOT NULL DEFAULT 0,
                user_id INTEGER NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES core_user (id)
            )
        """)
        print("✅ Created core_backteststrategy table")
        
        # Create BacktestResult table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS core_backtestresult (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                timeframe VARCHAR(5) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                initial_capital DECIMAL(12,2) NOT NULL,
                final_capital DECIMAL(12,2) NOT NULL,
                total_return DECIMAL(5,2) NOT NULL,
                annualized_return DECIMAL(5,2) NOT NULL,
                max_drawdown DECIMAL(5,2) NOT NULL,
                sharpe_ratio DECIMAL(5,2) NOT NULL,
                sortino_ratio DECIMAL(5,2),
                calmar_ratio DECIMAL(5,2),
                win_rate DECIMAL(5,2) NOT NULL,
                profit_factor DECIMAL(5,2) NOT NULL,
                total_trades INTEGER NOT NULL,
                winning_trades INTEGER NOT NULL,
                losing_trades INTEGER NOT NULL,
                avg_win DECIMAL(5,2) NOT NULL,
                avg_loss DECIMAL(5,2) NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (strategy_id) REFERENCES core_backteststrategy (id)
            )
        """)
        print("✅ Created core_backtestresult table")
        
        # Create SwingWatchlist table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS core_swingwatchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                symbols TEXT NOT NULL,
                is_public BOOLEAN NOT NULL DEFAULT 0,
                user_id INTEGER NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES core_user (id)
            )
        """)
        print("✅ Created core_swingwatchlist table")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS core_ohlcv_symbol_timestamp_idx ON core_ohlcv(symbol, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS core_ohlcv_symbol_timeframe_timestamp_idx ON core_ohlcv(symbol, timeframe, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS core_signal_symbol_triggered_at_idx ON core_signal(symbol, triggered_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS core_signal_is_active_triggered_at_idx ON core_signal(is_active, triggered_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS core_signalcomment_user_created_at_idx ON core_signalcomment(user_id, created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS core_signallike_user_created_at_idx ON core_signallike(user_id, created_at)")
        
        print("✅ Created indexes")
        
        print("\n🎉 All swing trading tables created successfully!")

def mark_migrations_applied():
    """Mark the swing trading migrations as applied"""
    
    with connection.cursor() as cursor:
        # Insert migration records
        cursor.execute("""
            INSERT OR IGNORE INTO django_migrations (app, name, applied)
            VALUES ('core', '0026_add_swing_trading_models', datetime('now'))
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO django_migrations (app, name, applied)
            VALUES ('core', '0027_swing_pro_upgrade', datetime('now'))
        """)
        
        print("✅ Marked migrations as applied")

if __name__ == "__main__":
    try:
        create_swing_trading_tables()
        mark_migrations_applied()
        print("\n🚀 Swing trading tables are ready!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
