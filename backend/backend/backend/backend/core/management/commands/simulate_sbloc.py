from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from time import sleep
from datetime import timedelta

from core.models import SblocSession
from core.services.sbloc import SblocService

class Command(BaseCommand):
    help = "Advance mock SBLOC session statuses every N seconds (dev/demo)"

    def handle(self, *args, **options):
        if not settings.USE_SBLOC_MOCK:
            self.stdout.write(self.style.WARNING("USE_SBLOC_MOCK false; exiting."))
            return

        seconds = int(getattr(settings, "SBLOC_STATUS_ADVANCE_SECONDS", 30))
        svc = SblocService()
        self.stdout.write(self.style.SUCCESS(f"Advancing SBLOC statuses every {seconds}s"))
        while True:
            cutoff = timezone.now() - timedelta(hours=3)
            qs = SblocSession.objects.filter(created_at__gte=cutoff).exclude(status="FUNDED")
            for s in qs:
                svc.advance_status(s)
            sleep(seconds)
