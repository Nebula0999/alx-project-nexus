from django.contrib import admin
from .models import Category, Product, ProductVariant, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug', 'is_active', 'created_at')
	search_fields = ('name', 'slug')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'sku', 'price', 'is_active')
	search_fields = ('name', 'sku')
	prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
	list_display = ('product', 'name', 'sku', 'price', 'is_active')
	search_fields = ('name', 'sku')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('order_number', 'user', 'status', 'total_amount', 'created_at')
	search_fields = ('order_number', 'user__username', 'billing_email')
	readonly_fields = ('created_at', 'updated_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ('order', 'product_variant', 'quantity', 'unit_price', 'total_price')
	search_fields = ('order__order_number', 'product_variant__sku')
