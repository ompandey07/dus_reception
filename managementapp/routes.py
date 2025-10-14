from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views , base_views , activity_log_views , reports_views

# ============================================================
# MANAGEMENT APP URL PATTERNS
# ============================================================
urlpatterns = [

    # =============================
    #  BASE VIEWS
    # =============================
    path('', base_views.index_page, name='index_page'),
    path('unauthorized/', base_views.unauthorized_page, name='unauthorized_page'),

    # =============================
    #  ACTIVITY LOG VIEWS
    # =============================
    path('activity/', activity_log_views.activity_log_view, name='activity_log_view'),
    path('activity/logs/', activity_log_views.get_activity_logs, name='get_activity_logs'),
    path('activity/stats/', activity_log_views.get_activity_stats, name='get_activity_stats'),
    path('activity/clear/', activity_log_views.clear_old_logs, name='clear_old_logs'),


    # =============================
    #  REPORTS VIEWS
    # =============================
    path('reports/', reports_views.booking_reports_view, name='booking_reports_view'),
    path('api/reports/', reports_views.get_booking_reports, name='get_booking_reports'),
    path('api/reports/export/', reports_views.export_booking_reports, name='export_booking_reports'),

    # =============================
    #  RENDER CALANDER VIEW
    # =============================
    path('calendar/', views.calendar_view, name='calendar_view'),
    
    # =============================
    #  CALANDER API ENDPOINTS
    # =============================
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