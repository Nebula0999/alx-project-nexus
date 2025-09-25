from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ('gateway', 'amount', 'currency', 'status', 'reference', 'created_at')
	search_fields = ('gateway', 'reference')
	readonly_fields = ('created_at',)
