from django.forms import ModelForm
from authentication.models import UserProfile, User


class UserUpdateForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = "__all__"
        exclude = ['user', 'balance', 'failed_login_attempts', 'bank', 'account_name', 'account_number']



class PaymentUpdate(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bank', 'account_name', 'account_number']