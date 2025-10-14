from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.views import View
from django.db.models import Sum, Count
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from managementapp.models import Booking
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
# UNIFIED LOGIN VIEW (ONE ROUTE FOR BOTH ADMIN & USER)
# ============================================================
class LoginView(View):
    """
    Single Login View: Automatically detects and handles both Admin and CustomUser login.
    Redirects to appropriate dashboard based on user type.
    """
    def get(self, request):
        return render(request, "Auth/login.html")

    def post(self, request):
        # Get credentials from request
        if request.content_type == 'application/json':
            import json
            try:
                data = json.loads(request.body)
                email = data.get('email', '').strip()
                password = data.get('password', '').strip()
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        else:
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
        
        # Validation
        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)
        
        # Try Admin Login First
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
            
            if user and (user.is_superuser or user.is_staff):
                # Admin Login Success
                return self._login_admin(request, user)
        except User.DoesNotExist:
            pass
        
        # Try Custom User Login
        try:
            custom_user = CustomUser.objects.get(login_email=email)
            if check_password(password, custom_user.login_password):
                # Custom User Login Success
                return self._login_custom_user(request, custom_user)
        except CustomUser.DoesNotExist:
            pass
        
        # Login Failed
        return JsonResponse({'error': 'Invalid email or password'}, status=400)
    
    def _login_admin(self, request, user):
        """Handle admin user login"""
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Prepare response
        if request.content_type == 'application/json':
            response = JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user_type': 'admin',
                'redirect': '/auth/admin/dashboard/'
            })
        else:
            response = redirect('admin_dashboard')
        
        # Set cookies
        response.set_cookie("access", access_token, httponly=True, samesite='Lax')
        response.set_cookie("refresh", refresh_token, httponly=True, samesite='Lax')
        response.set_cookie("user_type", 'admin', httponly=True, samesite='Lax')
        
        return response
    
    def _login_custom_user(self, request, custom_user):
        """Handle custom user login"""
        # Prepare response
        if request.content_type == 'application/json':
            response = JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user_type': 'user',
                'redirect': '/auth/user/dashboard/',
                'user_data': {
                    'id': custom_user.id,
                    'full_name': custom_user.full_name,
                    'email': custom_user.login_email
                }
            })
        else:
            response = redirect('user_dashboard')
        
        # Set cookies
        response.set_cookie("custom_user_id", custom_user.id, httponly=True, samesite='Lax')
        response.set_cookie("user_type", 'user', httponly=True, samesite='Lax')
        
        return response


# ============================================================
# UNIFIED LOGOUT VIEW (ONE ROUTE FOR BOTH)
# ============================================================
class LogoutView(View):
    """
    Single Logout View: Handles both Admin and CustomUser logout.
    Automatically detects user type and clears appropriate cookies.
    """
    def post(self, request):
        user_type = request.COOKIES.get("user_type")
        
        # Handle Admin Logout
        if user_type == 'admin':
            refresh_token = request.COOKIES.get("refresh")
            
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except TokenError:
                    pass
            
            # Prepare response
            if request.content_type == 'application/json':
                response = JsonResponse({
                    'success': True,
                    'message': 'Logged out successfully',
                    'redirect': '/login/'
                })
            else:
                response = redirect('login')
            
            # Clear admin cookies
            response.delete_cookie("access")
            response.delete_cookie("refresh")
            response.delete_cookie("user_type")
            
            return response
        
        # Handle Custom User Logout
        if request.content_type == 'application/json':
            response = JsonResponse({
                'success': True,
                'message': 'Logged out successfully',
                'redirect': '/login/'
            })
        else:
            response = redirect('login')
        
        # Clear custom user cookies
        response.delete_cookie("custom_user_id")
        response.delete_cookie("user_type")
        
        return response


# ============================================================
# ADMIN DASHBOARD VIEW
# ============================================================
class AdminDashboardView(View):
    """Renders dashboard page for authenticated admin users"""
    
    def dispatch(self, request, *args, **kwargs):
        # Check authentication
        access_token = request.COOKIES.get("access")
        user_type = request.COOKIES.get("user_type")
        
        if not access_token or user_type != 'admin':
            return redirect('login')
        
        # Validate token and get user
        auth = CookieJWTAuthentication()
        try:
            user_auth = auth.authenticate(request)
            if user_auth is None:
                return redirect('login')
            request.user = user_auth[0]
        except Exception:
            return redirect('login')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        
        user = request.user
        
        # Get statistics for admin (all bookings and users)
        total_bookings = Booking.objects.count()
        total_users = CustomUser.objects.count()
        total_advance = Booking.objects.aggregate(
            total=Sum('advance_given')
        )['total'] or 0
        
        # Get recent bookings for activity log
        recent_bookings = Booking.objects.select_related(
            'created_by_user', 'created_by_custom'
        ).order_by('-created_at')[:5]
        
        context = {
            "email": user.email,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "total_bookings": total_bookings,
            "total_users": total_users,
            "total_advance": total_advance,
            "recent_bookings": recent_bookings,
        }
        return render(request, "admin/dashboards.html", context)


