from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import EmailForm, ProfileForm, VerifyForm
from .models import EmailVerification

User = get_user_model()
RESEND_COOLDOWN = 60  # seconds


def register(request):
    if request.user.is_authenticated:
        return redirect("users:home")

    form = EmailForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]

        last = EmailVerification.objects.filter(email=email).first()
        if last and (timezone.now() - last.created_at).total_seconds() < RESEND_COOLDOWN:
            form.add_error("email", "Wait a minute before resending the code")
        else:
            code = EmailVerification.create_for(email)
            send_mail(
                subject="Confirmation code",
                message=f"Your code: {code}.",
                from_email=None,  # DEFAULT_FROM_EMAIL
                recipient_list=[email],
            )
            request.session["reg_email"] = email
            return redirect("users:verify_email")

    return render(request, "register.html", {"form": form})


def verify_email(request):
    email = request.session.get("reg_email")
    if not email:
        return redirect("users:register")

    form = VerifyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        verification = EmailVerification.objects.filter(email=email).first()

        if not verification or not verification.verify(form.cleaned_data["code"]):
            form.add_error("code", "Invalid or expired code")
        elif User.objects.filter(email=email).exists():
            form.add_error(None, "Email already exists")
        else:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=form.cleaned_data["password1"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                )
                verification.delete()
            del request.session["reg_email"]
            login(request, user)
            return redirect("users:home")

    return render(request, "verify.html", {"form": form, "email": email})

def home(request):
    from posts.views import feed
    return feed(request)



@login_required
def profile(request):
    form = ProfileForm(request.POST if request.method == "POST" else None,
                       request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("users:profile")
    return render(request, "profile.html", {"form": form, "account_tab": "profile"})
