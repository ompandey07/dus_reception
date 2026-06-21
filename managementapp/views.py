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
from managementapp.nepali_converter import get_bs_data_for_ad_date
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
    """Convert English date to accurate Nepali date using robust mathematical offline converter"""
    try:
        en_str = f"{english_date.year}-{english_date.month}-{english_date.day}"
        en_data = get_bs_data_for_ad_date(en_str)
        if not en_data:
            return None
        return {
            'year': en_data['year'],
            'month': en_data['month'],
            'day': en_data['day'],
            'month_name': en_data['str_month'],
            'formatted': f"{en_data['year']}-{str(en_data['month']).zfill(2)}-{str(en_data['day']).zfill(2)}",
            'formatted_nepali': f"{en_data['year']} {en_data['str_month']} {en_data['day']}"
        }
    except Exception as e:
        print(f"Error converting date: {e}")
        return None


def get_time_slot_display(time_slot):
    """Get display text for time slot"""
    time_slot_map = {
        'morning': '6 AM - 3 PM',
        'evening': '3 PM - 9 PM',
        'fullday': 'Full Day'
    }
    return time_slot_map.get(time_slot, time_slot)


# ============================================================
# CALENDAR VIEWS
# ============================================================
@login_required_dual(login_url='/unauthorized/')
def calendar_view(request):
    """Render the calendar booking page"""
    custom_users = CustomUser.objects.all()
    today = date.today()
    nepali_today = get_nepali_date(today)
    
    # Get choices for dropdowns
    event_types = Booking.EVENT_TYPE_CHOICES
    menu_types = Booking.MENU_TYPE_CHOICES
    time_slots = Booking.TIME_SLOT_CHOICES
    
    # Check if user is superuser (Django admin) or custom user
    is_superuser = request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff)
    custom_user_id = request.COOKIES.get("custom_user_id")
    is_custom_user = bool(custom_user_id)
    can_delete = is_superuser  # Only superusers can delete
    
    context = {
        'custom_users': custom_users,
        'today_nepali': nepali_today,
        'event_types': event_types,
        'menu_types': menu_types,
        'time_slots': time_slots,
        'is_superuser': is_superuser,
        'is_custom_user': is_custom_user,
        'can_delete': can_delete
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
                    'time_slot': booking.time_slot,
                    'time_slot_display': get_time_slot_display(booking.time_slot),
                    'color': booking.get_time_color(),
                    'is_full_day': booking.is_full_day_booking()
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
                'time_slot': booking.time_slot,
                'time_slot_display': get_time_slot_display(booking.time_slot),
                'phone_number': booking.phone_number,
                'email': booking.email or '',
                'event_type': booking.event_type,
                'event_type_display': booking.get_event_type_display(),
                'menu_type': booking.menu_type or '',
                'menu_type_display': booking.get_menu_type_display() if booking.menu_type else '',
                'no_of_pax': booking.no_of_pax or '',
                'additional_pax': booking.additional_pax or '',
                'rate': str(booking.rate) if booking.rate else '',
                'advance_given': str(booking.advance_given),
                'color': booking.get_time_color(),
                'is_full_day': booking.is_full_day_booking(),
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
            'time_slot': booking.time_slot,
            'time_slot_display': get_time_slot_display(booking.time_slot),
            'phone_number': booking.phone_number,
            'email': booking.email or '',
            'event_type': booking.event_type,
            'event_type_display': booking.get_event_type_display(),
            'menu_type': booking.menu_type or '',
            'menu_type_display': booking.get_menu_type_display() if booking.menu_type else '',
            'no_of_pax': booking.no_of_pax or '',
            'additional_pax': booking.additional_pax or '',
            'rate': str(booking.rate) if booking.rate else '',
            'advance_given': str(booking.advance_given),
            'color': booking.get_time_color(),
            'is_full_day': booking.is_full_day_booking(),
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
        
        required_fields = ['client_name', 'booking_date', 'time_slot', 
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
        
        # Validate rate if provided
        rate = None
        if data.get('rate') and data['rate'] != '':
            try:
                rate = float(data['rate'])
                if rate < 0:
                    return JsonResponse({'error': 'Rate cannot be negative'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid rate amount'}, status=400)
        
        booking_date = datetime.strptime(data['booking_date'], '%Y-%m-%d').date()
        time_slot = data['time_slot']
        is_full_day = (time_slot == 'fullday')
        
        # Check if there's already a full day booking on this date
        full_day_exists = Booking.objects.filter(booking_date=booking_date, time_slot='fullday').exists()
        if full_day_exists:
            return JsonResponse({'error': 'This date already has a full day booking. No other bookings allowed.'}, status=400)
        
        # If this is a full day booking, check if there are any bookings on this date
        if is_full_day:
            existing_bookings = Booking.objects.filter(booking_date=booking_date).count()
            if existing_bookings > 0:
                return JsonResponse({'error': 'Cannot create full day booking. There are already bookings on this date.'}, status=400)
        
        # Check max 2 bookings per day (only if not full day)
        if not is_full_day:
            bookings_on_date = Booking.objects.filter(booking_date=booking_date).count()
            if bookings_on_date >= 2:
                return JsonResponse({'error': 'Maximum 2 bookings per day'}, status=400)
            
            # Check if same time slot already exists
            same_slot_exists = Booking.objects.filter(booking_date=booking_date, time_slot=time_slot).exists()
            if same_slot_exists:
                return JsonResponse({'error': f'A booking already exists for {get_time_slot_display(time_slot)} on this date'}, status=400)
        
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
            time_slot=time_slot,
            phone_number=data['phone_number'],
            email=data.get('email', ''),
            event_type=data['event_type'],
            menu_type=data.get('menu_type', ''),
            no_of_pax=data.get('no_of_pax', ''),
            additional_pax=data.get('additional_pax', ''),
            rate=rate,
            advance_given=advance_given,
            created_by_user=created_by_user,
            created_by_custom=created_by_custom
        )
        
        log_activity(
            'create',
            'booking',
            entity_id=booking.id,
            entity_name=booking.client_name,
            description=f'Created new booking for {booking.client_name} on {booking.booking_date} ({booking.get_event_type_display()})' + (' [FULL DAY]' if is_full_day else ''),
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
                'time_slot': booking.time_slot,
                'time_slot_display': get_time_slot_display(booking.time_slot),
                'phone_number': booking.phone_number,
                'email': booking.email or '',
                'event_type': booking.event_type,
                'event_type_display': booking.get_event_type_display(),
                'menu_type': booking.menu_type or '',
                'menu_type_display': booking.get_menu_type_display() if booking.menu_type else '',
                'no_of_pax': booking.no_of_pax or '',
                'additional_pax': booking.additional_pax or '',
                'rate': str(booking.rate) if booking.rate else '',
                'advance_given': str(booking.advance_given),
                'color': booking.get_time_color(),
                'is_full_day': booking.is_full_day_booking(),
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
            new_time_slot = data.get('time_slot', booking.time_slot)
            new_is_full_day = (new_time_slot == 'fullday')
            
            if new_date != booking.booking_date or new_time_slot != booking.time_slot:
                # Check for full day bookings on new date
                full_day_exists = Booking.objects.filter(
                    booking_date=new_date, 
                    time_slot='fullday'
                ).exclude(id=booking_id).exists()
                
                if full_day_exists:
                    return JsonResponse({'error': 'The new date already has a full day booking. No other bookings allowed.'}, status=400)
                
                # If updating to a full day booking, check for existing bookings
                if new_is_full_day:
                    existing_count = Booking.objects.filter(booking_date=new_date).exclude(id=booking_id).count()
                    if existing_count > 0:
                        return JsonResponse({'error': 'Cannot set as full day booking. There are already bookings on this date.'}, status=400)
                
                # Check max 2 bookings and same time slot
                if not new_is_full_day:
                    count = Booking.objects.filter(booking_date=new_date).exclude(id=booking_id).count()
                    if count >= 2:
                        return JsonResponse({'error': 'Maximum 2 bookings per day on the new date'}, status=400)
                    
                    same_slot_exists = Booking.objects.filter(
                        booking_date=new_date, 
                        time_slot=new_time_slot
                    ).exclude(id=booking_id).exists()
                    if same_slot_exists:
                        return JsonResponse({'error': f'A booking already exists for {get_time_slot_display(new_time_slot)} on this date'}, status=400)
            
            booking.booking_date = new_date
        
        if 'time_slot' in data:
            booking.time_slot = data['time_slot']
        if 'phone_number' in data:
            booking.phone_number = data['phone_number']
        if 'email' in data:
            booking.email = data['email']
        if 'event_type' in data:
            booking.event_type = data['event_type']
        if 'menu_type' in data:
            booking.menu_type = data['menu_type']
        if 'no_of_pax' in data:
            booking.no_of_pax = data['no_of_pax']
        if 'additional_pax' in data:
            booking.additional_pax = data['additional_pax']
        
        # Handle rate field
        if 'rate' in data:
            if data['rate'] and data['rate'] != '':
                try:
                    rate = float(data['rate'])
                    if rate < 0:
                        return JsonResponse({'error': 'Rate cannot be negative'}, status=400)
                    booking.rate = rate
                except (ValueError, TypeError):
                    return JsonResponse({'error': 'Invalid rate amount'}, status=400)
            else:
                booking.rate = None
        
        if 'advance_given' in data:
            try:
                advance_given = float(data['advance_given'])
                if advance_given < 0:
                    return JsonResponse({'error': 'Advance given cannot be negative'}, status=400)
                booking.advance_given = advance_given
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid advance given amount'}, status=400)
        
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
            description=f'Updated booking for {booking.client_name} on {booking.booking_date} ({booking.get_event_type_display()})' + (' [FULL DAY]' if booking.is_full_day_booking() else ''),
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
                'time_slot': booking.time_slot,
                'time_slot_display': get_time_slot_display(booking.time_slot),
                'phone_number': booking.phone_number,
                'email': booking.email or '',
                'event_type': booking.event_type,
                'event_type_display': booking.get_event_type_display(),
                'menu_type': booking.menu_type or '',
                'menu_type_display': booking.get_menu_type_display() if booking.menu_type else '',
                'no_of_pax': booking.no_of_pax or '',
                'additional_pax': booking.additional_pax or '',
                'rate': str(booking.rate) if booking.rate else '',
                'advance_given': str(booking.advance_given),
                'color': booking.get_time_color(),
                'is_full_day': booking.is_full_day_booking(),
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
                'time_slot': booking.time_slot,
                'time_slot_display': get_time_slot_display(booking.time_slot),
                'phone_number': booking.phone_number,
                'email': booking.email or '',
                'event_type': booking.event_type,
                'event_type_display': booking.get_event_type_display(),
                'menu_type': booking.menu_type or '',
                'menu_type_display': booking.get_menu_type_display() if booking.menu_type else '',
                'no_of_pax': booking.no_of_pax or '',
                'additional_pax': booking.additional_pax or '',
                'rate': str(booking.rate) if booking.rate else '',
                'advance_given': str(booking.advance_given),
                'color': booking.get_time_color(),
                'is_full_day': booking.is_full_day_booking(),
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