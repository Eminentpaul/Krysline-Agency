from django import forms
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



User = User

class AffiliateRegistrationForm(forms.ModelForm):
    # Public identity for referral links
    username = forms.CharField(
        help_text="Choose a unique handle (letters, numbers, underscores only).",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. krysline_agent1'})
    )
    
    # Primary security identifier (Login ID)
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'agent@email.com'})
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Min 8 characters'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat password'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username').strip()
        # Security: Allow only alphanumeric and underscores
        if not re.match(r'^[\w]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")
        
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email').lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:
            raise ValidationError("Passwords do not match.")
        
        if password and len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"]) # Secure hashing
        if commit:
            user.save()
        return user