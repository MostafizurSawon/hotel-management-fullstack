from django import forms
from .models import Guest
from .services import create_guest_user_for_profile
from django.contrib.auth import get_user_model

User = get_user_model()

def _digits_only(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())


class GuestCreateForm(forms.ModelForm):
    _raw_phone_for_password: str | None = None

    class Meta:
        model = Guest
        fields = [
            "full_name", "phone_number", "email", "father_name", "nid_passport",
            "age", "profession", "company", "nationality", "address", "photo",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- Placeholders ---
        placeholders = {
            "full_name": "Full Name",
            "phone_number": "e.g., 01920693718",
            "email": "Email (optional)",
            "father_name": "Father Name",
            "nid_passport": "NID or Passport Number",
            "age": "Age",
            "profession": "Profession",
            "company": "Your Company",
            "nationality": "Nationality",
            "address": "Address",
            "photo": "Upload guest photo",
        }

        # Add Bootstrap/Vuexy classes and placeholders
        for name, field in self.fields.items():
            base = field.widget.attrs.get("class", "")
            if not isinstance(field.widget, (forms.FileInput,)):
                field.widget.attrs["class"] = (base + " form-control").strip()
            else:
                field.widget.attrs["class"] = (base + " form-control").strip()

            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]

        # Improve UX
        self.fields["age"].widget.input_type = "number"
        self.fields["age"].widget.attrs.update({"min": "0", "max": "120", "step": "1"})
        self.fields["phone_number"].widget.input_type = "tel"

        # ✅ Highlight invalid fields
        for name, field in self.fields.items():
            if self.errors.get(name):
                css = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (css + " is-invalid").strip()

    # def clean_phone_number(self):
    #     given = self.cleaned_data.get("phone_number")
    #     digits = _digits_only(given)
    #     if not digits:
    #         raise forms.ValidationError("Please provide a valid phone number.")
    #     self._raw_phone_for_password = digits
    #     normalized = f"88{digits}"
    #     return normalized

    def clean_phone_number(self):
        given = self.cleaned_data.get("phone_number", "")
        digits = _digits_only(given)  # strips +, spaces, dashes, etc.

        if not digits:
            raise forms.ValidationError("Please provide a valid phone number.")

        # Normalize: keep if already starts with 88, else prefix it.
        if digits.startswith("88"):
            normalized = digits
            raw_local = digits[2:] if len(digits) > 2 else ""
        else:
            normalized = f"88{digits}"
            raw_local = digits

        # Duplicate check: exclude self when editing
        exists = Guest.objects.exclude(pk=self.instance.pk).filter(phone_number=normalized).exists()
        if exists:
            raise forms.ValidationError("This phone number is already registered.")

        # Keep the local digits for default password (create flow only)
        self._raw_phone_for_password = raw_local
        return normalized

    def save(self, commit=True, request_user=None, auto_create_user=True):
        guest: Guest = super().save(commit=False)
        if request_user and not guest.created_by_id:
            guest.created_by = request_user
        if commit:
            guest.save()

        if auto_create_user:
            existing = User.objects.filter(phone_number=guest.phone_number).first()
            if existing and not guest.user_account_id:
                guest.user_account = existing
                guest.save(update_fields=["user_account"])
            elif not existing:
                default_pw = self._raw_phone_for_password or ""
                create_guest_user_for_profile(guest, default_password=default_pw)
        return guest



from django.forms import inlineformset_factory
from .models import GuestCompanion

class CompanionForm(forms.ModelForm):
    class Meta:
        model = GuestCompanion
        fields = ["name", "age", "nid_passport", "email", "father_name", "phone_number", "relation"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        placeholders = {
            "name": "Additional Guest Name",
            "age": "Age",
            "nid_passport": "NID/Passport",
            "email": "Email",
            "father_name": "Father Name",
            "phone_number": "Mobile",
            "relation": "Relation (optional)",
        }

        for name, field in self.fields.items():
            base = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (base + " form-control").strip()
            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]

        self.fields["age"].widget.input_type = "number"
        self.fields["age"].widget.attrs.update({"min": "0", "max": "120", "step": "1"})
        self.fields["phone_number"].widget.input_type = "tel"

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        if not phone:
            return ""  # optional for companions
        digits = "".join(ch for ch in phone if ch.isdigit())
        if digits.startswith("88"):
            return digits
        return f"88{digits}"

CompanionFormSet = inlineformset_factory(
    parent_model=Guest,
    model=GuestCompanion,
    form=CompanionForm,
    fields=["name", "age", "nid_passport", "email", "father_name", "phone_number", "relation"],
    extra=0,
    can_delete=True,
)
