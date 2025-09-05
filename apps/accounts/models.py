from django.conf import settings
from django.db import models


class Account(models.Model):
    """
    Simple profile/account model linked to Django's user model.

    This stores lightweight user-specific metadata that we don't want to put
    directly on the auth user model. It's created automatically when a User
    is created (signals will be added separately).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=150, blank=True)
    avatar = models.URLField(blank=True, null=True)
    provider = models.CharField(
        max_length=50, blank=True, help_text="e.g., 'google', 'email'"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or getattr(self.user, "username", str(self.user))
