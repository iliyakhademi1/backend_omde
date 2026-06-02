import tempfile
from pathlib import Path
import pandas as pd
import re
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import SupplierExcelFile, Product
from .serializers import SupplierExcelFileSerializer, ProductSerializer
from suppliers.models import Company

# ========== تابع کمکی برای تبدیل خودکار به تأمین‌کننده ==========
def ensure_supplier_and_company(user):
    if user.role != 'supplier':
        user.role = 'supplier'
        user.supplier_request_status = 'approved'
        user.save()
    if not hasattr(user, 'company'):
        info = getattr(user, 'supplier_info', {}) or {}
        Company.objects.create(
            owner=user,
            name=info.get('name', 'شرکت پیش‌فرض'),
            industry=info.get('industry', 'عمومی'),
            location=info.get('location', 'تهران'),
            is_verified=True
        )

# ========== تابع کمکی برای استخراج عدد (فقط ارقام) ==========
def extract_number(value):
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return 0
    # حذف همه کاراکترهای غیرعددی
    cleaned = ''.join(ch for ch in value if ch.isdigit())
    if cleaned == '':
        return 0
    return float(cleaned)

# ========== 1. آپلود فایل اکسل (با product_id) ==========
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_excel(request):
    ensure_supplier_and_company(request.user)
    if 'file' not in request.FILES:
        return Response({'error': 'هیچ فایلی ارسال نشده'}, status=400)

    file = request.FILES['file']
    ext = Path(file.name).suffix.lower()
    if ext not in ('.xlsx', '.xls', '.csv'):
        return Response({'error': 'فرمت فایل باید اکسل یا CSV باشد'}, status=400)

    try:
        df = pd.read_excel(file, header=None)
        if df.empty:
            return Response({'error': 'فایل خالی است'}, status=400)

        raw_headers = [str(cell).strip() if cell is not None else "" for cell in df.iloc[0].tolist()]

        headers_lower = [h.lower() for h in raw_headers]
        required_fields = {
            'name': ['name', 'نام', 'اسم', 'عنوان', 'product name', 'نام محصول', 'نام کالا'],
            'code': ['code', 'شناسه', 'کد', 'id', 'product code', 'کد محصول', 'شناسه محصول'],
            'price': ['price', 'قیمت', 'قیمت محصول', 'قیمت فروش']
        }
        missing = []
        for field, aliases in required_fields.items():
            if not any(alias in headers_lower for alias in aliases):
                missing.append(field)

        if missing:
            missing_persian = []
            if 'name' in missing:
                missing_persian.append('نام محصول')
            if 'code' in missing:
                missing_persian.append('شناسه یا کد محصول')
            if 'price' in missing:
                missing_persian.append('قیمت')
            error_msg = f"ستون‌های زیر یافت نشد: {', '.join(missing_persian)}"
            return Response({'error': error_msg}, status=400)

        rows_data = []
        for _, row in df.iloc[1:].iterrows():
            row_dict = {}
            for col_idx, header in enumerate(raw_headers):
                val = row.iloc[col_idx] if col_idx < len(row) else ""
                row_dict[header] = val if pd.notna(val) else ""
            row_dict["categories"] = []
            rows_data.append(row_dict)

        # حذف فایل قبلی شرکت
        SupplierExcelFile.objects.filter(company=request.user.company).delete()

        # همگام‌سازی با Product و افزودن product_id به هر ردیف
        for row in rows_data:
            code_val = ""
            name_val = ""
            price_val = 0
            category_val = ""
            for header, value in row.items():
                lower_h = header.lower()
                if any(alias in lower_h for alias in ['code', 'شناسه', 'کد', 'id']):
                    code_val = str(value)
                elif any(alias in lower_h for alias in ['name', 'نام', 'عنوان', 'product name']):
                    name_val = str(value)
                elif any(alias in lower_h for alias in ['price', 'قیمت']):
                    price_val = extract_number(value)
                elif any(alias in lower_h for alias in ['category', 'دسته']):
                    category_val = str(value)

            product, _ = Product.objects.update_or_create(
                company=request.user.company,
                code=code_val,
                defaults={
                    'name': name_val,
                    'price': price_val,
                    'category': category_val,
                }
            )
            row['product_id'] = product.id

        # ایجاد فایل جدید با rows_data دارای product_id
        excel_file = SupplierExcelFile.objects.create(
            company=request.user.company,
            file_name=file.name,
            headers=raw_headers,
            rows=rows_data
        )

        serializer = SupplierExcelFileSerializer(excel_file)
        return Response(serializer.data, status=201)

    except Exception as e:
        return Response({'error': f'خطا در پردازش: {str(e)}'}, status=500)


