from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

# ============================================================
# AUTHAPP ROUTES
# ============================================================
urlpatterns = [ 
    # --------------------------------------------------------
    # UNIFIED AUTH ROUTES (handles both admin & user)
    # --------------------------------------------------------
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("register/", views.CustomUserRegistrationView.as_view(), name="user_register"),
    
    # --------------------------------------------------------
    # DASHBOARD ROUTES
    # --------------------------------------------------------
    path("admin/dashboard/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("user/dashboard/", views.CustomUserDashboardView.as_view(), name="user_dashboard"),
    
    # --------------------------------------------------------
    # CUSTOM USER API ROUTES
    # --------------------------------------------------------
    path("api/users/", views.CustomUserAPIView.as_view(), name="user_list_api"),
    path("api/users/<int:user_id>/", views.CustomUserAPIView.as_view(), name="user_detail_api"),
]

# ============================================================
# Serve media files
# ============================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)