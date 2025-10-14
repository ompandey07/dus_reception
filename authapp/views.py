from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from managementapp.models import Booking, ActivityLog
from .models import CustomUser
import json

User = get_user_model()


# ============================================================
# ACTIVITY LOG HELPER FUNCTION
# ============================================================
def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(action, entity_type, entity_id=None, entity_name='', description='', request=None, performed_by_user=None, performed_by_custom=None):
    """
    Helper function to create activity logs
    Usage: log_activity('create', 'booking', booking.id, booking.client_name, 'Created new booking', request)
    """
    try:
        ip_address = get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        ActivityLog.objects.create(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            description=description,
            performed_by_user=performed_by_user,
            performed_by_custom=performed_by_custom,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Silent fail - don't break main functionality if logging fails
        print(f"Activity logging error: {e}")


# ============================================================
# UNIFIED LOGIN VIEW (ONE ROUTE FOR BOTH ADMIN & USER)
# ============================================================
def login_view(request):
    """Single Login View: Automatically detects and handles both Admin and CustomUser login.
    Redirects to appropriate dashboard based on user type."""
    
    # If user already logged in, redirect them directly
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('admin_dashboard')
        elif request.COOKIES.get("custom_user_id"):
            return redirect('user_dashboard')

    if request.method == 'GET':
        return render(request, "Auth/login.html")

    # Get credentials
    if request.content_type == 'application/json':
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
            login(request, user)
            
            # Log admin login activity
            log_activity(
                'login',
                'system',
                description=f'Admin user {user.username} logged in',
                request=request,
                performed_by_user=user
            )
            
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'user_type': 'admin',
                    'redirect': '/auth/admin/dashboard/'
                })
            return redirect('admin_dashboard')
    except User.DoesNotExist:
        pass

    # Try Custom User Login
    try:
        custom_user = CustomUser.objects.get(login_email=email)
        if check_password(password, custom_user.login_password):
            
            # Log custom user login activity
            log_activity(
                'login',
                'system',
                description=f'Custom user {custom_user.full_name} logged in',
                request=request,
                performed_by_custom=custom_user
            )
            
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
            
            # Set simple cookie to identify custom user session
            response.set_cookie("custom_user_id", custom_user.id, httponly=True, samesite='Lax')
            response.set_cookie("user_type", 'user', httponly=True, samesite='Lax')
            
            return response
    except CustomUser.DoesNotExist:
        pass

    # Login Failed
    return JsonResponse({'error': 'Invalid email or password'}, status=400)

# ============================================================
# UNIFIED LOGOUT VIEW (ONE ROUTE FOR BOTH)
# ============================================================
def logout_view(request):
    """Single Logout View: Handles both Admin and CustomUser logout.
    Automatically detects user type and clears appropriate cookies."""
    if request.method != 'POST':
        return redirect('login')

    user_type = request.COOKIES.get("user_type")

    # Handle Admin Logout
    if user_type == 'admin' or request.user.is_authenticated:
        
        # Log admin logout activity
        log_activity(
            'logout',
            'system',
            description=f'Admin user {request.user.username} logged out',
            request=request,
            performed_by_user=request.user
        )
        
        logout(request)
        if request.content_type == 'application/json':
            response = JsonResponse({
                'success': True,
                'message': 'Logged out successfully',
                'redirect': '/login/'
            })
        else:
            response = redirect('login')
        
        response.delete_cookie("user_type")
        return response

    # Handle Custom User Logout
    custom_user_id = request.COOKIES.get("custom_user_id")
    if custom_user_id:
        try:
            custom_user = CustomUser.objects.get(id=custom_user_id)
            # Log custom user logout activity
            log_activity(
                'logout',
                'system',
                description=f'Custom user {custom_user.full_name} logged out',
                request=request,
                performed_by_custom=custom_user
            )
        except CustomUser.DoesNotExist:
            pass
    
    if request.content_type == 'application/json':
        response = JsonResponse({
            'success': True,
            'message': 'Logged out successfully',
            'redirect': '/login/'
        })
    else:
        response = redirect('login')

    response.delete_cookie("custom_user_id")
    response.delete_cookie("user_type")
    
    return response

# ============================================================
# ADMIN DASHBOARD VIEW
# ============================================================
@login_required(login_url='/unauthorized/')
def admin_dashboard(request):
    """Renders dashboard page for authenticated admin users"""
    user = request.user
    
    if not (user.is_superuser or user.is_staff):
        return redirect('login')
    
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

def custom_user_dashboard(request):
    """Renders dashboard page for authenticated custom users"""
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
@login_required(login_url='/unauthorized/')
def custom_user_registration(request):
    """Handles custom user registration"""
    if request.method == 'GET':
        return render(request, "Auth/register.html")
    
    # Get data from request
    if request.content_type == 'application/json':
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
    
    # Log custom user registration activity
    log_activity(
        'create',
        'custom_user',
        entity_id=custom_user.id,
        entity_name=custom_user.full_name,
        description=f'New custom user registered: {custom_user.full_name} ({custom_user.login_email})',
        request=request,
        performed_by_user=request.user if request.user.is_authenticated else None
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
@login_required(login_url='/unauthorized/')
def custom_user_api(request, user_id=None):
    """Handles user CRUD operations via API"""
    if request.method == 'GET':
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
    
    elif request.method == 'PUT':
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Parse JSON data
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
        
        # Log custom user update activity
        log_activity(
            'update',
            'custom_user',
            entity_id=user.id,
            entity_name=user.full_name,
            description=f'Updated custom user: {user.full_name} ({user.login_email})',
            request=request,
            performed_by_user=request.user if request.user.is_authenticated else None
        )
        
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
    
    elif request.method == 'DELETE':
        user = get_object_or_404(CustomUser, id=user_id)
        user_name = user.full_name
        user_email = user.login_email
        
        # Log custom user deletion activity BEFORE deleting
        log_activity(
            'delete',
            'custom_user',
            entity_id=user.id,
            entity_name=user_name,
            description=f'Deleted custom user: {user_name} ({user_email})',
            request=request,
            performed_by_user=request.user if request.user.is_authenticated else None
        )
        
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User "{user_name}" deleted successfully'
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)