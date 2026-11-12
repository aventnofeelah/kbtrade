from django.core.exceptions import ValidationError

def validate_kbtu_email(value):
    if not value.lower().endswith("@kbtu.kz"):
        raise ValidationError("Email only with @kbtu.kz domain is allowed")