from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.db import models
from authapp.models import CustomUser


class Booking(models.Model):
    """
    Booking model for calendar events
    """
    EVENT_TYPE_CHOICES = [
        ('wedding', 'Wedding'),
        ('bartamanda', 'Bartamanda'),
        ('Rice Feeding', 'Rice Feeding'),
        ('conference', 'Conference'),
        ('birthday', 'Birthday Party'),
        ('anniversary', 'Anniversary'),
        ('corporate', 'Corporate Event'),
        ('engagement', 'Engagement'),
        ('bratabandha', 'Bratabandha'),
        ('reception', 'Reception'),
        ('seminar', 'Seminar/Workshop'),
        ('others', 'Others'),
    ]
    
    MENU_TYPE_CHOICES = [
        ('party', 'Party'),
        ('newari_bhoj', 'Newari Bhoj'),
        ('jabhu_bhoj', 'Jabhu Bhoj'),
        ('others', 'Others'),
    ]
    
    TIME_SLOT_CHOICES = [
        ('morning', '6 AM - 3 PM'),
        ('evening', '3 PM - 9 PM'),
        ('fullday', 'Full Day'),
    ]
    
    client_name = models.CharField(max_length=255)
    booking_date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES, default='morning')
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, default='others')
    menu_type = models.CharField(max_length=50, choices=MENU_TYPE_CHOICES, blank=True, null=True, help_text="Type of menu/food arrangement")
    no_of_pax = models.CharField(max_length=100, blank=True, null=True, help_text="Number of pax/guests")
    additional_pax = models.CharField(max_length=100, blank=True, null=True, help_text="Additional number of pax")
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Rate per pax/plate")
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
        'authapp.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings_created'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bookings'
        ordering = ['booking_date', 'time_slot']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
    
    def __str__(self):
        return f"{self.client_name} - {self.booking_date} ({self.get_event_type_display()})"
    
    def get_creator_name(self):
        """Get the name of who created this booking"""
        if self.created_by_user:
            return f"{self.created_by_user.get_full_name() or self.created_by_user.username} (Admin)"
        elif self.created_by_custom:
            return f"{self.created_by_custom.full_name} (User)"
        return "System"
    
    def get_time_color(self):
        """Get color based on time slot"""
        if self.time_slot == 'morning':
            return '#10b981'  # Green - Morning
        elif self.time_slot == 'evening':
            return '#f59e0b'  # Orange - Evening
        else:
            return '#8b5cf6'  # Purple - Full day
    
    def is_full_day_booking(self):
        """Check if this is a full day booking"""
        return self.time_slot == 'fullday'




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