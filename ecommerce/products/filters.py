import django_filters
from .models import Product
from django.utils import timezone


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    created_after = django_filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='categories__slug', lookup_expr='exact')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    is_digital = django_filters.BooleanFilter(field_name='is_digital')

    class Meta:
        model = Product
        fields = [
            'is_active', 'is_digital', 'category', 'min_price', 'max_price',
            'created_after', 'created_before'
        ]