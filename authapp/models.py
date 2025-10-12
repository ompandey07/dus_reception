from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# ============================================================
# CUSTOM USER MODEL
# ============================================================
class CustomUser(models.Model):
    full_name = models.CharField(max_length=255)
    login_email = models.EmailField(unique=True)
    login_password = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_custom_users'
    )

    class Meta:
        db_table = 'custom_users'
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.login_email})"