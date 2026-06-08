# accounts/serializers.py

from rest_framework import serializers
from .models import User

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'display_name', 'email', 'role', 'supplier_request_status', 'supplier_info']

class SupplierSignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    industry = serializers.CharField(max_length=100)
    location = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=15)
    email = serializers.EmailField()
    established = serializers.CharField(max_length=4)
    description = serializers.CharField()