from django.contrib import admin
from .models import SmsLog
@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "to", "result", "context", "booking_id")
    search_fields = ("to", "body", "result")
    list_filter = ("context", "provider")
