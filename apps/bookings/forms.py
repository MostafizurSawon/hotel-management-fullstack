from django import forms
from .models import Booking, Payment
from apps.room.models import Room
from datetime import timedelta
from django.utils import timezone

# class BookingForm(forms.ModelForm):
#     class Meta:
#         model = Booking
#         fields = [
#             "guest", "room",
#             "check_in", "check_out",
#             "nightly_rate",
#             "discount_amount", "payment_amount",
#             "notes",
#             "status",
#         ]
#         widgets = {
#             "guest": forms.Select(attrs={
#                 "class": "form-select",
#                 "id": "id_guest",
#                 "data-placeholder": "Select guest",
#             }),
#             "room": forms.Select(attrs={
#                 "class": "form-select",
#                 "id": "roomSelect",
#                 "data-placeholder": "Select room",
#             }),
#             "check_in": forms.DateInput(attrs={
#                 "type": "date", "class": "form-control", "id": "checkIn"
#             }),
#             "check_out": forms.DateInput(attrs={
#                 "type": "date", "class": "form-control", "id": "checkOut"
#             }),
#             # Readonly look; JS or server will set
#             "nightly_rate": forms.NumberInput(attrs={
#                 "class": "form-control", "id": "nightlyRate",
#                 "type": "number", "min": "0", "step": "1",
#                 "readonly": "readonly", "placeholder": "0",
#             }),
#             "discount_amount": forms.NumberInput(attrs={
#                 "class": "form-control", "id": "discountAmount",
#                 "type": "number", "min": "0", "step": "1", "placeholder": "0",
#             }),
#             "payment_amount": forms.NumberInput(attrs={
#                 "class": "form-control", "id": "paymentAmount",
#                 "type": "number", "min": "0", "step": "1", "placeholder": "0",
#             }),
#             "notes": forms.Textarea(attrs={
#                 "class": "form-control", "rows": 3,
#                 "placeholder": "Any special notes (optional)…",
#             }),
#             "status": forms.Select(attrs={"class": "form-select"}),
#         }

#     def __init__(self, *args, **kwargs):
#         rooms_qs = kwargs.pop("rooms_qs", None)
#         super().__init__(*args, **kwargs)

#         # status is optional on create; default set below
#         self.fields["status"].required = False

#         # Room queryset
#         self.fields["room"].queryset = (
#             rooms_qs if rooms_qs is not None
#             else Room.objects.select_related("category").order_by("room_number")
#         )

#         # Ensure readonly attr is present (defense in depth)
#         self.fields["nightly_rate"].widget.attrs["readonly"] = "readonly"

#         # create vs edit
#         is_edit = bool(getattr(self.instance, "pk", None))
#         if not is_edit:
#             self.fields["status"].initial = Booking.Status.RESERVED

#     def clean(self):
#         cleaned = super().clean()
#         ci = cleaned.get("check_in")
#         co = cleaned.get("check_out")

#         if ci and co:
#             if co < ci:
#                 self.add_error("check_out", "Check-out cannot be before check-in.")
#             elif co == ci:
#                 co_norm = ci + timedelta(days=1)   # same-day => 1 night
#                 cleaned["check_out"] = co_norm
#                 self.instance.check_out = co_norm  # model.clean() যেন নরমালাইজড ভ্যালু দেখে

#         # রুম থাকলে রেট ফিল আপডেট (সেফটি)
#         room = cleaned.get("room")
#         rate = cleaned.get("nightly_rate") or 0
#         if room and int(rate) <= 0:
#             cleaned["nightly_rate"] = getattr(room, "price", 0) or 0

#         return cleaned

#     def clean_discount_amount(self):
#         v = self.cleaned_data.get("discount_amount") or 0
#         return max(0, int(v))

#     def clean_payment_amount(self):
#         v = self.cleaned_data.get("payment_amount") or 0
#         return max(0, int(v))

#     def save(self, commit=True, request_user=None):
#         obj = super().save(commit=False)
#         if request_user and not obj.created_by_id:
#             obj.created_by = request_user
#         if commit:
#             obj.save()
#         return obj


