from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import LostFoundFilterForm, LostFoundPostForm
from .models import LostFoundPost


class LostFoundListView(ListView):
    model = LostFoundPost
    template_name = "lostfound.html"
    context_object_name = "posts"
    paginate_by = 12

    def get_queryset(self):
        qs = LostFoundPost.objects.filter(is_active=True).select_related(
            "category", "author"
        )

        self.filter_form = LostFoundFilterForm(self.request.GET or None)
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data["q"]:
                qs = qs.filter(
                    Q(title__icontains=data["q"])
                    | Q(description__icontains=data["q"])
                    | Q(location__icontains=data["q"])
                )
            if data["kind"]:
                qs = qs.filter(kind=data["kind"])
            if data["category"]:
                qs = qs.filter(category=data["category"])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


class LostFoundCreateView(LoginRequiredMixin, CreateView):
    form_class = LostFoundPostForm
    template_name = "lostfound_create.html"
    success_url = reverse_lazy("posts:lostfound")

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "Your post is published.")
        return super().form_valid(form)


