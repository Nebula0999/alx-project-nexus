from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from django.core import signing
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    throttle_scope = 'users'
    filterset_fields = {
        'is_active': ['exact'],
        'is_verified': ['exact'],
        'date_joined': ['date', 'date__lt', 'date__gt'] if hasattr(User, 'date_joined') else ['exact'],
    }
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'id']
    ordering = ['username']


@api_view(["GET"])  # link clicked from email
@permission_classes([permissions.AllowAny])
def verify_email_view(request, token: str):
    try:
        data = signing.loads(token, max_age=60 * 60 * 24)  # 24h validity
        user_id = data.get("uid")
        user = User.objects.get(id=user_id)
        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])
        return Response({"detail": "Email verified successfully."}, status=status.HTTP_200_OK)
    except signing.SignatureExpired:
        return Response({"detail": "Verification link expired."}, status=status.HTTP_400_BAD_REQUEST)
    except (signing.BadSignature, User.DoesNotExist):
        return Response({"detail": "Invalid verification link."}, status=status.HTTP_400_BAD_REQUEST)
