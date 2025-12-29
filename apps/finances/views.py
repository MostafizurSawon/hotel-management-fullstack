from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Expense, ExpenseCategory, Income, IncomeCategory
from .forms import ExpenseForm, ExpenseCategoryForm, IncomeForm, IncomeCategoryForm
from web_project import TemplateLayout, TemplateHelper
from django.http import JsonResponse


# -------------------- EXPENSE VIEWS --------------------

from django.db.models import Sum


class ExpenseDataAPIView(View):
    def get(self, request, *args, **kwargs):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '').strip()

        # Optional filters from query params
        category = request.GET.get('category', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        queryset = Expense.objects.select_related('exp_category').order_by('-date')

        total_records = queryset.count()

        # Apply search filter
        if search_value:
            queryset = queryset.filter(
                Q(exp_name__icontains=search_value) |
                Q(note__icontains=search_value) |
                Q(exp_category__name__icontains=search_value)
            )

        # Apply additional filters
        if category:
            queryset = queryset.filter(exp_category_id=category)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        filtered_records = queryset.count()

        # Get total sum of amount for filtered data
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0

        # Paginate
        paginated_queryset = queryset[start:start + length]

        data = []
        for index, expense in enumerate(paginated_queryset, start=start + 1):
            data.append({
                'id': expense.id,
                'sl': index,
                'date': expense.date.strftime('%Y-%m-%d'),
                'category': expense.exp_category.name if expense.exp_category else '',
                'name': expense.exp_name,
                'amount': f"{expense.amount} ৳",
                'note': expense.note or '—',
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data,
            'total_amount': float(total_amount)
        })


class ExpenseDetailAjaxView(View):
    def get(self, request, pk, *args, **kwargs):
        try:
            expense = Expense.objects.select_related("exp_category").get(pk=pk)
            return JsonResponse({
                "success": True,
                "expense": {
                    "id": expense.id,
                    "name": expense.exp_name,
                    "amount": str(expense.amount),
                    "date": expense.date.strftime('%Y-%m-%d'),
                    "note": expense.note,
                    "category_id": expense.exp_category.id if expense.exp_category else None,
                }
            })
        except Expense.DoesNotExist:
            return JsonResponse({"success": False, "message": "Expense not found."}, status=404)





class ExpenseView(View):
    template_name = "expense/expense_list.html"

    def get(self, request, *args, **kwargs):
        context = TemplateLayout.init(self, {})

        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        search_query = request.GET.get("search", "").strip()
        category_filter = request.GET.get("category", "")
        start_date = request.GET.get("start_date", "")
        end_date = request.GET.get("end_date", "")

        expenses = Expense.objects.select_related("exp_category").order_by("-date")

        if search_query:
            expenses = expenses.filter(
                Q(exp_name__icontains=search_query) |
                Q(note__icontains=search_query)
            )

        if category_filter:
            expenses = expenses.filter(exp_category_id=category_filter)
        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)

        paginator = Paginator(expenses, 10)
        page_number = request.GET.get("page")
        context["expenses"] = paginator.get_page(page_number)

        context["form"] = ExpenseForm()
        context["categories"] = ExpenseCategory.objects.all()
        context["search_query"] = search_query
        context["category_filter"] = category_filter
        context["start_date"] = start_date
        context["end_date"] = end_date
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        expense_id = kwargs.get("pk")
        instance = get_object_or_404(Expense, pk=expense_id) if expense_id else None
        form = ExpenseForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return JsonResponse({
                "success": True,
                "message": f"Expense {'updated' if instance else 'added'} successfully."
            })
        else:
            return JsonResponse({
                "success": False,
                "errors": form.errors,
                "message": "Failed to submit expense."
            }, status=400)



class ExpenseDeleteView(View):
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        expense.delete()
        return JsonResponse({
            "success": True,
            "message": "Expense deleted successfully."
        })




# Ajax Expense category



