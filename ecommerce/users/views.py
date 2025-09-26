from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from notifications.tasks import send_verification_email
from django.conf import settings

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # Ensure only verified users can obtain tokens
        email_or_username = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        if not email_or_username or not password:
            return Response({'detail': 'Username/email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        # Support login via username (primary USERNAME_FIELD)
        user = None
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(username=email_or_username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=email_or_username)
            except User.DoesNotExist:
                pass
        if user and not user.is_verified:
            return Response({'detail': 'Email not verified. Please verify your email before logging in.'}, status=status.HTTP_403_FORBIDDEN)
        return super().post(request, *args, **kwargs)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = UserSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Attempt async email via Celery; fallback to sync in dev if broker is unavailable
        try:
            send_verification_email.delay(user.id)
        except Exception:
            # Development fallback: execute synchronously
            if settings.DEBUG:
                send_verification_email(user.id)
            else:
                raise
        
        return Response(
            {"message": "User created successfully. Please check your email for verification."},
            status=status.HTTP_201_CREATED
        )


@api_view(["POST"])  # {"email": "user@example.com"}
@permission_classes([AllowAny])
def resend_verification_email(request):
    email = request.data.get('email')
    if not email:
        return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    if user.is_verified:
        return Response({"detail": "User already verified."}, status=status.HTTP_200_OK)
    try:
        send_verification_email.delay(user.id)
    except Exception:
        if settings.DEBUG:
            send_verification_email(user.id)
        else:
            raise
    return Response({"detail": "Verification email sent."}, status=status.HTTP_200_OK)