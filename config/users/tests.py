from django.contrib.auth import get_user_model
from django.test import TestCase


class AccountTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("student@kbtu.kz", "test-password-381", first_name="Student")

    def test_profile_requires_login(self):
        self.assertEqual(self.client.get("/profile/").status_code, 302)

    def test_profile_updates_name_but_not_verified_email(self):
        self.client.force_login(self.user)
        response = self.client.post("/profile/", {"first_name": "Aruzhan", "last_name": "Test", "email": "other@example.com"})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Aruzhan")
        self.assertEqual(self.user.email, "student@kbtu.kz")

    def test_login_and_authenticated_registration_redirect(self):
        response = self.client.post("/login/", {"username": self.user.email, "password": "test-password-381"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(self.client.get("/register/"), "/home/")

    def test_account_pages_render(self):
        self.client.force_login(self.user)
        for path in ("/profile/", "/profile/listings/", "/profile/password/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, self.user.email)

    def test_profile_avatar_upload(self):
        import tempfile
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        image = BytesIO()
        Image.new("RGB", (20, 20), "green").save(image, format="PNG")
        self.client.force_login(self.user)
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            response = self.client.post("/profile/", {
                "first_name": "Student", "last_name": "Test",
                "avatar": SimpleUploadedFile("avatar.png", image.getvalue(), content_type="image/png")})
            self.assertEqual(response.status_code, 302)
            self.user.refresh_from_db()
            self.assertTrue(self.user.avatar.storage.exists(self.user.avatar.name))

    def test_registration_verification_redirects_and_creates_account(self):
        from django.core import mail
        import re
        response = self.client.post("/register/", {"email": "new@kbtu.kz"})
        self.assertRedirects(response, "/register/verify/")
        self.assertFalse(get_user_model().objects.filter(email="new@kbtu.kz").exists())
        code = re.search(r"\d{6}", mail.outbox[0].body).group()
        response = self.client.post("/register/verify/", {
            "code": code, "first_name": "New", "last_name": "Student",
            "password1": "New-strong-test-password-762!", "password2": "New-strong-test-password-762!"})
        self.assertRedirects(response, "/home/")
        self.assertTrue(get_user_model().objects.filter(email="new@kbtu.kz").exists())

    def test_password_change_keeps_account_signed_in(self):
        self.client.force_login(self.user)
        response = self.client.post("/profile/password/", {
            "old_password": "test-password-381", "new_password1": "Other-strong-password-762!",
            "new_password2": "Other-strong-password-762!"})
        self.assertRedirects(response, "/profile/password/done/")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Other-strong-password-762!"))
        self.assertEqual(self.client.get("/profile/").status_code, 200)
