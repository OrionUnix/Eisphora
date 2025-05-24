from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'preferred_language', 'country', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input w-full p-2 border rounded'}),
            'email': forms.EmailInput(attrs={'class': 'form-input w-full p-2 border rounded'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select w-full p-2 border rounded'}),
            'country': forms.Select(attrs={'class': 'form-select w-full p-2 border rounded'}),
        }

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input w-full p-2 border rounded'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input w-full p-2 border rounded'}))