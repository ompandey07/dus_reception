from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q
from datetime import datetime, date, timedelta
import json
import nepali_datetime
from authapp.decorators import login_required_dual
from authapp.models import CustomUser
from .models import Booking, ActivityLog


# ============================================================
# ACTIVITY LOG HELPER FUNCTIONS
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
        print(f"Activity logging error: {e}")


# ============================================================
# NEPALI DATE HELPER
# ============================================================
def get_nepali_date(english_date):
    """Convert English date to Nepali date"""
    try:
        nepali_date = nepali_datetime.date.from_datetime_date(english_date)
        return {
            'year': nepali_date.year,
            'month': nepali_date.month,
            'day': nepali_date.day,
            'month_name': nepali_date.strftime('%B'),
            'formatted': nepali_date.strftime('%Y-%m-%d'),
            'formatted_nepali': nepali_date.strftime('%Y %B %d')
        }
    except Exception as e:
        print(f"Error converting date: {e}")
        return None


def get_shift_type(start_time, end_time):
    """Determine shift type based on start and end times"""
    from datetime import time
    
    morning_start = time(6, 0)
    afternoon_end = time(15, 0)
    evening_end = time(21, 0)
    
    # Morning shift: 6 AM to 3 PM
    if start_time == morning_start and end_time == afternoon_end:
        return 'morning'
    # Evening shift: 3 PM to 9 PM
    elif start_time == afternoon_end and end_time == evening_end:
        return 'evening'
    # Full day: 6 AM to 9 PM
    elif start_time == morning_start and end_time == evening_end:
        return 'fullday'
    # Custom time
    else:
        return 'custom'


# ============================================================
# CALENDAR VIEWS
# ============================================================
@login_required_dual(login_url='/unauthorized/')
def calendar_view(request):
    """Render the calendar booking page"""
    custom_users = CustomUser.objects.all()
    today = date.today()
    nepali_today = get_nepali_date(today)
    
    # Get event type choices for dropdown
    event_types = Booking.EVENT_TYPE_CHOICES
    
    context = {
        'custom_users': custom_users,
        'today_nepali': nepali_today,
        'event_types': event_types
    }
    return render(request, 'Function/calendar.html', context)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["GET"])
def get_calendar_data(request):
    """API endpoint to get calendar data with Nepali dates"""
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1)
        else:
            last_day = date(year, month + 1, 1)
        
        bookings = Booking.objects.filter(
            booking_date__gte=first_day,
            booking_date__lt=last_day
        )
        
        calendar_days = []
        current_date = first_day
        
        while current_date < last_day:
            nepali_date = get_nepali_date(current_date)
            day_bookings = bookings.filter(booking_date=current_date)
            
            day_data = {
                'date': current_date.strftime('%Y-%m-%d'),
                'day': current_date.day,
                'nepali_date': nepali_date,
                'is_today': current_date == date.today(),
                'booking_count': day_bookings.count(),
                'bookings': []
            }
            
            for booking in day_bookings:
                day_data['bookings'].append({
                    'id': booking.id,
                    'client_name': booking.client_name,
                    'event_type': booking.get_event_type_display(),
                    'start_time': booking.start_time.strftime('%H:%M'),
                    'end_time': booking.end_time.strftime('%H:%M'),
                    'color': booking.get_time_color(),
                    'shift_type': get_shift_type(booking.start_time, booking.end_time)
                })
            
            calendar_days.append(day_data)
            current_date = current_date + timedelta(days=1)
        
        return JsonResponse({
            'calendar_days': calendar_days,
            'year': year,
            'month': month
        }, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["GET"])
