from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from .models import CustomUser


def login_required_dual(login_url='/unauthorized/'):
    """
    Decorator that accepts BOTH Django admin users AND custom users (via cookies)
    Works with both function-based views and ensures custom users aren't redirected to unauthorized
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is Django admin user
            if request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            # Check if user is custom user (via cookie)
            custom_user_id = request.COOKIES.get("custom_user_id")
            user_type = request.COOKIES.get("user_type")
            
            if custom_user_id and user_type == 'user':
                try:
                    custom_user = CustomUser.objects.get(id=custom_user_id)
                    # Optionally attach custom user to request for use in view
                    request.custom_user = custom_user
                    return view_func(request, *args, **kwargs)
                except CustomUser.DoesNotExist:
                    pass
            
            # If neither admin nor custom user, redirect to login
            return redirect(login_url)
        
        return wrapper
    return decorator