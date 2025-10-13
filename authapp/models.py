from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUser(models.Model):
    """
    Custom User model for application-specific users.
    Separate from Django's built-in User model.
    """
    full_name = models.CharField(max_length=255)
    login_email = models.EmailField(unique=True)
    login_password = models.CharField(max_length=255)  # Hashed password
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_custom_users'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'custom_users'
        ordering = ['-created_at']
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'

    def __str__(self):
        return f"{self.full_name} ({self.login_email})"