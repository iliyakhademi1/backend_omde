# accounts/views.py
import random
import requests
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .models import OTP
from .serializers import UserProfileSerializer, SupplierSignupSerializer

User = get_user_model()


# ========== پروفایل کاربر ==========
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    user.display_name = request.data.get('display_name', user.display_name)
    user.email = request.data.get('email', user.email)
    user.save()
    serializer = UserProfileSerializer(user)
    return Response(serializer.data)


# ========== درخواست تأمین‌کنندگی ==========
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def supplier_signup(request):
    serializer = SupplierSignupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    user = request.user
    if user.role != 'customer':
        return Response({'error': 'فقط کاربران عادی می‌توانند درخواست دهند.'}, status=400)
    if user.supplier_request_status:
        return Response({'error': 'قبلاً درخواست داده‌اید.'}, status=400)
    user.supplier_info = serializer.validated_data
    user.supplier_request_status = 'pending'
    user.save()
    return Response({'message': 'درخواست ثبت شد.'}, status=201)


# ========== ارسال OTP با استفاده از API مستقیم sms.ir ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    phone = request.data.get('phone')
    if not phone or len(phone) < 11:
        return Response({'error': 'شماره موبایل نامعتبر است'}, status=400)

    code = str(random.randint(10000, 99999))
    OTP.objects.filter(phone=phone).delete()
    expires_at = timezone.now() + timedelta(minutes=2)
    OTP.objects.create(phone=phone, code=code, expires_at=expires_at)

    sms_sent = False
    error_message = None

    if settings.SMSIR_API_KEY and settings.SMSIR_TEMPLATE_ID:
        url = "https://api.sms.ir/v1/send/verify"
        headers = {
            "X-API-KEY": settings.SMSIR_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "mobile": phone,
            "templateId": int(settings.SMSIR_TEMPLATE_ID),
            "parameters": [{"name": "CODE", "value": code}]
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Response Text: {response.text}")

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    sms_sent = True
                    print("[DEBUG] sms_sent set to True because status=1")
                else:
                    error_message = data.get("message", "Unknown error")
                    print(f"[DEBUG] sms_sent remains False, error: {error_message}")
            else:
                error_message = f"HTTP {response.status_code}"
        except Exception as e:
            error_message = str(e)
            print(f"[DEBUG] Exception: {error_message}")
    else:
        error_message = "SMS.ir API key or template ID missing"

    print(f"[DEBUG] Final sms_sent: {sms_sent}")

    if sms_sent:
        return Response({'message': 'کد تأیید به شماره شما ارسال شد', 'expires_in_minutes': 2})

    if not settings.DEBUG:
        return Response({'error': 'امکان ارسال پیامک وجود ندارد'}, status=500)
    else:
        print(f"🔐 کد تأیید برای {phone}: {code}")
        if error_message:
            print(f"⚠️ خطای ارسال پیامک: {error_message}")
        return Response({'message': 'کد تأیید در کنسول چاپ شد (حالت تست)', 'expires_in_minutes': 2})


# ========== تأیید OTP و ورود/ثبت‌نام ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = request.data.get('phone')
    code = request.data.get('code')
    if not phone or not code:
        return Response({'error': 'شماره موبایل و کد الزامی است'}, status=400)
    try:
        otp_record = OTP.objects.get(phone=phone, code=code)
    except OTP.DoesNotExist:
        return Response({'error': 'کد نامعتبر است'}, status=400)
    if not otp_record.is_valid():
        return Response({'error': 'کد منقضی شده است'}, status=400)

    user, created = User.objects.get_or_create(
        username=phone,
        defaults={'phone': phone, 'display_name': f'کاربر {phone[-4:]}', 'role': 'customer'}
    )
    if not created and not user.phone:
        user.phone = phone
        user.save()

    otp_record.delete()
    refresh = RefreshToken.for_user(user)
    user_data = {
        'id': user.id,
        'phone': user.phone,
        'display_name': user.display_name,
        'email': user.email,
        'role': user.role,
    }
    requires_profile_completion = (not user.display_name or user.display_name.startswith('کاربر')) or not user.email
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': user_data,
        'requires_profile_completion': requires_profile_completion,
    })


# ========== مدیریت درخواست‌های تأمین‌کنندگی (فقط ادمین) ==========
@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_supplier(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'کاربر یافت نشد'}, status=404)

    if user.supplier_request_status != 'pending':
        return Response({'error': 'این کاربر درخواست در انتظار ندارد'}, status=400)

    user.role = 'supplier'
    user.supplier_request_status = 'approved'
    user.save()

    info = user.supplier_info or {}
    from suppliers.models import Company
    Company.objects.update_or_create(
        owner=user,
        defaults={
            'name': info.get('name', ''),
            'industry': info.get('industry', ''),
            'location': info.get('location', ''),
            'phone': info.get('phone', ''),
            'email': info.get('email', ''),
            'established': info.get('established', None),
            'description': info.get('description', ''),
            'is_verified': True,
        }
    )

    return Response({'message': 'کاربر با موفقیت تأمین‌کننده شد و شرکت ایجاد گردید.'})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_supplier(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'کاربر یافت نشد'}, status=404)

    if user.supplier_request_status != 'pending':
        return Response({'error': 'این کاربر درخواست در انتظار ندارد'}, status=400)

    user.supplier_request_status = 'rejected'
    user.save()

    return Response({'message': f'درخواست کاربر {user.username} رد شد'})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def pending_supplier_requests(request):
    users = User.objects.filter(supplier_request_status='pending')
    data = []
    for user in users:
        data.append({
            'id': user.id,
            'username': user.username,
            'phone': user.phone,
            'display_name': user.display_name,
            'supplier_info': user.supplier_info,
            'created_at': user.date_joined,
        })
    return Response(data)
