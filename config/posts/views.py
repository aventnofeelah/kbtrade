from itertools import chain

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import ListingForm, LostFoundFilterForm, LostFoundPostForm
from .models import Category, LostFoundPost, MarketItem


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




def feed(request, kind=None):
    kind = kind or request.GET.get("kind", "")
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    sort = request.GET.get("sort", "newest")
    market = MarketItem.objects.filter(is_active=True).select_related("category", "author")
    lost = LostFoundPost.objects.filter(is_active=True).select_related("category", "author")
    if query:
        search = Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)
        market, lost = market.filter(search), lost.filter(search)
    if category:
        market, lost = market.filter(category__name=category), lost.filter(category__name=category)
    if kind == "sale":
        lost = lost.none()
    elif kind in ("lost", "found", "lostfound"):
        market = market.none()
        if kind != "lostfound":
            lost = lost.filter(kind=kind)
    items = sorted(chain(market, lost), key=lambda item: item.created_at, reverse=sort != "oldest")
    page = Paginator(items, 12).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "feed.html", {
        "page_obj": page, "items": page.object_list, "total": len(items),
        "kind": kind, "q": query, "selected_category": category, "sort": sort,
        "querystring": params.urlencode(),
        "categories": Category.objects.values_list("name", flat=True).distinct().order_by("name"),
    })


def get_listing(section, pk, user, owner_only=False):
    models = {"market": MarketItem, "lostfound": LostFoundPost}
    if section not in models:
        raise Http404
    qs = models[section].objects.select_related("author", "category")
    if owner_only:
        qs = qs.filter(author=user)
    elif user.is_authenticated:
        qs = qs.filter(Q(is_active=True) | Q(author=user))
    else:
        qs = qs.filter(is_active=True)
    return get_object_or_404(qs, pk=pk)


def detail(request, section, pk):
    return render(request, "listing_detail.html", {"item": get_listing(section, pk, request.user)})


@login_required
def listing_form(request, section=None, pk=None, default_kind="sale"):
    item = get_listing(section, pk, request.user, owner_only=True) if pk else None
    initial = {"kind": request.GET.get("kind", default_kind)}
    form = ListingForm(request.POST if request.method == "POST" else None,
                       request.FILES or None, instance=item, initial=initial)
    if request.method == "POST" and form.is_valid():
        item = form.save(request.user)
        messages.success(request, "Your listing has been updated." if pk else "Your listing is live. Thanks for sharing!")
        return redirect(item)
    is_modal = request.GET.get("modal") == "1" and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    template = "includes/listing_form.html" if is_modal else "listing_form.html"
    return render(request, template, {
        "form": form, "item": item,
        "form_action": request.path,
        "category_options": list(Category.objects.values("id", "name", "section")),
    })


@login_required
def my_listings(request):
    items = sorted(chain(MarketItem.objects.filter(author=request.user).select_related("category"),
                         LostFoundPost.objects.filter(author=request.user).select_related("category")),
                   key=lambda item: item.created_at, reverse=True)
    return render(request, "my_listings.html", {"items": items, "account_tab": "listings"})


@login_required
@require_http_methods(["GET", "POST"])
def delete_listing(request, section, pk):
    item = get_listing(section, pk, request.user, owner_only=True)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Listing deleted.")
        return redirect("posts:my_listings")
    return render(request, "listing_delete.html", {"item": item})
