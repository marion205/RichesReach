"""
Weekly Transparency Report Service
Builds full report data: performance, abstentions, trading_mode breakdown, risk metrics.
Used by generate_weekly_report command and Celery task (email + optional public post).
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone

from .models import SignalRecord
from .transparency_dashboard import get_transparency_dashboard


def build_weekly_report_data(
    days: int = 7,
    end: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Build full weekly report data for the last N days.

    Returns:
        Dict with: start, end, performance (incl. profit_factor, max_drawdown),
        abstention_count, abstention_pct, by_trading_mode, key_changes,
        risk_metrics, signals_sample.
    """
    if end is None:
        end = timezone.now()
    start = end - timedelta(days=days)

    dashboard = get_transparency_dashboard()
    performance = dashboard.get_performance_summary(days=days)

    # All signals in period (any status)
    all_signals = SignalRecord.objects.filter(
        entry_timestamp__gte=start,
        entry_timestamp__lte=end,
    ).order_by('-entry_timestamp')

    closed = all_signals.filter(status='CLOSED')
    abstained = all_signals.filter(status='ABSTAINED')
    open_signals = all_signals.filter(status='OPEN')

    total_count = all_signals.count()
    abstention_count = abstained.count()
    abstention_pct = (abstention_count / total_count * 100.0) if total_count else 0.0

    # By trading_mode (paper vs live)
    by_mode: Dict[str, Dict[str, Any]] = {}
    for mode in ['PAPER', 'LIVE']:
        qs = all_signals.filter(trading_mode=mode)
        closed_mode = qs.filter(status='CLOSED')
        pnls = [s.pnl for s in closed_mode if s.pnl is not None]
        by_mode[mode] = {
            'total': qs.count(),
            'closed': closed_mode.count(),
            'abstained': qs.filter(status='ABSTAINED').count(),
            'total_pnl': sum(pnls) if pnls else 0.0,
        }

    # Key changes narrative from performance, abstention, and mode breakdown
    key_changes = _key_changes_from_data(performance, abstention_pct, by_mode)

    # Risk metrics derived from performance (max_drawdown, profit_factor, sharpe)
    risk_metrics = _risk_metrics_from_performance(performance)

    # Sample of recent signals for report body
    signals_sample = []
    for s in closed[:20]:
        signals_sample.append({
            'symbol': s.symbol,
            'action': s.action,
            'entry_price': s.entry_price,
            'exit_price': s.exit_price,
            'pnl': s.pnl,
            'status': s.status,
            'trading_mode': s.trading_mode or 'PAPER',
            'signal_id': s.signal_id or str(s.id),
            'entry_timestamp': s.entry_timestamp.isoformat() if s.entry_timestamp else None,
        })

    return {
        'start': start,
        'end': end,
        'days': days,
        'performance': performance,
        'abstention_count': abstention_count,
        'abstention_pct': round(abstention_pct, 1),
        'by_trading_mode': by_mode,
        'key_changes': key_changes,
        'risk_metrics': risk_metrics,
        'signals_sample': signals_sample,
        'total_signals_all_statuses': total_count,
        'closed_count': closed.count(),
        'open_count': open_signals.count(),
    }


def _key_changes_from_data(
    performance: Dict[str, Any],
    abstention_pct: float,
    by_mode: Dict[str, Dict[str, Any]],
) -> List[str]:
    """Build key-changes narrative from performance, abstention, and mode breakdown."""
    lines = []
    if performance.get('total_signals', 0) > 0:
        lines.append(f"Closed {performance['total_signals']} signals; win rate {performance.get('win_rate', 0):.1f}%; net P&L ${performance.get('total_pnl', 0):.2f} (after costs).")
    if abstention_pct > 0:
        lines.append(f"Abstained {abstention_pct:.1f}% of opportunities (confidence threshold / regime filter).")
    paper_pnl = by_mode.get('PAPER', {}).get('total_pnl', 0)
    live_pnl = by_mode.get('LIVE', {}).get('total_pnl', 0)
    if paper_pnl != 0 or live_pnl != 0:
        lines.append(f"Paper P&L: ${paper_pnl:.2f}; Live P&L: ${live_pnl:.2f}.")
    if not lines:
        lines.append("No trading activity this period.")
    return lines


