from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    AdminLoginSerializer, 
    AdminLogoutSerializer,
    CustomUserLoginSerializer,
    CustomUserLogoutSerializer,
    CustomUserRegistrationSerializer
)
from .models import CustomUser

User = get_user_model()


# ============================================================
# COOKIE JWT AUTHENTICATION
# ============================================================
class CookieJWTAuthentication(JWTAuthentication):
    """
    Reads JWT access token from cookie and authenticates the user.
    """
    def authenticate(self, request):
        access_token = request.COOKIES.get("access")
        if not access_token:
            return None
        
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        return super().authenticate(request)


# ============================================================
# SHARED LOGIN VIEW (ADMIN + CUSTOM USER)
# ============================================================
class LoginView(APIView):
    """
    Universal Login View:
    Handles both Admin and CustomUser login based on routing.
    """
    def get(self, request, user_type='admin'):
        # Render the login page with user_type context
        return render(request, "Auth/login.html", {"user_type": user_type})

    def post(self, request, user_type='admin'):
        # Route to appropriate serializer based on user_type
        if user_type == 'admin':
            serializer = AdminLoginSerializer(data=request.data)
            redirect_url = "admin_dashboard"
            cookie_based = True
        else:
            serializer = CustomUserLoginSerializer(data=request.data)
            redirect_url = "user_dashboard"
            cookie_based = False
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            # For JSON request
            if request.content_type == 'application/json':
                if cookie_based:
                    # Admin login with cookies
                    response = JsonResponse({
                        'success': True,
                        'message': 'Login successful',
                        'user_type': user_type
                    })
                    response.set_cookie("access", data["access"], httponly=True, samesite='Lax')
                    response.set_cookie("refresh", data["refresh"], httponly=True, samesite='Lax')
                    response.set_cookie("user_type", user_type, httponly=True, samesite='Lax')
                else:
                    # CustomUser login - just return JSON
                    response = JsonResponse({
                        'success': True,
                        'message': 'Login successful',
                        'user_type': user_type,
                        'user_data': data
                    })
                    # Set simple session cookie for custom user
                    response.set_cookie("custom_user_id", data["id"], httponly=True, samesite='Lax')
                    response.set_cookie("user_type", user_type, httponly=True, samesite='Lax')
                
                return response
            
            # For regular form submission
            if cookie_based:
                response = redirect(redirect_url)
                response.set_cookie("access", data["access"], httponly=True, samesite='Lax')
                response.set_cookie("refresh", data["refresh"], httponly=True, samesite='Lax')
                response.set_cookie("user_type", user_type, httponly=True, samesite='Lax')
            else:
                response = redirect(redirect_url)
                response.set_cookie("custom_user_id", data["id"], httponly=True, samesite='Lax')
                response.set_cookie("user_type", user_type, httponly=True, samesite='Lax')
            
            return response
        
        return JsonResponse(serializer.errors, status=400)


# ============================================================
# ADMIN LOGOUT VIEW
# ============================================================
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
class AdminLogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")
        if not refresh_token:
            return Response({"error": "No refresh token found"}, status=400)

        serializer = AdminLogoutSerializer(data={"refresh": refresh_token})
        if serializer.is_valid():
            serializer.save()
            response = redirect("admin_login")
            response.delete_cookie("access")
            response.delete_cookie("refresh")
            response.delete_cookie("user_type")
            return response
        return Response({"error": list(serializer.errors.values())[0][0]}, status=400)


# ============================================================
# CUSTOM USER LOGOUT VIEW
# ============================================================
class CustomUserLogoutView(APIView):
    def post(self, request):
        # Simple logout for custom users
        if request.content_type == 'application/json':
            response = JsonResponse({
                'success': True,
                'message': 'Logged out successfully'
            })
        else:
            response = redirect("user_login")
        
        response.delete_cookie("custom_user_id")
        response.delete_cookie("user_type")
        return response


# ============================================================
# ADMIN DASHBOARD VIEW
# ============================================================
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
class AdminDashboardView(APIView):
    """
    Renders dashboard page for authenticated admin users.
    """
    def get(self, request):
        user = request.user
        context = {
            "email": user.email,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }
        return render(request, "admin/dashboards.html", context)


# ============================================================
# CUSTOM USER DASHBOARD VIEW
# ============================================================
class CustomUserDashboardView(APIView):
    """
    Renders dashboard page for authenticated custom users.
    """
    def get(self, request):
        custom_user_id = request.COOKIES.get("custom_user_id")
        
        if not custom_user_id:
            return redirect("user_login")
        
        try:
            custom_user = CustomUser.objects.get(id=custom_user_id)
            context = {
                "full_name": custom_user.full_name,
                "email": custom_user.login_email,
                "created_at": custom_user.created_at,
                "updated_at": custom_user.updated_at,
            }
            return render(request, "user/user_dashboard.html", context)
        except CustomUser.DoesNotExist:
            return redirect("user_login")


# ============================================================
# CUSTOM USER REGISTRATION VIEW (Optional)
# ============================================================
class CustomUserRegistrationView(APIView):
    """
    Handles custom user registration.
    """
    def get(self, request):
        return render(request, "Auth/register.html")
    
    def post(self, request):
        serializer = CustomUserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            custom_user = serializer.save()
            
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': 'Registration successful',
                    'user_id': custom_user.id
                }, status=201)
            
            return redirect("user_login")
        
        return JsonResponse(serializer.errors, status=400)