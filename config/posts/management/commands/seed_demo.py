"""Create an explicitly labelled local demo without modifying existing accounts."""
import secrets
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from posts.models import Category, LostFoundPost, MarketItem


class Command(BaseCommand):
    help = "Add local sample listings and a demo account (DEBUG only)."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo data can only be created with DEBUG=True.")
        User = get_user_model()
        if User.objects.filter(email="demo@kbtu.kz").exists():
            self.stdout.write("Demo account already exists; nothing changed.")
            return
        password = secrets.token_urlsafe(12)
        user = User.objects.create_user("demo@kbtu.kz", password, first_name="Demo", last_name="Student")
        items = [
            ("market", "Calculus textbook, 8th edition", "Books & study", "book", 6000, "Library · Main building"),
            ("lost", "Wireless earbuds case", "Electronics", "earbuds", 0, "Main building · Cafeteria"),
            ("market", "Adjustable desk lamp", "Home & dorm", "lamp", 4500, "Dorm A · Common room"),
            ("found", "Keys with a blue keyring", "Accessories", "keys", 0, "Main building · Lobby"),
            ("market", "Grey hoodie · Size M", "Clothing", "hoodie", 7000, "Dorm B · Lobby"),
            ("market", "1.7L electric kettle", "Home & dorm", "kettle", 5000, "Dorm B · Shared kitchen"),
            ("found", "Compact navy umbrella", "Accessories", "umbrella", 0, "Main building · West entrance"),
            ("market", "Wooden desk organizer", "Home & dorm", "organizer", 2500, "Dorm B · Lobby"),
        ]
        for kind, title, category_name, image, price, location in items:
            section = "market" if kind == "market" else "lostfound"
            category, _ = Category.objects.get_or_create(section=section, name=category_name)
            data = dict(author=user, title=title, category=category, location=location,
                        description="Local demo listing for design review. This is sample data, not a real offer. "
                                    "You can edit this listing from the demo account to try the new interface.")
            if section == "market":
                item = MarketItem.objects.create(**data, price=price, condition="used")
            else:
                item = LostFoundPost.objects.create(**data, kind=kind, event_date=date.today())
            path = Path(settings.BASE_DIR) / "static" / "images" / "demo" / f"{image}.png"
            with path.open("rb") as source:
                item.image.save(path.name, File(source), save=True)
        self.stdout.write(self.style.SUCCESS("Created 8 sample listings. Local demo sign-in:"))
        self.stdout.write(f"Email: {user.email}\nPassword: {password}")
