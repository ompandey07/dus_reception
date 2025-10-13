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