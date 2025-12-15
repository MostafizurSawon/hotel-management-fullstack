from django import forms
from .models import Category, Room


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter category name (e.g., Deluxe, Suite)"
        })


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["room_number", "category", "name", "price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room_number"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter room number (e.g., A101)"
        })
        self.fields["category"].widget.attrs.update({
            "class": "form-select"
        })
        self.fields["name"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter room name (optional)"
        })
        self.fields["price"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter price (e.g., 1500.00)"
        })
