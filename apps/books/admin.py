from django.contrib import admin

# Register your models here.
from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "genre", "price", "stock", "created_at")
    list_filter = ("genre",)
    search_fields = ("title", "author", "genre")
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "author", "genre", "image", "description")
        }),
        ("Inventory & Pricing", {
            "fields": ("price", "stock")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

