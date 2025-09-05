from django.urls import path
from . import views

app_name = "books"

urlpatterns = [
    path("", views.home, name="home"),
    path("books/", views.book_list, name="list"),
    path("books/<slug:slug>/", views.book_detail, name="detail"),
    path("books/<slug:slug>/add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.cart_view, name="cart"),
]
