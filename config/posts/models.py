from django.db import models
from django.conf import settings
from django.urls import reverse

class BasePost(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="%(class)s_posts",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse("posts:detail", kwargs={"section": self.section, "pk": self.pk})

    @property
    def listing_kind(self):
        return "sale" if self.section == "market" else self.kind

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class LostFoundPost(BasePost):
    section = "lostfound"

    class Kind(models.TextChoices):
        LOST = "lost", "Lost"
        FOUND = "found", "Found"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"

    category = models.ForeignKey(
        "Category",
        on_delete=models.PROTECT,
        limit_choices_to={"section": "lostfound"},
        related_name="lostfound_posts",
    )
    kind = models.CharField(max_length=5, choices=Kind.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    location = models.CharField(max_length=200)
    event_date = models.DateField()
    image = models.ImageField(upload_to="lostfound/%Y/%m/", blank=True)


class MarketItem(BasePost):
    section = "market"

    class Status(models.TextChoices):
        ACTIVE = "active", "Available"
        SOLD = "sold", "Sold"

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    image = models.ImageField(upload_to="market/%Y/%m/", blank=True)
    location = models.CharField(max_length=200, blank=True)

    class Condition(models.TextChoices):
        NEW = "new", "New"
        USED = "used", "Used"

    category = models.ForeignKey(
        "Category",
        on_delete=models.PROTECT,
        limit_choices_to={"section": "market"},
        related_name="market_items",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=5, choices=Condition.choices)

class Category(models.Model):
    class Section(models.TextChoices):
        LOST_FOUND = "lostfound", "Lost/Found"
        MARKET = "market", "Market"

    name = models.CharField(max_length=100)
    section = models.CharField(max_length=10, choices=Section.choices)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["section", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["section", "name"], name="unique_category_name_per_section"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_section_display()})"

# TODO: model for items pictures