# ========== 2. دریافت آخرین فایل ==========
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def last_excel(request):
    ensure_supplier_and_company(request.user)
    try:
        last_file = SupplierExcelFile.objects.filter(company=request.user.company).latest('created_at')
        serializer = SupplierExcelFileSerializer(last_file)
        return Response(serializer.data)
    except SupplierExcelFile.DoesNotExist:
        return Response({'error': 'not found'}, status=404)


# ========== 3. حذف فایل ==========
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_excel_file(request, pk):
    ensure_supplier_and_company(request.user)
    try:
        file_obj = SupplierExcelFile.objects.get(pk=pk, company=request.user.company)
        file_obj.delete()
        return Response({'message': 'فایل با موفقیت حذف شد'})
    except SupplierExcelFile.DoesNotExist:
        return Response({'error': 'فایل یافت نشد'}, status=404)


# ========== 4. به‌روزرسانی دسته‌بندی ==========
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_row_categories(request, pk):
    ensure_supplier_and_company(request.user)
    try:
        excel_file = SupplierExcelFile.objects.get(pk=pk, company=request.user.company)
    except SupplierExcelFile.DoesNotExist:
        return Response({'error': 'فایل یافت نشد'}, status=404)

    row_index = request.data.get('row_index')
    categories = request.data.get('categories', [])
    if row_index is None:
        return Response({'error': 'row_index ارسال نشده'}, status=400)
    if not isinstance(categories, list):
        return Response({'error': 'categories باید آرایه باشد'}, status=400)
    if len(categories) > 3:
        return Response({'error': 'حداکثر ۳ دسته‌بندی قابل قبول است'}, status=400)
    if row_index < 0 or row_index >= len(excel_file.rows):
        return Response({'error': 'ردیف نامعتبر'}, status=400)

    excel_file.rows[row_index]['categories'] = categories
    excel_file.save(update_fields=['rows'])
    return Response({'success': True, 'row_index': row_index, 'categories': categories})


# ========== 5. تاریخچه دسته‌بندی ==========
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_category_history(request):
    ensure_supplier_and_company(request.user)
    company = request.user.company
    excel_files = SupplierExcelFile.objects.filter(company=company)
    categories_set = set()
    for file in excel_files:
        for row in file.rows:
            if 'categories' in row and isinstance(row['categories'], list):
                categories_set.update(row['categories'])
    return Response({'categories': sorted(categories_set)})


