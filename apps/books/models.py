# Create your models here.
from decimal import Decimal
from django.db import models
from django.urls import reverse
from cloudinary.models import CloudinaryField
from django.utils.text import slugify


class Book(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True, blank=True)
    author = models.CharField(max_length=200, blank=True)
    genre = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    stock = models.IntegerField(default=0)
    image = CloudinaryField("image", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["genre"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} — {self.author}" if self.author else self.title

    def is_in_stock(self) -> bool:
        return (self.stock or 0) > 0

    def get_absolute_url(self):
        return reverse("books:detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        # auto-generate slug if not provided
        if not self.slug:
            base = slugify(self.title)[:200]
            slug_candidate = base
            counter = 1
            while Book.objects.filter(slug=slug_candidate).exists():
                slug_candidate = f"{base}-{counter}"
                counter += 1
            self.slug = slug_candidate
        # ensure price is Decimal with two places
        if isinstance(self.price, (float, str)):
            self.price = Decimal(str(self.price))
        super().save(*args, **kwargs)
