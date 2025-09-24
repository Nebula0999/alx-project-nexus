from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from products.models import Order, Cart, CartItem, OrderItem

User = get_user_model()
@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id):
    """Send email verification to user."""
    try:
        user = User.objects.get(id=user_id)
        subject = 'Verify your email address'
        html_message = render_to_string('emails/verification.html', {'user': user})
        
        send_mail(
            subject=subject,
            message='',
            from_email='noreply@example.com',
            recipient_list=[user.email],
            html_message=html_message,
        )
        
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
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
            from_email='noreply@example.com',
            recipient_list=[order.billing_email],
            html_message=html_message,
        )
        
    except Order.DoesNotExist:
        pass
@shared_task
def process_abandoned_carts():
    """Process abandoned shopping carts."""
    from datetime import datetime, timedelta
    from products.models import Cart
    
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
    from products.models import Cart
    
    try:
        cart = Cart.objects.get(id=cart_id)
        subject = 'You have items waiting in your cart!'
        html_message = render_to_string('emails/abandoned_cart.html', {'cart': cart})
        
        send_mail(
            subject=subject,
            message='',
            from_email='noreply@example.com',
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