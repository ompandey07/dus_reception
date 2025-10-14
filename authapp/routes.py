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
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.custom_user_registration, name="user_register"),
    
    # --------------------------------------------------------
    # DASHBOARD ROUTES
    # --------------------------------------------------------
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("user/dashboard/", views.custom_user_dashboard, name="user_dashboard"),
    
    # --------------------------------------------------------
    # CUSTOM USER API ROUTES
    # --------------------------------------------------------
    path("api/users/", views.custom_user_api, name="user_list_api"),
    path("api/users/<int:user_id>/", views.custom_user_api, name="user_detail_api"),
]

# ============================================================
# Serve media files
# ============================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)