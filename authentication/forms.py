from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User
import re

class SecureLoginForm(forms.Form):
    # We use 'label' for the UI and 'widget' to define the HTML type
    email = forms.EmailField(
        max_length=150,
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Username or Email',
            'autocomplete': 'username'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        
        # Strict Email Regex for KAL Security
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_regex, email):
            raise ValidationError("Please enter a valid email address.")
            
        return email

    def clean(self):
        """Cross-field validation if needed."""
        cleaned_data = super().clean()
        # You can add logic here to check if the user is using a VPN 
        # or compare the username against a blacklist.
        return cleaned_data




class AffiliateRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
   