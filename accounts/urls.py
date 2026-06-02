from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile),
    path('update-profile/', views.update_profile),
    path('supplier-signup/', views.supplier_signup),
    path('send-otp/', views.send_otp),
    path('verify-otp/', views.verify_otp),
    path('approve-supplier/<int:user_id>/', views.approve_supplier), 
    path('reject-supplier/<int:user_id>/', views.reject_supplier),
    path('pending-requests/', views.pending_supplier_requests),  
]
