def cart_count(request):
    '''Provides cart_count for navbar badges.

    Returns a small context dict with the number of items in the authenticated
    user's cart. Safe to call for anonymous users.
    '''
    count = 0
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        try:
            cart = getattr(user, "cart", None)
            if cart is not None:
                count = cart.items.count()
        except Exception:
            count = 0
    return {"cart_count": count}
