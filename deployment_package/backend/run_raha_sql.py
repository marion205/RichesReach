#!/usr/bin/env python
"""Run 0025 and 0029 table-creation SQL so raha_signals and day_trading_signals exist."""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "richesreach.settings")
django.setup()

from django.db import connection

# 0025: day_trading_signals, strategy_performance, user_risk_budgets, signal_performance
sql_0025 = """
CREATE TABLE IF NOT EXISTS "day_trading_signals" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "signal_id" char(32) NOT NULL UNIQUE, "generated_at" datetime NOT NULL, "mode" varchar(10) NOT NULL, "symbol" varchar(10) NOT NULL, "side" varchar(5) NOT NULL, "features" text NOT NULL, "score" decimal NOT NULL, "entry_price" decimal NOT NULL, "stop_price" decimal NOT NULL, "target_prices" text NOT NULL, "time_stop_minutes" integer NOT NULL, "atr_5m" decimal NULL, "suggested_size_shares" integer NOT NULL, "risk_per_trade_pct" decimal NOT NULL, "notes" text NOT NULL);
CREATE TABLE IF NOT EXISTS "strategy_performance" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "mode" varchar(10) NOT NULL, "period" varchar(10) NOT NULL, "period_start" datetime NOT NULL, "period_end" datetime NOT NULL, "total_signals" integer NOT NULL, "signals_evaluated" integer NOT NULL, "winning_signals" integer NOT NULL, "losing_signals" integer NOT NULL, "breakeven_signals" integer NOT NULL, "win_rate" decimal NOT NULL, "total_pnl_dollars" decimal NOT NULL, "total_pnl_percent" decimal NOT NULL, "avg_pnl_per_signal" decimal NOT NULL, "sharpe_ratio" decimal NULL, "max_drawdown" decimal NULL, "max_drawdown_duration_days" integer NULL, "sortino_ratio" decimal NULL, "calmar_ratio" decimal NULL, "worst_single_loss" decimal NULL, "best_single_win" decimal NULL, "equity_curve" text NOT NULL, "calculated_at" datetime NOT NULL, "notes" text NOT NULL);
CREATE TABLE IF NOT EXISTS "user_risk_budgets" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "account_value" decimal NOT NULL, "max_daily_risk_pct" decimal NOT NULL, "daily_risk_used_pct" decimal NOT NULL, "daily_risk_reset_date" date NOT NULL, "max_weekly_risk_pct" decimal NOT NULL, "weekly_risk_used_pct" decimal NOT NULL, "weekly_risk_reset_date" date NOT NULL, "max_daily_loss_pct" decimal NOT NULL, "daily_pnl_pct" decimal NOT NULL, "trading_paused" bool NOT NULL, "trading_paused_until" datetime NULL, "pause_reason" text NOT NULL, "max_position_size_pct" decimal NOT NULL, "min_position_size_pct" decimal NOT NULL, "use_volatility_sizing" bool NOT NULL, "volatility_lookback_days" integer NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "user_id" bigint NOT NULL UNIQUE REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE IF NOT EXISTS "signal_performance" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "horizon" varchar(5) NOT NULL, "evaluated_at" datetime NOT NULL, "price_at_horizon" decimal NOT NULL, "pnl_dollars" decimal NOT NULL, "pnl_percent" decimal NOT NULL, "hit_stop" bool NOT NULL, "hit_target_1" bool NOT NULL, "hit_target_2" bool NOT NULL, "hit_time_stop" bool NOT NULL, "outcome" varchar(20) NOT NULL, "max_favorable_excursion" decimal NULL, "max_adverse_excursion" decimal NULL, "signal_id" bigint NOT NULL REFERENCES "day_trading_signals" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX IF NOT EXISTS "day_trading_signals_generated_at_1a4cb023" ON "day_trading_signals" ("generated_at");
CREATE INDEX IF NOT EXISTS "day_trading_signals_mode_ad471933" ON "day_trading_signals" ("mode");
CREATE INDEX IF NOT EXISTS "day_trading_signals_symbol_69cea6bb" ON "day_trading_signals" ("symbol");
CREATE INDEX IF NOT EXISTS "day_trading_generat_bc3fc7_idx" ON "day_trading_signals" ("generated_at", "mode");
CREATE INDEX IF NOT EXISTS "day_trading_symbol_4a226c_idx" ON "day_trading_signals" ("symbol", "generated_at");
CREATE INDEX IF NOT EXISTS "day_trading_mode_e33e91_idx" ON "day_trading_signals" ("mode", "score");
CREATE UNIQUE INDEX IF NOT EXISTS "strategy_performance_mode_period_period_start_period_end_fae67ca2_uniq" ON "strategy_performance" ("mode", "period", "period_start", "period_end");
CREATE INDEX IF NOT EXISTS "signal_performance_signal_id_163b699e" ON "signal_performance" ("signal_id");
"""

