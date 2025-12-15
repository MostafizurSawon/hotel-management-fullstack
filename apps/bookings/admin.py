from django.contrib import admin
from .models import Booking, Payment

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("kind", "method", "amount", "txn_ref", "received_at", "note", "created_by")
    ordering = ("-received_at", "-id")
    show_change_link = True

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id", "guest", "room",
        "check_in", "check_out",
        "nightly_rate", "nights",
        "gross_amount", "discount_amount",
        "net_amount", "payment_amount", "due_amount",
        "status", "created_at",
    )
    list_filter = ("status", "room", "check_in", "check_out", "created_at")
    search_fields = (
        "guest__full_name", "guest__phone_number", "guest__email",
        "room__room_number",
    )
    date_hierarchy = "check_in"
    ordering = ("-created_at",)
    readonly_fields = (
        "nights", "gross_amount", "net_amount", "payment_amount", "due_amount",
        "created_at", "updated_at",
    )
    raw_id_fields = ("guest", "room", "created_by")
    inlines = [PaymentInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "kind", "method", "amount", "received_at", "created_by")
    list_filter  = ("kind", "method", "received_at")
    search_fields = ("booking__id", "booking__guest__full_name", "txn_ref", "note")
    autocomplete_fields = ("booking", "created_by")
    date_hierarchy = "received_at"
    ordering = ("-received_at", "-id")
