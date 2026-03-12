from django.forms import ModelForm
from .models import Expense


class ExpenseForm(ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'description', 'status']

class ExpenseAddForm(ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'description']