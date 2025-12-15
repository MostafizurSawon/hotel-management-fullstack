from django.contrib import admin
from .models import Category, Room

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "room_number", "name", "category", "price", "created_at", "updated_at")
    list_filter = ("category",)
    search_fields = ("room_number", "name")