class ExpenseCategoryAjaxView(View):
    def post(self, request, *args, **kwargs):
        category_id = request.POST.get("id", "").strip()
        name = request.POST.get("name", "").strip()

        instance = None
        if category_id.isdigit():
            instance = ExpenseCategory.objects.filter(pk=int(category_id)).first()

        form = ExpenseCategoryForm(request.POST, instance=instance)

        if form.is_valid():
            category = form.save()
            return JsonResponse({
                "success": True,
                "id": category.id,
                "name": category.name,
                "message": f"Category {'updated' if instance else 'created'} successfully."
            })
        else:
            return JsonResponse({
                "success": False,
                "errors": form.errors,
                "message": "Validation failed."
            }, status=400)





class ExpenseCategoryView(View):
    template_name = "expense/expense_category_list.html"

    def get(self, request, *args, **kwargs):
        context = TemplateLayout.init(self, {})
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        search_query = request.GET.get("search", "").strip()
        categories = ExpenseCategory.objects.all().order_by("-created_at")

        if search_query:
            categories = categories.filter(name__icontains=search_query)

        paginator = Paginator(categories, 10)
        page_number = request.GET.get("page")
        context["categories"] = paginator.get_page(page_number)
        context["form"] = ExpenseCategoryForm()
        context["search_query"] = search_query
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        category_id = kwargs.get("pk")
        instance = get_object_or_404(ExpenseCategory, pk=category_id) if category_id else None
        form = ExpenseCategoryForm(request.POST, instance=instance)

        if form.is_valid():
            form.save()
            messages.success(request, f"Expense category {'updated' if instance else 'created'} successfully.")
        else:
            messages.error(request, "Failed to save category.")

        return redirect("expense_category_list")



class ExpenseCategoryDeleteView(View):
    def post(self, request, pk):
        category = get_object_or_404(ExpenseCategory, pk=pk)
        category.delete()
        return JsonResponse({"success": True, "message": "Expense category deleted."})


# -------------------- INCOME VIEWS --------------------




class IncomeDataAPIView(View):
    def get(self, request, *args, **kwargs):
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '').strip()
        category = request.GET.get('category', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        queryset = Income.objects.select_related('income_category').order_by('-date')

        total_records = queryset.count()

        if search_value:
            queryset = queryset.filter(
                Q(income_name__icontains=search_value) |
                Q(note__icontains=search_value) |
                Q(income_category__name__icontains=search_value)
            )

        if category:
            queryset = queryset.filter(income_category_id=category)
        if start_date:
            queryset = queryset.filter(date__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(date__lte=parse_date(end_date))

        filtered_records = queryset.count()
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0

        paginated_queryset = queryset[start:start + length]
        data = []

        for index, income in enumerate(paginated_queryset, start=start + 1):
            data.append({
                'id': income.id,  # ✅ Add this line
                'sl': index,
                'date': income.date.strftime('%Y-%m-%d'),
                'category': income.income_category.name if income.income_category else '',
                'name': income.income_name,
                'amount': f"{income.amount:.2f} ৳",
                'note': income.note or '—',
            })


        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'total_amount': total_amount,
            'data': data
        })


class IncomeDetailAjaxView(View):
    def get(self, request, pk, *args, **kwargs):
        try:
            income = Income.objects.select_related("income_category").get(pk=pk)
            return JsonResponse({
                "success": True,
                "income": {
                    "id": income.id,
                    "name": income.income_name,
                    "amount": str(income.amount),
                    "date": income.date.strftime('%Y-%m-%d'),
                    "note": income.note,
                    "category_id": income.income_category.id if income.income_category else None,
                }
            })
        except Income.DoesNotExist:
            return JsonResponse({"success": False, "message": "Income not found."}, status=404)




