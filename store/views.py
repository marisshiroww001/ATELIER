
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from django.urls import reverse
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives

from django.utils.html import escape

from decimal import Decimal
from collections import defaultdict

from .models import (
    Product,
    Category,
    Cart,
    CartItem,
    Order,
    OrderItem,
    DeliveryZone,
    Collection
)
from urllib.parse import urlencode

import uuid
import requests
import hashlib
import hmac
import json
import logging


logger = logging.getLogger(__name__)


# ==================================================
# GENERAL
# ==================================================

def home(request):
    return render(request, 'store/home.html')



def shop(request):
    from django.db.models import Q

    search_query = request.GET.get('q', '').strip()

    products = (
        Product.objects
        .filter(is_available=True)
        .select_related('category')
        .prefetch_related('gallery')
    )

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        ).distinct()

    categories = Category.objects.all()

    return render(request, 'store/shop.html', {
        'products': products,
        'categories': categories,
        'search_query': search_query,
    })



def product_detail(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug,
        is_available=True
    )

    return render(request, 'store/product_detail.html', {
        'product': product,
    })


# ==================================================
# CART
# ==================================================

@login_required
@require_POST

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    # Require customers to log in before adding products.
    if not request.user.is_authenticated:
        messages.info(
            request,
            "Please log in or create an account to add items to your shopping bag."
        )

        next_url = reverse(
            'product_detail',
            kwargs={'slug': product.slug}
        )

        login_url = (
            f"{reverse('account_login')}?"
            f"{urlencode({'next': next_url})}"
        )

        return redirect(login_url)

    size = request.POST.get('size')

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        messages.error(request, "Please enter a valid quantity.")
        return redirect('product_detail', slug=product.slug)

    if size not in dict(CartItem.SIZE_CHOICES):
        messages.error(request, "Please select a valid size.")
        return redirect('product_detail', slug=product.slug)

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('product_detail', slug=product.slug)

    if quantity > product.stock_quantity:
        messages.error(
            request,
            "The requested quantity exceeds available stock."
        )
        return redirect('product_detail', slug=product.slug)

    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=size,
        defaults={'quantity': quantity}
    )

    if not created:
        new_quantity = cart_item.quantity + quantity

        if new_quantity > product.stock_quantity:
            messages.error(
                request,
                "The requested quantity exceeds available stock."
            )
            return redirect('product_detail', slug=product.slug)

        cart_item.quantity = new_quantity
        cart_item.save()

    messages.success(
        request,
        f"{product.name} has been added to your bag."
    )

    return redirect('product_detail', slug=product.slug)


@login_required
def cart_detail(request):
    cart = Cart.objects.filter(user=request.user).first()

    cart_items = (
        list(cart.items.select_related('product'))
        if cart else []
    )

    cart_total = sum(
        (item.subtotal for item in cart_items),
        Decimal('0.00')
    )

    return render(request, 'store/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'cart_total': cart_total,
    })


@login_required
@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    product_name = cart_item.product.name
    cart_item.delete()

    messages.success(request, f"{product_name} has been removed from your bag.")

    return redirect('cart')


@login_required
@require_POST
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        messages.error(request, "Please enter a valid quantity.")
        return redirect('cart')

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('cart')

    if quantity > cart_item.product.stock_quantity:
        messages.error(request, "The requested quantity exceeds available stock.")
        return redirect('cart')

    cart_item.quantity = quantity
    cart_item.save()

    messages.success(request, "Your bag has been updated.")

    return redirect('cart')


# ==================================================
# CHECKOUT
# ==================================================

