"""
Celery tasks for transparency dashboard
Automated weekly report generation: file, optional email, optional public snippet.
"""
import os
import logging
from celery import shared_task
from django.core.management import call_command
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def generate_weekly_report_task():
    """
    Generate weekly transparency report (Sunday 8 PM server time when using crontab).
    Writes report file; optionally sends email (WEEKLY_REPORT_EMAILS) and emits public snippet (PUBLISH_WEEKLY_REPORT_PUBLIC).
    """
    try:
        logger.info("Generating weekly transparency report...")
        output_dir = getattr(settings, 'WEEKLY_REPORT_OUTPUT_DIR', None) or os.getcwd()
        output_file = os.path.join(output_dir, 'weekly_report.md')
        args = ['--days', '7', '--output', output_file]
        if os.getenv('WEEKLY_REPORT_EMAILS'):
            args.append('--email')
        if os.getenv('PUBLISH_WEEKLY_REPORT_PUBLIC', '').lower() == 'true':
            args.append('--public')
        call_command('generate_weekly_report', *args)
        logger.info("Weekly transparency report generated successfully")
    except Exception as e:
        logger.error("Failed to generate weekly report: %s", e, exc_info=True)
        raise
