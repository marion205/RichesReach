"""
RichesReach Investment Committee - Strategy Governance System

This is your "Citadel Board" - defines KPI targets, thresholds, and rules for
when strategies need review, modification, or retirement.

Think of this as your internal Investment Committee that reviews strategy health
the same way Citadel reviews pod performance.
"""
from django.db import models
from django.utils import timezone
from decimal import Decimal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StrategyStatus(models.TextChoices):
    """Strategy health status"""
    ACTIVE = 'ACTIVE', 'Active - Meeting all KPIs'
    WATCH = 'WATCH', 'Watch - Below target but above minimum'
    REVIEW = 'REVIEW', 'Review Required - Below minimum thresholds'
    PAUSED = 'PAUSED', 'Paused - Temporarily disabled'
    RETIRED = 'RETIRED', 'Retired - Permanently disabled'


class StrategyKPITargets:
    """
    KPI targets for each mode (SAFE vs AGGRESSIVE).
    
    These are the "Investment Committee" standards - what we expect
    from a strategy to keep it active.
    """
    
    # SAFE mode targets (conservative, retail-friendly)
    SAFE_TARGETS = {
        'min_sharpe_ratio': Decimal('1.0'),  # Minimum Sharpe to stay active
        'target_sharpe_ratio': Decimal('1.5'),  # Target Sharpe (what we aim for)
        'min_win_rate': Decimal('45.0'),  # Minimum win rate %
        'target_win_rate': Decimal('55.0'),  # Target win rate %
        'max_drawdown_pct': Decimal('8.0'),  # Max acceptable drawdown %
        'min_signals_evaluated': 50,  # Need at least 50 signals before judging
        'min_avg_pnl_per_signal': Decimal('0.3'),  # Minimum 0.3% avg return per signal
        'max_worst_single_loss': Decimal('5.0'),  # Max acceptable single loss %
        'min_calmar_ratio': Decimal('0.5'),  # Return / Max DD ratio
    }
    
    # AGGRESSIVE mode targets (higher risk, higher reward)
    AGGRESSIVE_TARGETS = {
        'min_sharpe_ratio': Decimal('0.8'),  # Lower minimum (more volatile)
        'target_sharpe_ratio': Decimal('1.2'),  # Target Sharpe
        'min_win_rate': Decimal('40.0'),  # Lower win rate acceptable
        'target_win_rate': Decimal('50.0'),  # Target win rate %
        'max_drawdown_pct': Decimal('15.0'),  # Higher drawdown acceptable
        'min_signals_evaluated': 50,  # Same minimum sample size
        'min_avg_pnl_per_signal': Decimal('0.5'),  # Higher avg return expected
        'max_worst_single_loss': Decimal('8.0'),  # Higher single loss acceptable
        'min_calmar_ratio': Decimal('0.3'),  # Lower Calmar acceptable
    }
    
    @classmethod
    def get_targets(cls, mode: str) -> dict:
        """Get KPI targets for a specific mode"""
        if mode == 'SAFE':
            return cls.SAFE_TARGETS
        elif mode == 'AGGRESSIVE':
            return cls.AGGRESSIVE_TARGETS
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    @classmethod
    def get_minimum_thresholds(cls, mode: str) -> dict:
        """Get minimum thresholds (below which strategy needs review)"""
        targets = cls.get_targets(mode)
        return {
            'sharpe_ratio': targets['min_sharpe_ratio'],
            'win_rate': targets['min_win_rate'],
            'max_drawdown': targets['max_drawdown_pct'],
            'avg_pnl': targets['min_avg_pnl_per_signal'],
            'worst_loss': targets['max_worst_single_loss'],
            'calmar_ratio': targets['min_calmar_ratio'],
        }
    
    @classmethod
    def get_target_values(cls, mode: str) -> dict:
        """Get target values (what we aim for)"""
        targets = cls.get_targets(mode)
        return {
            'sharpe_ratio': targets['target_sharpe_ratio'],
            'win_rate': targets['target_win_rate'],
        }


