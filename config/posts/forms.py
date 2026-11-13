from django import forms
from django.utils import timezone

from .models import Category, LostFoundPost

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
