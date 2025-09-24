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