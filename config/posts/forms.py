from django import forms
from django.utils import timezone

from .models import Category, LostFoundPost, MarketItem

MAX_IMAGE_MB = 5


class LostFoundPostForm(forms.ModelForm):
    class Meta:
        model = LostFoundPost
        fields = [
            "kind",
            "title",
            "category",
            "location",
            "event_date",
            "description",
            "image",
        ]
        labels = {
            "kind": "What happened?",
            "event_date": "Date",
            "image": "Photo (optional)",
        }
        help_texts = {
            "event_date": "When did you lose or find it?",
            "location": "Building, floor, room, or the closest landmark.",
            "description": "Colour, brand, distinctive marks. Don't post details only the owner would know (serial numbers, contents).",
        }
        widgets = {
            "kind": forms.RadioSelect,
            "title": forms.TextInput(attrs={"placeholder": "e.g. Black leather wallet"}),
            "location": forms.TextInput(attrs={"placeholder": "e.g. Main building, room 305"}),
            "event_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["kind"].choices = LostFoundPost.Kind.choices
        self.fields["kind"].initial = LostFoundPost.Kind.LOST
        self.fields["category"].empty_label = "Select a category"
        self.fields["event_date"].widget.attrs["max"] = timezone.localdate().isoformat()

    def clean_event_date(self):
        date = self.cleaned_data["event_date"]
        if date > timezone.localdate():
            raise forms.ValidationError("The date can't be in the future.")
        return date

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and hasattr(image, "size") and image.size > MAX_IMAGE_MB * 1024 * 1024:
            raise forms.ValidationError(f"The image must be smaller than {MAX_IMAGE_MB} MB.")
        return image


class LostFoundFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Search title, place, description"}),
    )
    kind = forms.ChoiceField(
        required=False,
        label="Type",
        choices=[("", "Lost and found")] + LostFoundPost.Kind.choices,
    )
    category = forms.ModelChoiceField(
        required=False,
        label="Category",
        queryset=Category.objects.filter(section=Category.Section.LOST_FOUND),
        empty_label="All categories",
    )


class ListingForm(forms.Form):
    kind = forms.ChoiceField(label="Listing type", choices=[("sale", "For sale"), ("lost", "Lost"), ("found", "Found")])
    image = forms.ImageField(required=False, label="Item photo", widget=forms.FileInput(attrs={"accept": "image/*"}))
    remove_image = forms.BooleanField(required=False, label="Remove current photo")
    title = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"placeholder": "e.g. Calculus textbook, 8th edition"}))
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Tell the community a little more about your item…"}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label="Choose a category")
    price = forms.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2, label="Price (₸)")
    condition = forms.ChoiceField(required=False, choices=[("", "Select condition"), ("new", "New"), ("used", "Used")])
    location = forms.CharField(required=False, max_length=200, widget=forms.TextInput(attrs={"placeholder": "e.g. Main building, library"}))
    event_date = forms.DateField(required=False, label="Date", widget=forms.DateInput(attrs={"type": "date"}))
    status = forms.ChoiceField(required=False, choices=[])
    is_active = forms.BooleanField(required=False, initial=True, label="Visible in the campus feed")

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        if instance:
            kwargs["initial"] = {name: getattr(instance, name, None) for name in self.base_fields}
            kwargs["initial"].update(kind=instance.listing_kind, category=instance.category_id)
        super().__init__(*args, **kwargs)
        kind = self.data.get("kind") if self.is_bound else self.initial.get("kind", "sale")
        if instance:
            # Changing a sale into a lost item would require moving records between models.
            self.fields["kind"].choices = ([("sale", "For sale")] if instance.section == "market"
                                           else [("lost", "Lost"), ("found", "Found")])
        section = "market" if kind == "sale" else "lostfound"
        self.fields["category"].queryset = Category.objects.filter(section=section)
        self.fields["category"].label_from_instance = lambda obj: obj.name
        self.fields["status"].choices = ([("active", "Available"), ("sold", "Sold")] if kind == "sale"
                                           else [("open", "Open"), ("resolved", "Resolved")])
        self.fields["event_date"].widget.attrs["max"] = timezone.localdate().isoformat()

    def clean(self):
        data = super().clean()
        required = ["price", "condition"] if data.get("kind") == "sale" else ["location", "event_date"]
        for field in required:
            if data.get(field) in (None, "") and field not in self.errors:
                self.add_error(field, "This field is required.")
        date = data.get("event_date")
        if date and date > timezone.localdate():
            self.add_error("event_date", "The date can't be in the future.")
        image = data.get("image")
        if image and image.size > MAX_IMAGE_MB * 1024 * 1024:
            self.add_error("image", "The image must be smaller than 5 MB.")
        return data

    def save(self, author):
        data = self.cleaned_data
        item = self.instance or (MarketItem() if data["kind"] == "sale" else LostFoundPost())
        if not item.pk:
            item.author = author
        for name in ["title", "description", "category", "location", "is_active"]:
            setattr(item, name, data[name])
        if data["kind"] == "sale":
            item.price, item.condition = data["price"], data["condition"]
            item.status = data["status"] or "active"
        else:
            item.kind, item.event_date = data["kind"], data["event_date"]
            item.status = data["status"] or "open"
        if data.get("remove_image"):
            item.image = ""
        if data.get("image") and "image" in self.files:
            item.image = data["image"]
        item.save()
        return item
