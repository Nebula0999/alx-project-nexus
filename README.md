# alx-project-nexus

Comprehensive e-commerce reference project built on Django and Django REST Framework. The codebase demonstrates a modular architecture split into small apps: `users`, `products`, `notifications`, and `payments` (skeleton). It includes models for products, categories, product variants, orders and order items, and a custom lightweight `User` model.

This README documents the project's architecture, app responsibilities, models and fields, tasks/processes (Celery), setup and development steps, testing guidance, and recommendations for production hardening.

---

## Table of Contents

- Project overview
- Apps & responsibilities
	- `users`
	- `products`
	- `notifications`
	- `payments`
- Data models (detailed)
- Background tasks (Celery)
- API & authentication
- Development setup
- Running tests and migrations
- Recommendations & next steps

---

## Project overview

`alx-project-nexus` is an educational e-commerce backend demonstrating core e-commerce primitives: product catalog, product variants, categories, shopping cart / orders, and user registration with email verification. It uses Django for the web framework, Django REST Framework for building APIs, and Celery (with Redis in settings) for background jobs such as sending email and processing abandoned carts.

The codebase follows a modular app layout. Each app aims to encapsulate a single domain:

- `users` — user model, serializers, and authentication views (custom user model is present in `users/models.py`).
- `products` — product catalog models, orders, variants, and related API views/serializers.
- `notifications` — Celery tasks for sending verification emails, order confirmations, abandoned cart reminders, and low-stock alerts.
- `payments` — placeholder app where payment integrations and models should live.

---

## Apps & responsibilities

### users

Location: `ecommerce/users`.

Responsibilities:

- Define a custom `User` model used by the project (`AUTH_USER_MODEL = 'users.User'`). The model is a lightweight implementation that stores username, email, names, password and basic flags. It includes compatibility `is_anonymous` and `is_authenticated` properties so Django auth checks and third-party code that expects these attributes do not raise errors.
- Provide registration and authentication endpoints using DRF and JWT.

Key file(s):

- `models.py` — custom `User` model.
- `serializers.py` — user serializer and JWT serializer (used in views).
- `views.py` — registration and token obtain views.

Notes:

- The existing `User` model is intentionally minimal; consider using `AbstractBaseUser` + `PermissionsMixin` for a production-ready implementation with proper password hashing, managers, and admin integration.

### products

Location: `ecommerce/products`.

Responsibilities:

- Product catalog modeling: categories, products, product variants.
- Order modeling: `Order` and `OrderItem` models for capturing purchases and billing/shipping information.
- Exposes API views and serializers to register users and manage tokens (some authentication helpers appear here).

Key models (see Data models section for field-level detail):

- `Category` — hierarchical categories with parent-child support.
- `Product` — product entity with flexible attributes (JSON field), price, SKU, and M2M categories.
- `ProductVariant` — variant of a product with unique SKU, price, and attributes (JSON).
- `Order` — captures the order lifecycle, totals, billing/shipping info, and status choices.
- `OrderItem` — line items attached to orders.

### notifications

Location: `ecommerce/notifications`.

Responsibilities:

- Celery task definitions for asynchronous processing and email sending.
- Tasks in `tasks.py` include:
	- `send_verification_email` — send a verification email to a user (Celery task, retries configured).
	- `send_order_confirmation` — send order confirmation emails.
	- `process_abandoned_carts` — find carts abandoned for >1 hour and queue reminder emails.
	- `send_abandoned_cart_email` — send an email reminding customers of inactive carts.
	- `update_low_stocks_alerts` — find product variants with low stock and mark alerts as sent.

Notes:

- The tasks import models lazily inside the task functions to avoid circular import issues at startup.
- Celery configuration in `settings.py` uses Redis as the broker and result backend.

### payments

Location: `ecommerce/payments`.

Responsibilities:

