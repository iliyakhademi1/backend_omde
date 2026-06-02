from django.db import models
from django.conf import settings
from suppliers.models import Company

class SupplierExcelFile(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='excel_files')
    file_name = models.CharField(max_length=255)
    headers = models.JSONField()
    rows = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.file_name} - {self.company.name}"


class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=15, decimal_places=0)
    category = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='favorite_products',
        blank=True
    )

    class Meta:
        unique_together = ('company', 'code')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.company.name}"