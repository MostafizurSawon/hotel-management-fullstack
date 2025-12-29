from __future__ import annotations
from django.contrib import admin

from .models import (
    ExpenseCategory, Expense,
    IncomeCategory, Income,
)

# -----------------------------
# EXPENSES
# -----------------------------
@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("-created_at",)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "exp_category", "exp_name", "amount_display", "note")
    list_filter = ("exp_category", "date")
    search_fields = ("exp_name", "note")
    date_hierarchy = "date"
    actions = ["export_csv"]

    @admin.display(description="Amount")
    def amount_display(self, obj):
        return _money(obj.amount)

    @admin.action(description="Export selected expenses (CSV)")
    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=expenses.csv"
        writer = csv.writer(response)
        writer.writerow(["id", "date", "category", "name", "amount", "note"])
        for e in queryset.select_related("exp_category"):
            writer.writerow([e.id, e.date, getattr(e.exp_category, "name", ""), e.exp_name, e.amount, (e.note or "").replace("\n", " ").strip()])
        return response


# -----------------------------
# INCOMES
# -----------------------------
@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("-created_at",)

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "income_category", "income_name", "amount_display", "note")
    list_filter = ("income_category", "date")
    search_fields = ("income_name", "note")
    date_hierarchy = "date"
    actions = ["export_csv"]

    @admin.display(description="Amount")
    def amount_display(self, obj):
        return _money(obj.amount)

    @admin.action(description="Export selected incomes (CSV)")
    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=incomes.csv"
        writer = csv.writer(response)
        writer.writerow(["id", "date", "category", "name", "amount", "note"])
        for i in queryset.select_related("income_category"):
            writer.writerow([i.id, i.date, getattr(i.income_category, "name", ""), i.income_name, i.amount, (i.note or "").replace("\n", " ").strip()])
        return response
