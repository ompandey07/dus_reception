from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

# ============================================================
# Backup App URL Patterns
# ============================================================
urlpatterns = [ 
    # --------------------------------------------------------
    # ADMIN AUTH ROUTES
    # --------------------------------------------------------
    # path('takebackup/', views.take_backup_control, name='take_backup_control'),

    
    
]

# ============================================================
# Serve media files in development and production
# ============================================================
if settings.DEBUG:
    # In Debug mode (development)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In Production mode (also allow media serving)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)