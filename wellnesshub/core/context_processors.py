from .models import CartItem


def cart_count(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == 'customer':
            count = CartItem.objects.filter(user=request.user).count()
            return {'cart_count': count}
    return {'cart_count': 0}
