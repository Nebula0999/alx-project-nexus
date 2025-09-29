import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = "Diagnose static files setup: shows STATIC_ROOT existence, sample admin assets, and potential misconfigurations."

    def add_arguments(self, parser):  # pragma: no cover - simple args
        parser.add_argument('--list', action='store_true', help='List first 25 collected admin assets.')

    def handle(self, *args, **options):
        static_root = Path(settings.STATIC_ROOT)
        self.stdout.write(f"STATIC_URL: {settings.STATIC_URL}")
        self.stdout.write(f"STATIC_ROOT: {static_root}")
        self.stdout.write(f"STATICFILES_DIRS: {getattr(settings, 'STATICFILES_DIRS', [])}")
        if not static_root.exists():
            self.stdout.write(self.style.ERROR("STATIC_ROOT does not exist. collectstatic likely did not run."))
            return
        if not any(static_root.iterdir()):
            self.stdout.write(self.style.ERROR("STATIC_ROOT exists but is empty. collectstatic produced no output."))
        admin_css = static_root / 'admin' / 'css' / 'base.css'
        if admin_css.exists():
            self.stdout.write(self.style.SUCCESS("Found admin/css/base.css"))
        else:
            self.stdout.write(self.style.WARNING("Missing admin/css/base.css — admin static not collected."))
        # Look for manifest file if using Manifest storage
        manifest = static_root / 'staticfiles.json'
        if 'Manifest' in settings.STATICFILES_STORAGE:
            if manifest.exists():
                self.stdout.write(self.style.SUCCESS("Found staticfiles.json (Manifest storage OK)."))
            else:
                self.stdout.write(self.style.WARNING("staticfiles.json missing; Manifest storage may break hashed references."))
        # Check for accidental inclusion of STATIC_ROOT in STATICFILES_DIRS
        if any(Path(p) == static_root for p in getattr(settings, 'STATICFILES_DIRS', [])):
            self.stdout.write(self.style.ERROR("STATIC_ROOT is inside STATICFILES_DIRS (misconfiguration)."))
        if options.get('list'):
            admin_dir = static_root / 'admin'
            if admin_dir.exists():
                files = []
                for root, _, fns in os.walk(admin_dir):
                    for f in fns:
                        rel = Path(root).joinpath(f).relative_to(static_root)
                        files.append(str(rel))
                        if len(files) >= 25:
                            break
                    if len(files) >= 25:
                        break
                self.stdout.write("Sample admin assets:\n" + "\n".join(files))
        self.stdout.write(self.style.NOTICE("If admin assets are missing on Render: ensure buildCommand runs 'python ecommerce/manage.py collectstatic' and that DEBUG is 0 with WhiteNoise middleware present."))
