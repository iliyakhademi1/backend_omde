from django.urls import path
from . import views

urlpatterns = [
    path('', views.companies_list, name='companies_list'),
    path('list/', views.companies_list, name='companies_list_alt'),
    path('<int:pk>/', views.company_detail, name='company_detail'),
    path('<int:pk>/excel-data/', views.company_excel_data, name='company_excel_data'),
    path('<int:pk>/like/', views.company_like, name='company_like'),
]