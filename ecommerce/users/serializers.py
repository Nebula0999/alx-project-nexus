from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for creating and viewing users.

    - `password` is write-only and will be hashed before saving.
    - read_only fields protect internal flags.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'password',
            'phone', 'is_verified', 'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('is_verified', 'is_active', 'created_at', 'updated_at')

    def create(self, validated_data):
        raw_password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(raw_password)
        user.save(update_fields=['password'])
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=['password'])
        return instance

    
class CustomTokenObtainPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']