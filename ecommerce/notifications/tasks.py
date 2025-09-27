from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core import signing
from products.models import Order, OrderItem
import logging

logger = logging.getLogger('notifications.tasks')

User = get_user_model()

@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id):
    """Send email verification and record attempt metrics.

    Tracking fields on the User model are updated:
      - verification_email_last_attempt
      - verification_email_attempts (incremented atomically)
      - verification_email_last_success (set only on successful send)

    In dev/eager mode we often want to avoid raising an exception all the way
    to the API caller; set EMAIL_SILENT_FAIL=true (default in DEBUG) to swallow
    final failures after retries.
    """
    from django.utils import timezone
    from django.db import models
    silent = getattr(settings, 'EMAIL_SILENT_FAIL', settings.DEBUG)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    # Record attempt timestamp & increment attempts
    User.objects.filter(pk=user.pk).update(
        verification_email_last_attempt=timezone.now(),
        verification_email_attempts=models.F('verification_email_attempts') + 1
    )

    try:
        subject = 'Verify your email address'
        token = signing.dumps({"uid": user.id})
        verify_url = f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/api/verify-email/{token}/"
        html_message = render_to_string('emails/verification.html', {
            'user': user,
            'verify_url': verify_url,
        })
        sent = send_mail(
            subject=subject,
            message='',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[user.email],
            html_message=html_message,
        )
        logger.debug(f"Verification email attempted send={sent} to={user.email} url={verify_url}")
        if sent:
            User.objects.filter(pk=user.pk).update(
                verification_email_last_success=timezone.now()
            )
    except Exception as exc:
        logger.exception("Error sending verification email")
        try:
            self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            if not silent:
                raise
@shared_task
def send_order_confirmation(order_id):
    """Send order confirmation email."""
    from products.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        subject = f'Order Confirmation #{order.order_number}'
        html_message = render_to_string('emails/order_confirmation.html', {'order': order})
        
        send_mail(
            subject=subject,
            message='',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[order.billing_email],
            html_message=html_message,
        )
        
    except Order.DoesNotExist:
        pass
@shared_task
def process_abandoned_carts():
    """Process abandoned shopping carts."""
    from datetime import datetime, timedelta
    try:
        from products.models import Cart
    except ImportError:
        # Cart model not implemented — nothing to do
        return

    # Find carts abandoned for more than 1 hour
    abandoned_time = datetime.now() - timedelta(hours=1)
    abandoned_carts = Cart.objects.filter(
        updated_at__lt=abandoned_time,
        is_abandoned_email_sent=False
    )

    for cart in abandoned_carts:
        send_abandoned_cart_email.delay(cart.id)
        cart.is_abandoned_email_sent = True
        cart.save()

@shared_task
def send_abandoned_cart_email(cart_id):
    """Send abandoned cart reminder email."""
    try:
        from products.models import Cart
    except ImportError:
        return

    try:
        cart = Cart.objects.get(id=cart_id)
        subject = 'You have items waiting in your cart!'
        html_message = render_to_string('emails/abandoned_cart.html', {'cart': cart})
        
        send_mail(
            subject=subject,
            message='',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[cart.billing_email],
            html_message=html_message,
        )
        
    except Cart.DoesNotExist:
        pass

@shared_task
def update_low_stocks_alerts():
    """Update low stock alerts for products."""
    from products.models import ProductVariant
    
    low_stock_variants = ProductVariant.objects.filter(stock__lte=5, low_stock_alert_sent=False)
    
    for variant in low_stock_variants:
        # Logic to notify admin or update alert status
        variant.low_stock_alert_sent = True
        variant.save()