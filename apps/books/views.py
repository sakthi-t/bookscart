from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render

from .models import Book
from apps.orders.models import Cart, CartItem


def home(request):
    """Homepage: simple carousel + brief description + featured books."""
    featured = Book.objects.order_by("-created_at")[:6]
    return render(request, "books/home.html", {"featured": featured})


def book_list(request):
    """List or search books and paginate (6 per page). New items appear at the end."""
    q = request.GET.get("q", "").strip()

    # ORDER: oldest first so new books are appended at the end
    qs = Book.objects.all().order_by("created_at")

    if q:
        tokens = [t for t in q.split() if t]
        token_queries = []
        for tok in tokens:
            tok_q = (
                Q(title__icontains=tok)
                | Q(author__icontains=tok)
                | Q(genre__icontains=tok)
                | Q(description__icontains=tok)
            )
            token_queries.append(tok_q)
        if token_queries:
            combined = token_queries[0]
            for tq in token_queries[1:]:
                combined &= tq
            qs = qs.filter(combined)

    # Pagination: 6 per page
    per_page = 6
    paginator = Paginator(qs, per_page)

    # safe page number parsing
    try:
        page_num = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page_num = 1

    page_obj = paginator.get_page(page_num)

    # preserve other GET params (like q)
    params = request.GET.copy()
    if "page" in params:
        params.pop("page")
    qs_params = params.urlencode()

    # sliding 5-page window
    window_size = 5
    total_pages = paginator.num_pages
    window_start = ((page_obj.number - 1) // window_size) * window_size + 1
    window_end = min(window_start + window_size - 1, total_pages)
    page_range = range(window_start, window_end + 1)

    context = {
        "books": page_obj.object_list,   # iterate 'books' in template
        "page_obj": page_obj,
        "paginator": paginator,
        "page_range": page_range,
        "window_start": window_start,
        "window_end": window_end,
        "has_prev_window": window_start > 1,
        "has_next_window": window_end < total_pages,
        "prev_window_page": max(1, window_start - 1),
        "next_window_page": min(total_pages, window_end + 1),
        "query": q,
        "qs_params": qs_params,
    }
    return render(request, "books/list.html", context)


def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)
    return render(request, "books/detail.html", {"book": book})


@login_required
def add_to_cart(request, slug):
    """Add a book to the logged-in user's cart.

    Enforces: quantity >= 1 and not greater than available stock. If a CartItem
    already exists, increase quantity but never exceed the book.stock.
    """
    book = get_object_or_404(Book, slug=slug)
    try:
        qty = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        qty = 1

    if qty < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect(book.get_absolute_url())

    if not book.is_in_stock():
        messages.error(request, "This book is out of stock.")
        return redirect(book.get_absolute_url())

    if qty > book.stock:
        messages.error(request, f"Cannot add more than available stock ({book.stock}).")
        return redirect(book.get_absolute_url())

    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Use defaults with the requested qty so creation validates
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        book=book,
        defaults={"quantity": qty, "price_at_add": book.price},
    )

    if created:
        # If created, ensure it doesn't exceed stock (we already checked qty <= stock above)
        pass
    else:
        new_quantity = item.quantity + qty
        if new_quantity > book.stock:
            messages.error(request, f"You can only have up to {book.stock} of this item in your cart.")
            return redirect(book.get_absolute_url())
        item.quantity = new_quantity

    # snapshot price if not set
    if item.price_at_add is None:
        item.price_at_add = book.price
    item.save()
    messages.success(request, f"Added {qty} × {book.title} to your cart.")
    return redirect(reverse("books:detail", kwargs={"slug": book.slug}))


@login_required
def cart_view(request):
    """Show the current user's cart and items."""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = list(cart.items.select_related("book").all())
    # compute line totals to avoid needing a custom template filter
    items_with_totals = []
    total = Decimal("0.00")
    for it in items:
        line_total = (it.quantity * it.price_at_add)
        items_with_totals.append({"item": it, "line_total": line_total})
        total += line_total
    return render(request, "books/cart.html", {"cart": cart, "items": items_with_totals, "total": total})
