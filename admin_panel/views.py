from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from accounts.models import User

@staff_member_required
def pending_requests(request):
    users = User.objects.filter(supplier_request_status='pending')
    return render(request, 'admin_panel/pending_requests.html', {'users': users})

@staff_member_required
def approve_user(request, user_id):
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    user = get_object_or_404(User, id=user_id)
    if user.supplier_request_status == 'pending':
        user.role = 'supplier'
        user.supplier_request_status = 'approved'
        user.save()
        messages.success(request, f'کاربر {user.username} تأمین‌کننده شد.')
    else:
        messages.error(request, 'این کاربر درخواست در انتظار ندارد.')
    return redirect('admin_panel:pending_requests')

@staff_member_required
def reject_user(request, user_id):
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    user = get_object_or_404(User, id=user_id)
    if user.supplier_request_status == 'pending':
        user.supplier_request_status = 'rejرخواست کاربر {user.username} رد شد.'
    else:
        messages.error(request, 'این کاربر درخواست در انتظار ندارد.')
    return redirect('admin_panel:pending_requests')

@staff_member_required
def approve_user(request, user_id):
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    user = get_object_or_404(User, id=user_id)
    if user.supplier_request_status == 'pending':
        user.role = 'supplier'
        user.supplier_request_status = 'approved'
        user.save()
        messages.success(request, f'کاربر {user.username} تأمین‌کننده شد.')
    else:
        messages.error(request, 'این کاربر درخواست در انتظار ندارد.')
    return redirect('admin_panel:pending_requests')

@staff_member_required
def reject_user(request, user_id):
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    user = get_object_or_404(User, id=user_id)
    if user.supplier_request_status == 'pending':
        user.supplier_request_status = 'rejرخواست کاربر {user.username} رد شد.'
    else:
        messages.error(request, 'این کاربر درخواست در انتظار ندارد.')
    return redirect('admin_panel:pending_requests')

