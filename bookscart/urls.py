"""URL configuration for bookscart project."""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # allauth provides login/signup + social auth routes
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("apps.accounts.urls")),
    # app urlconfs
    path("", include("apps.books.urls")),
    path("orders/", include("apps.orders.urls")),
    path("chatbot/", include("apps.chatbot.urls")),
]

# In development serve media files if MEDIA_ROOT is configured
if settings.DEBUG and getattr(settings, "MEDIA_ROOT", None):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
