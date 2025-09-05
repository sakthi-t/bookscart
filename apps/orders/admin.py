from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    search_fields = ("user__username", "user__email")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "book", "quantity", "price_at_add", "added_at")
    search_fields = ("cart__user__username", "book__title")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_amount", "created_at", "is_verified")
    list_filter = ("status", "is_verified", "created_at")
    search_fields = ("user__username", "user__email", "id")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "book", "quantity", "price", "created_at")
    search_fields = ("order__id", "book__title")
