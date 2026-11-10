from django.contrib import admin
from .models import (
    Category,
    Product,
    ProductImage,
    Cart,
    CartItem,
    Order,
    OrderItem,
    DeliveryZone,
)
from .models import Collection

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "stock_quantity",
        "is_available",
        "is_new_arrival",
    )

    list_filter = (
        "category",
        "is_available",
        "is_new_arrival",
    )

    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}

    list_editable = (
        "price",
        "stock_quantity",
        "is_available",
        "is_new_arrival",
    )

    inlines = [ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "alt_text", "is_primary", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("product__name", "alt_text")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    readonly_fields = (
        "product",
        "product_name",
        "size",
        "quantity",
        "unit_price",
        "subtotal",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "order_number",
        "user",
        "full_name",
        "total",
        "status",
        "payment_status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
        "created_at",
    )

    search_fields = (
        "order_number",
        "full_name",
        "email",
        "phone_number",
        "user__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [OrderItemInline]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    search_fields = ("user__email",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "size", "quantity", "added_at")
    list_filter = ("size",)
    search_fields = ("product__name", "cart__user__email")

@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "county",
        "delivery_fee",
        "is_active",
    )

    list_filter = ("county", "is_active")

    search_fields = ("name", "county")

    list_editable = ("delivery_fee", "is_active")

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('products',)