class StrategyHealthCheck:
    """
    Evaluates a strategy's performance against Investment Committee KPIs.
    Returns status and recommendations.
    """
    
    def __init__(self, strategy_performance, mode: str):
        """
        Args:
            strategy_performance: StrategyPerformance model instance
            mode: 'SAFE' or 'AGGRESSIVE'
        """
        self.strategy = strategy_performance
        self.mode = mode
        self.targets = StrategyKPITargets.get_targets(mode)
        self.minimums = StrategyKPITargets.get_minimum_thresholds(mode)
    
    def evaluate(self) -> dict:
        """
        Evaluate strategy health and return status + recommendations.
        
        Returns:
            {
                'status': StrategyStatus,
                'score': float (0-100),
                'issues': list of issues found,
                'recommendations': list of recommendations,
                'kpi_status': dict of each KPI's status
            }
        """
        issues = []
        recommendations = []
        kpi_status = {}
        score = 100.0
        
        # Check if we have enough data
        if self.strategy.signals_evaluated < self.targets['min_signals_evaluated']:
            return {
                'status': StrategyStatus.WATCH,
                'score': 50.0,
                'issues': [f"Insufficient data: {self.strategy.signals_evaluated} signals (need {self.targets['min_signals_evaluated']})"],
                'recommendations': ['Continue collecting data before full evaluation'],
                'kpi_status': {},
                'insufficient_data': True
            }
        
        # Check Sharpe ratio
        sharpe = self.strategy.sharpe_ratio or Decimal('0.0')
        if sharpe < self.minimums['sharpe_ratio']:
            issues.append(f"Sharpe ratio {sharpe:.2f} below minimum {self.minimums['sharpe_ratio']}")
            score -= 20
            kpi_status['sharpe'] = 'FAIL'
        elif sharpe < self.targets['target_sharpe_ratio']:
            issues.append(f"Sharpe ratio {sharpe:.2f} below target {self.targets['target_sharpe_ratio']}")
            score -= 10
            kpi_status['sharpe'] = 'WATCH'
        else:
            kpi_status['sharpe'] = 'PASS'
        
        # Check win rate
        win_rate = self.strategy.win_rate or Decimal('0.0')
        if win_rate < self.minimums['win_rate']:
            issues.append(f"Win rate {win_rate:.1f}% below minimum {self.minimums['win_rate']}%")
            score -= 15
            kpi_status['win_rate'] = 'FAIL'
        elif win_rate < self.targets['target_win_rate']:
            issues.append(f"Win rate {win_rate:.1f}% below target {self.targets['target_win_rate']}%")
            score -= 7
            kpi_status['win_rate'] = 'WATCH'
        else:
            kpi_status['win_rate'] = 'PASS'
        
        # Check max drawdown
        max_dd = abs(self.strategy.max_drawdown or Decimal('0.0'))
        if max_dd > self.minimums['max_drawdown']:
            issues.append(f"Max drawdown {max_dd:.1f}% exceeds limit {self.minimums['max_drawdown']}%")
            score -= 20
            kpi_status['max_drawdown'] = 'FAIL'
        else:
            kpi_status['max_drawdown'] = 'PASS'
        
        # Check average PnL
        avg_pnl = self.strategy.avg_pnl_per_signal or Decimal('0.0')
        if avg_pnl < self.minimums['avg_pnl']:
            issues.append(f"Avg PnL {avg_pnl:.2f}% below minimum {self.minimums['avg_pnl']}%")
            score -= 15
            kpi_status['avg_pnl'] = 'FAIL'
        else:
            kpi_status['avg_pnl'] = 'PASS'
        
        # Check worst single loss
        worst_loss = abs(self.strategy.worst_single_loss or Decimal('0.0'))
        if worst_loss > self.minimums['worst_loss']:
            issues.append(f"Worst single loss {worst_loss:.1f}% exceeds limit {self.minimums['worst_loss']}%")
            score -= 10
            kpi_status['worst_loss'] = 'FAIL'
        else:
            kpi_status['worst_loss'] = 'PASS'
        
        # Check Calmar ratio
        calmar = self.strategy.calmar_ratio or Decimal('0.0')
        if calmar < self.minimums['calmar_ratio']:
            issues.append(f"Calmar ratio {calmar:.2f} below minimum {self.minimums['calmar_ratio']}")
            score -= 10
            kpi_status['calmar'] = 'FAIL'
        else:
            kpi_status['calmar'] = 'PASS'
        
        # Determine status
        if score < 50:
            status = StrategyStatus.REVIEW
            recommendations.append("Strategy requires immediate review - multiple KPIs failing")
            recommendations.append("Consider: tightening filters, reducing universe, or pausing strategy")
        elif score < 75:
            status = StrategyStatus.WATCH
            recommendations.append("Strategy below target - monitor closely")
            recommendations.append("Consider: adjusting parameters or universe selection")
        else:
            status = StrategyStatus.ACTIVE
            recommendations.append("Strategy meeting all targets - continue as is")
        
        # Add mode-specific recommendations
        if self.mode == 'SAFE' and win_rate < 50:
            recommendations.append("For SAFE mode, consider focusing on higher-probability setups")
        elif self.mode == 'AGGRESSIVE' and max_dd > 12:
            recommendations.append("For AGGRESSIVE mode, consider tightening stop losses")
        
        return {
            'status': status,
            'score': max(0, score),
            'issues': issues,
            'recommendations': recommendations,
            'kpi_status': kpi_status,
            'insufficient_data': False
        }
    
    def get_report(self) -> str:
        """Generate a human-readable report"""
        evaluation = self.evaluate()
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║  RICHESREACH INVESTMENT COMMITTEE - STRATEGY HEALTH REPORT   ║
╚══════════════════════════════════════════════════════════════╝

Strategy: {self.mode} Mode
Period: {self.strategy.period}
Evaluation Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PERFORMANCE METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Signals Evaluated: {self.strategy.signals_evaluated}
Win Rate: {self.strategy.win_rate:.1f}% (Target: {self.targets['target_win_rate']}%)
Sharpe Ratio: {self.strategy.sharpe_ratio or 0:.2f} (Target: {self.targets['target_sharpe_ratio']})
Max Drawdown: {abs(self.strategy.max_drawdown or 0):.1f}% (Limit: {self.minimums['max_drawdown']}%)
Avg PnL per Signal: {self.strategy.avg_pnl_per_signal or 0:.2f}% (Target: {self.targets['min_avg_pnl_per_signal']}%)
Calmar Ratio: {self.strategy.calmar_ratio or 0:.2f} (Min: {self.minimums['calmar_ratio']})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 KPI STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for kpi, status in evaluation['kpi_status'].items():
            icon = '✅' if status == 'PASS' else '⚠️' if status == 'WATCH' else '❌'
            report += f"{icon} {kpi.upper()}: {status}\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 OVERALL STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: {evaluation['status'].label}
Health Score: {evaluation['score']:.0f}/100

"""
        
        if evaluation['issues']:
            report += "⚠️ ISSUES FOUND:\n"
            for issue in evaluation['issues']:
                report += f"  • {issue}\n"
            report += "\n"
        
        if evaluation['recommendations']:
            report += "💡 RECOMMENDATIONS:\n"
            for rec in evaluation['recommendations']:
                report += f"  • {rec}\n"
        
        report += "\n" + "═" * 63 + "\n"
        
        return report

