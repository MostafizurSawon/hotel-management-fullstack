from __future__ import annotations
from django.contrib import admin
from django.db.models import Sum
from django.http import HttpResponse
import csv

from .models import (
    ExpenseCategory, Expense,
    IncomeCategory, Income,
)

# -----------------------------
# HELPERS
# -----------------------------
def money(amount):
    try:
        return f"{amount:,} ৳"
    except Exception:
        return amount


# =============================
# EXPENSES
# =============================

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "date",
        "exp_category",
        "exp_name",
        "amount_display",
        "short_note",
        "created_at",
    )

    list_filter = ("exp_category", "date")
    search_fields = ("exp_name", "note", "exp_category__name")
    date_hierarchy = "date"
    ordering = ("-date", "-created_at")
    list_per_page = 25
    readonly_fields = ("created_at",)
    autocomplete_fields = ("exp_category",)
    actions = ["export_csv"]

    fieldsets = (
        ("Expense Information", {
            "fields": ("exp_category", "exp_name", "date", "amount")
        }),
        ("Additional Info", {
            "fields": ("note",),
            "classes": ("collapse",),
        }),
        ("System Info", {
            "fields": ("created_at",),
        }),
    )

    @admin.display(description="Amount")
    def amount_display(self, obj):
        return money(obj.amount)

    @admin.display(description="Note")
    def short_note(self, obj):
        if obj.note:
            return obj.note[:40] + ("..." if len(obj.note) > 40 else "")
        return "-"

    @admin.action(description="Export selected expenses (CSV)")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=expenses.csv"
        writer = csv.writer(response)

        writer.writerow(["ID", "Date", "Category", "Name", "Amount", "Note"])

        for e in queryset.select_related("exp_category"):
            writer.writerow([
                e.id,
                e.date,
                e.exp_category.name if e.exp_category else "",
                e.exp_name,
                e.amount,
                (e.note or "").replace("\n", " ").strip(),
            ])

        return response

    def changelist_view(self, request, extra_context=None):
        """
        Show total expense amount on top of list page
        """
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data["cl"].queryset
            total = qs.aggregate(total=Sum("amount"))["total"] or 0
            response.context_data["total_amount"] = money(total)
        except Exception:
            pass
        return response


# =============================
# INCOMES
# =============================

@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at",)


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "date",
        "income_category",
        "income_name",
        "amount_display",
        "short_note",
        "created_at",
    )

    list_filter = ("income_category", "date")
    search_fields = ("income_name", "note", "income_category__name")
    date_hierarchy = "date"
    ordering = ("-date", "-created_at")
    list_per_page = 25
    readonly_fields = ("created_at",)
    autocomplete_fields = ("income_category",)
    actions = ["export_csv"]

    fieldsets = (
        ("Income Information", {
            "fields": ("income_category", "income_name", "date", "amount")
        }),
        ("Additional Info", {
            "fields": ("note",),
            "classes": ("collapse",),
        }),
        ("System Info", {
            "fields": ("created_at",),
        }),
    )

    @admin.display(description="Amount")
    def amount_display(self, obj):
        return money(obj.amount)

    @admin.display(description="Note")
    def short_note(self, obj):
        if obj.note:
            return obj.note[:40] + ("..." if len(obj.note) > 40 else "")
        return "-"

    @admin.action(description="Export selected incomes (CSV)")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=incomes.csv"
        writer = csv.writer(response)

        writer.writerow(["ID", "Date", "Category", "Name", "Amount", "Note"])

        for i in queryset.select_related("income_category"):
            writer.writerow([
                i.id,
                i.date,
                i.income_category.name if i.income_category else "",
                i.income_name,
                i.amount,
                (i.note or "").replace("\n", " ").strip(),
            ])

        return response

    def changelist_view(self, request, extra_context=None):
        """
        Show total income amount on top of list page
        """
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data["cl"].queryset
            total = qs.aggregate(total=Sum("amount"))["total"] or 0
            response.context_data["total_amount"] = money(total)
        except Exception:
            pass
        return response