@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        messages.error(request, "Your shopping bag is empty.")
        return redirect('cart')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        county = request.POST.get('county', '').strip()
        delivery_notes = request.POST.get('delivery_notes', '').strip()
        delivery_zone_id = request.POST.get('delivery_zone')

        required_fields = [
            full_name,
            email,
            phone_number,
            address,
            city,
            county,
            delivery_zone_id,
        ]

        if not all(required_fields):
            messages.error(request, "Please complete all required fields.")
            return redirect('checkout')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect('checkout')

        if len(phone_number) < 7 or len(phone_number) > 20:
            messages.error(request, "Please enter a valid phone number.")
            return redirect('checkout')

        delivery_zone = get_object_or_404(
            DeliveryZone,
            id=delivery_zone_id,
            is_active=True
        )

        if county.casefold() != delivery_zone.county.casefold():
            messages.error(request, "Your selected delivery zone does not match your county.")
            return redirect('checkout')

        with transaction.atomic():
            cart = Cart.objects.select_for_update().filter(
                user=request.user
            ).first()

            if not cart:
                messages.error(request, "Your shopping bag is empty.")
                return redirect('cart')

            cart_items = list(
                cart.items.select_related('product')
            )

            if not cart_items:
                messages.error(request, "Your shopping bag is empty.")
                return redirect('cart')

            requested_quantities = defaultdict(int)

            for item in cart_items:
                requested_quantities[item.product_id] += item.quantity

            products = {}

            for product_id in sorted(requested_quantities):
                product = Product.objects.select_for_update().get(
                    id=product_id
                )

                products[product_id] = product

                if not product.is_available:
                    messages.error(
                        request,
                        f"{product.name} is no longer available."
                    )
                    return redirect('cart')

                if product.stock_quantity < requested_quantities[product_id]:
                    messages.error(
                        request,
                        f"Insufficient stock for {product.name}."
                    )
                    return redirect('cart')

            subtotal = sum(
                (
                    products[item.product_id].price * item.quantity
                    for item in cart_items
                ),
                Decimal('0.00')
            )

            delivery_fee = delivery_zone.delivery_fee
            total = subtotal + delivery_fee

            order = Order.objects.create(
                user=request.user,
                delivery_zone=delivery_zone,
                order_number=f"AT-{uuid.uuid4().hex[:10].upper()}",
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                address=address,
                city=city,
                county=delivery_zone.county,
                delivery_notes=delivery_notes,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total=total,
                status='pending',
                payment_status='pending',
            )

            for item in cart_items:
                product = products[item.product_id]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    size=item.size,
                    quantity=item.quantity,
                    unit_price=product.price,
                    subtotal=product.price * item.quantity,
                )

        return redirect(
            'order_confirmation',
            order_number=order.order_number
        )

    cart_items = list(
        cart.items.select_related('product')
    )

    requested_quantities = defaultdict(int)

    for item in cart_items:
        requested_quantities[item.product_id] += item.quantity

    for product_id, quantity in requested_quantities.items():
        product = next(
            item.product for item in cart_items
            if item.product_id == product_id
        )

        if not product.is_available or quantity > product.stock_quantity:
            messages.error(
                request,
                f"Please review the availability of {product.name}."
            )
            return redirect('cart')

    cart_total = sum(
        (item.subtotal for item in cart_items),
        Decimal('0.00')
    )

    delivery_zones = DeliveryZone.objects.filter(is_active=True)

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'delivery_zones': delivery_zones,
    })


# ==================================================
# ORDER CONFIRMATION
# ==================================================

@login_required
def order_confirmation(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        order_number=order_number,
        user=request.user
    )

    return render(request, 'store/order_confirmation.html', {
        'order': order,
    })


# ==================================================
# EMAIL CONFIRMATION
# ==================================================

