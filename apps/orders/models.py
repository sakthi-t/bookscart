import hashlib, secrets
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.books.models import Book


class Cart(models.Model):
    """A simple DB-backed cart tied to a user (one cart per user)."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Cart({self.user})"

    def total(self) -> Decimal:
        items = self.items.select_related("book").all()
        return sum((item.quantity * item.price_at_add for item in items), Decimal("0.00"))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_add = models.DecimalField(max_digits=8, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "book")

    def clean(self):
        # Ensure quantity is at least 1 and does not exceed available stock
        if self.quantity < 1:
            raise ValidationError("Quantity must be at least 1.")
        if self.book.stock is None:
            return
        if self.quantity > self.book.stock:
            raise ValidationError("Cannot add more than available stock for this book.")

    def save(self, *args, **kwargs):
        # set price snapshot if not provided
        if self.price_at_add is None:
            self.price_at_add = self.book.price or Decimal("0.00")
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"CartItem({self.book.title} x {self.quantity})"


class Order(models.Model):
    STATUS_AWAITING_VERIFICATION = "AWAITING_VERIFICATION"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_REFUNDED = "REFUNDED"
    STATUS_RETURNED = "RETURNED"

    STATUS_CHOICES = [
        (STATUS_AWAITING_VERIFICATION, "Awaiting Verification"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_REFUNDED, "Refunded"),
        (STATUS_RETURNED, "Returned"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_AWAITING_VERIFICATION)
    # otp_code = models.CharField(max_length=10, blank=True)  # store the verification code
    is_verified = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order({self.id}) - {self.user} - {self.status}"

    def calculate_total(self):
        total = sum((oi.quantity * oi.price for oi in self.items.select_related("book").all()), Decimal("0.00"))
        self.total_amount = total
        return total

    def mark_verified(self):
        """Mark the order verified and set status to IN_PROGRESS (caller should handle stock decrement transactionally)."""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.status = self.STATUS_IN_PROGRESS
        self.save(update_fields=["is_verified", "verified_at", "status"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)  # snapshot price at order time
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.quantity < 1:
            raise ValidationError("Order item quantity must be at least 1.")
        if self.book.stock is None:
            return
        if self.quantity > self.book.stock:
            raise ValidationError("Cannot order more than available stock for this book.")

    def save(self, *args, **kwargs):
        if self.price is None:
            self.price = self.book.price or Decimal("0.00")
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"OrderItem({self.book.title} x {self.quantity})"
