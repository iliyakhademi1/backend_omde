from django.urls import path
from . import views

urlpatterns = [
    # مدیریت فایل اکسل
    path('upload-excel/', views.upload_excel, name='upload-excel'),
    path('last-excel/', views.last_excel, name='last-excel'),
    path('excel-file/<int:pk>/', views.delete_excel_file, name='delete-excel-file'),
    path('excel-file/<int:pk>/update-categories/', views.update_row_categories, name='update-categories'),
    path('category-history/', views.get_category_history, name='category-history'),
    path('excel-file/<int:pk>/update-cell/', views.update_cell, name='update-cell'),
    path('excel-file/<int:pk>/add-row/', views.add_row, name='add-row'),

    # محصولات و لایک
    path('', views.product_list, name='product-list'),          # GET /api/products/?company_id=2
    path('<int:pk>/like/', views.product_like, name='product-like'),  # POST /api/products/5/like/
]