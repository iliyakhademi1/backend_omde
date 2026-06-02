from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'phone', 'display_name', 'role', 'supplier_request_status')
    list_filter = ('role', 'supplier_request_status')
    search_fields = ('username', 'phone', 'display_name')

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        extra = (('اطلاعات اضافی', {'fields': ('phone', 'display_name', 'role', 'supplier_request_status', 'supplier_info')}),)
        return fieldsets + extra

admin.site.register(User, CustomUserAdmin)