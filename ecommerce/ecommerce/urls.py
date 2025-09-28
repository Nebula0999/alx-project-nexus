"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.db import connections
from django.core.cache import caches
import time
from rest_framework.routers import DefaultRouter

from users.views_api import UserViewSet, verify_email_view
from products.views_api import ProductViewSet
from payments.views_api import PaymentViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from users.views import RegisterView, resend_verification_email, CustomTokenObtainPairView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'payments', PaymentViewSet, basename='payment')

def health_view(request):
    started = time.time()
    db_ok = True
    cache_ok = True
    db_error = None
    cache_error = None
    # DB check (default connection)
    try:
        with connections['default'].cursor() as cur:
            cur.execute('SELECT 1;')
            cur.fetchone()
    except Exception as exc:  # pragma: no cover (depends on infra)
        db_ok = False
        db_error = str(exc)[:200]
    # Cache check
    try:
        cache = caches['default']
        cache.set('__healthcheck__', '1', 5)
        val = cache.get('__healthcheck__')
        if val != '1':
            raise RuntimeError('cache_miss')
    except Exception as exc:  # pragma: no cover
        cache_ok = False
        cache_error = str(exc)[:200]
    elapsed_ms = int((time.time() - started) * 1000)
    overall = db_ok and cache_ok
    status_code = 200 if overall else 503
    return JsonResponse({
        'status': 'ok' if overall else 'degraded',
        'db': db_ok,
        'cache': cache_ok,
        'elapsed_ms': elapsed_ms,
        'db_error': db_error,
        'cache_error': cache_error,
    }, status=status_code)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_view),  # Enhanced health check
    path('api/', include(router.urls)),
    # auth
    path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/resend-verification/', resend_verification_email, name='resend-verification'),
    path('api/verify-email/<str:token>/', verify_email_view, name='verify-email'),
    # OpenAPI / Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