class IncomeView(View):
    template_name = "income/income_list.html"

    def get(self, request, *args, **kwargs):
        context = TemplateLayout.init(self, {})
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        search_query = request.GET.get("search", "").strip()
        category_filter = request.GET.get("category", "")
        start_date = request.GET.get("start_date", "")
        end_date = request.GET.get("end_date", "")

        incomes = Income.objects.select_related("income_category").order_by("-date")

        if search_query:
            incomes = incomes.filter(
                Q(income_name__icontains=search_query) |
                Q(note__icontains=search_query)
            )
        if category_filter:
            incomes = incomes.filter(income_category_id=category_filter)
        if start_date:
            incomes = incomes.filter(date__gte=start_date)
        if end_date:
            incomes = incomes.filter(date__lte=end_date)

        paginator = Paginator(incomes, 10)
        page_number = request.GET.get("page")
        context["incomes"] = paginator.get_page(page_number)

        context["form"] = IncomeForm()
        context["categories"] = IncomeCategory.objects.all()
        context["search_query"] = search_query
        context["category_filter"] = category_filter
        context["start_date"] = start_date
        context["end_date"] = end_date

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        income_id = kwargs.get("pk")
        instance = get_object_or_404(Income, pk=income_id) if income_id else None
        form = IncomeForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return JsonResponse({
                "success": True,
                "message": f"Income {'updated' if instance else 'added'} successfully."
            })
        else:
            return JsonResponse({
                "success": False,
                "errors": form.errors,
                "message": "Failed to submit income."
            }, status=400)



class IncomeDeleteView(View):
    def post(self, request, pk):
        income = get_object_or_404(Income, pk=pk)
        income.delete()
        return JsonResponse({
            "success": True,
            "message": "Income deleted successfully."
        })



class IncomeCategoryAjaxView(View):
    def post(self, request, *args, **kwargs):
        category_id = request.POST.get("id", "").strip()
        name = request.POST.get("name", "").strip()

        instance = None
        if category_id.isdigit():
            instance = IncomeCategory.objects.filter(pk=int(category_id)).first()

        form = IncomeCategoryForm(request.POST, instance=instance)

        if form.is_valid():
            category = form.save()
            return JsonResponse({
                "success": True,
                "id": category.id,
                "name": category.name,
                "message": f"Category {'updated' if instance else 'created'} successfully."
            })
        else:
            return JsonResponse({
                "success": False,
                "errors": form.errors,
                "message": "Validation failed."
            }, status=400)


class IncomeCategoryView(View):
    template_name = "income/income_category_list.html"

    def get(self, request, *args, **kwargs):
        context = TemplateLayout.init(self, {})
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        search_query = request.GET.get("search", "").strip()
        categories = IncomeCategory.objects.all().order_by("-created_at")

        if search_query:
            categories = categories.filter(name__icontains=search_query)

        paginator = Paginator(categories, 10)
        page_number = request.GET.get("page")
        context["categories"] = paginator.get_page(page_number)
        context["form"] = IncomeCategoryForm()
        context["search_query"] = search_query
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        category_id = kwargs.get("pk")
        instance = get_object_or_404(IncomeCategory, pk=category_id) if category_id else None
        form = IncomeCategoryForm(request.POST, instance=instance)

        if form.is_valid():
            form.save()
            messages.success(request, f"Income category {'updated' if instance else 'created'} successfully.")
        else:
            messages.error(request, "Failed to save category.")

        return redirect("income_category_list")



class IncomeCategoryDeleteView(View):
    def post(self, request, pk):
        category = get_object_or_404(IncomeCategory, pk=pk)
        category.delete()
        return JsonResponse({
            "success": True,
            "message": "Income category deleted successfully."
        })




from django.views import View
from django.shortcuts import render
from django.db.models import Sum, Q

# class LedgerView(View):
#     template_name = "finance/ledger.html"

#     def get(self, request):
#         context = TemplateLayout.init(self, {})
#         context["layout"] = "vertical"
#         context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

