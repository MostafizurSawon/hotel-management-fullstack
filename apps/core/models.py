from django.db import models

# Create your models here.
class SmsLog(models.Model):
    class Kind(models.TextChoices):
        CREATED   = "CREATED", "Booking Created"
        STATUS    = "STATUS",  "Status Changed"
        PAYMENT   = "PAYMENT", "Payment/Checkout"
        OTHER     = "OTHER",   "Other"

    to = models.CharField(max_length=32, db_index=True)
    body = models.TextField()
    result = models.CharField(max_length=40)              # e.g., "SENT: <id>" or "FAILED: 400"
    provider = models.CharField(max_length=50, default="JBDSMS")
    context = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    booking_id = models.IntegerField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
