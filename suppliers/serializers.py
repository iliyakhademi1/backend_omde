from rest_framework import serializers
from .models import Company

class CompanySerializer(serializers.ModelSerializer):
    # تعداد محصولات مرتبط با این شرکت
    products_count = serializers.IntegerField(source='products.count', read_only=True)
    
    # فیلد وضعیت علاقه‌مندی کاربر به شرکت
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'industry', 'location', 'phone', 'email',
            'rating', 'products_count', 'established', 'description', 
            'is_verified', 'is_favorite'   # ← اضافه شد
        ]

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.liked_by.filter(id=request.user.id).exists()
        return False