def get_bookings(request):
    """API endpoint to get all bookings with Nepali dates"""
    try:
        created_by_filter = request.GET.get('created_by', None)
        bookings = Booking.objects.all()
        
        if created_by_filter:
            if created_by_filter.startswith('user_'):
                user_id = created_by_filter.replace('user_', '')
                bookings = bookings.filter(created_by_user_id=user_id)
            elif created_by_filter.startswith('custom_'):
                custom_id = created_by_filter.replace('custom_', '')
                bookings = bookings.filter(created_by_custom_id=custom_id)
        
        bookings_data = []
        for booking in bookings:
            nepali_date = get_nepali_date(booking.booking_date)
            bookings_data.append({
                'id': booking.id,
                'client_name': booking.client_name,
                'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
                'booking_date_nepali': nepali_date['formatted_nepali'] if nepali_date else '',
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M'),
                'phone_number': booking.phone_number,
                'email': booking.email or '',
                'event_type': booking.event_type,
                'event_type_display': booking.get_event_type_display(),
                'menu_type': booking.menu_type or '',
                'no_of_packs': booking.no_of_packs or '',
                'advance_given': str(booking.advance_given),
                'color': booking.get_time_color(),
                'shift_type': get_shift_type(booking.start_time, booking.end_time),
                'created_by': booking.get_creator_name(),
                'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({'bookings': bookings_data}, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["GET"])
def get_booking_detail(request, booking_id):
    """API endpoint to get detailed booking information"""
    try:
        booking = Booking.objects.get(id=booking_id)
        nepali_date = get_nepali_date(booking.booking_date)
        
        booking_data = {
            'id': booking.id,
            'client_name': booking.client_name,
            'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
            'booking_date_formatted': booking.booking_date.strftime('%B %d, %Y'),
            'booking_date_nepali': nepali_date['formatted_nepali'] if nepali_date else '',
            'nepali_year': nepali_date['year'] if nepali_date else '',
            'nepali_month': nepali_date['month_name'] if nepali_date else '',
            'nepali_day': nepali_date['day'] if nepali_date else '',
            'start_time': booking.start_time.strftime('%H:%M'),
            'end_time': booking.end_time.strftime('%H:%M'),
            'phone_number': booking.phone_number,
            'email': booking.email or '',
            'event_type': booking.event_type,
            'event_type_display': booking.get_event_type_display(),
            'menu_type': booking.menu_type or '',
            'no_of_packs': booking.no_of_packs or '',
            'advance_given': str(booking.advance_given),
            'color': booking.get_time_color(),
            'shift_type': get_shift_type(booking.start_time, booking.end_time),
            'created_by': booking.get_creator_name(),
            'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return JsonResponse({'booking': booking_data}, status=200)
    
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["POST"])
def create_booking(request):
    """API endpoint to create a new booking"""
    try:
        data = json.loads(request.body)
        
        required_fields = ['client_name', 'booking_date', 'start_time', 'end_time', 
                          'phone_number', 'event_type', 'advance_given']
        for field in required_fields:
            if field not in data or data[field] == '' or data[field] is None:
                return JsonResponse({'error': f'{field.replace("_", " ").title()} is required'}, status=400)
        
        # Validate advance_given
        try:
            advance_given = float(data['advance_given'])
            if advance_given < 0:
                return JsonResponse({'error': 'Advance given cannot be negative'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid advance given amount'}, status=400)
        
        booking_date = datetime.strptime(data['booking_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        if end_time <= start_time:
            return JsonResponse({'error': 'End time must be after start time'}, status=400)
        
        bookings_on_date = Booking.objects.filter(booking_date=booking_date).count()
        if bookings_on_date >= 2:
            return JsonResponse({'error': 'Maximum 2 bookings per day'}, status=400)
        
        created_by_user = None
        created_by_custom = None
        
        if request.user.is_authenticated:
            created_by_user = request.user
        else:
            custom_user_id = request.COOKIES.get("custom_user_id")
            if custom_user_id:
                try:
                    created_by_custom = CustomUser.objects.get(id=custom_user_id)
                except CustomUser.DoesNotExist:
                    pass
        
        booking = Booking.objects.create(
            client_name=data['client_name'],
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            phone_number=data['phone_number'],
            email=data.get('email', ''),
            event_type=data['event_type'],
            menu_type=data.get('menu_type', ''),
            no_of_packs=data.get('no_of_packs', ''),
            advance_given=advance_given,
            created_by_user=created_by_user,
            created_by_custom=created_by_custom
        )
        
        log_activity(
            'create',
            'booking',
            entity_id=booking.id,
            entity_name=booking.client_name,
            description=f'Created new booking for {booking.client_name} on {booking.booking_date} ({booking.get_event_type_display()})',
            request=request,
            performed_by_user=created_by_user,
            performed_by_custom=created_by_custom
        )
        
        nepali_date = get_nepali_date(booking.booking_date)
        
        return JsonResponse({
            'message': 'Booking created successfully',
            'booking': {
                'id': booking.id,
                'client_name': booking.client_name,
                'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
                'booking_date_nepali': nepali_date['formatted_nepali'] if nepali_date else '',
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M'),
                'phone_number': booking.phone_number,
                'email': booking.email or '',
                'event_type': booking.event_type,
                'event_type_display': booking.get_event_type_display(),
                'menu_type': booking.menu_type or '',
                'no_of_packs': booking.no_of_packs or '',
                'advance_given': str(booking.advance_given),
                'color': booking.get_time_color(),
                'shift_type': get_shift_type(booking.start_time, booking.end_time),
                'created_by': booking.get_creator_name()
            }
        }, status=201)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["PUT"])
def update_booking(request, booking_id):
    """API endpoint to update a booking"""
    try:
        booking = Booking.objects.get(id=booking_id)
        data = json.loads(request.body)
        
        if 'client_name' in data:
            booking.client_name = data['client_name']
        if 'booking_date' in data:
            new_date = datetime.strptime(data['booking_date'], '%Y-%m-%d').date()
            if new_date != booking.booking_date:
                count = Booking.objects.filter(booking_date=new_date).exclude(id=booking_id).count()
                if count >= 2:
                    return JsonResponse({'error': 'Maximum 2 bookings per day on the new date'}, status=400)
            booking.booking_date = new_date
        if 'start_time' in data:
            booking.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'end_time' in data:
            booking.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        if 'phone_number' in data:
            booking.phone_number = data['phone_number']
        if 'email' in data:
            booking.email = data['email']
        if 'event_type' in data:
            booking.event_type = data['event_type']
        if 'menu_type' in data:
            booking.menu_type = data['menu_type']
        if 'no_of_packs' in data:
            booking.no_of_packs = data['no_of_packs']
        if 'advance_given' in data:
            try:
                advance_given = float(data['advance_given'])
                if advance_given < 0:
                    return JsonResponse({'error': 'Advance given cannot be negative'}, status=400)
                booking.advance_given = advance_given
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid advance given amount'}, status=400)
        
        if booking.end_time <= booking.start_time:
            return JsonResponse({'error': 'End time must be after start time'}, status=400)
        
        booking.save()
        
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
            'update',
            'booking',
            entity_id=booking.id,
            entity_name=booking.client_name,
            description=f'Updated booking for {booking.client_name} on {booking.booking_date} ({booking.get_event_type_display()})',
            request=request,
            performed_by_user=performed_by_user,
            performed_by_custom=performed_by_custom
        )
        
        nepali_date = get_nepali_date(booking.booking_date)
        
        return JsonResponse({
            'message': 'Booking updated successfully',
            'booking': {
                'id': booking.id,
                'client_name': booking.client_name,
                'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
                'booking_date_nepali': nepali_date['formatted_nepali'] if nepali_date else '',
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M'),
                'phone_number': booking.phone_number,
                'email': booking.email or '',
                'event_type': booking.event_type,
                'event_type_display': booking.get_event_type_display(),
                'menu_type': booking.menu_type or '',
                'no_of_packs': booking.no_of_packs or '',
                'advance_given': str(booking.advance_given),
                'color': booking.get_time_color(),
                'shift_type': get_shift_type(booking.start_time, booking.end_time),
                'created_by': booking.get_creator_name()
            }
        }, status=200)
    
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["DELETE"])
def delete_booking(request, booking_id):
    """API endpoint to delete a booking"""
    try:
        booking = Booking.objects.get(id=booking_id)
        
        booking_client_name = booking.client_name
        booking_date = booking.booking_date
        booking_event_type = booking.get_event_type_display()
        
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
            'delete',
            'booking',
            entity_id=booking.id,
            entity_name=booking_client_name,
            description=f'Deleted booking for {booking_client_name} on {booking_date} ({booking_event_type})',
            request=request,
            performed_by_user=performed_by_user,
            performed_by_custom=performed_by_custom
        )
        
        booking.delete()
        
        return JsonResponse({'message': 'Booking deleted successfully'}, status=200)
    
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["GET"])
def get_bookings_by_date(request, date_str):
    """API endpoint to get bookings for a specific date"""
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        bookings = Booking.objects.filter(booking_date=booking_date)
        nepali_date = get_nepali_date(booking_date)
        
        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                'id': booking.id,
                'client_name': booking.client_name,
                'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
                'booking_date_nepali': nepali_date['formatted_nepali'] if nepali_date else '',
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M'),
                'phone_number': booking.phone_number,
                'email': booking.email or '',
                'event_type': booking.event_type,
                'event_type_display': booking.get_event_type_display(),
                'menu_type': booking.menu_type or '',
                'no_of_packs': booking.no_of_packs or '',
                'advance_given': str(booking.advance_given),
                'color': booking.get_time_color(),
                'shift_type': get_shift_type(booking.start_time, booking.end_time),
                'created_by': booking.get_creator_name(),
                'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'bookings': bookings_data,
            'date_info': {
                'english': booking_date.strftime('%B %d, %Y'),
                'nepali': nepali_date['formatted_nepali'] if nepali_date else ''
            }
        }, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)