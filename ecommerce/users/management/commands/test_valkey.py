import os
from django.core.management.base import BaseCommand, CommandError

try:
    import valkey  # type: ignore
except ImportError as e:  # pragma: no cover
    raise ImportError("The 'valkey' package is not installed. Add it to requirements.txt.") from e


class Command(BaseCommand):
    help = "Test Valkey (Redis-compatible) connectivity and basic get/set operations"

    def add_arguments(self, parser):
        parser.add_argument('--url', dest='url', help='Override Valkey URL (valkeys:// or redis://)', default=None)
        parser.add_argument('--key', dest='key', help='Key name to use', default='integration:test')
        parser.add_argument('--value', dest='value', help='Value to set', default='hello world')
        parser.add_argument('--ttl', dest='ttl', type=int, help='Optional TTL seconds', default=None)

    def handle(self, *args, **options):
        url = options['url'] or os.getenv('VALKEY_URL') or os.getenv('REDIS_URL')
        if not url:
            raise CommandError("No Valkey/Redis URL provided. Set VALKEY_URL or REDIS_URL or use --url.")

        key = options['key']
        value = options['value']
        ttl = options['ttl']

        self.stdout.write(self.style.NOTICE(f"Connecting to Valkey at: {url}"))
        try:
            client = valkey.from_url(url)
        except Exception as exc:
            raise CommandError(f"Connection initialization failed: {exc}") from exc

        try:
            if ttl:
                client.set(key, value, ex=ttl)
            else:
                client.set(key, value)
            raw = client.get(key)
            if raw is None:
                raise CommandError("Value read back is None (unexpected).")
            decoded = raw.decode('utf-8', errors='replace')
        except Exception as exc:
            raise CommandError(f"Set/Get failed: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Key '{key}' set & retrieved successfully: '{decoded}'"))
        info = {}
        try:
            info = client.info()  # type: ignore[attr-defined]
        except Exception:
            pass
        if info:
            version = info.get('server', {}).get('valkey_version') or info.get('redis_version')
            self.stdout.write(f"Server version: {version}")
            self.stdout.write(f"Mode: {info.get('server', {}).get('redis_mode')}")

        self.stdout.write(self.style.SUCCESS("Valkey connectivity test completed."))
