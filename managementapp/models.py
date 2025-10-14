from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.db import models
from authapp.models import CustomUser


class Booking(models.Model):
    """
    Booking model for calendar events
    """
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    client_name = models.CharField(max_length=255)
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    email = models.EmailField(blank=True, null=True)
    event_type = models.CharField(max_length=255)
    advance_given = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Track who created this booking
    created_by_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings_created'
    )
    created_by_custom = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings_created'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bookings'
        ordering = ['booking_date', 'start_time']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
    
    def __str__(self):
        return f"{self.client_name} - {self.booking_date} ({self.event_type})"
    
    def get_creator_name(self):
        """Get the name of who created this booking"""
        if self.created_by_user:
            return f"{self.created_by_user.get_full_name() or self.created_by_user.username} (Admin)"
        elif self.created_by_custom:
            return f"{self.created_by_custom.full_name} (User)"
        return "System"
    
    def clean(self):
        """Validate that end_time is after start_time"""
        from django.core.exceptions import ValidationError
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError('End time must be after start time.')
        




class ActivityLog(models.Model):
    """
    Activity Log model to track all actions in the system
    """
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('login', 'Logged In'),
        ('logout', 'Logged Out'),
    ]
    
    ENTITY_CHOICES = [
        ('booking', 'Booking'),
        ('user', 'User'),
        ('custom_user', 'Custom User'),
        ('system', 'System'),
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=50, choices=ENTITY_CHOICES)
    entity_id = models.IntegerField(null=True, blank=True)
    entity_name = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    
    # Track who performed this action
    performed_by_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities_performed'
    )
    performed_by_custom = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities_performed'
    )
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['entity_type']),
        ]
    
    def __str__(self):
        return f"{self.get_performer_name()} {self.get_action_display()} {self.entity_type} - {self.created_at}"
    
    def get_performer_name(self):
        """Get the name of who performed this action"""
        if self.performed_by_user:
            return f"{self.performed_by_user.get_full_name() or self.performed_by_user.username} (Admin)"
        elif self.performed_by_custom:
            return f"{self.performed_by_custom.full_name} (User)"
        return "System"
    
    def get_action_icon(self):
        """Return appropriate icon for the action"""
        icons = {
            'create': 'ri-add-circle-line',
            'update': 'ri-edit-line',
            'delete': 'ri-delete-bin-line',
            'login': 'ri-login-box-line',
            'logout': 'ri-logout-box-line',
        }
        return icons.get(self.action, 'ri-information-line')
    
    def get_action_color(self):
        """Return appropriate color class for the action"""
        colors = {
            'create': 'green',
            'update': 'blue',
            'delete': 'red',
            'login': 'purple',
            'logout': 'gray',
        }
        return colors.get(self.action, 'gray')