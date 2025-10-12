from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser

User = get_user_model()

# ============================================================
# ADMIN AUTH SERIALIZERS
# ============================================================
class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        user = authenticate(username=user_obj.username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        # Only allow superuser or staff
        if not (user.is_superuser or user.is_staff):
            raise serializers.ValidationError("Access denied. Only admin users can log in.")

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "email": user.email,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }


class AdminLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        token = attrs.get("refresh")
        if not token:
            raise serializers.ValidationError("Refresh token is required")
        self.token = token
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except Exception:
            raise serializers.ValidationError("Invalid or expired token")


# ============================================================
# CUSTOM USER AUTH SERIALIZERS
# ============================================================
class CustomUserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            custom_user = CustomUser.objects.get(login_email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        # Check password
        if not check_password(password, custom_user.login_password):
            raise serializers.ValidationError("Invalid email or password")

        # Create a simple token (you can use JWT if needed)
        return {
            "id": custom_user.id,
            "full_name": custom_user.full_name,
            "email": custom_user.login_email,
            "created_at": custom_user.created_at,
            "updated_at": custom_user.updated_at,
        }


class CustomUserLogoutSerializer(serializers.Serializer):
    """Simple logout serializer for custom users"""
    pass


class CustomUserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['full_name', 'login_email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        # Check if email already exists
        if CustomUser.objects.filter(login_email=data['login_email']).exists():
            raise serializers.ValidationError("Email already registered")
        
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        custom_user = CustomUser.objects.create(
            full_name=validated_data['full_name'],
            login_email=validated_data['login_email'],
            login_password=make_password(password),
            created_by=self.context.get('created_by')
        )
        
        return custom_user