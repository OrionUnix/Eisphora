from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, help_text='Requis. Entrez une adresse email valide.')
    country = forms.ChoiceField(choices=[('FR', 'France'), ('US', 'United States')], required=True, help_text='Sélectionnez votre pays.')

    class Meta:
        model = User
        fields = ('username', 'email', 'country', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save(using='auth_db')
            UserProfile.objects.using('auth_db').create(user=user, country=self.cleaned_data['country'])
        return user