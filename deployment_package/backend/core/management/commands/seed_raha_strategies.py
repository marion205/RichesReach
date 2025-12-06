"""
Management command to seed initial RAHA strategies into the database.

Usage:
    python manage.py seed_raha_strategies
    python manage.py seed_raha_strategies --reset  # Delete existing strategies first
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.raha_models import Strategy, StrategyVersion
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed initial RAHA strategies (ORB, Momentum, Supply/Demand, Fade ORB)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing strategies before seeding'
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)
        
        if reset:
            self.stdout.write(self.style.WARNING('🗑️  Deleting existing RAHA strategies...'))
            Strategy.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ Deleted existing strategies'))
        
        self.stdout.write(self.style.SUCCESS('\n🌱 Seeding RAHA strategies...\n'))
        
        with transaction.atomic():
            strategies_data = [
                {
                    'slug': 'orb_opening_range_breakout',
                    'name': 'Opening Range Breakout (ORB)',
                    'category': 'FUTURES',
                    'description': 'PJ Trades style ORB strategy. Identifies the opening range (first 15 minutes) and trades breakouts with volume confirmation. Best for NQ, ES, and high-volatility stocks.',
                    'influencer_ref': 'pj_trades',
                    'market_type': 'FUTURES',
                    'timeframe_supported': ['1m', '5m', '15m'],
                    'logic_ref': 'ORB_v1',
                    'config_schema': {
                        'type': 'object',
                        'properties': {
                            'orb_minutes': {
                                'type': 'number',
                                'default': 15,
                                'minimum': 5,
                                'maximum': 30,
                                'description': 'Opening range duration in minutes'
                            },
                            'min_range_atr_pct': {
                                'type': 'number',
                                'default': 0.5,
                                'minimum': 0.1,
                                'maximum': 2.0,
                                'description': 'Minimum range as % of ATR (filters choppy days)'
                            },
                            'volume_multiplier': {
                                'type': 'number',
                                'default': 1.5,
                                'minimum': 1.0,
                                'maximum': 5.0,
                                'description': 'Volume surge multiplier (e.g., 1.5 = 1.5x average)'
                            },
                            'risk_per_trade': {
                                'type': 'number',
                                'default': 0.01,
                                'minimum': 0.001,
                                'maximum': 0.05,
                                'description': 'Risk per trade as % of account'
                            },
                            'take_profit_r': {
                                'type': 'number',
                                'default': 2.0,
                                'minimum': 1.0,
                                'maximum': 5.0,
                                'description': 'Take profit in R multiples'
                            }
                        }
                    }
                },
                {
                    'slug': 'momentum_breakout',
                    'name': 'Momentum Breakout',
                    'category': 'MOMENTUM',
                    'description': 'Ross Cameron style momentum strategy. Trades pre-market gappers (>15%) with volume surge and VWAP confirmation. Best for small-cap stocks and high-volatility days.',
                    'influencer_ref': 'ross_cameron',
                    'market_type': 'STOCKS',
                    'timeframe_supported': ['1m', '5m', '15m'],
                    'logic_ref': 'MOMENTUM_BREAKOUT_v1',
                    'config_schema': {
                        'type': 'object',
                        'properties': {
                            'gap_threshold': {
                                'type': 'number',
                                'default': 15.0,
                                'minimum': 5.0,
                                'maximum': 50.0,
                                'description': 'Minimum gap % to trigger signal'
                            },
                            'volume_multiplier': {
                                'type': 'number',
                                'default': 2.0,
                                'minimum': 1.0,
                                'maximum': 5.0,
                                'description': 'Volume surge multiplier'
                            },
                            'rsi_threshold': {
                                'type': 'number',
                                'default': 60.0,
                                'minimum': 50.0,
                                'maximum': 80.0,
                                'description': 'RSI threshold for entry (longs > threshold, shorts < 100-threshold)'
                            },
                            'risk_per_trade': {
                                'type': 'number',
                                'default': 0.01,
                                'minimum': 0.001,
                                'maximum': 0.05,
                                'description': 'Risk per trade as % of account'
                            },
                            'take_profit_r': {
                                'type': 'number',
                                'default': 2.0,
                                'minimum': 1.0,
                                'maximum': 5.0,
                                'description': 'Take profit in R multiples'
                            }
                        }
                    }
                },
                {
                    'slug': 'supply_demand_reversal',
                    'name': 'Supply/Demand Zone Reversal',
                    'category': 'REVERSAL',
                    'description': 'Steven Hart style supply/demand strategy. Identifies institutional zones and trades pin bar rejections with momentum confirmation. Best for forex and swing trading.',
                    'influencer_ref': 'steven_hart',
                    'market_type': 'FOREX',
                    'timeframe_supported': ['5m', '15m', '1h', '4h'],
                    'logic_ref': 'SUPPLY_DEMAND_v1',
                    'config_schema': {
                        'type': 'object',
                        'properties': {
                            'risk_reward_ratio': {
                                'type': 'number',
                                'default': 2.0,
                                'minimum': 1.0,
                                'maximum': 5.0,
                                'description': 'Minimum risk:reward ratio'
                            },
                            'zone_lookback': {
                                'type': 'number',
                                'default': 20,
                                'minimum': 10,
                                'maximum': 50,
                                'description': 'Candles to look back for swing points'
                            },
                            'risk_per_trade': {
                                'type': 'number',
                                'default': 0.01,
                                'minimum': 0.001,
                                'maximum': 0.05,
                                'description': 'Risk per trade as % of account'
                            }
                        }
                    }
                },
                {
                    'slug': 'fade_orb_failure',
                    'name': 'Fade ORB Failure',
                    'category': 'REVERSAL',
                    'description': 'Trading Champ style fade strategy. Detects false ORB breakouts and trades the reversal on 50% retrace with MACD divergence. Best for choppy markets and mean reversion.',
                    'influencer_ref': 'trading_champ',
                    'market_type': 'STOCKS',
                    'timeframe_supported': ['5m', '15m'],
                    'logic_ref': 'FADE_ORB_v1',
                    'config_schema': {
                        'type': 'object',
                        'properties': {
                            'risk_reward_ratio': {
                                'type': 'number',
                                'default': 3.0,
                                'minimum': 1.0,
                                'maximum': 5.0,
                                'description': 'Risk:reward ratio (higher for fades)'
                            },
                            'orb_minutes': {
                                'type': 'number',
                                'default': 15,
                                'minimum': 5,
                                'maximum': 30,
                                'description': 'Opening range duration'
                            },
                            'retrace_pct': {
                                'type': 'number',
                                'default': 0.5,
                                'minimum': 0.3,
                                'maximum': 0.7,
                                'description': 'Retrace % before entering fade'
                            },
                            'risk_per_trade': {
                                'type': 'number',
                                'default': 0.01,
                                'minimum': 0.001,
                                'maximum': 0.05,
                                'description': 'Risk per trade as % of account'
                            }
                        }
                    }
                }
            ]
            
            for strategy_data in strategies_data:
                slug = strategy_data.pop('slug')
                logic_ref = strategy_data.pop('logic_ref')
                config_schema = strategy_data.pop('config_schema')
                
                # Create or get strategy
                strategy, created = Strategy.objects.get_or_create(
                    slug=slug,
                    defaults=strategy_data
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created strategy: {strategy.name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️  Strategy already exists: {strategy.name}'))
                    # Update existing strategy
                    for key, value in strategy_data.items():
                        setattr(strategy, key, value)
                    strategy.save()
                
                # Create version 1
                version, v_created = StrategyVersion.objects.get_or_create(
                    strategy=strategy,
                    version=1,
                    defaults={
                        'config_schema': config_schema,
                        'logic_ref': logic_ref,
                        'is_default': True
                    }
                )
                
                if v_created:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Created version 1'))
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Version 1 already exists'))
                    # Update existing version
                    version.config_schema = config_schema
                    version.logic_ref = logic_ref
                    version.save()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Successfully seeded RAHA strategies!\n'))
        self.stdout.write(self.style.SUCCESS('📊 Summary:'))
        self.stdout.write(f'   • Total strategies: {Strategy.objects.count()}')
        self.stdout.write(f'   • Total versions: {StrategyVersion.objects.count()}\n')
        
        self.stdout.write(self.style.SUCCESS('🚀 Next steps:'))
        self.stdout.write('   1. Run migrations: python manage.py migrate')
        self.stdout.write('   2. Test GraphQL: query { strategies { id name } }')
        self.stdout.write('   3. Enable strategies via GraphQL mutations\n')

