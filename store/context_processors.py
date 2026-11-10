from django.db.models import Sum
from .models import CartItem


def cart_item_count(request):

    if request.user.is_authenticated:

        total = CartItem.objects.filter(
            cart__user=request.user
        ).aggregate(
            total_quantity=Sum('quantity')
        )['total_quantity']

        return {
            'cart_item_count': total or 0
        }

    return {
        'cart_item_count': 0
    }