# class BookingForm(forms.ModelForm):
#     # accept both 'DD-MM-YYYY' (from user typing) and 'YYYY-MM-DD' (HTML date input)
#     check_in = forms.DateField(
#         input_formats=['%d-%m-%Y', '%Y-%m-%d'],
#         # render as HTML5 date input so browser shows calendar; format for rendering should be ISO
#         widget=forms.DateInput(format='%Y-%m-%d', attrs={
#             "type": "date",
#             "class": "form-control", "id": "checkIn", "placeholder": "DD-MM-YYYY",
#         }),
#         required=True
#     )
#     check_out = forms.DateField(
#         input_formats=['%d-%m-%Y', '%Y-%m-%d'],
#         widget=forms.DateInput(format='%Y-%m-%d', attrs={
#             "type": "date",
#             "class": "form-control", "id": "checkOut", "placeholder": "DD-MM-YYYY",
#         }),
#         required=True
#     )

#     class Meta:
#         model = Booking
#         fields = [
#             "guest", "room",
#             "check_in", "check_out",
#             "nightly_rate",
#             "discount_amount", "payment_amount",
#             "notes",
#             "status",
#         ]
#         widgets = {
#             "guest": forms.Select(attrs={
#                 "class": "form-select", "id": "id_guest", "data-placeholder": "Select guest",
#             }),
#             "room": forms.Select(attrs={
#                 "class": "form-select", "id": "roomSelect", "data-placeholder": "Select room",
#             }),
#             # nightly_rate, discount, payment, notes, status stay same
#             "nightly_rate": forms.NumberInput(attrs={
#                 "class": "form-control", "id": "nightlyRate",
#                 "type": "number", "min": "0", "step": "1",
#                 "readonly": "readonly", "placeholder": "0",
#             }),
#             "discount_amount": forms.NumberInput(attrs={
#                 "class": "form-control", "id": "discountAmount",
#                 "type": "number", "min": "0", "step": "1", "placeholder": "0",
#             }),
#             "payment_amount": forms.NumberInput(attrs={
#                 "class": "form-control", "id": "paymentAmount",
#                 "type": "number", "min": "0", "step": "1", "placeholder": "0",
#             }),
#             "notes": forms.Textarea(attrs={
#                 "class": "form-control", "rows": 3,
#                 "placeholder": "Any special notes (optional)…",
#             }),
#             "status": forms.Select(attrs={"class": "form-select"}),
#         }

#     def __init__(self, *args, **kwargs):
#         rooms_qs = kwargs.pop("rooms_qs", None)
#         super().__init__(*args, **kwargs)

#         # status optional on create
#         self.fields["status"].required = False

#         self.fields["room"].queryset = (
#             rooms_qs if rooms_qs is not None
#             else Room.objects.select_related("category").order_by("room_number")
#         )

#         # ensure readonly attr remains
#         self.fields["nightly_rate"].widget.attrs["readonly"] = "readonly"

#         is_edit = bool(getattr(self.instance, "pk", None))
#         if not is_edit:
#             self.fields["status"].initial = Booking.Status.RESERVED

#     def clean(self):
#         cleaned = super().clean()
#         ci = cleaned.get("check_in")
#         co = cleaned.get("check_out")

#         if ci and co:
#             if co < ci:
#                 self.add_error("check_out", "Check-out cannot be before check-in.")
#             elif co == ci:
#                 co_norm = ci + timedelta(days=1)
#                 cleaned["check_out"] = co_norm
#                 # keep model instance using date object
#                 self.instance.check_out = co_norm

#         room = cleaned.get("room")
#         rate = cleaned.get("nightly_rate") or 0
#         if room and int(rate) <= 0:
#             cleaned["nightly_rate"] = getattr(room, "price", 0) or 0

#         return cleaned

#     def clean_discount_amount(self):
#         v = self.cleaned_data.get("discount_amount") or 0
#         return max(0, int(v))

#     def clean_payment_amount(self):
#         v = self.cleaned_data.get("payment_amount") or 0
#         return max(0, int(v))

