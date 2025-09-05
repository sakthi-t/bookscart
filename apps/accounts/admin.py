from django.contrib import admin
from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "display_name", "user", "provider", "created_at")
    search_fields = ("display_name", "user__username", "user__email", "provider")
    readonly_fields = ("created_at", "updated_at")
