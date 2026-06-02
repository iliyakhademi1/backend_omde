from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.pending_requests, name='pending_requests'),
    path('approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('reject/<int:user_id>/', views.reject_user, name='reject_user'),
]