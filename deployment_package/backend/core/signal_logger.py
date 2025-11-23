"""
Signal Logger - Logs every day trading and swing trading pick for performance tracking
"""
import logging
from django.utils import timezone
from decimal import Decimal
from .signal_performance_models import DayTradingSignal, SwingTradingSignal

logger = logging.getLogger(__name__)


def log_day_trading_signal(pick_dict, mode):
    """
    Log a day trading pick to the database for performance tracking.
    
    Args:
        pick_dict: Dict with keys: symbol, side, score, features, risk, notes, universe_source
        mode: 'SAFE' or 'AGGRESSIVE'
    
    Returns:
        DayTradingSignal instance or None if logging fails
    """
    try:
        signal = DayTradingSignal.objects.create(
            generated_at=timezone.now(),
            mode=mode,
            universe_source=pick_dict.get('universe_source', 'CORE'),  # Track source
            symbol=pick_dict.get('symbol', ''),
            side=pick_dict.get('side', 'LONG'),
            features=pick_dict.get('features', {}),
            score=pick_dict.get('score', 0),
            entry_price=pick_dict.get('risk', {}).get('entryPrice', pick_dict.get('risk', {}).get('stop', 0) + pick_dict.get('risk', {}).get('atr5m', 0)),  # Use entryPrice if available
            stop_price=pick_dict.get('risk', {}).get('stop', 0),
            target_prices=pick_dict.get('risk', {}).get('targets', []),
            time_stop_minutes=pick_dict.get('risk', {}).get('timeStopMin', 240),
            atr_5m=pick_dict.get('risk', {}).get('atr5m', 0),
            suggested_size_shares=pick_dict.get('risk', {}).get('sizeShares', 100),
            risk_per_trade_pct=0.005 if mode == 'SAFE' else 0.012,  # 0.5% or 1.2%
            notes=pick_dict.get('notes', '')
        )
        logger.debug(f"✅ Logged signal: {signal.symbol} {signal.side} ({mode}, source: {signal.universe_source})")
        return signal
    except Exception as e:
        logger.error(f"❌ Error logging signal: {e}", exc_info=True)
        return None


def log_signals_batch(picks_list, mode):
    """
    Log multiple signals in a batch.
    
    Args:
        picks_list: List of pick dicts
        mode: 'SAFE' or 'AGGRESSIVE'
    
    Returns:
        List of DayTradingSignal instances
    """
    signals = []
    for pick in picks_list:
        signal = log_day_trading_signal(pick, mode)
        if signal:
            signals.append(signal)
    logger.info(f"📊 Logged {len(signals)} signals for {mode} mode")
    return signals


def log_swing_trading_signal(pick_dict, strategy):
    """
    Log a swing trading pick to the database for performance tracking.
    
    Args:
        pick_dict: Dict with keys: symbol, side, strategy, score, features, risk, entry_price, notes, universe_source
        strategy: 'MOMENTUM', 'BREAKOUT', or 'MEAN_REVERSION'
    
    Returns:
        SwingTradingSignal instance or None if logging fails
    """
    try:
        signal = SwingTradingSignal.objects.create(
            generated_at=timezone.now(),
            strategy=strategy,
            universe_source=pick_dict.get('universe_source', 'CORE'),
            symbol=pick_dict.get('symbol', ''),
            side=pick_dict.get('side', 'LONG'),
            features=pick_dict.get('features', {}),
            score=Decimal(str(pick_dict.get('score', 0))),
            entry_price=Decimal(str(pick_dict.get('entry_price', pick_dict.get('risk', {}).get('stop', 0) + 1))),
            stop_price=Decimal(str(pick_dict.get('risk', {}).get('stop', 0))),
            target_prices=pick_dict.get('risk', {}).get('targets', []),
            hold_days=pick_dict.get('risk', {}).get('holdDays', 3),
            atr_1d=Decimal(str(pick_dict.get('risk', {}).get('atr1d', 0))),
            suggested_size_shares=pick_dict.get('risk', {}).get('sizeShares', 100),
            risk_per_trade_pct=Decimal('0.01'),  # 1% default for swing trades
            notes=pick_dict.get('notes', '')
        )
        logger.debug(f"✅ Logged swing signal: {signal.symbol} {signal.side} ({strategy}, source: {signal.universe_source})")
        return signal
    except Exception as e:
        logger.error(f"❌ Error logging swing signal: {e}", exc_info=True)
        return None


def log_swing_signals_batch(picks_list, strategy):
    """
    Log multiple swing signals in a batch.
    
    Args:
        picks_list: List of pick dicts
        strategy: 'MOMENTUM', 'BREAKOUT', or 'MEAN_REVERSION'
    
    Returns:
        List of SwingTradingSignal instances
    """
    signals = []
    for pick in picks_list:
        signal = log_swing_trading_signal(pick, strategy)
        if signal:
            signals.append(signal)
    logger.info(f"📊 Logged {len(signals)} swing signals for {strategy} strategy")
    return signals

