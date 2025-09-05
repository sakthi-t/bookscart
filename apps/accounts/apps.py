from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self):
        # Import signals so they are registered when the app is ready
        # This ensures Account objects are created on user creation / social signups
        import apps.accounts.signals  # noqa
