from django import forms

# Income Expense
from .models import Expense, ExpenseCategory, Income, IncomeCategory



class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name']


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['exp_category', 'exp_name', 'date', 'amount', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class IncomeCategoryForm(forms.ModelForm):
    class Meta:
        model = IncomeCategory
        fields = ['name']


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['income_category', 'income_name', 'date', 'amount', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
