"""
Re-save all AlpacaConnection rows so existing plaintext tokens get encrypted.
Run after setting ALPACA_TOKEN_ENCRYPTION_KEY (or FERNET_KEY) in production.
Skips rows that are already encrypted.
"""
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Re-encrypt existing AlpacaConnection tokens (run after setting ALPACA_TOKEN_ENCRYPTION_KEY)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report how many rows would be updated",
        )

    def handle(self, *args, **options):
        try:
            from core.models import AlpacaConnection
            from core.alpaca_token_encryption import _get_fernet, _looks_fernet
        except ImportError as e:
            self.stdout.write(self.style.ERROR("Import failed: %s" % e))
            return

        if _get_fernet() is None:
            self.stdout.write(
                self.style.WARNING(
                    "ALPACA_TOKEN_ENCRYPTION_KEY (or FERNET_KEY) not set; "
                    "tokens will remain plaintext. Set the key and run again."
                )
            )
            return

        connections = list(AlpacaConnection.objects.all())
        to_encrypt = [
            c for c in connections
            if (c.access_token and not _looks_fernet(c.access_token))
            or (c.refresh_token and not _looks_fernet(c.refresh_token))
        ]

        if not to_encrypt:
            self.stdout.write(self.style.SUCCESS(
                "No AlpacaConnection rows with plaintext tokens (all encrypted or empty)."
            ))
            return

        if options["dry_run"]:
            self.stdout.write(
                "Would re-encrypt %d AlpacaConnection row(s)." % len(to_encrypt)
            )
            return

        updated = 0
        for conn in to_encrypt:
            try:
                plain_access = conn.get_decrypted_access_token()
                plain_refresh = conn.get_decrypted_refresh_token()
                conn.access_token = plain_access or ""
                conn.refresh_token = plain_refresh or ""
                conn.save(update_fields=["access_token", "refresh_token", "updated_at"])
                updated += 1
            except Exception as e:
                logger.exception("Failed to re-encrypt AlpacaConnection pk=%s: %s", conn.pk, e)
                self.stdout.write(self.style.ERROR("  Failed pk=%s: %s" % (conn.pk, e)))

        self.stdout.write(self.style.SUCCESS("Re-encrypted %d AlpacaConnection row(s)." % updated))
