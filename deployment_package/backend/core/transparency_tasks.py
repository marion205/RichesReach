"""
Celery tasks for transparency dashboard
Automated weekly report generation
"""
from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


@shared_task
def generate_weekly_report_task():
    """
    Generate weekly transparency report
    Runs every Monday at 9 AM
    """
    try:
        logger.info("Generating weekly transparency report...")
        call_command('generate_weekly_report', '--days', '7')
        logger.info("Weekly transparency report generated successfully")
    except Exception as e:
        logger.error(f"Failed to generate weekly report: {e}", exc_info=True)
        raise