def _risk_metrics_from_performance(performance: Dict[str, Any]) -> Dict[str, Any]:
    """Derive risk metrics from performance summary (max_drawdown, profit_factor, sharpe)."""
    return {
        'max_drawdown_pct': performance.get('max_drawdown', 0.0),
        'profit_factor': performance.get('profit_factor', 0.0),
        'sharpe_ratio': performance.get('sharpe_ratio', 0.0),
    }


def render_report_markdown(data: Dict[str, Any], dashboard_url: str = '/transparency', methodology_url: str = '/methodology') -> str:
    """Render report data as Markdown."""
    p = data['performance']
    lines = [
        "# Weekly Transparency Report",
        "",
        f"**Period:** {data['start'].strftime('%B %d, %Y')} - {data['end'].strftime('%B %d, %Y')}",
        f"**Generated:** {timezone.now().strftime('%B %d, %Y at %H:%M UTC')}",
        "",
        "---",
        "",
        "## Performance Summary",
        "",
        f"- **Total Signals (closed):** {p.get('total_signals', 0)}",
        f"- **Win Rate:** {p.get('win_rate', 0):.1f}%",
        f"- **Total P&L (net of costs):** ${p.get('total_pnl', 0):.2f}",
        f"- **Average P&L:** ${p.get('avg_pnl', 0):.2f}",
        f"- **Sharpe Ratio:** {p.get('sharpe_ratio', 0):.2f}",
        f"- **Profit Factor:** {p.get('profit_factor', 0):.2f}",
        f"- **Max Drawdown:** {p.get('max_drawdown', 0):.2f}%",
        "",
        "## Abstentions",
        "",
        f"- **Abstained (confidence / regime):** {data['abstention_count']} ({data['abstention_pct']:.1f}% of opportunities)",
        "",
        "## By Trading Mode",
        "",
    ]
    for mode, stats in data['by_trading_mode'].items():
        lines.append(f"- **{mode}:** {stats['total']} signals, {stats['closed']} closed, P&L ${stats['total_pnl']:.2f}")
    lines.extend([
        "",
        "## Key Changes",
        "",
    ])
    for line in data['key_changes']:
        lines.append(f"- {line}")
    lines.extend([
        "",
        "---",
        "",
        "## Recent Signals",
        "",
        "| Symbol | Action | Entry | Exit | P&L | Mode |",
        "|--------|--------|-------|------|-----|------|",
    ])
    for s in data['signals_sample']:
        entry = f"${s['entry_price']:.2f}" if s.get('entry_price') else "N/A"
        exit_ = f"${s['exit_price']:.2f}" if s.get('exit_price') else "N/A"
        pnl = f"${s['pnl']:.2f}" if s.get('pnl') is not None else "N/A"
        lines.append(f"| {s['symbol']} | {s['action']} | {entry} | {exit_} | {pnl} | {s.get('trading_mode', 'PAPER')} |")
    lines.extend([
        "",
        "---",
        "",
        "## Full Data Access",
        "",
        f"- **Dashboard:** {dashboard_url}",
        f"- **Methodology:** {methodology_url}",
        "- **CSV Export:** Available via API / GraphQL",
        "",
        "---",
        "",
        "*This report is generated automatically. All P&L is calculated net of costs.*",
    ])
    return "\n".join(lines)


def anonymized_public_snippet(data: Dict[str, Any]) -> str:
    """Short anonymized summary for public post (e.g. X / blog)."""
    p = data['performance']
    return (
        f"This week: {p.get('total_signals', 0)} signals, "
        f"net ${p.get('total_pnl', 0):.2f} after costs, "
        f"{data['abstention_pct']:.0f}% abstained (regime/confidence). "
        "Full dashboard & CSV: "
    )