def send_order_confirmation_email(order):
    """
    Sends a branded HTML and plain-text payment receipt
    to the customer after successful payment.
    """

    subject = f"ATELIER | Payment Confirmed - {order.order_number}"

    order_items = list(order.items.all())

    # Plain-text email version
    text_items = []

    for item in order_items:
        text_items.append(
            f"{item.product_name} | "
            f"Size: {item.size} | "
            f"Quantity: {item.quantity} | "
            f"KSh {item.subtotal:,.2f}"
        )

    items_text = "\n".join(text_items)

    message = f"""
Hello {order.full_name},

Thank you for shopping with ATELIER.

Your payment has been successfully received.

ORDER CONFIRMATION
----------------------------------------

Order Number: {order.order_number}
Payment Status: PAID
Order Status: PROCESSING

ITEMS PURCHASED
----------------------------------------

{items_text}

----------------------------------------
Subtotal: KSh {order.subtotal:,.2f}
Delivery: KSh {order.delivery_fee:,.2f}
TOTAL PAID: KSh {order.total:,.2f}

DELIVERY INFORMATION
----------------------------------------

Name: {order.full_name}
Email: {order.email}
Phone: {order.phone_number}
Address: {order.address}
City: {order.city}
County: {order.county}

{f"Delivery Notes: {order.delivery_notes}" if order.delivery_notes else ""}

Your order is now being prepared.

Thank you for choosing ATELIER.

ATELIER
Thoughtfully selected. Beautifully delivered.
"""

    # Escape customer-provided information before inserting
    # it into the HTML email.
    safe_name = escape(order.full_name)
    safe_order_number = escape(order.order_number)
    safe_email = escape(order.email)
    safe_phone = escape(order.phone_number)
    safe_address = escape(order.address)
    safe_city = escape(order.city)
    safe_county = escape(order.county)
    safe_notes = escape(order.delivery_notes)

    # Build the product rows.
    item_rows = ""

    for item in order_items:
        item_rows += f"""
        <tr>
            <td style="padding:15px 8px;border-bottom:1px solid #eee8e2;">
                <strong style="color:#242424;font-size:13px;">
                    {escape(item.product_name)}
                </strong>
                <br>
                <span style="color:#888;font-size:12px;">
                    Size: {escape(item.size)} |
                    Quantity: {item.quantity}
                </span>
            </td>

            <td style="padding:15px 8px;border-bottom:1px solid #eee8e2;text-align:right;white-space:nowrap;color:#242424;font-size:13px;">
                KSh {item.subtotal:,.2f}
            </td>
        </tr>
        """

    notes_html = ""

    if safe_notes:
        notes_html = f"""
        <p style="margin:8px 0;color:#666;font-size:13px;">
            <strong>Delivery notes:</strong> {safe_notes}
        </p>
        """

    # Branded HTML email.
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ATELIER Payment Confirmation</title>
    </head>

    <body style="margin:0;padding:0;background-color:#f4f2ef;font-family:Arial,Helvetica,sans-serif;">

        <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
               style="background-color:#f4f2ef;padding:35px 12px;">

            <tr>
                <td align="center">

                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                           style="max-width:620px;background:#ffffff;">

                        <!-- BRAND HEADER -->

                        <tr>
                            <td style="background:#242424;padding:35px 25px;text-align:center;">

                                <h1 style="margin:0;color:#ffffff;font-family:Georgia,serif;font-size:30px;font-weight:normal;letter-spacing:7px;">
                                    ATELIER
                                </h1>

                                <p style="margin:10px 0 0;color:#d7c5b8;font-size:10px;letter-spacing:3px;">
                                    THOUGHTFULLY SELECTED. BEAUTIFULLY DELIVERED.
                                </p>

                            </td>
                        </tr>

                        <!-- MAIN MESSAGE -->

                        <tr>
                            <td style="padding:40px 35px 25px;">

                                <p style="margin:0 0 12px;color:#9a735f;font-size:10px;font-weight:bold;letter-spacing:2px;">
                                    PAYMENT CONFIRMATION
                                </p>

                                <h2 style="margin:0 0 15px;color:#242424;font-family:Georgia,serif;font-size:27px;font-weight:normal;">
                                    Thank you, {safe_name}.
                                </h2>

                                <p style="margin:0;color:#777;font-size:14px;line-height:1.8;">
                                    Your payment has been received successfully.
                                    We're delighted you chose ATELIER.
                                    Your order is now being prepared.
                                </p>

                            </td>
                        </tr>

                        <!-- PAYMENT STATUS -->

                        <tr>
                            <td style="padding:0 35px 25px;">

                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                                       style="background:#f7f6f3;border:1px solid #e8e5e1;">

                                    <tr>
                                        <td style="padding:20px;">

                                            <p style="margin:0 0 8px;color:#999;font-size:10px;letter-spacing:1.5px;">
                                                ORDER NUMBER
                                            </p>

                                            <p style="margin:0 0 18px;color:#242424;font-size:14px;font-weight:bold;">
                                                {safe_order_number}
                                            </p>

                                            <span style="display:inline-block;padding:7px 13px;background:#e9eee6;color:#53664b;font-size:10px;font-weight:bold;letter-spacing:1px;">
                                                PAYMENT SUCCESSFUL
                                            </span>

                                        </td>
                                    </tr>

                                </table>

                            </td>
                        </tr>

                        <!-- ITEMS -->

                        <tr>
                            <td style="padding:10px 35px;">

                                <h3 style="margin:0 0 15px;color:#242424;font-family:Georgia,serif;font-size:19px;font-weight:normal;">
                                    Your order
                                </h3>

                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">

                                    {item_rows}

                                </table>

                            </td>
                        </tr>

                        <!-- TOTALS -->

                        <tr>
                            <td style="padding:20px 35px 30px;">

                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">

                                    <tr>
                                        <td style="padding:8px 0;color:#777;font-size:13px;">
                                            Subtotal
                                        </td>
                                        <td style="padding:8px 0;text-align:right;color:#242424;font-size:13px;">
                                            KSh {order.subtotal:,.2f}
                                        </td>
                                    </tr>

                                    <tr>
                                        <td style="padding:8px 0;color:#777;font-size:13px;">
                                            Delivery
                                        </td>
                                        <td style="padding:8px 0;text-align:right;color:#242424;font-size:13px;">
                                            KSh {order.delivery_fee:,.2f}
                                        </td>
                                    </tr>

                                    <tr>
                                        <td colspan="2" style="padding-top:15px;border-top:1px solid #e8e5e1;"></td>
                                    </tr>

                                    <tr>
                                        <td style="padding:8px 0;color:#242424;font-size:14px;font-weight:bold;">
                                            Total paid
                                        </td>
                                        <td style="padding:8px 0;text-align:right;color:#242424;font-size:18px;font-weight:bold;">
                                            KSh {order.total:,.2f}
                                        </td>
                                    </tr>

                                </table>

                            </td>
                        </tr>

                        <!-- DELIVERY DETAILS -->

                        <tr>
                            <td style="padding:30px 35px;background:#f7f6f3;">

                                <h3 style="margin:0 0 18px;color:#242424;font-family:Georgia,serif;font-size:19px;font-weight:normal;">
                                    Delivery details
                                </h3>

                                <p style="margin:8px 0;color:#666;font-size:13px;">
                                    <strong>Name:</strong> {safe_name}
                                </p>

                                <p style="margin:8px 0;color:#666;font-size:13px;">
                                    <strong>Email:</strong> {safe_email}
                                </p>

                                <p style="margin:8px 0;color:#666;font-size:13px;">
                                    <strong>Phone:</strong> {safe_phone}
                                </p>

                                <p style="margin:8px 0;color:#666;font-size:13px;">
                                    <strong>Address:</strong> {safe_address}
                                </p>

                                <p style="margin:8px 0;color:#666;font-size:13px;">
                                    <strong>City:</strong> {safe_city}
                                </p>

                                <p style="margin:8px 0;color:#666;font-size:13px;">
                                    <strong>County:</strong> {safe_county}
                                </p>

                                {notes_html}

                            </td>
                        </tr>

                        <!-- FOOTER -->

                        <tr>
                            <td style="padding:35px 25px;text-align:center;">

                                <p style="margin:0 0 12px;color:#242424;font-family:Georgia,serif;font-size:20px;letter-spacing:3px;">
                                    ATELIER
                                </p>

                                <p style="margin:0 0 12px;color:#888;font-size:12px;line-height:1.7;">
                                    Thank you for shopping with us.<br>
                                    We look forward to serving you again.
                                </p>

                                <p style="margin:20px 0 0;color:#aaa;font-size:10px;">
                                    This is an automated order confirmation email.
                                </p>

                            </td>
                        </tr>

                    </table>

                </td>
            </tr>

        </table>

    </body>
    </html>
    """

    try:
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )

        email_message.attach_alternative(
            html_message,
            "text/html"
        )

        email_message.send(fail_silently=False)

        logger.info(
            "ATELIER payment confirmation email sent for order %s",
            order.order_number
        )

    except Exception:
        logger.exception(
            "Payment confirmation email failed for order %s",
            order.order_number
        )


# ==================================================
# SHARED PAYMENT PROCESSOR
# ==================================================

def process_successful_payment(order):
    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(
            id=order.id
        )

        # Prevent duplicate processing if callback and webhook
        # both report the same successful payment.
        if locked_order.payment_status == 'paid':
            return locked_order

        order_items = list(
            locked_order.items.all().order_by('product_id')
        )

        requested_quantities = defaultdict(int)

        for item in order_items:
            requested_quantities[item.product_id] += item.quantity

        products = {}
        stock_available = True

        for product_id in sorted(requested_quantities):
            product = Product.objects.select_for_update().get(
                id=product_id
            )

            products[product_id] = product

            if product.stock_quantity < requested_quantities[product_id]:
                stock_available = False

        if stock_available:
            for product_id, quantity in requested_quantities.items():
                product = products[product_id]

                product.stock_quantity -= quantity
                product.is_available = product.stock_quantity > 0

                product.save(
                    update_fields=[
                        'stock_quantity',
                        'is_available',
                    ]
                )
        else:
            logger.critical(
                "PAYMENT RECEIVED BUT STOCK IS INSUFFICIENT. "
                "Manual review required for order %s.",
                locked_order.order_number
            )

        # Clear the customer's cart after successful payment.
        Cart.objects.filter(user=locked_order.user).delete()

        locked_order.payment_status = 'paid'
        locked_order.status = 'processing'

        locked_order.save(
            update_fields=[
                'payment_status',
                'status',
                'updated_at',
            ]
        )

        # Send the email only after the database transaction commits.
        transaction.on_commit(
            lambda: send_order_confirmation_email(locked_order)
        )

    return locked_order


# ==================================================
# PAYSTACK API HELPERS
# ==================================================

def get_paystack_transaction(reference):
    if not settings.PAYSTACK_SECRET_KEY:
        raise ValueError("Paystack secret key is not configured.")

    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }

    response = requests.get(
        f'{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}',
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    if not result.get('status'):
        return None

    return result.get('data', {})


def verify_paystack_transaction(reference, order):
    payment = get_paystack_transaction(reference)

    if not payment:
        return False

    try:
        expected_amount = int(
            (Decimal(str(order.total)) * 100).quantize(Decimal('1'))
        )
    except (ValueError, TypeError):
        return False

    return (
        payment.get('status') == 'success'
        and payment.get('reference') == reference
        and payment.get('reference') == order.paystack_reference
        and payment.get('amount') == expected_amount
        and payment.get('currency') == 'KES'
    )


# ==================================================
# INITIATE PAYSTACK PAYMENT
# ==================================================

@login_required
@require_POST
def initiate_paystack_payment(request, order_number):
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user
    )

    if order.payment_status == 'paid':
        messages.info(request, "This order has already been paid.")
        return redirect(
            'order_confirmation',
            order_number=order.order_number
        )

    if not settings.PAYSTACK_SECRET_KEY:
        messages.error(request, "Payment service is not configured.")
        return redirect(
            'order_confirmation',
            order_number=order.order_number
        )

    if order.paystack_reference:
        try:
            previous_payment = get_paystack_transaction(
                order.paystack_reference
            )

            if previous_payment is None:
                messages.warning(
                    request,
                    "We couldn't confirm your previous payment. Please try again shortly."
                )
                return redirect(
                    'order_confirmation',
                    order_number=order.order_number
                )

            previous_status = previous_payment.get('status')

            if previous_status == 'success':
                if verify_paystack_transaction(
                    order.paystack_reference,
                    order
                ):
                    process_successful_payment(order)
                    messages.success(
                        request,
                        "Your payment was successful!"
                    )
                else:
                    messages.error(
                        request,
                        "The previous payment could not be verified. Please contact support."
                    )

                return redirect(
                    'order_confirmation',
                    order_number=order.order_number
                )

            if previous_status in ('pending', 'ongoing', 'processing'):
                messages.info(
                    request,
                    "Your previous payment is still being processed. Please wait for confirmation."
                )
                return redirect(
                    'order_confirmation',
                    order_number=order.order_number
                )

            if previous_status not in ('failed', 'abandoned'):
                messages.warning(
                    request,
                    "We cannot determine the status of your previous payment yet. Please contact support if necessary."
                )
                return redirect(
                    'order_confirmation',
                    order_number=order.order_number
                )

            order.payment_status = 'failed'
            order.save(update_fields=['payment_status'])

        except requests.RequestException:
            logger.exception(
                "Could not verify previous payment for order %s",
                order.order_number
            )

            messages.error(
                request,
                "We couldn't check your previous payment. Please try again shortly."
            )

            return redirect(
                'order_confirmation',
                order_number=order.order_number
            )

    reference = f"AT-{uuid.uuid4().hex.upper()}"

    order.paystack_reference = reference
    order.payment_status = 'pending'

    order.save(
        update_fields=[
            'paystack_reference',
            'payment_status',
            'updated_at',
        ]
    )

    payment_data = {
        'email': order.email,
        'amount': int(
            (Decimal(str(order.total)) * 100).quantize(Decimal('1'))
        ),
        'currency': 'KES',
        'reference': reference,
        'callback_url': request.build_absolute_uri(
            reverse('paystack_callback')
        ),
        'channels': ['card', 'mobile_money'],
    }

    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(
            f'{settings.PAYSTACK_BASE_URL}/transaction/initialize',
            json=payment_data,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        if result.get('status'):
            authorization_url = result.get(
                'data', {}
            ).get('authorization_url')

            if authorization_url:
                return redirect(authorization_url)

        logger.error(
            "Paystack initialization returned an unsuccessful response: %s",
            result
        )

        order.payment_status = 'failed'
        order.save(update_fields=['payment_status'])

        messages.error(
            request,
            "We couldn't initiate your payment. Please try again."
        )

    except (requests.RequestException, ValueError):
        logger.exception(
            "Paystack initialization failed for order %s",
            order.order_number
        )

        messages.error(
            request,
            "We couldn't confirm that payment was started. Please check your order status before retrying."
        )

    return redirect(
        'order_confirmation',
        order_number=order.order_number
    )


# ==================================================
# PAYSTACK CALLBACK
# ==================================================

def paystack_callback(request):
    reference = (
        request.GET.get('reference')
        or request.GET.get('trxref')
    )

    if not reference:
        messages.error(
            request,
            "We did not receive a payment reference. Please check your order."
        )
        return redirect('shop')

    order = Order.objects.filter(
        paystack_reference=reference
    ).first()

    if not order:
        messages.error(
            request,
            "We couldn't find an order linked to this payment."
        )
        return redirect('shop')

    try:
        payment_is_valid = verify_paystack_transaction(
            reference,
            order
        )

        if payment_is_valid:
            process_successful_payment(order)

            messages.success(
                request,
                "Your payment was successful! Your order is confirmed."
            )
        else:
            messages.warning(
                request,
                "Your payment has not been confirmed yet. Please check your order status."
            )

    except requests.RequestException:
        logger.exception(
            "Paystack callback verification failed for reference %s",
            reference
        )

        messages.error(
            request,
            "We couldn't verify your payment just yet. Please check your order status."
        )

    except (ValueError, TypeError):
        logger.exception(
            "Payment processing issue for order %s",
            order.order_number
        )

        messages.error(
            request,
            "Your payment needs manual review. Please contact support."
        )

    return redirect(
        'order_confirmation',
        order_number=order.order_number
    )


# ==================================================
# PAYSTACK WEBHOOK
# ==================================================

@csrf_exempt
@require_POST
def paystack_webhook(request):
    if not settings.PAYSTACK_SECRET_KEY:
        return HttpResponse(status=500)

    signature = request.headers.get(
        'x-paystack-signature',
        ''
    )

    expected_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        request.body,
        hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return HttpResponse(status=401)

    try:
        event = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    if event.get('event') != 'charge.success':
        return HttpResponse(status=200)

    reference = event.get('data', {}).get('reference')

    if not reference:
        return HttpResponse(status=200)

    order = Order.objects.filter(
        paystack_reference=reference
    ).first()

    if not order:
        return HttpResponse(status=200)

    try:
        payment_is_valid = verify_paystack_transaction(
            reference,
            order
        )

        if payment_is_valid:
            process_successful_payment(order)

    except requests.RequestException:
        logger.exception(
            "Webhook verification failed for reference %s",
            reference
        )
        return HttpResponse(status=500)

    except (ValueError, TypeError):
        logger.exception(
            "Webhook payment processing failed for reference %s",
            reference
        )
        return HttpResponse(status=500)

    return HttpResponse(status=200)

def collection_detail(request, slug):

    if slug == 'new-arrivals':

        collection = None

        products = (
            Product.objects
            .filter(
                is_available=True,
                is_new_arrival=True
            )
            .select_related('category')
            .prefetch_related('gallery')
        )

        page_title = 'New Arrivals'
        page_description = 'Discover the latest additions to the ATELIER collection.'

    else:

        collection = get_object_or_404(
            Collection,
            slug=slug,
            is_active=True
        )

        products = (
            collection.products
            .filter(is_available=True)
            .select_related('category')
            .prefetch_related('gallery')
        )

        page_title = collection.name
        page_description = collection.description

    return render(request, 'store/collection_detail.html', {
        'collection': collection,
        'products': products,
        'page_title': page_title,
        'page_description': page_description,
    })
