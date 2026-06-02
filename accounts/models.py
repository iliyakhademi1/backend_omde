from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone   # اضافه شود

class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    display_name = models.CharField(max_length=100, blank=True)
    ROLE_CHOICES = (
        ('customer', 'مشتری'),
        ('supplier', 'تأمین‌کننده'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    supplier_request_status = models.CharField(
        max_length=10,
        choices=(('pending','در انتظار'), ('approved','تایید شده'), ('rejected','رد شده')),
        null=True, blank=True
    )
    supplier_info = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.username


class OTP(models.Model):
    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"{self.phone} - {self.code}"