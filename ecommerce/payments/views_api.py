from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Payment
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'gateway': ['exact'],
        'currency': ['exact'],
        'amount': ['exact', 'lt', 'lte', 'gt', 'gte'],
        'created_at': ['date', 'date__lt', 'date__gt'],
    }
    search_fields = ['reference', 'gateway', 'currency']
    ordering_fields = ['amount', 'created_at']
    ordering = ['-created_at']
    throttle_scope = 'payments'

    @method_decorator(cache_page(30))  # 30 second cache
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
