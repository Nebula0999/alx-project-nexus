from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'gateway', 'amount', 'currency', 'status', 'reference', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')
