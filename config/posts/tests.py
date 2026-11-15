from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Category, LostFoundPost, MarketItem


class ListingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("owner@kbtu.kz", "test-password-381")
        self.other = get_user_model().objects.create_user("other@kbtu.kz", "test-password-381")
        self.category = Category.objects.create(name="Test electronics", section="market")
        self.lost_category = Category.objects.create(name="Test keys", section="lostfound")
        self.data = {"kind": "sale", "title": "Desk lamp", "description": "Good condition",
                     "category": self.category.pk, "price": "4500", "condition": "used",
                     "location": "Campus", "status": "active", "is_active": "on"}

    def test_create_assigns_logged_in_author(self):
        self.client.force_login(self.user)
        response = self.client.post("/listings/new/", {**self.data, "author": self.other.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MarketItem.objects.get().author, self.user)

    def test_conditional_validation(self):
        self.client.force_login(self.user)
        for changes in ({"price": "-1"}, {"price": ""}, {"category": self.lost_category.pk}):
            response = self.client.post("/listings/new/", {**self.data, **changes})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(MarketItem.objects.exists())

    def test_lost_requires_location_and_date(self):
        self.client.force_login(self.user)
        data = {**self.data, "kind": "lost", "category": self.lost_category.pk,
                "price": "", "condition": "", "location": "", "event_date": "", "status": "open"}
        self.client.post("/listings/new/", data)
        self.assertFalse(LostFoundPost.objects.exists())
        response = self.client.post("/listings/new/", {**data, "location": "Library", "event_date": "2026-01-01"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(LostFoundPost.objects.get().kind, "lost")

    def test_edit_and_delete_are_owner_only(self):
        item = MarketItem.objects.create(author=self.user, title="Private lamp", description="Lamp",
                                        category=self.category, price=4500, condition="used")
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(f"/listings/market/{item.pk}/edit/", self.data).status_code, 404)
        self.assertEqual(self.client.post(f"/listings/market/{item.pk}/delete/").status_code, 404)
        self.client.force_login(self.user)
        response = self.client.post(f"/listings/market/{item.pk}/edit/", {**self.data, "price": "3000", "status": "sold"})
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.price, 3000)
        self.assertEqual(item.status, "sold")
        self.client.get(f"/listings/market/{item.pk}/delete/")
        self.assertTrue(MarketItem.objects.filter(pk=item.pk).exists())
        self.client.post(f"/listings/market/{item.pk}/delete/")
        self.assertFalse(MarketItem.objects.filter(pk=item.pk).exists())

    def test_hidden_items_are_private(self):
        item = MarketItem.objects.create(author=self.user, title="Hidden lamp", description="Lamp",
                                        category=self.category, price=4500, condition="used", is_active=False)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Hidden lamp")
        self.assertEqual(self.client.get(f"/listings/market/{item.pk}/").status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(f"/listings/market/{item.pk}/").status_code, 200)

    def test_creation_requires_login(self):
        response = self.client.post("/listings/new/", self.data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MarketItem.objects.exists())

    def test_legacy_lost_creation_defaults_to_lost(self):
        self.client.force_login(self.user)
        response = self.client.get("/lost-found/new/")
        self.assertEqual(response.context["form"]["kind"].value(), "lost")

    def test_modal_url_still_renders_full_page_without_ajax(self):
        self.client.force_login(self.user)
        response = self.client.get("/listings/new/?modal=1")
        self.assertContains(response, '<html lang="en">')
        fragment = self.client.get("/listings/new/?modal=1", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertNotContains(fragment, '<html lang="en">')
        self.assertContains(fragment, 'data-listing-form')

    def test_upload_persists_and_can_be_removed(self):
        import tempfile
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        image = BytesIO()
        Image.new("RGB", (20, 20), "yellow").save(image, format="PNG")
        self.client.force_login(self.user)
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            response = self.client.post("/listings/new/", {
                **self.data, "image": SimpleUploadedFile("item.png", image.getvalue(), content_type="image/png")})
            self.assertEqual(response.status_code, 302)
            item = MarketItem.objects.get()
            self.assertTrue(item.image.storage.exists(item.image.name))
            self.client.post(f"/listings/market/{item.pk}/edit/", {**self.data, "remove_image": "on"})
            item.refresh_from_db()
            self.assertFalse(item.image)

    def test_invalid_image_is_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.user)
        response = self.client.post("/listings/new/", {
            **self.data, "image": SimpleUploadedFile("item.png", b"not an image", content_type="image/png")})
        self.assertEqual(response.status_code, 200)
        self.assertIn("image", response.context["form"].errors)
        self.assertFalse(MarketItem.objects.exists())

    def test_search_and_category_filter_across_sections(self):
        MarketItem.objects.create(author=self.user, title="Desk lamp", description="Study light",
                                  category=self.category, price=4500, condition="used")
        LostFoundPost.objects.create(author=self.other, title="Lost keys", description="Blue keyring",
                                     category=self.lost_category, kind="lost", location="Library", event_date="2026-01-01")
        response = self.client.get("/", {"q": "Library"})
        self.assertContains(response, "Lost keys")
        self.assertNotContains(response, "Desk lamp")
        response = self.client.get("/", {"category": self.category.name})
        self.assertContains(response, "Desk lamp")
        self.assertNotContains(response, "Lost keys")
        response = self.client.get("/", {"kind": "sale"})
        self.assertNotContains(response, "Lost keys")
