from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from datetime import datetime, date, timedelta
from authapp.decorators import login_required_dual
from authapp.models import CustomUser
from .models import Booking, ActivityLog
import json


# ============================================================
# BOOKING REPORTS VIEW
# ============================================================
@login_required_dual(login_url='/unauthorized/')
def booking_reports_view(request):
    """Render the booking reports page"""
    custom_users = CustomUser.objects.all()
    
    # Get current date info
    today = date.today()
    
    # Get event types for filter
    event_types = Booking.objects.values_list('event_type', flat=True).distinct()
    
    context = {
        'custom_users': custom_users,
        'event_types': event_types,
        'today': today
    }
    return render(request, 'admin/booking_reports.html', context)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["GET"])
def get_booking_reports(request):
    """API endpoint to get filtered booking reports with pagination"""
    try:
        # Get filter parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)
        event_type = request.GET.get('event_type', None)
        created_by_filter = request.GET.get('created_by', None)
        search = request.GET.get('search', None)
        min_advance = request.GET.get('min_advance', None)
        max_advance = request.GET.get('max_advance', None)
        
        # Start with all bookings
        bookings = Booking.objects.all()
        
        # Apply filters
        if date_from:
            bookings = bookings.filter(booking_date__gte=date_from)
        if date_to:
            bookings = bookings.filter(booking_date__lte=date_to)
        if event_type:
            bookings = bookings.filter(event_type=event_type)
        if min_advance:
            bookings = bookings.filter(advance_given__gte=min_advance)
        if max_advance:
            bookings = bookings.filter(advance_given__lte=max_advance)
        
        # Apply created_by filter
        if created_by_filter:
            if created_by_filter.startswith('user_'):
                user_id = created_by_filter.replace('user_', '')
                bookings = bookings.filter(created_by_user_id=user_id)
            elif created_by_filter.startswith('custom_'):
                custom_id = created_by_filter.replace('custom_', '')
                bookings = bookings.filter(created_by_custom_id=custom_id)
        
        # Apply search
        if search:
            bookings = bookings.filter(
                Q(client_name__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(email__icontains=search) |
                Q(event_type__icontains=search)
            )
        
        # Order by booking date descending
        bookings = bookings.order_by('-booking_date', '-start_time')
        
        # Calculate statistics before pagination
        total_bookings = bookings.count()
        total_advance = bookings.aggregate(Sum('advance_given'))['advance_given__sum'] or 0
        
        # Get event type breakdown
        event_breakdown = bookings.values('event_type').annotate(
            count=Count('id'),
            total_advance=Sum('advance_given')
        ).order_by('-count')
        
        # Paginate
        paginator = Paginator(bookings, per_page)
        page_obj = paginator.get_page(page)
        
        # Convert bookings to JSON
        bookings_data = []
        for booking in page_obj:
            from .views import get_nepali_date
            nepali_date = get_nepali_date(booking.booking_date)
            
            bookings_data.append({
                'id': booking.id,
                'client_name': booking.client_name,
                'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
                'booking_date_formatted': booking.booking_date.strftime('%B %d, %Y'),
                'booking_date_nepali': nepali_date['formatted_nepali'] if nepali_date else '',
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M'),
                'phone_number': booking.phone_number,
                'email': booking.email or '',
                'event_type': booking.event_type,
                'advance_given': float(booking.advance_given),
                'created_by': booking.get_creator_name(),
                'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Log report generation activity
        from .views import log_activity, get_client_ip
        performed_by_user = None
        performed_by_custom = None
        
        if request.user.is_authenticated:
            performed_by_user = request.user
        else:
            custom_user_id = request.COOKIES.get("custom_user_id")
            if custom_user_id:
                try:
                    performed_by_custom = CustomUser.objects.get(id=custom_user_id)
                except CustomUser.DoesNotExist:
                    pass
        
        filter_desc = []
        if date_from: filter_desc.append(f"from {date_from}")
        if date_to: filter_desc.append(f"to {date_to}")
        if event_type: filter_desc.append(f"event: {event_type}")
        
        log_activity(
            'view',
            'booking',
            description=f'Generated booking report ({total_bookings} bookings{", " + ", ".join(filter_desc) if filter_desc else ""})',
            request=request,
            performed_by_user=performed_by_user,
            performed_by_custom=performed_by_custom
        )
        
        return JsonResponse({
            'bookings': bookings_data,
            'statistics': {
                'total_bookings': total_bookings,
                'total_advance': float(total_advance),
                'event_breakdown': list(event_breakdown)
            },
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': total_bookings,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'per_page': per_page
            }
        }, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["GET"])
def export_booking_reports(request):
    """Export booking reports to CSV"""
    import csv
    from django.http import HttpResponse
    
    try:
        # Get same filters as report view
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)
        event_type = request.GET.get('event_type', None)
        created_by_filter = request.GET.get('created_by', None)
        search = request.GET.get('search', None)
        
        bookings = Booking.objects.all()
        
        # Apply same filters
        if date_from:
            bookings = bookings.filter(booking_date__gte=date_from)
        if date_to:
            bookings = bookings.filter(booking_date__lte=date_to)
        if event_type:
            bookings = bookings.filter(event_type=event_type)
        if created_by_filter:
            if created_by_filter.startswith('user_'):
                user_id = created_by_filter.replace('user_', '')
                bookings = bookings.filter(created_by_user_id=user_id)
            elif created_by_filter.startswith('custom_'):
                custom_id = created_by_filter.replace('custom_', '')
                bookings = bookings.filter(created_by_custom_id=custom_id)
        if search:
            bookings = bookings.filter(
                Q(client_name__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(email__icontains=search) |
                Q(event_type__icontains=search)
            )
        
        bookings = bookings.order_by('-booking_date', '-start_time')
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="booking_report_{date.today()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Client Name', 'Booking Date', 'Start Time', 'End Time', 
                        'Phone Number', 'Email', 'Event Type', 'Advance Given', 
                        'Created By', 'Created At'])
        
        for booking in bookings:
            writer.writerow([
                booking.client_name,
                booking.booking_date.strftime('%Y-%m-%d'),
                booking.start_time.strftime('%H:%M'),
                booking.end_time.strftime('%H:%M'),
                booking.phone_number,
                booking.email or '',
                booking.event_type,
                float(booking.advance_given),
                booking.get_creator_name(),
                booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Log export activity
        from .views import log_activity
        performed_by_user = None
        performed_by_custom = None
        
        if request.user.is_authenticated:
            performed_by_user = request.user
        else:
            custom_user_id = request.COOKIES.get("custom_user_id")
            if custom_user_id:
                try:
                    performed_by_custom = CustomUser.objects.get(id=custom_user_id)
                except CustomUser.DoesNotExist:
                    pass
        
        log_activity(
            'export',
            'booking',
            description=f'Exported {bookings.count()} bookings to CSV',
            request=request,
            performed_by_user=performed_by_user,
            performed_by_custom=performed_by_custom
        )
        
        return response
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)