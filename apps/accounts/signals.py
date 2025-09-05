# apps/accounts/signals.py
import logging
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from allauth.account.signals import user_signed_up

from .models import Account

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_account_for_user(sender, instance, created, **kwargs):
    """Create a linked Account (and Cart if available) after the User transaction commits."""
    if not created:
        return

    def _create():
        try:
            Account.objects.get_or_create(
                user=instance,
                defaults={
                    "display_name": instance.get_full_name() or getattr(instance, "username", "")
                },
            )
        except Exception as exc:
            logger.exception("Failed to create Account for user %s: %s", instance, exc)

        # Create a Cart for the user if the Cart model exists
        try:
            from apps.orders.models import Cart
        except Exception:
            Cart = None

        if Cart is not None:
            try:
                Cart.objects.get_or_create(user=instance)
            except Exception as exc:
                logger.exception("Failed to create Cart for user %s: %s", instance, exc)

    transaction.on_commit(_create)


@receiver(user_signed_up)
def populate_profile_on_social_signup(request, user, sociallogin=None, **kwargs):
    """
    Populate Account fields when a user signs up via social provider (e.g., Google).
    Runs immediately on allauth's signal; internal operations are on_commit-safe.
    """
    def _populate():
        try:
            account, _ = Account.objects.get_or_create(user=user)
            if sociallogin and getattr(sociallogin, "account", None):
                provider = sociallogin.account.provider
                account.provider = provider

                extra = getattr(sociallogin.account, "extra_data", {}) or {}
                account.display_name = (
                    extra.get("name")
                    or account.display_name
                    or user.get_full_name()
                    or getattr(user, "username", "")
                )
                account.avatar = extra.get("picture") or account.avatar
                account.save()
        except Exception as exc:
            logger.exception("Failed to populate Account for social signup user %s: %s", user, exc)

        # Ensure user has a cart (if Cart model exists)
        try:
            from apps.orders.models import Cart
        except Exception:
            Cart = None

        if Cart is not None:
            try:
                Cart.objects.get_or_create(user=user)
            except Exception as exc:
                logger.exception("Failed to create Cart after social signup for user %s: %s", user, exc)

    transaction.on_commit(_populate)
