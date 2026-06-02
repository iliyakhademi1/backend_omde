# products/serializers.py
from rest_framework import serializers
from .models import SupplierExcelFile, Product

class SupplierExcelFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierExcelFile
        fields = ['id', 'file_name', 'headers', 'rows', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'company', 'name', 'price', 'category', 'code', 'is_liked']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.liked_by.filter(id=request.user.id).exists()
        return False