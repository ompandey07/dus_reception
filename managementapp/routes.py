from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views , base_views

# ============================================================
# MANAGEMENT APP URL PATTERNS
# ============================================================
urlpatterns = [

    # index view
    path('', base_views.index_page, name='index_page'),


    # Calendar view
    path('calendar/', views.calendar_view, name='calendar_view'),
    
    # API endpoints
    path('api/calendar-data/', views.get_calendar_data, name='get_calendar_data'),
    path('api/bookings/', views.get_bookings, name='get_bookings'),
    path('api/bookings/<int:booking_id>/detail/', views.get_booking_detail, name='get_booking_detail'),
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