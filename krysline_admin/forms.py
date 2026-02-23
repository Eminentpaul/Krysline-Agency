from django.forms import ModelForm
from authentication.models import User 


class UserUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = ['user_type', 'is_active']