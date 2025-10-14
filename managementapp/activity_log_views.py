from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from authapp.decorators import login_required_dual
from .models import ActivityLog
import json


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


@login_required_dual(login_url='/unauthorized/')
def activity_log_view(request):
    """Render the activity log page"""
    return render(request, 'admin/activity_log.html')


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["GET"])
def get_activity_logs(request):
    """API endpoint to get activity logs with filters and pagination"""
    try:
        # Get filter parameters
        action_filter = request.GET.get('action', None)
        entity_filter = request.GET.get('entity_type', None)
        performer_filter = request.GET.get('performer', None)
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)
        search_query = request.GET.get('search', '').strip()
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        # Start with all logs
        logs = ActivityLog.objects.all()
        
        # Apply filters
        if action_filter:
            logs = logs.filter(action=action_filter)
        
        if entity_filter:
            logs = logs.filter(entity_type=entity_filter)
        
        if performer_filter:
            if performer_filter.startswith('user_'):
                user_id = performer_filter.replace('user_', '')
                logs = logs.filter(performed_by_user_id=user_id)
            elif performer_filter.startswith('custom_'):
                custom_id = performer_filter.replace('custom_', '')
                logs = logs.filter(performed_by_custom_id=custom_id)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(created_at__gte=date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire end date
            date_to_obj = date_to_obj + timedelta(days=1)
            logs = logs.filter(created_at__lt=date_to_obj)
        
        if search_query:
            logs = logs.filter(
                Q(entity_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Get total count before pagination
        total_count = logs.count()
        
        # Paginate
        paginator = Paginator(logs, per_page)
        page_obj = paginator.get_page(page)
        
        # Prepare response data
        logs_data = []
        for log in page_obj:
            logs_data.append({
                'id': log.id,
                'action': log.action,
                'action_display': log.get_action_display(),
                'action_icon': log.get_action_icon(),
                'action_color': log.get_action_color(),
                'entity_type': log.entity_type,
                'entity_type_display': log.get_entity_type_display(),
                'entity_id': log.entity_id,
                'entity_name': log.entity_name,
                'description': log.description,
                'performed_by': log.get_performer_name(),
                'ip_address': log.ip_address,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'created_at_readable': log.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        
        return JsonResponse({
            'logs': logs_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': total_count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'per_page': per_page
            }
        }, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["GET"])
def get_activity_stats(request):
    """API endpoint to get activity statistics"""
    try:
        # Get date range (default: last 30 days)
        days = int(request.GET.get('days', 30))
        date_from = datetime.now() - timedelta(days=days)
        
        logs = ActivityLog.objects.filter(created_at__gte=date_from)
        
        # Count by action type
        action_stats = logs.values('action').annotate(count=Count('id'))
        
        # Count by entity type
        entity_stats = logs.values('entity_type').annotate(count=Count('id'))
        
        # Total activities
        total_activities = logs.count()
        
        # Today's activities
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_activities = logs.filter(created_at__gte=today_start).count()
        
        # Most active users
        user_activity = logs.filter(performed_by_user__isnull=False).values(
            'performed_by_user__username', 'performed_by_user__first_name', 'performed_by_user__last_name'
        ).annotate(count=Count('id')).order_by('-count')[:5]
        
        custom_activity = logs.filter(performed_by_custom__isnull=False).values(
            'performed_by_custom__full_name'
        ).annotate(count=Count('id')).order_by('-count')[:5]
        
        return JsonResponse({
            'total_activities': total_activities,
            'today_activities': today_activities,
            'action_stats': list(action_stats),
            'entity_stats': list(entity_stats),
            'top_admin_users': list(user_activity),
            'top_custom_users': list(custom_activity),
            'date_range_days': days
        }, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_dual(login_url='/unauthorized/')
@require_http_methods(["DELETE"])
def clear_old_logs(request):
    """API endpoint to clear logs older than specified days (admin only)"""
    try:
        # Only allow admins to clear logs
        if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_staff):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        data = json.loads(request.body)
        days = int(data.get('days', 90))
        
        date_threshold = datetime.now() - timedelta(days=days)
        deleted_count = ActivityLog.objects.filter(created_at__lt=date_threshold).delete()[0]
        
        # Log this action
        log_activity(
            'delete',
            'system',
            description=f'Cleared {deleted_count} activity logs older than {days} days',
            request=request,
            performed_by_user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully cleared {deleted_count} old activity logs',
            'deleted_count': deleted_count
        }, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)