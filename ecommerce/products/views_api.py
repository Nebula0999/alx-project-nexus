from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Product
from .filters import ProductFilter
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .serializers import ProductListSerializer, ProductDetailSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related('variants', 'categories')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # exact or field lookups for filtering
    filterset_class = ProductFilter
    # simple text search
    search_fields = ['name', 'slug', 'description', 'short_description', 'sku']
    # ordering support
    ordering_fields = ['price', 'created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer

    @method_decorator(cache_page(60))  # cache list responses for 60 seconds
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