# 0029: raha_* (depends on day_trading_signals)
sql_0029 = """
CREATE TABLE IF NOT EXISTS "raha_strategies" ("id" char(32) NOT NULL PRIMARY KEY, "slug" varchar(100) NOT NULL UNIQUE, "name" varchar(200) NOT NULL, "category" varchar(20) NOT NULL, "description" text NOT NULL, "influencer_ref" varchar(50) NOT NULL, "market_type" varchar(20) NOT NULL, "timeframe_supported" text NOT NULL, "enabled" bool NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL);
CREATE TABLE IF NOT EXISTS "raha_strategy_versions" ("id" char(32) NOT NULL PRIMARY KEY, "version" integer NOT NULL, "config_schema" text NOT NULL, "logic_ref" varchar(100) NOT NULL, "is_default" bool NOT NULL, "created_at" datetime NOT NULL, "strategy_id" char(32) NOT NULL REFERENCES "raha_strategies" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE IF NOT EXISTS "raha_signals" ("id" char(32) NOT NULL PRIMARY KEY, "symbol" varchar(10) NOT NULL, "timestamp" datetime NOT NULL, "timeframe" varchar(10) NOT NULL, "signal_type" varchar(20) NOT NULL, "price" decimal NOT NULL, "stop_loss" decimal NULL, "take_profit" decimal NULL, "confidence_score" decimal NOT NULL, "meta" text NOT NULL, "day_trading_signal_id" bigint NULL REFERENCES "day_trading_signals" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NULL REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED, "strategy_version_id" char(32) NOT NULL REFERENCES "raha_strategy_versions" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE IF NOT EXISTS "raha_backtest_runs" ("id" char(32) NOT NULL PRIMARY KEY, "symbol" varchar(10) NOT NULL, "timeframe" varchar(10) NOT NULL, "start_date" date NOT NULL, "end_date" date NOT NULL, "parameters" text NOT NULL, "status" varchar(20) NOT NULL, "metrics" text NULL, "equity_curve" text NULL, "trade_log" text NULL, "created_at" datetime NOT NULL, "completed_at" datetime NULL, "user_id" bigint NOT NULL REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED, "strategy_version_id" char(32) NOT NULL REFERENCES "raha_strategy_versions" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE IF NOT EXISTS "raha_user_strategy_settings" ("id" char(32) NOT NULL PRIMARY KEY, "parameters" text NOT NULL, "enabled" bool NOT NULL, "auto_trade_enabled" bool NOT NULL, "max_daily_loss_percent" decimal NULL, "max_concurrent_positions" integer NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "strategy_version_id" char(32) NOT NULL REFERENCES "raha_strategy_versions" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NOT NULL REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX IF NOT EXISTS "raha_strategies_category_d64bef05" ON "raha_strategies" ("category");
CREATE INDEX IF NOT EXISTS "raha_strategies_market_type_7b8e0b6b" ON "raha_strategies" ("market_type");
CREATE INDEX IF NOT EXISTS "raha_strategies_enabled_e5bea267" ON "raha_strategies" ("enabled");
CREATE UNIQUE INDEX IF NOT EXISTS "raha_strategy_versions_strategy_id_version_f99372bd_uniq" ON "raha_strategy_versions" ("strategy_id", "version");
CREATE INDEX IF NOT EXISTS "raha_strategy_versions_is_default_954072c0" ON "raha_strategy_versions" ("is_default");
CREATE INDEX IF NOT EXISTS "raha_strategy_versions_strategy_id_8e256844" ON "raha_strategy_versions" ("strategy_id");
CREATE INDEX IF NOT EXISTS "raha_signals_symbol_65252298" ON "raha_signals" ("symbol");
CREATE INDEX IF NOT EXISTS "raha_signals_timestamp_3fa53795" ON "raha_signals" ("timestamp");
CREATE INDEX IF NOT EXISTS "raha_signals_day_trading_signal_id_cc2bfba9" ON "raha_signals" ("day_trading_signal_id");
CREATE INDEX IF NOT EXISTS "raha_signals_user_id_7befbd50" ON "raha_signals" ("user_id");
CREATE INDEX IF NOT EXISTS "raha_signals_strategy_version_id_026f9b06" ON "raha_signals" ("strategy_version_id");
CREATE INDEX IF NOT EXISTS "raha_signal_timesta_bb2499_idx" ON "raha_signals" ("timestamp", "strategy_version_id");
CREATE INDEX IF NOT EXISTS "raha_signal_symbol_2131ed_idx" ON "raha_signals" ("symbol", "timestamp");
CREATE INDEX IF NOT EXISTS "raha_signal_user_id_7f89df_idx" ON "raha_signals" ("user_id", "timestamp");
CREATE INDEX IF NOT EXISTS "raha_signal_strateg_650647_idx" ON "raha_signals" ("strategy_version_id", "signal_type");
CREATE INDEX IF NOT EXISTS "raha_backtest_runs_symbol_523826a9" ON "raha_backtest_runs" ("symbol");
CREATE INDEX IF NOT EXISTS "raha_backtest_runs_start_date_d0e22608" ON "raha_backtest_runs" ("start_date");
CREATE INDEX IF NOT EXISTS "raha_backtest_runs_end_date_c6218016" ON "raha_backtest_runs" ("end_date");
CREATE INDEX IF NOT EXISTS "raha_backtest_runs_status_7b0d1e3c" ON "raha_backtest_runs" ("status");
CREATE INDEX IF NOT EXISTS "raha_backtest_runs_user_id_c40e64ac" ON "raha_backtest_runs" ("user_id");
CREATE INDEX IF NOT EXISTS "raha_backtest_runs_strategy_version_id_ceeaf276" ON "raha_backtest_runs" ("strategy_version_id");
CREATE UNIQUE INDEX IF NOT EXISTS "raha_user_strategy_settings_user_id_strategy_version_id_9cc7d526_uniq" ON "raha_user_strategy_settings" ("user_id", "strategy_version_id");
CREATE INDEX IF NOT EXISTS "raha_user_strategy_settings_enabled_c063ea5a" ON "raha_user_strategy_settings" ("enabled");
CREATE INDEX IF NOT EXISTS "raha_user_strategy_settings_strategy_version_id_5bc91c3b" ON "raha_user_strategy_settings" ("strategy_version_id");
CREATE INDEX IF NOT EXISTS "raha_user_strategy_settings_user_id_c5a6ba8c" ON "raha_user_strategy_settings" ("user_id");
"""

def main():
    with connection.cursor() as cur:
        for block in (sql_0025.strip().split(";"), sql_0029.strip().split(";")):
            for stmt in block:
                stmt = stmt.strip()
                if not stmt:
                    continue
                try:
                    cur.execute(stmt)
                    print("OK:", stmt[:60] + "...")
                except Exception as e:
                    if "already exists" in str(e) or "duplicate" in str(e).lower():
                        print("SKIP (exists):", stmt[:50] + "...")
                    else:
                        print("ERROR:", stmt[:60], "->", e)
    print("Done.")

if __name__ == "__main__":
    main()
