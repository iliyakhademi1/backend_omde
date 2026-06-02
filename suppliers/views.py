# suppliers/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Company
from .serializers import CompanySerializer
from products.models import SupplierExcelFile

# ========== 1. لیست همه شرکت‌ها ==========
@api_view(['GET'])
@permission_classes([AllowAny])
def companies_list(request):
    companies = Company.objects.all()
    serializer = CompanySerializer(companies, many=True, context={'request': request})
    return Response(serializer.data)

# ========== 2. جزئیات یک شرکت (برای صفحه /companies/[id]) ==========
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    serializer = CompanySerializer(company, context={'request': request})
    return Response(serializer.data)

# ========== 3. دریافت آخرین فایل اکسل شرکت (برای نمایش در حالت جدول) ==========
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def company_excel_data(request, pk):
    company = get_object_or_404(Company, pk=pk)
    excel_file = SupplierExcelFile.objects.filter(company=company).first()
    if not excel_file:
        return Response({'headers': [], 'rows': []}, status=200)
    return Response({
        'headers': excel_file.headers,
        'rows': excel_file.rows
    })

# ========== 4. لایک شرکت (جدید) ==========
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_like(request, pk):
    company = get_object_or_404(Company, pk=pk)
    user = request.user
    if company.liked_by.filter(id=user.id).exists():
        company.liked_by.remove(user)
        liked = False
    else:
        company.liked_by.add(user)
        liked = True
    return Response({'liked': liked})