# ========== 6. به‌روزرسانی سلول (همگام‌سازی با Product در صورت تغییر قیمت) ==========
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_cell(request, pk):
    ensure_supplier_and_company(request.user)
    try:
        excel_file = SupplierExcelFile.objects.get(pk=pk, company=request.user.company)
    except SupplierExcelFile.DoesNotExist:
        return Response({'error': 'فایل یافت نشد'}, status=404)

    row_index = request.data.get('row_index')
    column_name = request.data.get('column_name')
    new_value = request.data.get('new_value')
    if row_index is None or column_name is None:
        return Response({'error': 'row_index و column_name الزامی هستند'}, status=400)
    if row_index < 0 or row_index >= len(excel_file.rows):
        return Response({'error': 'ردیف نامعتبر'}, status=400)
    if column_name not in excel_file.headers:
        return Response({'error': 'ستون نامعتبر'}, status=400)

    old_value = excel_file.rows[row_index].get(column_name, '')
    excel_file.rows[row_index][column_name] = new_value
    excel_file.save(update_fields=['rows'])

    # اگر ستون قیمت تغییر کرده است، مقدار Product را نیز به‌روز کنیم
    lower_col = column_name.lower()
    if any(alias in lower_col for alias in ['price', 'قیمت']):
        product_id = excel_file.rows[row_index].get('product_id')
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                product.price = extract_number(new_value)
                product.save(update_fields=['price'])
            except Product.DoesNotExist:
                pass

    return Response({'success': True, 'row_index': row_index, 'column_name': column_name, 'new_value': new_value})


# ========== 7. افزودن ردیف (اصلاح شده با product_id) ==========
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_row(request, pk):
    ensure_supplier_and_company(request.user)
    try:
        excel_file = SupplierExcelFile.objects.get(pk=pk, company=request.user.company)
    except SupplierExcelFile.DoesNotExist:
        return Response({'error': 'فایل یافت نشد'}, status=404)

    row_data = request.data.get('row_data')
    if not row_data or not isinstance(row_data, dict):
        return Response({'error': 'داده ردیف معتبر نیست'}, status=400)

    # اعتبارسنجی ستون‌های اجباری
    headers_lower = [h.lower() for h in excel_file.headers]
    required_fields = {
        'name': ['name', 'نام', 'اسم', 'عنوان', 'product name', 'نام محصول', 'نام کالا'],
        'code': ['code', 'شناسه', 'کد', 'id', 'product code', 'کد محصول', 'شناسه محصول'],
        'price': ['price', 'قیمت', 'قیمت محصول', 'قیمت فروش']
    }
    missing = []
    for field, aliases in required_fields.items():
        matched_header = None
        for header in excel_file.headers:
            if header.lower() in aliases:
                matched_header = header
                break
        if not matched_header or matched_header not in row_data:
            missing.append(field)
    if missing:
        missing_persian = []
        if 'name' in missing:
            missing_persian.append('نام محصول')
        if 'code' in missing:
            missing_persian.append('شناسه یا کد محصول')
        if 'price' in missing:
            missing_persian.append('قیمت')
        return Response({'error': f"داده ارسالی شامل ستون‌های الزامی نیست: {', '.join(missing_persian)}"}, status=400)

    if 'categories' not in row_data:
        row_data['categories'] = []
    for header in excel_file.headers:
        if header not in row_data:
            row_data[header] = ""

    # همگام‌سازی با Product و گرفتن product.id
    code_val = row_data.get('code', '')
    name_val = row_data.get('name', '')
    price_val = extract_number(row_data.get('price', 0))
    category_val = row_data.get('category', '')
    product, _ = Product.objects.update_or_create(
        company=request.user.company,
        code=code_val,
        defaults={
            'name': name_val,
            'price': price_val,
            'category': category_val,
        }
    )
    row_data['product_id'] = product.id

    excel_file.rows.append(row_data)
    excel_file.save(update_fields=['rows'])

    return Response({'success': True, 'new_row': row_data, 'row_index': len(excel_file.rows) - 1})


# ========== 8. دریافت لیست محصولات (برای فرانت‌اند) ==========
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_list(request):
    company_id = request.query_params.get('company_id')
    if company_id:
        products = Product.objects.filter(company_id=company_id)
    else:
        products = Product.objects.all()
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data)


# ========== 9. لایک محصول ==========
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_like(request, pk):
    product = get_object_or_404(Product, pk=pk)
    user = request.user
    if product.liked_by.filter(id=user.id).exists():
        product.liked_by.remove(user)
        liked = False
    else:
        product.liked_by.add(user)
        liked = True
    return Response({'liked': liked})