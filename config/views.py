from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import requires_csrf_token

@requires_csrf_token
def server_error(request, template_name='500.html'):
    """هندلر خطای 500 امن - بدون افشای اطلاعات"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'خطای داخلی سرور'
        }, status=500)
    return render(request, template_name, status=500)

@requires_csrf_token
def page_not_found(request, exception, template_name='404.html'):
    """هندلر خطای 404 امن"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'صفحه مورد نظر یافت نشد'
        }, status=404)
    return render(request, template_name, status=404)