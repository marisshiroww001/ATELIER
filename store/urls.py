
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('shop/', views.shop, name='shop'),

    path(
        'product/<slug:slug>/',
        views.product_detail,
        name='product_detail'
    ),

    path(
        'collections/<slug:slug>/',
        views.collection_detail,
        name='collection_detail'
    ),

    path(
        'cart/add/<int:product_id>/',
        views.add_to_cart,
        name='add_to_cart'
    ),

    path('cart/', views.cart_detail, name='cart'),

    path(
        'cart/remove/<int:item_id>/',
        views.remove_from_cart,
        name='remove_from_cart'
    ),

    path(
        'cart/update/<int:item_id>/',
        views.update_cart_item,
        name='update_cart_item'
    ),

    path('checkout/', views.checkout, name='checkout'),

    path(
        'order-confirmation/<str:order_number>/',
        views.order_confirmation,
        name='order_confirmation'
    ),

    # Paystack callback and webhook
    path(
        'payment/callback/',
        views.paystack_callback,
        name='paystack_callback'
    ),

    path(
        'payment/webhook/',
        views.paystack_webhook,
        name='paystack_webhook'
    ),

    # Generic payment route stays last
    path(
        'payment/<str:order_number>/',
        views.initiate_paystack_payment,
        name='initiate_paystack_payment'
    ),
]
