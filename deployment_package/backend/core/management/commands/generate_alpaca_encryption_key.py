"""
Generate a Fernet key for ALPACA_TOKEN_ENCRYPTION_KEY (or FERNET_KEY).
Use this key in production so Alpaca OAuth tokens are encrypted at rest.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a Fernet key for Alpaca token encryption (ALPACA_TOKEN_ENCRYPTION_KEY)"

    def handle(self, *args, **options):
        try:
            from cryptography.fernet import Fernet
            key = Fernet.generate_key().decode()
        except ImportError:
            self.stdout.write(
                self.style.ERROR("Install cryptography: pip install cryptography")
            )
            return
        self.stdout.write(self.style.SUCCESS("Generated Fernet key (set in production):"))
        self.stdout.write("")
        self.stdout.write("  ALPACA_TOKEN_ENCRYPTION_KEY=" + key)
        self.stdout.write("")
        self.stdout.write("Add this to your production environment (ECS, K8s secret, or .env.production).")
        self.stdout.write("Then (optional) run: python manage.py rotate_alpaca_token_encryption")
