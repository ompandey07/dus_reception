from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views , base_views

# ============================================================
# Backup App URL Patterns
# ============================================================
urlpatterns = [
    # Main calendar view
    path('calendar/', views.calendar_view, name='calendar'),
    
    # API endpoints
    path('api/bookings/', views.get_bookings, name='get_bookings'),
    path('api/bookings/date/<str:date_str>/', views.get_bookings_by_date, name='get_bookings_by_date'),
    path('api/bookings/create/', views.create_booking, name='create_booking'),
    path('api/bookings/<int:booking_id>/update/', views.update_booking, name='update_booking'),
    path('api/bookings/<int:booking_id>/delete/', views.delete_booking, name='delete_booking'),
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