# Deploying Project Nexus (Django + DRF + Celery optional) to PythonAnywhere

This guide assumes you already have a (free or paid) PythonAnywhere account and a Bash console open there.

## 1. Clone the Repository
```
cd ~
mkdir -p sites && cd sites
git clone https://github.com/Nebula0999/alx-project-nexus.git
cd alx-project-nexus/ecommerce
```

## 2. Create Virtual Environment
(Choose the same Python version as your web app later – e.g. Python 3.12 if available on your plan.)
```
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
```

If `mysqlclient` or other compiled deps fail on free tier, remove them from `requirements.txt` (not needed unless you actually use MySQL) and reinstall.

## 3. Environment Variables (.env)
Create a `.env` file (DON'T put real secrets in git):
```
cat > .env <<'EOF'
DJANGO_SECRET_KEY=replace_me_secure
DEBUG=0
ALLOWED_HOSTS=localhost,127.0.0.1
PYTHONANYWHERE_DOMAIN=yourusername.pythonanywhere.com
SITE_URL=https://yourusername.pythonanywhere.com
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
CELERY_EAGER=true
EOF
```
Adjust as needed. If you add a real SMTP configuration, remember to disable console backend and set proper credentials.

## 4. Database Setup
PythonAnywhere free tier uses SQLite by default. You can stick with the bundled `db.sqlite3` or migrate to Postgres (paid tiers). No change needed if staying on SQLite—just run migrations.
```
python manage.py migrate --noinput
python manage.py createsuperuser
```

## 5. Static Files
```
python manage.py collectstatic --noinput
```
Ensure `STATIC_ROOT` (already set to `staticfiles/`) now contains collected assets.

## 6. WSGI Configuration
On the PythonAnywhere Dashboard:
- Go to Web tab → Add a new web app → Manual configuration (or Django if you prefer, but manual gives control).
- Select the Python version matching the venv you created.
- Set the working directory to: `/home/yourusername/sites/alx-project-nexus/ecommerce`
- Virtualenv: `/home/yourusername/sites/alx-project-nexus/ecommerce/venv`
- Open the generated WSGI file (link on the Web tab) and edit the content to include:
```python
import os, sys
path = '/home/yourusername/sites/alx-project-nexus/ecommerce'
if path not in sys.path:
    sys.path.append(path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```
- Remove any default Flask example code.

## 7. WhiteNoise
Already configured. No extra steps needed beyond collectstatic.

## 8. Celery (Optional)
PythonAnywhere free tier does NOT provide always-on background workers. Options:
- (Simple) Keep `CELERY_EAGER=true` so tasks (email verification) run synchronously.
- (Paid) Use a separate always-on task to run a Celery worker (requires external Redis/Valkey). You’d provision a managed Redis (e.g. Upstash/Aiven) and set `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`.
- (Cron) If you only need periodic tasks, use PythonAnywhere scheduled tasks calling `python manage.py runscript` or a custom management command instead of Celery beat.

If you later add a broker, set in `.env`:
```
CELERY_BROKER_URL=rediss://:password@host:port/1
CELERY_RESULT_BACKEND=rediss://:password@host:port/2
CELERY_EAGER=false
```

## 9. Health Endpoint
Accessible at `/health/`; for PythonAnywhere you can test with:
```
curl -I https://yourusername.pythonanywhere.com/health/
```
If SQLite is locked or there’s an issue, you’ll see a non-200 which can help debugging.

## 10. Security Hardening
- Confirm `DEBUG=0`.
- Generate a long random `DJANGO_SECRET_KEY` (e.g. via Python shell: `import secrets; print(secrets.token_urlsafe(64))`).
- Add a custom domain (paid) and update `ALLOWED_HOSTS` & `SITE_URL`.
- Add HTTPS (PythonAnywhere handles TLS termination automatically on paid custom domain; the default *.pythonanywhere.com is already HTTPS-enabled).

## 11. Admin Access
Visit: `https://yourusername.pythonanywhere.com/admin/`

## 12. Logs
On Web tab: view server and error logs. Email debugging prints to console logger (so appears in server log) unless you switch to a real SMTP backend.

## 13. Common Issues
| Symptom | Fix |
|---------|-----|
| 500 after deploy | Check error log; often missing SECRET_KEY or migrations not run. |
| Static files 404 | Re-run `collectstatic`; confirm STATIC_URL and STATIC_ROOT unchanged. |
| ImportError ecommerce.wsgi.application | Ensure WSGI file sets `DJANGO_SETTINGS_MODULE` correctly and path appended. |
| Tasks not executing | You are in eager mode; this is expected without a worker. |
| Slow first request | PythonAnywhere spins up the worker; subsequent requests faster. |

## 14. Updating Code
```
cd ~/sites/alx-project-nexus
git pull origin main
source ecommerce/venv/bin/activate
pip install -r ecommerce/requirements.txt
python ecommerce/manage.py migrate --noinput
python ecommerce/manage.py collectstatic --noinput
# Reload from Web dashboard (or touch WSGI file)
```

## 15. Optional: Separate Settings
If you prefer separate prod settings, you can create `ecommerce/settings_production.py` importing from base and override email/broker/channel config; then set:
```
DJANGO_SETTINGS_MODULE=ecommerce.settings_production
```
inside the WSGI file and scheduled tasks.

---
Deployment complete. Adjust the `.env` as you scale (switch to Postgres, external cache, real email backend, removing eager Celery fallback).