- Design area for payment gateway integration (Stripe, PayPal, etc.). The current `models.py` is a placeholder — implement `Payment`, `Transaction`, or gateway-specific models as needed.

---

## Data models (detailed)

This section documents the main models found in `products` and `users` apps.

### users.User

- Fields:
	- `username` (unique CharField) — the user identifier used as `USERNAME_FIELD`.
	- `email` (EmailField, unique) — user's email.
	- `first_name`, `last_name` — name parts.
	- `password` — stored as text in the current model (note: replace with Django password hashing if converting to `AbstractBaseUser`).
	- `phone` — optional phone number.
	- `is_verified` (Boolean) — whether email has been verified.
	- `is_active` (Boolean) — active flag.
	- `created_at`, `updated_at` — timestamps.

- Compatibility properties:
	- `is_anonymous` — property returning `False` (ensures code checking this attribute won't raise AttributeError).
	- `is_authenticated` — property returning `True`.

Notes: For full auth integration, implement `set_password`, `check_password`, and use Django's password hashing.

### products.Category

- `id` — UUID primary key.
- `name`, `slug`, `description`, `parent` — hierarchical category fields.
- `is_active`, `created_at` — state and timestamp.

### products.Product

- `id` — UUID primary key.
- `name`, `slug`, `description`, `short_description`.
- `sku` (unique), `price`, `compare_price`.
- `categories` — ManyToMany to `Category`.
- `attributes` — JSON field for flexible attribute storage (GinIndex applied for queries on Postgres).
- `is_active`, `is_digital`, `weight`, `dimensions` (JSON).

Indexes: `slug`, `sku`, `is_active`, `price` and a `GinIndex` for `attributes`.

### products.ProductVariant

- `id` — UUID primary key.
- `product` — ForeignKey to `Product`.
- `name`, `sku` (unique), `price`, `attributes` (JSON), `is_active`, `created_at`.

Useful for modeling SKUs that vary by color, size, or other attributes.

### products.Order

- `id` — UUID primary key.
- `order_number` (unique) and `user` relation.
- `status` choices: `pending`, `confirmed`, `processing`, `shipped`, `delivered`, `cancelled`, `refunded`.
- Pricing breakdown: `total_amount`, `tax_amount`, `shipping_amount`, `discount_amount`.
- Billing fields: `billing_first_name`, `billing_last_name`, `billing_email`, `billing_phone`, `billing_address` (JSON).
- Shipping fields: `shipping_first_name`, `shipping_last_name`, `shipping_address` (JSON).
- `notes`, `created_at`, `updated_at`.

### products.OrderItem

- Fields: `order` (ForeignKey), `product_variant` (ForeignKey), `quantity`, `unit_price`, `total_price`, `created_at`.

---

## Background tasks (Celery)

Celery is used for asynchronous tasks. The project settings configure Redis for both broker and result backend.

Key tasks (in `notifications/tasks.py`):

- `send_verification_email(user_id)` — constructs and sends an email using `render_to_string('emails/verification.html', {'user': user})`. Retries up to 3 times.
- `send_order_confirmation(order_id)` — sends order confirmation using a template `emails/order_confirmation.html` and `order.billing_email`.
- `process_abandoned_carts()` — finds `Cart` instances that have not been updated for more than an hour and queues `send_abandoned_cart_email` for each; marks `is_abandoned_email_sent`.
- `send_abandoned_cart_email(cart_id)` — sends an abandoned cart reminder using `cart.billing_email`.
- `update_low_stocks_alerts()` — finds `ProductVariant` instances with `stock <= 5` and marks `low_stock_alert_sent`.

Notes:

- Task functions import models inside the function to avoid import-time circular dependencies.
- When running Celery in development, start a worker with the Django settings configured and ensure Redis is reachable.

---

## API & authentication

- JWT authentication is integrated using `djangorestframework-simplejwt` (token obtain view override is present in `users.views` / `products.views` as `CustomTokenObtainPairView`).
- Registration endpoint is provided by `RegisterView` in `users.views` and will enqueue a verification email via Celery when a user registers.

Example usage (registering a user):

POST /api/register/ with JSON payload:

{
	"username": "alice",
	"email": "alice@example.com",
	"first_name": "Alice",
	"last_name": "A",
	"password": "securepass"
}

The endpoint returns a simple message and triggers a Celery task to send a verification email.

---

## Development setup

Prerequisites

- Python 3.11+ (the repo uses 3.13 in some compiled files, but 3.11/3.12+ should work). Install with your OS package manager or pyenv.
- Redis (for Celery broker and results) — local Redis server or hosted instance.
- A Postgres database is recommended for JSONField indexing (GinIndex). SQLite will work for local development but will ignore gin indexes.

Install dependencies (from project root):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Environment

- Copy or create `.env` if your project loads env vars (not included). Otherwise edit `ecommerce/ecommerce/settings.py` to match your DB and Redis credentials.

Database & migrations

```powershell
python "c:\Users\Allan N\OneDrive\Desktop\alx_be_python\alx-project-nexus-1\ecommerce\manage.py" makemigrations
python "c:\Users\Allan N\OneDrive\Desktop\alx_be_python\alx-project-nexus-1\ecommerce\manage.py" migrate
```

Create a superuser (optional):

```powershell
python "c:\Users\Allan N\OneDrive\Desktop\alx_be_python\alx-project-nexus-1\ecommerce\manage.py" createsuperuser
```

Run the development server

```powershell
python "c:\Users\Allan N\OneDrive\Desktop\alx_be_python\alx-project-nexus-1\ecommerce\manage.py" runserver
```

Running Celery worker (in a new terminal) — example using Redis and the project settings:

```powershell
celery -A ecommerce worker --loglevel=info
```

To run scheduled beat tasks:

```powershell
celery -A ecommerce beat --loglevel=info
```

---

## Running tests

Run Django tests with:

```powershell
python "c:\Users\Allan N\OneDrive\Desktop\alx_be_python\alx-project-nexus-1\ecommerce\manage.py" test
```

If you see errors during test DB setup about missing migrations for an app (for example `Dependency on app with no migrations: users`), create migrations for the app first:

```powershell
python "c:\Users\Allan N\OneDrive\Desktop\alx_be_python\alx-project-nexus-1\ecommerce\manage.py" makemigrations users
python "c:\Users\Allan N\OneDrive\Desktop\alx_be_python\alx-project-nexus-1\ecommerce\manage.py" migrate
```

---

## Recommendations & next steps

1. Replace the minimal `users.User` model with a full Django custom user based on `AbstractBaseUser` and `PermissionsMixin`. This ensures proper password hashing, authentication backend compatibility, admin usability, and manager implementation.

2. Implement `payments` models to capture gateway transactions and idempotency keys. Integrate with a payment provider (Stripe recommended for prototyping).

3. Harden secrets and sensitive configuration: move Redis URLs, DB credentials, and `SECRET_KEY` into environment variables or a secrets manager.

4. Add email templates in `templates/emails/` and configure `EMAIL_BACKEND` / SMTP credentials in `settings.py`.

5. Add thorough tests per app: model tests, serializer tests, and view tests. Add CI (GitHub Actions) to run tests on push.

6. Consider adding API documentation (OpenAPI/Swagger) using `drf_yasg` or `drf_spectacular` (both are already in `INSTALLED_APPS`). Export schema and enable an interactive UI.

7. If using Postgres, keep the `GinIndex` on JSON fields to accelerate attribute queries.

---

If you want, I can:

- Create initial migrations for `users` and `products` and run them (commit migration files),
- Convert the `User` model to a complete custom user implementation,
- Add example `.env` and local development instructions tailored to your machine,
- Generate API docs from DRF serializers/views.

Tell me which you'd like me to do next and I will proceed.