#         # Filters
#         search = request.GET.get("search", "").strip()
#         income_category = request.GET.get("income_category", "")
#         expense_category = request.GET.get("expense_category", "")
#         start_date = request.GET.get("start_date", "")
#         end_date = request.GET.get("end_date", "")

#         # Income Query
#         incomes = Income.objects.select_related("income_category").order_by("date")
#         if search:
#             incomes = incomes.filter(Q(income_name__icontains=search) | Q(note__icontains=search))
#         if income_category:
#             incomes = incomes.filter(income_category_id=income_category)
#         if start_date:
#             incomes = incomes.filter(date__gte=start_date)
#         if end_date:
#             incomes = incomes.filter(date__lte=end_date)

#         # Expense Query
#         expenses = Expense.objects.select_related("exp_category").order_by("date")
#         if search:
#             expenses = expenses.filter(Q(exp_name__icontains=search) | Q(note__icontains=search))
#         if expense_category:
#             expenses = expenses.filter(exp_category_id=expense_category)
#         if start_date:
#             expenses = expenses.filter(date__gte=start_date)
#         if end_date:
#             expenses = expenses.filter(date__lte=end_date)

#         # Match income & expense rows
#         income_list = list(incomes)
#         expense_list = list(expenses)
#         max_length = max(len(income_list), len(expense_list))
#         income_list += [None] * (max_length - len(income_list))
#         expense_list += [None] * (max_length - len(expense_list))

#         total_income = sum(i.amount for i in income_list if i)
#         total_expense = sum(e.amount for e in expense_list if e)
#         balance = total_income - total_expense

#         context.update({
#             "combined_data": zip(income_list, expense_list),
#             "total_income": total_income,
#             "total_expense": total_expense,
#             "balance": balance,
#             "income_categories": IncomeCategory.objects.all(),
#             "expense_categories": ExpenseCategory.objects.all(),
#             "search": search,
#             "income_category_filter": income_category,
#             "expense_category_filter": expense_category,
#             "start_date": start_date,
#             "end_date": end_date,
#         })

#         return render(request, self.template_name, context)

from django.views import View
from django.shortcuts import render
from django.db.models import Q, Sum
from django.utils.dateparse import parse_date

from .models import Expense, ExpenseCategory
from apps.bookings.models import Payment


class LedgerView(View):
    template_name = "finance/ledger.html"

    def get(self, request):
        context = TemplateLayout.init(self, {})
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)

        # Filters
        search = request.GET.get("search", "").strip()
        start_date = request.GET.get("start_date", "")
        end_date = request.GET.get("end_date", "")
        expense_category = request.GET.get("expense_category", "")

        # ------------------ INCOME (Booking Payment) ------------------
        incomes = Payment.objects.all().order_by("received_at")

        if start_date:
            incomes = incomes.filter(received_at__date__gte=parse_date(start_date))
        if end_date:
            incomes = incomes.filter(received_at__date__lte=parse_date(end_date))

        if search:
            incomes = incomes.filter(
                Q(reference__icontains=search) |
                Q(booking__guest__name__icontains=search)
            )

        # ------------------ EXPENSE ------------------
        expenses = Expense.objects.select_related("exp_category").order_by("date")

        if expense_category:
            expenses = expenses.filter(exp_category_id=expense_category)

        if start_date:
            expenses = expenses.filter(date__gte=parse_date(start_date))
        if end_date:
            expenses = expenses.filter(date__lte=parse_date(end_date))

        if search:
            expenses = expenses.filter(
                Q(exp_name__icontains=search) |
                Q(note__icontains=search)
            )

        # ------------------ ALIGN ROWS ------------------
        income_list = list(incomes)
        expense_list = list(expenses)

        max_len = max(len(income_list), len(expense_list))
        income_list += [None] * (max_len - len(income_list))
        expense_list += [None] * (max_len - len(expense_list))

        # ------------------ TOTALS ------------------
        total_income = incomes.aggregate(s=Sum("amount"))["s"] or 0
        total_expense = expenses.aggregate(s=Sum("amount"))["s"] or 0
        balance = total_income - total_expense

        context.update({
            "combined_data": zip(income_list, expense_list),
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "expense_categories": ExpenseCategory.objects.all(),
            "search": search,
            "start_date": start_date,
            "end_date": end_date,
            "expense_category_filter": expense_category,
        })

        return render(request, self.template_name, context)




