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

from .models import Booking, CustomUser


def get_nepali_date(english_date):
    """Convert English date to Nepali date"""
    try:
        nepali_date = nepali_datetime.date.from_datetime_date(english_date)
        return {
            'year': nepali_date.year,
            'month': nepali_date.month,
            'day': nepali_date.day,
            'month_name': nepali_date.strftime('%B'),  # Nepali month name
            'formatted': nepali_date.strftime('%Y-%m-%d'),
            'formatted_nepali': nepali_date.strftime('%Y %B %d')
        }
    except Exception as e:
        print(f"Error converting date: {e}")
        return None


def calendar_view(request):
    """Render the calendar booking page"""
    # Get all custom users for filter dropdown
    custom_users = CustomUser.objects.all()
    
    # Get current date info
    today = date.today()
    nepali_today = get_nepali_date(today)
    
    context = {
        'custom_users': custom_users,
        'today_nepali': nepali_today
    }
    return render(request, 'Function/calendar.html', context)


@require_http_methods(["GET"])
def get_calendar_data(request):
    """API endpoint to get calendar data with Nepali dates"""
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
        
        # Get first and last day of the month
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1)
        else:
            last_day = date(year, month + 1, 1)
        
        # Get all bookings for the month
        bookings = Booking.objects.filter(
            booking_date__gte=first_day,
            booking_date__lt=last_day
        )
        
        # Create calendar data
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
                    'event_type': booking.event_type,
                    'start_time': booking.start_time.strftime('%H:%M'),
                    'end_time': booking.end_time.strftime('%H:%M')
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


@require_http_methods(["GET"])
def get_bookings(request):
    """API endpoint to get all bookings with Nepali dates"""
    try:
        # Get filter parameter
        created_by_filter = request.GET.get('created_by', None)
        
        bookings = Booking.objects.all()
        
        # Apply filter if provided
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
                'advance_given': str(booking.advance_given),
                'created_by': booking.get_creator_name(),
                'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({'bookings': bookings_data}, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
            'advance_given': str(booking.advance_given),
            'created_by': booking.get_creator_name(),
            'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return JsonResponse({'booking': booking_data}, status=200)
    
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
                'advance_given': str(booking.advance_given),
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


@require_http_methods(["POST"])
def create_booking(request):
    """API endpoint to create a new booking"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['client_name', 'booking_date', 'start_time', 'end_time', 
                          'phone_number', 'event_type']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'{field} is required'}, status=400)
        
        # Parse date and time
        booking_date = datetime.strptime(data['booking_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        # Validate time
        if end_time <= start_time:
            return JsonResponse({'error': 'End time must be after start time'}, status=400)
        
        # Check booking limit
        bookings_on_date = Booking.objects.filter(booking_date=booking_date).count()
        if bookings_on_date >= 2:
            return JsonResponse({'error': 'Maximum 2 bookings per day'}, status=400)
        
        # Create booking
        booking = Booking.objects.create(
            client_name=data['client_name'],
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            phone_number=data['phone_number'],
            email=data.get('email', ''),
            event_type=data['event_type'],
            advance_given=data.get('advance_given', 0.00),
            created_by_user=request.user if request.user.is_authenticated else None
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
                'advance_given': str(booking.advance_given),
                'created_by': booking.get_creator_name()
            }
        }, status=201)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["PUT"])
def update_booking(request, booking_id):
    """API endpoint to update a booking"""
    try:
        booking = Booking.objects.get(id=booking_id)
        data = json.loads(request.body)
        
        # Update fields
        if 'client_name' in data:
            booking.client_name = data['client_name']
        if 'booking_date' in data:
            new_date = datetime.strptime(data['booking_date'], '%Y-%m-%d').date()
            if new_date != booking.booking_date:
                count = Booking.objects.filter(booking_date=new_date).count()
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
        if 'advance_given' in data:
            booking.advance_given = data['advance_given']
        
        # Validate time
        if booking.end_time <= booking.start_time:
            return JsonResponse({'error': 'End time must be after start time'}, status=400)
        
        booking.save()
        
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
                'advance_given': str(booking.advance_given),
                'created_by': booking.get_creator_name()
            }
        }, status=200)
    
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["DELETE"])
def delete_booking(request, booking_id):
    """API endpoint to delete a booking"""
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.delete()
        
        return JsonResponse({'message': 'Booking deleted successfully'}, status=200)
    
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)