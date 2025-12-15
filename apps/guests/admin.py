from django.contrib import admin
from .models import Guest, GuestCompanion

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "nationality", "profession", "created_at")
    list_filter  = ("nationality", "profession", "created_at")
    search_fields = ("full_name", "phone_number", "email", "nid_passport", "address")
    readonly_fields = ("created_at", "updated_at")

@admin.register(GuestCompanion)
class GuestCompanionAdmin(admin.ModelAdmin):
    list_display = ("name", "guest", "phone_number", "relation", "created_at")
    search_fields = ("name", "guest__full_name", "phone_number", "nid_passport", "email")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")
