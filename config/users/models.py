import secrets

from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.hashers import check_password, make_password

from django.utils import timezone
from django.db import models

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields["is_staff"] is not True:
            raise ValueError("A superuser must have is_staff=True")
        if extra_fields["is_superuser"] is not True:
            raise ValueError("A superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    # phone = models.CharField(max_length=20, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class EmailVerification(models.Model):
    CODE_TTL = timedelta(minutes=10)
    MAX_ATTEMPTS = 5

    email = models.EmailField(db_index=True)
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def create_for(cls, email):
        email = email.lower()
        code = f"{secrets.randbelow(1_000_000):06d}"
        cls.objects.filter(email=email).delete()
        cls.objects.create(
            email=email,
            code_hash=make_password(code),
            expires_at=timezone.now() + cls.CODE_TTL,
        )
        return code

    def verify(self, code):
        if self.attempts >= self.MAX_ATTEMPTS or timezone.now() > self.expires_at:
            return False
        self.attempts += 1
        self.save(update_fields=["attempts"])
        return check_password(code, self.code_hash)

    def __str__(self):
        return f"{self.email} (until {self.expires_at:%H:%M})"