# views.py
import csv
from django.http import HttpResponse
from django.db.models import Q
from django.utils.dateparse import parse_date

from .models import Expense



def export_ledger_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ledger.csv"'

    writer = csv.writer(response)

    # Header (ledger-style)
    writer.writerow([
        "Income Date", "Income Category", "Income Name", "Income Amount",
        "Expense Date", "Expense Category", "Expense Name", "Expense Amount",
        "Balance"
    ])

    # Filters
    search = request.GET.get("search", "").strip()
    expense_cat = request.GET.get("expense_category")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # ---------------- INCOME (Booking Payment) ----------------
    incomes = Payment.objects.all().order_by("received_at")

    if start_date:
        incomes = incomes.filter(received_at__date__gte=parse_date(start_date))
    if end_date:
        incomes = incomes.filter(received_at__date__lte=parse_date(end_date))
    if search:
        incomes = incomes.filter(
            Q(reference__icontains=search) |
            Q(booking__guest__name__icontains=search)
        )

    # ---------------- EXPENSE ----------------
    expenses = Expense.objects.select_related("exp_category").all().order_by("date")

    if expense_cat:
        expenses = expenses.filter(exp_category_id=expense_cat)
    if start_date:
        expenses = expenses.filter(date__gte=parse_date(start_date))
    if end_date:
        expenses = expenses.filter(date__lte=parse_date(end_date))
    if search:
        expenses = expenses.filter(
            Q(exp_name__icontains=search)
        )

    income_list = list(incomes)
    expense_list = list(expenses)

    max_len = max(len(income_list), len(expense_list))

    income_list += [None] * (max_len - len(income_list))
    expense_list += [None] * (max_len - len(expense_list))

    total_income = sum(i.amount for i in income_list if i)
    total_expense = sum(e.amount for e in expense_list if e)
    balance = total_income - total_expense

    # Rows
    for inc, exp in zip(income_list, expense_list):
        writer.writerow([
            inc.received_at.date() if inc else "",
            "Booking" if inc else "",
            "Booking Income" if inc else "",
            inc.amount if inc else "",

            exp.date if exp else "",
            exp.exp_category.name if exp and exp.exp_category else "",
            exp.exp_name if exp else "",
            exp.amount if exp else "",

            ""  # balance only in footer
        ])

    # Footer
    writer.writerow([])
    writer.writerow([
        "", "", "Total Income", total_income,
        "", "", "Total Expense", total_expense,
        balance
    ])

    return response



# pdf


from django.views import View
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.db.models import Q, Sum

from .models import Expense


class LedgerPrintView(View):
    template_name = "finance/ledger_print.html"

    def get(self, request):
        search = request.GET.get("search", "").strip()
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        expense_category = request.GET.get("expense_category")

        # INCOME (Booking)
        incomes = Payment.objects.all().order_by("received_at")
        if start_date:
            incomes = incomes.filter(received_at__date__gte=parse_date(start_date))
        if end_date:
            incomes = incomes.filter(received_at__date__lte=parse_date(end_date))
        if search:
            incomes = incomes.filter(
                Q(reference__icontains=search) |
                Q(booking__guest__name__icontains=search)
            )

        # EXPENSE
        expenses = Expense.objects.select_related("exp_category").all().order_by("date")
        if expense_category:
            expenses = expenses.filter(exp_category_id=expense_category)
        if start_date:
            expenses = expenses.filter(date__gte=parse_date(start_date))
        if end_date:
            expenses = expenses.filter(date__lte=parse_date(end_date))
        if search:
            expenses = expenses.filter(exp_name__icontains=search)

        income_list = list(incomes)
        expense_list = list(expenses)

        max_len = max(len(income_list), len(expense_list))
        income_list += [None] * (max_len - len(income_list))
        expense_list += [None] * (max_len - len(expense_list))

        context = {
            "combined_data": zip(income_list, expense_list),
            "total_income": sum(i.amount for i in incomes),
            "total_expense": sum(e.amount for e in expenses),
            "balance": sum(i.amount for i in incomes) - sum(e.amount for e in expenses),
            "start_date": start_date,
            "end_date": end_date,
        }

        return render(request, self.template_name, context)



