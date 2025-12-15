from django.conf import settings
from django.db import models
from django.utils import timezone

def guest_photo_path(instance, filename):
    # media/guests/<phone or id>/photo_<timestamp>.ext
    base = instance.phone_number or f"guest_{instance.id or 'new'}"
    return f"guests/{base}/photo_{int(timezone.now().timestamp())}_{filename}"

class Guest(models.Model):
    # Core identity
    full_name     = models.CharField(max_length=150)
    phone_number  = models.CharField(max_length=20, db_index=True, unique=True)
    email         = models.EmailField(blank=True, null=True)
    father_name   = models.CharField(max_length=150, blank=True)
    nid_passport  = models.CharField(max_length=64, blank=True, help_text="NID or Passport")
    age           = models.PositiveSmallIntegerField(blank=True, null=True)
    profession    = models.CharField(max_length=120, blank=True)
    company       = models.CharField(max_length=120, blank=True)
    nationality   = models.CharField(max_length=90, blank=True)
    address       = models.TextField(blank=True)

    photo         = models.ImageField(upload_to=guest_photo_path, blank=True, null=True)

    # Audit
    created_at    = models.DateTimeField(default=timezone.now)
    updated_at    = models.DateTimeField(auto_now=True)
    created_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_guests"
    )

    # Optional link to a future auth account (guest portal)
    user_account  = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="guest_profile"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone_number"]),
            models.Index(fields=["full_name"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["phone_number"],
                name="uniq_guest_phone"
            ),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"


class GuestCompanion(models.Model):
    guest = models.ForeignKey(
        "guests.Guest",
        on_delete=models.CASCADE,
        related_name="companions"
    )

    # Core companion details (keep it light and practical)
    name         = models.CharField(max_length=150, blank=True, null=True)
    age          = models.PositiveSmallIntegerField(blank=True, null=True)
    nid_passport = models.CharField(max_length=64, blank=True)
    email        = models.EmailField(blank=True, null=True)
    father_name  = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)  # not unique
    relation     = models.CharField(max_length=80, blank=True, help_text="Relation to main guest (optional)")

    created_at   = models.DateTimeField(default=timezone.now)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — Companion of {self.guest.full_name}"
