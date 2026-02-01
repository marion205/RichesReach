"""
Generate Weekly Transparency Report
Automated weekly summary of signals, performance, and methodology notes.
"""
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.transparency_dashboard import get_transparency_dashboard
from core.methodology_page import get_methodology_summary
from core.models import SignalRecord


class Command(BaseCommand):
    help = 'Generate weekly transparency report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='weekly_report.md',
            help='Output markdown filename (default: weekly_report.md)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to include in report (default: 7)'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        days = options['days']
        
        self.stdout.write("📊 Generating weekly transparency report...")
        
        # Get data
        dashboard_service = get_transparency_dashboard()
        performance = dashboard_service.get_performance_summary(days=days)
        
        # Get signals from last week
        cutoff_date = timezone.now() - timedelta(days=days)
        signals = SignalRecord.objects.filter(
            entry_timestamp__gte=cutoff_date
        ).order_by('-entry_timestamp')
        
        # Generate report
        report_lines = [
            f"# Weekly Transparency Report",
            f"",
            f"**Period:** {cutoff_date.strftime('%B %d, %Y')} - {timezone.now().strftime('%B %d, %Y')}",
            f"**Generated:** {timezone.now().strftime('%B %d, %Y at %H:%M UTC')}",
            f"",
            f"---",
            f"",
            f"## Performance Summary",
            f"",
            f"- **Total Signals:** {performance['total_signals']}",
            f"- **Win Rate:** {performance['win_rate']:.1f}%",
            f"- **Total P&L:** ${performance['total_pnl']:.2f}",
            f"- **Average P&L:** ${performance['avg_pnl']:.2f}",
            f"- **Sharpe Ratio:** {performance['sharpe_ratio']:.2f}",
            f"- **Max Drawdown:** {performance['max_drawdown']:.2f}%",
            f"",
            f"---",
            f"",
            f"## Methodology Notes",
            f"",
            get_methodology_summary(),
            f"",
            f"---",
            f"",
            f"## Recent Signals",
            f"",
        ]
        
        if signals.exists():
            report_lines.append(f"| Symbol | Action | Entry | Exit | P&L | Status |")
            report_lines.append(f"|--------|-------|-------|------|-----|--------|")
            
            for signal in signals[:20]:  # Top 20
                entry_str = f"${signal.entry_price:.2f}" if signal.entry_price else "N/A"
                exit_str = f"${signal.exit_price:.2f}" if signal.exit_price else "N/A"
                pnl_str = f"${signal.pnl:.2f}" if signal.pnl is not None else "N/A"
                
                report_lines.append(
                    f"| {signal.symbol} | {signal.action} | {entry_str} | {exit_str} | {pnl_str} | {signal.status} |"
                )
        else:
            report_lines.append("No signals generated during this period.")
        
        report_lines.extend([
            f"",
            f"---",
            f"",
            f"## Full Data Access",
            f"",
            f"- **Dashboard:** https://richesreach.com/transparency",
            f"- **Methodology:** https://richesreach.com/methodolgy",
            f"- **CSV Export:** Available via API endpoint",
            f"",
            f"---",
            f"",
            f"*This report is generated automatically. All P&L is calculated net of costs.*",
        ])
        
        # Write report
        output_path = os.path.join(os.getcwd(), output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Weekly report generated: {output_path}"))
        self.stdout.write(f"\n📊 Report Statistics:")
        self.stdout.write(f"   - Period: {days} days")
        self.stdout.write(f"   - Signals: {signals.count()}")
        self.stdout.write(f"   - Win Rate: {performance['win_rate']:.1f}%")
        self.stdout.write(f"   - Total P&L: ${performance['total_pnl']:.2f}")