import os
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.utils.timezone import now

from itertools import zip_longest

from .models import Income, Expense
from .utils import render_to_pdf

def ledger_export_pdf(request):
    search = request.GET.get('search')
    income_category = request.GET.get('income_category')
    expense_category = request.GET.get('expense_category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    income_qs = Income.objects.all().order_by('date')
    expense_qs = Expense.objects.all().order_by('date')

    # Filters
    if search:
        income_qs = income_qs.filter(income_name__icontains=search)
        expense_qs = expense_qs.filter(exp_name__icontains=search)

    if income_category:
        income_qs = income_qs.filter(income_category_id=income_category)

    if expense_category:
        expense_qs = expense_qs.filter(exp_category_id=expense_category)

    if start_date:
        start_date = parse_date(start_date)
        income_qs = income_qs.filter(date__gte=start_date)
        expense_qs = expense_qs.filter(date__gte=start_date)

    if end_date:
        end_date = parse_date(end_date)
        income_qs = income_qs.filter(date__lte=end_date)
        expense_qs = expense_qs.filter(date__lte=end_date)

    # Totals
    total_income = sum(i.amount for i in income_qs)
    total_expense = sum(e.amount for e in expense_qs)
    balance = total_income - total_expense

    # Combine row-wise for table
    combined_data = list(zip_longest(income_qs, expense_qs))

    context = {
        'combined_data': combined_data,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'now': now(),
        'start_date': start_date,
        'end_date': end_date,
    }


    return render_to_pdf('ledger_pdf.html', context)


    # (PDF rendering next step e korbo)
    # return HttpResponse("Filtered data ready", content_type="text/plain")




# only income
from django.utils.timezone import now
from django.db.models import Q
from .models import Income
from .utils import render_to_pdf

def income_export_pdf(request):
    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    incomes = Income.objects.select_related("income_category").order_by("-date")

    if search:
        incomes = incomes.filter(
            Q(income_name__icontains=search) |
            Q(note__icontains=search)
        )
    if category:
        incomes = incomes.filter(income_category_id=category)
    if start_date:
        incomes = incomes.filter(date__gte=start_date)
    if end_date:
        incomes = incomes.filter(date__lte=end_date)

    context = {
        "incomes": incomes,
        "total_income": sum(i.amount for i in incomes),
        "now": now()
    }

    return render_to_pdf("income/income_list_pdf.html", context)



from django.utils.timezone import now
from django.utils.dateparse import parse_date
from django.shortcuts import render
from django.http import HttpResponse
from .models import Expense
from .utils import render_to_pdf

def expense_export_pdf(request):
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    expenses = Expense.objects.all()

    if search:
        expenses = expenses.filter(exp_name__icontains=search)
    if category:
        expenses = expenses.filter(exp_category_id=category)
    if start_date:
        expenses = expenses.filter(date__gte=parse_date(start_date))
    if end_date:
        expenses = expenses.filter(date__lte=parse_date(end_date))

    total_expense = sum(e.amount for e in expenses)

    context = {
        'expenses': expenses,
        'total_expense': total_expense,
        'now': now()
    }

    return render_to_pdf('expense/expense_list_pdf.html', context)
