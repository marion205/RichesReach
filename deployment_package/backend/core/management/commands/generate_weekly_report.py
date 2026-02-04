"""
Generate Weekly Transparency Report
Automated weekly summary: performance, abstentions, by trading_mode, methodology.
Supports: file output, optional email to subscribers, optional public snippet (e.g. X/blog).
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from core.weekly_report_service import (
    build_weekly_report_data,
    render_report_markdown,
    anonymized_public_snippet,
)
from core.methodology_page import get_methodology_summary


def _get_dashboard_url() -> str:
    base = getattr(settings, 'BASE_URL', '') or os.getenv('BASE_URL', 'https://richesreach.com')
    return base.rstrip('/') + '/transparency'


def _get_methodology_url() -> str:
    base = getattr(settings, 'BASE_URL', '') or os.getenv('BASE_URL', 'https://richesreach.com')
    return base.rstrip('/') + '/methodology'


def _send_weekly_email(report_data: dict, markdown_body: str) -> int:
    """Send weekly report email to opted-in addresses. Returns count sent."""
    from django.core.mail import send_mail
    to_emails = getattr(settings, 'WEEKLY_REPORT_EMAILS', None) or os.getenv('WEEKLY_REPORT_EMAILS', '')
    if not to_emails:
        return 0
    if isinstance(to_emails, str):
        to_emails = [e.strip() for e in to_emails.split(',') if e.strip()]
    if not to_emails:
        return 0
    dashboard_url = _get_dashboard_url()
    p = report_data['performance']
    subject = (
        f"Weekly Transparency Report: {p.get('total_signals', 0)} signals, "
        f"net ${p.get('total_pnl', 0):.2f} (net of costs)"
    )
    body_plain = (
        f"Period: {report_data['start'].strftime('%Y-%m-%d')} to {report_data['end'].strftime('%Y-%m-%d')}\n\n"
        f"Total signals (closed): {p.get('total_signals', 0)}\n"
        f"Win rate: {p.get('win_rate', 0):.1f}%\n"
        f"Total P&L: ${p.get('total_pnl', 0):.2f}\n"
        f"Abstained: {report_data['abstention_count']} ({report_data['abstention_pct']:.1f}%)\n\n"
        f"View full dashboard: {dashboard_url}\n\n"
        "---\n\n"
        + markdown_body
    )
    sent = send_mail(
        subject=subject,
        message=body_plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=to_emails,
        fail_silently=True,
    )
    return sent


def _post_to_public_snippet(report_data: dict) -> None:
    """Post anonymized snippet when PUBLISH_WEEKLY_REPORT_PUBLIC is set (log or webhook)."""
    import logging
    snippet = anonymized_public_snippet(report_data)
    dashboard_url = _get_dashboard_url()
    full_text = snippet + dashboard_url
    if not (getattr(settings, 'PUBLISH_WEEKLY_REPORT_PUBLIC', False) or os.getenv('PUBLISH_WEEKLY_REPORT_PUBLIC', '').lower() == 'true'):
        return
    webhook_url = os.getenv('WEEKLY_REPORT_WEBHOOK_URL', '').strip()
    if webhook_url:
        try:
            import requests
            requests.post(webhook_url, json={'text': full_text}, timeout=10)
            logging.getLogger(__name__).info("Weekly report snippet posted to webhook")
        except ImportError:
            logging.getLogger(__name__).warning("requests not installed; log snippet only")
            logging.getLogger(__name__).info("Weekly report public snippet: %s", full_text[:200] + "..." if len(full_text) > 200 else full_text)
        except Exception as e:
            logging.getLogger(__name__).warning("Webhook post failed: %s", e)
    else:
        logging.getLogger(__name__).info(
            "Weekly report public snippet: %s",
            full_text[:200] + "..." if len(full_text) > 200 else full_text,
        )


class Command(BaseCommand):
    help = 'Generate weekly transparency report (file, optional email, optional public snippet)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='weekly_report.md',
            help='Output markdown filename (default: weekly_report.md)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to include (default: 7)',
        )
        parser.add_argument(
            '--email',
            action='store_true',
            help='Send report to WEEKLY_REPORT_EMAILS (comma-separated)',
        )
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='Skip email even if WEEKLY_REPORT_EMAILS is set (e.g. when running from cron)',
        )
        parser.add_argument(
            '--public',
            action='store_true',
            help='Emit public snippet (log; set PUBLISH_WEEKLY_REPORT_PUBLIC for real post)',
        )

    def handle(self, *args, **options):
        output_file = options['output']
        days = options['days']
        do_email = options['email'] and not options['no_email']
        do_public = options['public']

        self.stdout.write("📊 Generating weekly transparency report...")

        report_data = build_weekly_report_data(days=days)
        dashboard_url = _get_dashboard_url()
        methodology_url = _get_methodology_url()
        markdown_body = render_report_markdown(
            report_data,
            dashboard_url=dashboard_url,
            methodology_url=methodology_url,
        )

        output_path = os.path.join(os.getcwd(), output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_body)

        self.stdout.write(self.style.SUCCESS(f"\n✅ Weekly report generated: {output_path}"))

        p = report_data['performance']
        self.stdout.write(f"\n📊 Report Statistics:")
        self.stdout.write(f"   - Period: {days} days")
        self.stdout.write(f"   - Signals (closed): {p.get('total_signals', 0)}")
        self.stdout.write(f"   - Abstained: {report_data['abstention_count']} ({report_data['abstention_pct']:.1f}%)")
        self.stdout.write(f"   - Win Rate: {p.get('win_rate', 0):.1f}%")
        self.stdout.write(f"   - Total P&L: ${p.get('total_pnl', 0):.2f}")
        self.stdout.write(f"   - Profit Factor: {p.get('profit_factor', 0):.2f}")

        if do_email:
            sent = _send_weekly_email(report_data, markdown_body)
            if sent:
                self.stdout.write(self.style.SUCCESS(f"   - Email sent to {sent} recipient(s)"))
            else:
                self.stdout.write("   - Email skipped (no WEEKLY_REPORT_EMAILS or send failed)")

        if do_public:
            _post_to_public_snippet(report_data)
            self.stdout.write("   - Public snippet emitted (webhook or log)")
