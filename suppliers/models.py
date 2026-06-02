from django.db import models
from django.conf import settings

class Company(models.Model):
    name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    rating = models.FloatField(default=0.0)
    products_count = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='company'
    )
    request_info = models.JSONField(default=dict, blank=True)

    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    established = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='favorite_companies',
        blank=True
    )

    def __str__(self):
        return self.name