#     def save(self, commit=True, request_user=None):
#         obj = super().save(commit=False)
#         if request_user and not obj.created_by_id:
#             obj.created_by = request_user
#         # DO NOT convert dates to strings here — keep as date objects
#         if commit:
#             obj.save()
#         return obj


from django import forms
from .models import Booking
from apps.room.models import Room
from datetime import timedelta

class BookingForm(forms.ModelForm):
    # accept both 'DD-MM-YYYY' (from user typing) and 'YYYY-MM-DD' (HTML date input)
    check_in = forms.DateField(
        input_formats=['%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            "type": "date",
            "class": "form-control", "id": "checkIn", "placeholder": "DD-MM-YYYY",
        }),
        required=True
    )
    check_out = forms.DateField(
        input_formats=['%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            "type": "date",
            "class": "form-control", "id": "checkOut", "placeholder": "DD-MM-YYYY",
        }),
        required=True
    )

    class Meta:
        model = Booking
        fields = [
            "guest", "room",
            "check_in", "check_out",
            "nightly_rate",
            "extra_amount",           # NEW
            "discount_amount", "payment_amount",
            "notes",
            "status",
        ]
        widgets = {
            "guest": forms.Select(attrs={
                "class": "form-select", "id": "id_guest", "data-placeholder": "Select guest",
            }),
            "room": forms.Select(attrs={
                "class": "form-select", "id": "roomSelect", "data-placeholder": "Select room",
            }),
            "nightly_rate": forms.NumberInput(attrs={
                "class": "form-control", "id": "nightlyRate",
                "type": "number", "min": "0", "step": "1",
                "readonly": "readonly", "placeholder": "0",
            }),
            "extra_amount": forms.NumberInput(attrs={
                "class": "form-control", "id": "extraAmount",
                "type": "number", "min": "0", "step": "1", "placeholder": "0",
            }),
            "discount_amount": forms.NumberInput(attrs={
                "class": "form-control", "id": "discountAmount",
                "type": "number", "min": "0", "step": "1", "placeholder": "0",
            }),
            "payment_amount": forms.NumberInput(attrs={
                "class": "form-control", "id": "paymentAmount",
                "type": "number", "min": "0", "step": "1", "placeholder": "0",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control", "rows": 3,
                "placeholder": "Any special notes (optional)…",
            }),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        rooms_qs = kwargs.pop("rooms_qs", None)
        super().__init__(*args, **kwargs)
        self.fields["status"].required = False
        self.fields["room"].queryset = (
            rooms_qs if rooms_qs is not None
            else Room.objects.select_related("category").order_by("room_number")
        )
        self.fields["nightly_rate"].widget.attrs["readonly"] = "readonly"
        is_edit = bool(getattr(self.instance, "pk", None))
        if not is_edit:
            self.fields["status"].initial = Booking.Status.RESERVED

    def clean(self):
        cleaned = super().clean()
        ci = cleaned.get("check_in")
        co = cleaned.get("check_out")

        if ci and co:
            if co < ci:
                self.add_error("check_out", "Check-out cannot be before check-in.")
            elif co == ci:
                co_norm = ci + timedelta(days=1)
                cleaned["check_out"] = co_norm
                self.instance.check_out = co_norm

        room = cleaned.get("room")
        rate = cleaned.get("nightly_rate") or 0
        if room and int(rate) <= 0:
            cleaned["nightly_rate"] = getattr(room, "price", 0) or 0

        # ensure extra_amount non-negative
        extra = cleaned.get("extra_amount") or 0
        cleaned["extra_amount"] = max(0, int(extra))

        return cleaned

    def clean_discount_amount(self):
        v = self.cleaned_data.get("discount_amount") or 0
        return max(0, int(v))

    def clean_payment_amount(self):
        v = self.cleaned_data.get("payment_amount") or 0
        return max(0, int(v))

    def clean_extra_amount(self):
        v = self.cleaned_data.get("extra_amount") or 0
        return max(0, int(v))

    def save(self, commit=True, request_user=None):
        obj = super().save(commit=False)
        if request_user and not obj.created_by_id:
            obj.created_by = request_user
        if commit:
            obj.save()
        return obj


class PaymentForm(forms.ModelForm):
    amount = forms.IntegerField(min_value=1, label="Amount (BDT)")

    class Meta:
        model = Payment
        fields = ("kind", "method", "amount", "txn_ref", "note", "received_at")

    def __init__(self, *args, **kwargs):
        self.booking = kwargs.pop("booking", None)
        super().__init__(*args, **kwargs)
        self.fields["received_at"].required = False
        # 🔑 make sure booking is present during is_valid() / full_clean()
        if self.booking:
            self.instance.booking = self.booking

    def save(self, commit=True):
        obj = super().save(commit=False)
        # (defensive) ensure booking stays set even if save() is called directly
        if self.booking:
            obj.booking = self.booking
        if commit:
            obj.full_clean()
            obj.save()
        return obj




class PaymentEditForm(forms.ModelForm):
    # Amount BDT (integer). Model already stores int, so keep it simple.
    amount = forms.IntegerField(
        min_value=1,
        label="Amount (BDT)",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter amount in BDT",
        })
    )

    class Meta:
        model = Payment
        fields = ("kind", "method", "amount", "txn_ref", "note", "received_at")
        widgets = {
            "kind": forms.Select(attrs={
                "class": "form-select",
            }),
            "method": forms.Select(attrs={
                "class": "form-select",
            }),
            "txn_ref": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Slip / Transaction ID (optional)",
            }),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Add any note (optional)…",
            }),
            "received_at": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),
        }

    def clean(self):
        cleaned = super().clean()
        # over/under validation একইভাবে থাকবে — model.clean() চলবেই save-এর সময়
        return cleaned




