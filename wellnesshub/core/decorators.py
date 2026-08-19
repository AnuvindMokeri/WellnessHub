from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            profile = getattr(request.user, 'profile', None)
            if not profile or profile.role != role:
                messages.error(request, "You don't have access to that page.")
                return redirect('home')
            if role == 'vendor':
                vendor = getattr(request.user, 'vendor', None)
                if not vendor or vendor.status != 'approved':
                    messages.warning(request, 'Your vendor account is pending admin approval.')
                    return redirect('vendor_pending')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


admin_required = role_required('admin')
vendor_required = role_required('vendor')
customer_required = role_required('customer')
