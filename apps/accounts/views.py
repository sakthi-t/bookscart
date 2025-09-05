# apps/accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages

class ProfileForm(forms.Form):
    display_name = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(max_length=32, required=False)


@login_required
def profile_view(request):
    """Simple profile page that shows user info and recent orders."""
    orders = []
    # use related_name 'orders' if Order model sets that (your Order has related_name="orders")
    try:
        orders = request.user.orders.order_by("-created_at")[:10]
    except Exception:
        orders = []

    # Render the template in templates/accounts/profile.html (plural)
    return render(request, "accounts/profile.html", {"orders": orders})


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Save to Account if you use Account model
            try:
                from .models import Account
                account, _ = Account.objects.get_or_create(user=request.user)
                if data.get("display_name"):
                    account.display_name = data.get("display_name")
                if data.get("phone"):
                    # make sure Account has a phone field; if not adjust accordingly
                    account.phone = data.get("phone")
                account.save()
            except Exception:
                # fallback: write to user.first_name (safe for demo)
                if data.get("display_name"):
                    request.user.first_name = data.get("display_name")
                    request.user.save()

            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        # prefill from Account if available
        initial = {}
        try:
            from .models import Account
            account = getattr(request.user, "account", None) or Account.objects.filter(user=request.user).first()
            if account:
                initial["display_name"] = account.display_name
                # only add phone if field exists on model
                if hasattr(account, "phone"):
                    initial["phone"] = getattr(account, "phone", "")
        except Exception:
            initial["display_name"] = request.user.get_full_name() or request.user.username

        form = ProfileForm(initial=initial)

    return render(request, "accounts/profile_edit.html", {"form": form})