# Guest Mode
from django import forms
from datetime import timedelta
from apps.bookings.models import Booking
from apps.room.models import Room


class GuestBookingForm(forms.ModelForm):
    # date inputs (same UX as admin)
    check_in = forms.DateField(
        input_formats=['%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            "type": "date",
            "class": "form-control",
            "id": "checkIn",
        }),
        required=True
    )

    check_out = forms.DateField(
        input_formats=['%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={
            "type": "date",
            "class": "form-control",
            "id": "checkOut",
        }),
        required=True
    )

    class Meta:
        model = Booking
        fields = [
            "room",
            "check_in",
            "check_out",
            "nightly_rate",
            "notes",
        ]
        widgets = {
            "room": forms.Select(attrs={
                "class": "form-select",
                "id": "roomSelect",
            }),
            "nightly_rate": forms.NumberInput(attrs={
                "class": "form-control",
                "id": "nightlyRate",
                "readonly": "readonly",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Any special notes (optional)…",
            }),
        }

    def __init__(self, *args, **kwargs):
        rooms_qs = kwargs.pop("rooms_qs", None)
        super().__init__(*args, **kwargs)

        # room list
        self.fields["room"].queryset = (
            rooms_qs if rooms_qs is not None
            else Room.objects.select_related("category").order_by("room_number")
        )

        # guest cannot edit these (forced backend)
        self.fields["nightly_rate"].required = False

    def clean(self):
        cleaned = super().clean()

        ci = cleaned.get("check_in")
        co = cleaned.get("check_out")

        # date validation
        if ci and co:
            if co <= ci:
                cleaned["check_out"] = ci + timedelta(days=1)

        room = cleaned.get("room")

        # always freeze room price
        if room:
            cleaned["nightly_rate"] = int(getattr(room, "price", 0) or 0)

        return cleaned

    def save(self, commit=True, guest=None, request_user=None):
        obj = super().save(commit=False)

        # 🔒 force guest ownership
        if guest:
            obj.guest = guest

        # 🔒 guest booking rules
        obj.status = Booking.Status.PENDING
        obj.discount_amount = 0
        obj.payment_amount = 0
        obj.extra_amount = 0

        if request_user:
            obj.created_by = request_user

        if commit:
            obj.save()

        return obj
