from django.urls import path
from .views import (
    ExpenseView, ExpenseDeleteView, ExpenseCategoryView, ExpenseCategoryDeleteView,
    IncomeView, IncomeDeleteView, IncomeCategoryView, IncomeCategoryDeleteView, LedgerView
)

from .views import ExpenseDataAPIView,ExpenseCategoryAjaxView,ExpenseDetailAjaxView, IncomeDataAPIView, IncomeDetailAjaxView, IncomeCategoryAjaxView, export_ledger_csv
from. import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # Expense
    path('expenses/data/', login_required(ExpenseDataAPIView.as_view()), name='expense_data'),
    path('expenses/data/<int:pk>/', login_required(ExpenseDetailAjaxView.as_view()), name='expense_detail_ajax'),

    path('expenses/', login_required(ExpenseView.as_view()), name='expense_list'),
    path('expenses/edit/<int:pk>/', login_required(ExpenseView.as_view()), name='edit_expense'),
    path('expenses/delete/<int:pk>/', login_required(ExpenseDeleteView.as_view()), name='delete_expense'),

    # Expense Categories
    path("expense-categories/ajax/save/", login_required(ExpenseCategoryAjaxView.as_view()), name="ajax_expense_category_save"),
    path('expense-categories/', login_required(ExpenseCategoryView.as_view()), name='expense_category_list'),
    path('expense-categories/edit/<int:pk>/', login_required(ExpenseCategoryView.as_view()), name='edit_expense_category'),
    path('expense-categories/delete/<int:pk>/', login_required(ExpenseCategoryDeleteView.as_view()), name='delete_expense_category'),

    # Income
    path('incomes/data/', login_required(IncomeDataAPIView.as_view()), name='income_data'),
    path('incomes/data/<int:pk>/', login_required(IncomeDetailAjaxView.as_view()), name='income_detail_ajax'),
    path("income-categories/ajax/save/", login_required(IncomeCategoryAjaxView.as_view()), name="ajax_income_category_save"),

    path('incomes/', login_required(IncomeView.as_view()), name='income_list'),
    path('incomes/edit/<int:pk>/', login_required(IncomeView.as_view()), name='edit_income'),
    path('incomes/delete/<int:pk>/', login_required(IncomeDeleteView.as_view()), name='delete_income'),

    # Income Categories
    path('income-categories/', login_required(IncomeCategoryView.as_view()), name='income_category_list'),
    path('income-categories/edit/<int:pk>/', login_required(IncomeCategoryView.as_view()), name='edit_income_category'),
    path('income-categories/delete/<int:pk>/', login_required(IncomeCategoryDeleteView.as_view()), name='delete_income_category'),

    # Ledger
    path('ledger/', login_required(LedgerView.as_view()), name='ledger_view'),
    path('ledger/export-csv/', export_ledger_csv, name='ledger_export_csv'),

    path('ledger/pdf/', views.ledger_export_pdf, name='ledger_export_pdf'),

    # only income
    path('incomes/export/pdf/', login_required(views.income_export_pdf), name='income_export_pdf'),

    path('expenses/export-pdf/', login_required(views.expense_export_pdf), name='expense_export_pdf'),


]
