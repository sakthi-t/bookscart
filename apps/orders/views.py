import random
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.core.mail import send_mail
from django.urls import reverse
from django.http import HttpResponseBadRequest
from django.utils import timezone

from django.conf import settings

from .models import Order, OrderItem, Cart
from apps.books.models import Book


@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related("book").all()
    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("books:cart")

    # create order and order items
    order = Order.objects.create(user=request.user)
    total = Decimal("0.00")
    for ci in items:
        # validate stock again
        if ci.quantity > ci.book.stock:
            messages.error(request, f"Insufficient stock for {ci.book.title}. Please adjust your cart.")
            order.delete()
            return redirect("books:cart")
        oi = OrderItem.objects.create(order=order, book=ci.book, quantity=ci.quantity, price=ci.price_at_add)
        total += oi.quantity * oi.price

    order.total_amount = total
    # mark as in-progress / verified immediately
    order.is_verified = True
    order.status = Order.STATUS_IN_PROGRESS
    order.verified_at = timezone.now()
    order.save(update_fields=["total_amount", "is_verified", "status", "verified_at"])

    # Atomically decrement stock and finalize
    with transaction.atomic():
        book_ids = [oi.book_id for oi in order.items.all()]
        books_qs = Book.objects.select_for_update().filter(id__in=book_ids)
        books = {b.id: b for b in books_qs}

        for oi in order.items.select_related("book").all():
            b = books.get(oi.book_id)
            if b is None or oi.quantity > b.stock:
                messages.error(request, f"Insufficient stock for {oi.book.title}. Order cannot be completed.")
                # optionally: order.status = Order.STATUS_CANCELLED; order.save()
                return redirect("books:cart")

        for oi in order.items.select_related("book").all():
            b = books[oi.book_id]
            b.stock = b.stock - oi.quantity
            b.save()

    # clear the user's cart
    cart.items.all().delete()

    messages.success(request, "Order placed successfully and is now in progress.")
    return redirect(reverse("orders:history"))



@login_required
def order_history(request):
    qs = Order.objects.filter(user=request.user).order_by("-created_at").prefetch_related("items__book")
    return render(request, "orders/history.html", {"orders": qs})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # owner or staff only
    if not (request.user.is_staff or order.user_id == request.user.id):
        return HttpResponseBadRequest("Not allowed")
    # prefetch items+books for display
    order = (Order.objects
             .filter(id=order_id)
             .prefetch_related("items__book")
             .get())
    return render(request, "orders/detail.html", {"order": order})
