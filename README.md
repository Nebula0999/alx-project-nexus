# alx-project-nexus

Modern educational e‑commerce backend built with **Django 5**, **Django REST Framework**, **Celery**, **Redis**, **PostgreSQL**, and **JWT auth**. It demonstrates a clean modular architecture across `users`, `products`, `notifications`, and `payments` plus production‑leaning concerns: email verification, filtering/search/ordering, throttling, caching, pagination, OpenAPI docs, and background task patterns.

---
## Feature Highlights

| Domain | Implemented Features |
|--------|----------------------|
| Auth & Users | Custom user model (AbstractBaseUser + PermissionsMixin), registration, JWT auth, email verification + resend, unverified login blocking |
| Catalog | Categories, Products (JSON attributes + GIN index), Product Variants |
| Orders | Orders & OrderItems with pricing breakdown + status workflow |
| Email | Verification emails (signed token, 24h expiry), order confirmation (placeholder), test email management command |
| Filtering/Search | django-filter advanced filters (price ranges, created ranges, category slug), DRF SearchFilter & OrderingFilter |
| Pagination | PageNumber pagination with client `?page_size=` (capped at 100) |
| Throttling | Global anon/user + scoped throttles (users, payments, products) |
| Caching | Per-list view caching (Products: 60s, Payments: 30s) via Redis |
| Background Tasks | Celery tasks for verification, orders, abandoned cart, low stock (with retries & logging) |
| Config | Local Redis defaults + env overrides, Celery eager dev mode, SMTP configurable |
| API Docs | drf-spectacular schema + Swagger & ReDoc endpoints |

---
## Table of Contents

1. Architecture & Apps
2. Data Models Overview
3. Authentication & Email Verification Flow
4. Filtering, Searching, Ordering
5. Pagination
6. Throttling
7. Caching Strategy
8. Background Tasks (Celery)
9. OpenAPI / Documentation
10. Configuration & Environment (.env)
11. Development & Operations
12. Testing
13. Management Commands
14. Security & Hardening Notes
15. Roadmap / Next Improvements

---
## 1. Architecture & Apps

| App | Responsibility |
|-----|----------------|
| `users` | Custom user model, registration, JWT auth, verification, resend flow |
| `products` | Catalog (Category/Product/Variant), Orders, OrderItems, API & filters |
| `notifications` | Celery task definitions (email & operational tasks) |
| `payments` | Starter payment record model (extend for gateways) |

Key supporting modules: `ecommerce.pagination`, DRF settings, Celery, Redis cache configuration.

---
## 2. Data Models Overview

### users.User
- Extends `AbstractBaseUser` + `PermissionsMixin` (manager provides `create_user` / `create_superuser`).
- Fields: `username`, `email`, `first_name`, `last_name`, `phone`, `is_verified`, `is_active`, `is_staff`, timestamps.
- Authentication: password hashing via Django auth; JWT tokens disallowed until `is_verified` true.

### products.Category / Product / ProductVariant
- `Product.attributes` & `ProductVariant.attributes`: JSON (flexible metadata). Indexed with `GinIndex` for Postgres.
- Category hierarchy supported via self-FK.

### orders.Order / OrderItem
- Order pricing fields: total, tax, shipping, discount + status choices.
- Address fields stored as JSON for flexible schema.

### payments.Payment
- Minimal placeholder: gateway, amount, currency, status, reference, created_at.

---
## 3. Authentication & Email Verification Flow

Endpoints:
- `POST /api/register/` — create user (async or eager Celery email send).
- `GET /api/verify-email/<token>/` — mark user verified (signed token, 24h expiry).
- `POST /api/resend-verification/ {"email": "user@example.com"}` — resend if not verified.
- `POST /api/auth/token/` — obtains JWT **only if user is verified** (403 otherwise).
- `POST /api/auth/token/refresh/` — refresh access token.

Verification Email:
1. Registration schedules (or immediately executes in eager mode) `send_verification_email`.
2. Task signs payload `{ uid: <user_id> }` using Django signing; constructs absolute URL via `SITE_URL`.
3. Template: `templates/emails/verification.html` (HTML button + fallback link).
4. Token expiry: 24 hours (`max_age=60*60*24`). Expired or tampered tokens return descriptive 400.

Resilience:
- Celery `max_retries=3` with exponential-ish (60s) retry for transient failures.
- Dev fallback: if broker unreachable & `DEBUG=True`, task executes synchronously.

---
## 4. Filtering, Searching, Ordering

Global DRF backends:
```
django_filters.rest_framework.DjangoFilterBackend
rest_framework.filters.SearchFilter
rest_framework.filters.OrderingFilter
```

### Products (`/api/products/`)
Advanced filter class: `ProductFilter` supports:
- `min_price`, `max_price` (numeric)
- `created_after`, `created_before` (ISO8601 datetime)
- `category` (Category slug)
- `is_active`, `is_digital`

Query Examples:
```
/api/products/?min_price=10&max_price=50&category=electronics&ordering=-price
/api/products/?search=wireless&page=2&page_size=25
/api/products/?created_after=2025-09-01T00:00:00Z&created_before=2025-09-30T23:59:59Z
```

### Payments (`/api/payments/`)
Filterable: `status`, `gateway`, `currency`, `amount` (lt/lte/gt/gte), created_at range.
Search: `reference`, `gateway`, `currency`. Ordering: `amount`, `created_at`.

### Users (`/api/users/`)
Search: username, email, first/last names.
Filter: `is_verified`, `is_active`.

