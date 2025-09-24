"""
Celery Tasks for Swing Trading
"""
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np

from core.models import OHLCV, Signal, TraderScore
from .indicators import calculate_all_indicators, validate_ohlcv_data
from .ml_scoring import SwingTradingML, generate_signal_score, create_signal_thesis
from .risk_management import RiskManager

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def scan_symbol_for_signals(self, symbol: str, timeframe: str = "1d"):
    """
    Scan a symbol for swing trading signals
    
    Args:
        symbol: Stock symbol to scan
        timeframe: Timeframe for analysis (1d, 5m, 1h, etc.)
    """
    try:
        logger.info(f"Scanning {symbol} for signals on {timeframe} timeframe")
        
        # Get recent OHLCV data
        ohlcv_data = OHLCV.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('-timestamp')[:100]  # Last 100 data points
        
        if len(ohlcv_data) < 50:
            logger.warning(f"Insufficient data for {symbol}: {len(ohlcv_data)} points")
            return
        
        # Convert to DataFrame
        df_data = []
        for ohlcv in ohlcv_data:
            df_data.append({
                'timestamp': ohlcv.timestamp,
                'open': float(ohlcv.open_price),
                'high': float(ohlcv.high_price),
                'low': float(ohlcv.low_price),
                'close': float(ohlcv.close_price),
                'volume': ohlcv.volume,
                'symbol': symbol
            })
        
        df = pd.DataFrame(df_data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Validate data
        if not validate_ohlcv_data(df):
            logger.error(f"Invalid OHLCV data for {symbol}")
            return
        
        # Calculate indicators
        df_with_indicators = calculate_all_indicators(df)
        
        # Initialize ML system
        ml_system = SwingTradingML()
        
        # Detect patterns
        patterns = ml_system.detect_swing_patterns(df_with_indicators)
        
        # Process each pattern
        for pattern in patterns:
            try:
                # Check if signal already exists for this timestamp
                existing_signal = Signal.objects.filter(
                    symbol=symbol,
                    timeframe=timeframe,
                    triggered_at__date=pattern['timestamp'].date(),
                    signal_type=pattern['pattern_type']
                ).first()
                
                if existing_signal:
                    continue
                
                # Generate signal score
                signal_score = generate_signal_score(pattern['features'], pattern['pattern_type'])
                
                # Calculate risk levels
                risk_manager = RiskManager()
                entry_price = pattern['features'].get('close', df_with_indicators.iloc[-1]['close'])
                atr = pattern['features'].get('atr_14', entry_price * 0.02)
                
                # Determine signal direction
                if 'long' in pattern['pattern_type']:
                    stop_price = entry_price - (atr * 1.2)
                    target_price = entry_price + (atr * 2.5)
                else:
                    stop_price = entry_price + (atr * 1.2)
                    target_price = entry_price - (atr * 2.5)
                
                # Create signal
                signal = Signal.objects.create(
                    symbol=symbol,
                    timeframe=timeframe,
                    triggered_at=pattern['timestamp'],
                    signal_type=pattern['pattern_type'],
                    entry_price=entry_price,
                    stop_price=stop_price,
                    target_price=target_price,
                    ml_score=signal_score,
                    features=pattern['features'],
                    thesis=create_signal_thesis(pattern['pattern_type'], pattern['features']),
                    atr_multiplier=1.2
                )
                
                # Calculate risk/reward ratio
                if stop_price and target_price:
                    risk = abs(entry_price - stop_price)
                    reward = abs(target_price - entry_price)
                    if risk > 0:
                        signal.risk_reward_ratio = reward / risk
                        signal.save()
                
                logger.info(f"Created signal for {symbol}: {pattern['pattern_type']} with score {signal_score:.2%}")
                
            except Exception as e:
                logger.error(f"Error processing pattern for {symbol}: {e}")
                continue
        
        logger.info(f"Completed scanning {symbol} - found {len(patterns)} patterns")
        
    except Exception as e:
        logger.error(f"Error scanning {symbol}: {e}")
        raise


@shared_task
def update_ohlcv_indicators(symbol: str, timeframe: str = "1d"):
    """
    Update technical indicators for OHLCV data
    
    Args:
        symbol: Stock symbol
        timeframe: Timeframe
    """
    try:
        logger.info(f"Updating indicators for {symbol} {timeframe}")
        
        # Get OHLCV data
        ohlcv_data = OHLCV.objects.filter(
            symbol=symbol,
            timeframe=timeframe
        ).order_by('timestamp')
        
        if len(ohlcv_data) < 50:
            logger.warning(f"Insufficient data for {symbol}: {len(ohlcv_data)} points")
            return
        
        # Convert to DataFrame
        df_data = []
        for ohlcv in ohlcv_data:
            df_data.append({
                'timestamp': ohlcv.timestamp,
                'open': float(ohlcv.open_price),
                'high': float(ohlcv.high_price),
                'low': float(ohlcv.low_price),
                'close': float(ohlcv.close_price),
                'volume': ohlcv.volume
            })
        
        df = pd.DataFrame(df_data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate indicators
        df_with_indicators = calculate_all_indicators(df)
        
        # Update OHLCV records with calculated indicators
        for i, (timestamp, row) in enumerate(df_with_indicators.iterrows()):
            try:
                ohlcv = OHLCV.objects.get(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp
                )
                
                # Update indicators
                ohlcv.ema_12 = row.get('ema_12')
                ohlcv.ema_26 = row.get('ema_26')
                ohlcv.rsi_14 = row.get('rsi_14')
                ohlcv.atr_14 = row.get('atr_14')
                ohlcv.volume_sma_20 = row.get('volume_sma_20')
                
                ohlcv.save()
                
            except OHLCV.DoesNotExist:
                continue
            except Exception as e:
                logger.error(f"Error updating OHLCV indicators: {e}")
                continue
        
        logger.info(f"Updated indicators for {symbol} {timeframe}")
        
    except Exception as e:
        logger.error(f"Error updating OHLCV indicators: {e}")
        raise


@shared_task
def validate_signals():
    """
    Validate existing signals against current market data
    """
    try:
        logger.info("Starting signal validation")
        
        # Get active signals from the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_signals = Signal.objects.filter(
            is_active=True,
            triggered_at__gte=thirty_days_ago,
            is_validated=False
        )
        
        validated_count = 0
        
        for signal in active_signals:
            try:
                # Get current price data
                latest_ohlcv = OHLCV.objects.filter(
                    symbol=signal.symbol,
                    timeframe=signal.timeframe
                ).order_by('-timestamp').first()
                
                if not latest_ohlcv:
                    continue
                
                current_price = float(latest_ohlcv.close_price)
                days_since_triggered = (timezone.now() - signal.triggered_at).days
                
                # Check if signal should be validated
                should_validate = False
                validation_price = current_price
                
                if signal.signal_type.endswith('_long'):
                    # Long signal - check if target hit or stop hit
                    if signal.target_price and current_price >= float(signal.target_price):
                        should_validate = True
                        validation_price = float(signal.target_price)
                    elif signal.stop_price and current_price <= float(signal.stop_price):
                        should_validate = True
                        validation_price = float(signal.stop_price)
                else:
                    # Short signal - check if target hit or stop hit
                    if signal.target_price and current_price <= float(signal.target_price):
                        should_validate = True
                        validation_price = float(signal.target_price)
                    elif signal.stop_price and current_price >= float(signal.stop_price):
                        should_validate = True
                        validation_price = float(signal.stop_price)
                
                # Time-based validation (30 days max)
                if days_since_triggered >= 30:
                    should_validate = True
                    validation_price = current_price
                
                if should_validate:
                    signal.is_validated = True
                    signal.validation_price = validation_price
                    signal.validation_timestamp = timezone.now()
                    signal.is_active = False
                    signal.save()
                    
                    validated_count += 1
                    logger.info(f"Validated signal {signal.id} for {signal.symbol}")
                
            except Exception as e:
                logger.error(f"Error validating signal {signal.id}: {e}")
                continue
        
        logger.info(f"Validated {validated_count} signals")
        
    except Exception as e:
        logger.error(f"Error in signal validation: {e}")
        raise


@shared_task
def update_trader_scores():
    """
    Update trader performance scores
    """
    try:
        logger.info("Updating trader scores")
        
        # Get all users with signals
        users_with_signals = Signal.objects.values_list('created_by', flat=True).distinct()
        
        for user_id in users_with_signals:
            if not user_id:
                continue
                
            try:
                # Get user's signals
                user_signals = Signal.objects.filter(created_by_id=user_id)
                
                if not user_signals.exists():
                    continue
                
                # Get or create trader score
                trader_score, created = TraderScore.objects.get_or_create(user_id=user_id)
                
                # Calculate metrics
                total_signals = user_signals.count()
                validated_signals = user_signals.filter(is_validated=True)
                
                if validated_signals.exists():
                    # Calculate win rate
                    winning_signals = 0
                    total_pnl = 0
                    
                    for signal in validated_signals:
                        if signal.signal_type.endswith('_long'):
                            if signal.validation_price and signal.validation_price > float(signal.entry_price):
                                winning_signals += 1
                                pnl = (signal.validation_price - float(signal.entry_price)) / float(signal.entry_price)
                            else:
                                pnl = (signal.validation_price - float(signal.entry_price)) / float(signal.entry_price)
                        else:
                            if signal.validation_price and signal.validation_price < float(signal.entry_price):
                                winning_signals += 1
                                pnl = (float(signal.entry_price) - signal.validation_price) / float(signal.entry_price)
                            else:
                                pnl = (float(signal.entry_price) - signal.validation_price) / float(signal.entry_price)
                        
                        total_pnl += pnl
                    
                    win_rate = winning_signals / validated_signals.count()
                    avg_return = total_pnl / validated_signals.count()
                    
                    # Calculate consistency score (based on win rate stability)
                    consistency_score = min(1.0, win_rate * 1.2)  # Simplified
                    
                    # Calculate accuracy score (based on ML score vs actual outcome)
                    accuracy_score = min(1.0, win_rate * 1.1)  # Simplified
                    
                    # Calculate discipline score (based on risk management)
                    signals_with_stops = user_signals.filter(stop_price__isnull=False).count()
                    discipline_score = signals_with_stops / total_signals if total_signals > 0 else 0
                    
                    # Update trader score
                    trader_score.total_signals = total_signals
                    trader_score.validated_signals = validated_signals.count()
                    trader_score.win_rate = win_rate
                    trader_score.accuracy_score = accuracy_score
                    trader_score.consistency_score = consistency_score
                    trader_score.discipline_score = discipline_score
                    trader_score.overall_score = (
                        accuracy_score * 0.4 +
                        consistency_score * 0.3 +
                        discipline_score * 0.3
                    )
                    
                    trader_score.save()
                    
                    logger.info(f"Updated trader score for user {user_id}: {trader_score.overall_score:.2%}")
                
            except Exception as e:
                logger.error(f"Error updating trader score for user {user_id}: {e}")
                continue
        
        logger.info("Completed trader score updates")
        
    except Exception as e:
        logger.error(f"Error updating trader scores: {e}")
        raise


@shared_task
def cleanup_old_data():
    """
    Clean up old OHLCV data and inactive signals
    """
    try:
        logger.info("Starting data cleanup")
        
        # Clean up OHLCV data older than 1 year
        one_year_ago = timezone.now() - timedelta(days=365)
        old_ohlcv = OHLCV.objects.filter(timestamp__lt=one_year_ago)
        old_ohlcv_count = old_ohlcv.count()
        old_ohlcv.delete()
        
        # Clean up inactive signals older than 6 months
        six_months_ago = timezone.now() - timedelta(days=180)
        old_signals = Signal.objects.filter(
            is_active=False,
            triggered_at__lt=six_months_ago
        )
        old_signals_count = old_signals.count()
        old_signals.delete()
        
        logger.info(f"Cleaned up {old_ohlcv_count} old OHLCV records and {old_signals_count} old signals")
        
    except Exception as e:
        logger.error(f"Error in data cleanup: {e}")
        raise


@shared_task
def generate_daily_report():
    """
    Generate daily swing trading report
    """
    try:
        logger.info("Generating daily report")
        
        # Get today's signals
        today = timezone.now().date()
        today_signals = Signal.objects.filter(triggered_at__date=today)
        
        # Get signal statistics
        total_signals = today_signals.count()
        signal_types = today_signals.values('signal_type').annotate(count=Count('id'))
        
        # Get top performing symbols
        top_symbols = today_signals.values('symbol').annotate(count=Count('id')).order_by('-count')[:10]
        
        # Get average ML score
        avg_ml_score = today_signals.aggregate(avg_score=Avg('ml_score'))['avg_score'] or 0
        
        report = {
            'date': today.isoformat(),
            'total_signals': total_signals,
            'signal_types': list(signal_types),
            'top_symbols': list(top_symbols),
            'avg_ml_score': float(avg_ml_score),
            'generated_at': timezone.now().isoformat()
        }
        
        logger.info(f"Daily report generated: {total_signals} signals, avg score {avg_ml_score:.2%}")
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise


@shared_task
def train_ml_models():
    """
    Train ML models on historical data
    """
    try:
        logger.info("Training ML models")
        
        # Get historical data for training
        training_data = []
        
        # Get signals from the last 6 months
        six_months_ago = timezone.now() - timedelta(days=180)
        historical_signals = Signal.objects.filter(
            triggered_at__gte=six_months_ago,
            is_validated=True
        )
        
        for signal in historical_signals:
            # Get OHLCV data around the signal
            ohlcv_data = OHLCV.objects.filter(
                symbol=signal.symbol,
                timeframe=signal.timeframe,
                timestamp__lte=signal.triggered_at
            ).order_by('-timestamp')[:50]
            
            if len(ohlcv_data) >= 30:
                # Convert to DataFrame and calculate indicators
                df_data = []
                for ohlcv in ohlcv_data:
                    df_data.append({
                        'timestamp': ohlcv.timestamp,
                        'open': float(ohlcv.open_price),
                        'high': float(ohlcv.high_price),
                        'low': float(ohlcv.low_price),
                        'close': float(ohlcv.close_price),
                        'volume': ohlcv.volume
                    })
                
                df = pd.DataFrame(df_data)
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                
                # Calculate indicators
                df_with_indicators = calculate_all_indicators(df)
                
                if len(df_with_indicators) > 0:
                    # Get features from the signal date
                    signal_row = df_with_indicators.iloc[-1]
                    
                    # Determine if signal was profitable
                    is_profitable = False
                    if signal.validation_price:
                        if signal.signal_type.endswith('_long'):
                            is_profitable = signal.validation_price > float(signal.entry_price)
                        else:
                            is_profitable = signal.validation_price < float(signal.entry_price)
                    
                    training_data.append({
                        'features': signal_row.to_dict(),
                        'target': 1 if is_profitable else 0,
                        'signal_type': signal.signal_type
                    })
        
        if len(training_data) >= 100:
            # Initialize ML system and train
            ml_system = SwingTradingML()
            
            # Convert to DataFrame
            df_training = pd.DataFrame(training_data)
            
            # Extract features
            feature_columns = [col for col in df_training['features'].iloc[0].keys() if col not in ['timestamp']]
            X = pd.DataFrame(df_training['features'].tolist())[feature_columns].fillna(0)
            y = df_training['target']
            
            # Train models
            ml_system.train_models(pd.concat([X, y], axis=1), target_column='target')
            
            logger.info(f"Trained ML models on {len(training_data)} samples")
        else:
            logger.warning(f"Insufficient training data: {len(training_data)} samples")
        
    except Exception as e:
        logger.error(f"Error training ML models: {e}")
        raise