# ============================================================
# CUSTOM USER DASHBOARD VIEW
# ============================================================
class CustomUserDashboardView(View):
    """Renders dashboard page for authenticated custom users"""
    
    def get(self, request):
        
        custom_user_id = request.COOKIES.get("custom_user_id")
        user_type = request.COOKIES.get("user_type")
        
        if not custom_user_id or user_type != 'user':
            return redirect("login")
        
        try:
            custom_user = CustomUser.objects.get(id=custom_user_id)
            
            # Get statistics for this specific user (only their bookings)
            user_bookings = Booking.objects.filter(created_by_custom=custom_user)
            total_bookings = user_bookings.count()
            total_advance = user_bookings.aggregate(
                total=Sum('advance_given')
            )['total'] or 0
            
            # Get recent bookings created by this user
            recent_bookings = user_bookings.order_by('-created_at')[:5]
            
            context = {
                "full_name": custom_user.full_name,
                "email": custom_user.login_email,
                "created_at": custom_user.created_at,
                "updated_at": custom_user.updated_at,
                "total_bookings": total_bookings,
                "total_advance": total_advance,
                "recent_bookings": recent_bookings,
            }
            return render(request, "user/user_dashboard.html", context)
        except CustomUser.DoesNotExist:
            return redirect("login")


# ============================================================
# CUSTOM USER REGISTRATION VIEW
# ============================================================
class CustomUserRegistrationView(View):
    """Handles custom user registration"""
    
    def get(self, request):
        return render(request, "Auth/register.html")
    
    def post(self, request):
        # Get data from request
        if request.content_type == 'application/json':
            import json
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        else:
            data = request.POST
        
        full_name = data.get('full_name', '').strip()
        login_email = data.get('login_email', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        # Validation
        errors = {}
        
        if not full_name:
            errors['full_name'] = 'Full name is required'
        
        if not login_email:
            errors['login_email'] = 'Email is required'
        elif CustomUser.objects.filter(login_email=login_email).exists():
            errors['login_email'] = 'Email already registered'
        
        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters'
        
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'
        
        if errors:
            return JsonResponse(errors, status=400)
        
        # Create user
        custom_user = CustomUser.objects.create(
            full_name=full_name,
            login_email=login_email,
            login_password=make_password(password),
            created_by=request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        )
        
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Registration successful',
                'user_id': custom_user.id,
                'redirect': '/login/'
            }, status=201)
        
        return redirect("login")


# ============================================================
# CUSTOM USER API VIEW (List, Update, Delete)
# ============================================================
class CustomUserAPIView(View):
    """Handles user CRUD operations via API"""
    
    def get(self, request, user_id=None):
        """List all users or get single user"""
        if user_id:
            # Get single user
            user = get_object_or_404(CustomUser, id=user_id)
            return JsonResponse({
                'id': user.id,
                'full_name': user.full_name,
                'login_email': user.login_email,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        else:
            # List all users
            users = CustomUser.objects.all().order_by('-created_at')
            users_data = [{
                'id': user.id,
                'full_name': user.full_name,
                'login_email': user.login_email,
                'created_at': user.created_at.isoformat() if user.created_at else None
            } for user in users]
            
            return JsonResponse({
                'users': users_data,
                'count': len(users_data)
            })
    
    def put(self, request, user_id):
        """Update user"""
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Parse JSON data
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        full_name = data.get('full_name', '').strip()
        login_email = data.get('login_email', '').strip()
        
        # Validation
        if not full_name:
            return JsonResponse({'error': 'Full name is required'}, status=400)
        
        if not login_email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        # Check if email already exists for another user
        if CustomUser.objects.filter(login_email=login_email).exclude(id=user_id).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)
        
        # Update user
        user.full_name = full_name
        user.login_email = login_email
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'full_name': user.full_name,
                'login_email': user.login_email,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        })
    
    def delete(self, request, user_id):
        """Delete user"""
        user = get_object_or_404(CustomUser, id=user_id)
        user_name = user.full_name
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User "{user_name}" deleted successfully'
        })