---
## 5. Pagination

Custom paginator: `StandardResultsSetPagination`.
- Default page size: 20
- Client override: `?page_size=<n>`
- Max page size: 100

Example:
```
/api/products/?page=3&page_size=50
```

Response structure:
```
{
  "count": 123,
  "next": "...",
  "previous": null,
  "results": [ ... ]
}
```

---
## 6. Throttling

Configured in `REST_FRAMEWORK`:
- Global: `AnonRateThrottle` (100/hour), `UserRateThrottle` (1000/hour)
- Scoped rates:
  - `users`: 500/hour
  - `payments`: 300/hour
  - `products`: 800/hour (set scope in view to activate)

429 responses include `Retry-After` header when limits exceeded.

---
## 7. Caching Strategy

- Product list: 60s (`@cache_page(60)`).
- Payment list: 30s (`@cache_page(30)`).
- Redis-backed (Django cache configured). Full URL (including query params) forms cache key.
- Safe for high-read catalog endpoints; invalidation occurs naturally after TTL. Extend with explicit busting if you add admin edits at scale.

---
## 8. Background Tasks (Celery)

Principal tasks (in `notifications/tasks.py`):
- `send_verification_email(user_id)`
- `send_order_confirmation(order_id)` (template placeholder)
- `process_abandoned_carts()` + `send_abandoned_cart_email(cart_id)`
- `update_low_stocks_alerts()`

### Dev Eager Mode
If `DEBUG=True` & `CELERY_EAGER=true` (default in settings), tasks run synchronously – no broker/worker required.

### Running real workers
```
celery -A ecommerce worker -l info -P solo   # Windows uses solo pool
celery -A ecommerce beat -l info             # If periodic tasks needed
```

---
## 9. OpenAPI / Documentation

Generated with **drf-spectacular**.
Endpoints:
- `/api/schema/` (raw schema JSON/YAML)
- `/api/docs/swagger/` (Swagger UI)
- `/api/docs/redoc/` (ReDoc)

Extend schema via `SPECTACULAR_SETTINGS` or per-view `extend_schema` decorators for examples.

---
## 10. Configuration & Environment (.env)

Sample `.env` (DO NOT commit real secrets):
```
DJANGO_SECRET_KEY=change-me
DEBUG=true

# Postgres
DB_NAME=ecommerce
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432

# Redis (local)
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
CELERY_EAGER=true

# Email (Gmail example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=app-password-here
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=you@gmail.com
SITE_URL=http://127.0.0.1:8000
```

> For production: disable eager mode, enforce HTTPS, rotate secrets, add SPF/DKIM.

---
## 11. Development & Operations

Install & Run:
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ecommerce/manage.py migrate
python ecommerce/manage.py runserver
```

Optional (async mode):
```powershell
celery -A ecommerce worker -l info -P solo
```

Test email configuration:
```powershell
python ecommerce/manage.py test_email you@example.com
```

---
## 12. Testing

Run all tests:
```powershell
python ecommerce/manage.py test
```

Pagination tests confirm `page_size` caps at 100.
Recommended to add: order creation, verification link tests, filter coverage, permission checks.

---
## 13. Management Commands

| Command | Purpose |
|---------|---------|
| `test_email <recipient>` | Send a test email using current SMTP config |

Add more (e.g., `rebuild_index`, `resend_failed_emails`) as system grows.

---
## 14. Security & Hardening Notes

- Move all credentials to environment or secret manager (never commit real passwords).
- Enforce HTTPS + secure cookies in production.
- Add DRF permission refinements (e.g., staff-only endpoints) & object-level checks.
- Consider rate limiting registration & verification resend endpoints separately.
- Add monitoring/log aggregation (structured logs already started for email tasks).

---
## 15. Roadmap / Next Improvements

1. Shopping Cart model + workflows (ties into abandoned cart tasks more concretely).
2. Payment gateway integration (Stripe Checkout / webhooks) & idempotent order capture.
3. Inventory & stock reservation logic + low stock notifications to admin channel.
4. Promotion / coupon subsystem (percentage, fixed, conditional rules).
5. Full-text or vector search backend (PG trigram / Elasticsearch / OpenSearch).
6. Image/media handling (S3 + thumbnails) and CDN integration.
7. Improve email templates (HTML + plain text fallback + translation/i18n).
8. CI pipeline (GitHub Actions) with linting (flake8/ruff), type hints (mypy), and test coverage gates.
9. WebSocket / SSE channel for order status updates.
10. Soft delete & audit log (GDPR friendly) for key models.

---
### Quick Reference (Cheat Sheet)

| Action | Example |
|--------|---------|
| Register | `POST /api/register/` |
| Resend verification | `POST /api/resend-verification/ {"email": "user@x.com"}` |
| Verify | `GET /api/verify-email/<token>/` |
| Obtain token | `POST /api/auth/token/` |
| Products filter | `/api/products/?min_price=10&category=shirts` |
| Pagination | `/api/products/?page=2&page_size=50` |
| Ordering | `/api/products/?ordering=-price` |
| Search | `/api/products/?search=wireless` |
| Schema | `/api/schema/` |
| Swagger UI | `/api/docs/swagger/` |
| ReDoc | `/api/docs/redoc/` |

---
Contributions, experimentation, and extension are encouraged. This project is intentionally structured to be a solid starting point you can evolve into a production-grade platform. Feel free to open issues or extend functionality as you learn.

---
**Happy building!**

