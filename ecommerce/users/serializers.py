from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.contrib.auth import get_user_model
from .models import User

User = get_user_model()

class UserSerializer(ModelSerializer):
    full_name = SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'phone', 'is_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
class CustomTokenObtainPairSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']