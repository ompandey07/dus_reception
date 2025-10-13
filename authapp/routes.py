from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

# ============================================================
# AUTHAPP ROUTES
# ============================================================
urlpatterns = [ 
    # --------------------------------------------------------
    # ADMIN AUTH ROUTES
    # --------------------------------------------------------
    path("admin/login/", views.LoginView.as_view(), {'user_type': 'admin'}, name="admin_login"),
    path("admin/logout/", views.AdminLogoutView.as_view(), name="admin_logout"),
    path("admin/dashboard/", views.AdminDashboardView.as_view(), name="admin_dashboard"),

    # --------------------------------------------------------
    # CUSTOM USER AUTH ROUTES
    # --------------------------------------------------------
    path("user/login/", views.LoginView.as_view(), {'user_type': 'user'}, name="user_login"),
    path("user/logout/", views.CustomUserLogoutView.as_view(), name="user_logout"),
    path("user/dashboard/", views.CustomUserDashboardView.as_view(), name="user_dashboard"),
    path("user/register/", views.CustomUserRegistrationView.as_view(), name="user_register"),
    path("api/users/", views.CustomUserAPIView.as_view(), name="user_list_api"),
    path("api/users/<int:user_id>/", views.CustomUserAPIView.as_view(), name="user_detail_api"),
]

# ============================================================
# Serve media files in development and production
# ============================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)