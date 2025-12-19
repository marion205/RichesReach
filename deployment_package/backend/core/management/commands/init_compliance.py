"""
Django management command to initialize compliance statuses
"""
from django.core.management.base import BaseCommand
from core.models import ComplianceStatus
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Initialize compliance statuses in the database'

    def handle(self, *args, **options):
        compliance_data = [
            {
                'standard': 'SOC2',
                'status': 'Compliant',
                'score': 95,
                'last_audit_date': date(2024, 1, 15),
                'next_audit_date': date(2025, 1, 15),
            },
            {
                'standard': 'PCI_DSS',
                'status': 'Compliant',
                'score': 98,
                'last_audit_date': date(2024, 2, 1),
                'next_audit_date': date(2025, 2, 1),
            },
            {
                'standard': 'GDPR',
                'status': 'Compliant',
                'score': 92,
                'last_audit_date': date(2024, 1, 20),
                'next_audit_date': date(2025, 1, 20),
            },
            {
                'standard': 'CCPA',
                'status': 'Compliant',
                'score': 89,
                'last_audit_date': date(2024, 1, 25),
                'next_audit_date': date(2025, 1, 25),
            },
        ]
        
        for data in compliance_data:
            # IDEMPOTENT: Use update_or_create to safely run multiple times
            compliance, created = ComplianceStatus.objects.update_or_create(
                standard=data['standard'],  # Unique key
                defaults={
                    'status': data['status'],
                    'score': data['score'],
                    'last_audit_date': data['last_audit_date'],
                    'next_audit_date': data['next_audit_date'],
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created compliance status: {compliance.standard}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Updated compliance status: {compliance.standard} (idempotent)')
                )

