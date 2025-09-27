"""Custom email backends for the project.

Provides an opt-in INSECURE backend that disables TLS certificate verification
strictly for local debugging of environments where a corporate proxy, antivirus
MITM, or broken local cert store causes repeated SSL verification failures.

Usage (DEV ONLY):
  1. Keep EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  2. Set EMAIL_INSECURE_SKIP_VERIFY=true in your environment
  3. Run the test email command again

NEVER use this in production. It removes a critical security guarantee.
"""

from django.core.mail.backends.smtp import EmailBackend
import ssl
import smtplib


class InsecureSMTPEmailBackend(EmailBackend):
    """SMTP backend that disables TLS certificate verification (DEV ONLY)."""

    def open(self):  # Overridden to inject unverified contexts
        if self.connection:  # pragma: no cover - defensive
            return False
        try:
            if self.use_ssl:
                context = ssl._create_unverified_context()
                self.connection = smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    local_hostname=self.local_hostname,
                    timeout=self.timeout,
                    context=context,
                )
            else:
                self.connection = smtplib.SMTP(
                    self.host,
                    self.port,
                    local_hostname=self.local_hostname,
                    timeout=self.timeout,
                )
                self.connection.ehlo()
                if self.use_tls:
                    context = ssl._create_unverified_context()
                    self.connection.starttls(context=context)
                    self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            self.close()
            raise
