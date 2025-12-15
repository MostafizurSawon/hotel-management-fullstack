from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Q
from django.utils import timezone

from apps.guests.models import Guest
from apps.room.models import Room


from django.conf import settings
from django.db import models
from django.db.models import Sum, Q, F, Index
from django.core.exceptions import ValidationError

class Booking(models.Model):
    class Status(models.TextChoices):
        RESERVED    = "RESERVED", "Reserved"
        CHECKED_IN  = "CHECKED_IN", "Checked-In"
        CHECKED_OUT = "CHECKED_OUT", "Checked-Out"
        CANCELLED   = "CANCELLED", "Cancelled"

    guest           = models.ForeignKey(Guest, on_delete=models.PROTECT, related_name="bookings")
    room            = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="bookings")

    check_in        = models.DateField()
    check_out       = models.DateField()

    # snapshot fields (freeze price at booking time) — store in BDT (integer)
    nights          = models.PositiveIntegerField(default=0)
    nightly_rate    = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Store in BDT (integer taka, e.g., 100)"
    )

    # money fields (all in BDT integers)
    gross_amount    = models.PositiveIntegerField(default=0)
    discount_amount = models.PositiveIntegerField(default=0)
    net_amount      = models.PositiveIntegerField(default=0)
    payment_amount  = models.PositiveIntegerField(default=0)
    due_amount      = models.PositiveIntegerField(default=0)
    extra_amount    = models.PositiveIntegerField(default=0)

    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.RESERVED)
    notes           = models.TextField(null=True, blank=True)

    created_by      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="created_bookings"
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            Index(fields=["room", "check_in", "check_out"], name="booking_room_dates_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=Q(check_out__gt=F('check_in')), name="booking_check_out_after_in"),
        ]

    def __str__(self):
        g = getattr(self.guest, "full_name", "Guest")
        rn = getattr(self.room, "room_number", "Room")
        # optional: format dates nicer
        return f"Booking #{self.pk or '—'} — {g} in {rn} [{self.check_in} → {self.check_out}]"

    # ---------- computed totals ----------
    @property
    def total_paid(self) -> int:
        charges = self.payments.filter(kind="CHARGE").aggregate(s=Sum("amount"))["s"] or 0
        refunds = self.payments.filter(kind="REFUND").aggregate(s=Sum("amount"))["s"] or 0
        return int(charges - refunds)

    @property
    def balance_due(self) -> int:
        return max(0, int(self.net_amount or 0) - self.total_paid)

    def sync_payment_caches(self, save=True):
        """Keep cached columns in sync (handy for lists/reports)."""
        self.payment_amount = self.total_paid
        self.due_amount = self.balance_due
        if save:
            # use super().save to avoid infinite full_clean() loops if overridden
            super(Booking, self).save(update_fields=["payment_amount", "due_amount", "updated_at"])

    # ---------- business rules ----------
    def clean(self):
        errors = {}

        # ---- Date rules ----
        if self.check_in and self.check_out:
            if self.check_out <= self.check_in:
                errors["check_out"] = "Check-out must be later than check-in (minimum 1 night)."
        else:
            errors["check_in"] = errors.get("check_in") or "Both check-in and check-out are required."

        # ---- Nights ----
        if not errors.get("check_out") and self.check_in and self.check_out:
            self.nights = (self.check_out - self.check_in).days

        # ---- Nightly rate snapshot (expects BDT integer from Room.price) ----
        if (self.nightly_rate is None or self.nightly_rate == 0) and self.room_id:
            try:
                self.nightly_rate = int(getattr(self.room, "price", 0) or 0)
            except Exception:
                self.nightly_rate = 0

        # ---- Totals (gross/discount/net) — all integers ----
        rate   = int(self.nightly_rate or 0)     # BDT per night
        nights = int(self.nights or 0)
        extra  = int(self.extra_amount or 0)
        self.gross_amount    = rate * nights + extra
        self.discount_amount = max(0, int(self.discount_amount or 0))
        self.net_amount      = max(0, self.gross_amount - self.discount_amount)

        # ---- Sync payment caches if this booking already exists ----
        if self.pk:
            # careful: total_paid will run DB queries
            self.payment_amount = self.total_paid
        else:
            self.payment_amount = int(self.payment_amount or 0)

        # Prevent lowering net below what has already been paid
        if self.pk and self.total_paid > self.net_amount:
            errors["net_amount"] = "Net amount cannot be lower than what’s already paid."

        # Do not allow payment cache to exceed current net
        if self.payment_amount > self.net_amount:
            errors["payment_amount"] = "Payment cannot exceed net amount."

        # ---- Due recompute ----
        self.due_amount = max(0, self.net_amount - self.payment_amount)

        # ---- Availability overlap (same room & overlapping date range) ----
        if self.room_id and self.check_in and self.check_out:
            conflict = (
                Booking.objects
                .filter(room_id=self.room_id)
                .exclude(pk=self.pk)  # ignore self on update
                .filter(check_in__lt=self.check_out, check_out__gt=self.check_in)
                .exists()
            )
            if conflict:
                errors["room"] = "Selected room is not available for the chosen dates."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Validate before saving
        self.full_clean()
        super().save(*args, **kwargs)


class Payment(models.Model):
    class Kind(models.TextChoices):
        CHARGE = "CHARGE", "Charge"   # customer pays
        REFUND = "REFUND", "Refund"   # money returned

    class Method(models.TextChoices):
        CASH     = "CASH", "Cash"
        CARD     = "CARD", "Card"
        BKASH    = "BKASH", "bKash"
        NAGAD    = "NAGAD", "Nagad"
        BANK     = "BANK", "Bank Transfer"
        OTHER    = "OTHER", "Other"

    booking       = models.ForeignKey("Booking", on_delete=models.CASCADE, related_name="payments")
    kind          = models.CharField(max_length=10, choices=Kind.choices, default=Kind.CHARGE)
    method        = models.CharField(max_length=10, choices=Method.choices, default=Method.CASH)

    # money stored in BDT (integer)
    amount        = models.PositiveIntegerField(help_text="Store in BDT (integer taka, e.g., 100)")
    txn_ref       = models.CharField(max_length=100, blank=True, null=True)
    note          = models.CharField(max_length=255, blank=True, null=True)

    received_at   = models.DateTimeField(default=timezone.now)
    created_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="received_payments"
    )
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-received_at", "-id",)
        indexes = [
            models.Index(fields=("booking", "received_at")),
        ]
        constraints = [
            models.CheckConstraint(check=Q(amount__gt=0), name="payment_amount_gt_0"),
        ]

    def clean(self):
        if self.amount is None or self.amount <= 0:
            raise ValidationError({"amount": "Amount must be a positive value."})

        # Prevent overpayment relative to booking.net_amount
        existing = self.booking.payments.exclude(pk=self.pk)
        paid = (
            (existing.filter(kind=self.Kind.CHARGE).aggregate(s=Sum("amount", default=0))["s"] or 0)
            - (existing.filter(kind=self.Kind.REFUND).aggregate(s=Sum("amount", default=0))["s"] or 0)
        )

        delta = self.amount if self.kind == self.Kind.CHARGE else -self.amount
        new_paid = paid + delta

        if new_paid > self.booking.net_amount:
            raise ValidationError({"amount": "This payment would exceed the booking’s net amount."})
        if new_paid < 0:
            raise ValidationError({"amount": "Refund exceeds collected amount."})

    def __str__(self):
        sign = "+" if self.kind == self.Kind.CHARGE else "−"
        return f"Payment {sign}৳{int(self.amount)} for Booking #{self.booking_id}"
