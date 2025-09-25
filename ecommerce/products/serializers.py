from rest_framework import serializers
from django.db import transaction
from .models import (
    Category, Product, ProductVariant,
    Order, OrderItem
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'parent', 'is_active', 'created_at')


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ('id', 'product', 'name', 'sku', 'price', 'attributes', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'short_description', 'sku', 'price', 'is_active')


class ProductDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'description', 'short_description', 'sku',
            'price', 'compare_price', 'categories', 'attributes', 'is_active',
            'is_digital', 'weight', 'dimensions', 'created_at', 'updated_at', 'variants'
        )
        read_only_fields = ('created_at', 'updated_at')


class OrderItemSerializer(serializers.ModelSerializer):
    product_variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.filter(is_active=True))

    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product_variant', 'quantity', 'unit_price', 'total_price', 'created_at')
        read_only_fields = ('id', 'unit_price', 'total_price', 'created_at')


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)
    order_items = OrderItemSerializer(many=True, source='items', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'total_amount', 'tax_amount', 'shipping_amount', 'discount_amount',
            'billing_first_name', 'billing_last_name', 'billing_email', 'billing_phone', 'billing_address',
            'shipping_first_name', 'shipping_last_name', 'shipping_address', 'notes',
            'created_at', 'items', 'order_items'
        ]
        read_only_fields = ('id', 'order_number', 'total_amount', 'created_at')

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        # create order skeleton
        order = Order.objects.create(**validated_data, order_number=self._generate_order_number(), total_amount=0)
        total = 0
        for item in items_data:
            pv = item['product_variant']
            qty = item['quantity']
            unit_price = pv.price
            item_total = unit_price * qty
            OrderItem.objects.create(
                order=order,
                product_variant=pv,
                quantity=qty,
                unit_price=unit_price,
                total_price=item_total
            )
            total += item_total

            # Optional: update inventory here (requires a stock field on ProductVariant)
        order.total_amount = total
        order.save(update_fields=['total_amount'])
        return order

    def _generate_order_number(self):
        import uuid
        return str(uuid.uuid4()).split('-')[0].upper()
from rest_framework import serializers
from .models import Product, ProductVariant, Category


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'children']
    
    def get_children(self, obj):
        if hasattr(obj, 'children'):
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []
class ProductVariantSerializer(serializers.ModelSerializer):
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'sku', 'price', 'attributes', 'is_available']
    
    def get_is_available(self, obj):
        # Check inventory availability
        return obj.is_active
class ProductSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'sku', 'price', 'compare_price', 'categories', 'variants',
            'attributes', 'images', 'is_in_stock', 'is_digital',
            'weight', 'dimensions', 'created_at', 'updated_at'
        ]
    
    def get_images(self, obj):

        # Return product images
        return []  # Implement image handling
    
    def get_is_in_stock(self, obj):
        # Check if any variant is in stock
        return True  # Implement stock checking logic