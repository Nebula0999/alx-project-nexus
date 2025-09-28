from django.db import models


class Payment(models.Model):
    """Basic Payment record placeholder.

    This model is intentionally minimal: store a gateway, amount, currency and
    a status. Integrate with a real gateway (Stripe, PayPal) by storing
    gateway-specific ids and webhooks.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    gateway = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'

    def __str__(self):
        return f"{self.gateway} {self.amount} {self.currency} ({self.status})"

# Create your models here.
