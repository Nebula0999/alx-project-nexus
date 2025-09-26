import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = "Send a test email to verify SMTP configuration. Usage: manage.py test_email you@example.com"

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Recipient email address')

    def handle(self, *args, **options):
        recipient = options['recipient']
        subject = 'Test Email'
        body = 'This is a test email from the ecommerce project.'
        self.stdout.write(self.style.NOTICE(f"Sending test email to {recipient} via {settings.EMAIL_HOST}:{settings.EMAIL_PORT} (TLS={settings.EMAIL_USE_TLS} SSL={settings.EMAIL_USE_SSL})"))
        try:
            sent = send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        except Exception as exc:
            raise CommandError(f"Failed to send email: {exc}")
        if sent:
            self.stdout.write(self.style.SUCCESS("Email sent successfully."))
        else:
            raise CommandError("send_mail returned 0 (not sent)")