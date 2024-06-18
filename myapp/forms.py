from django import forms 
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# forms.py


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user



class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)




class ScraperForm(forms.Form):
    username = forms.CharField(label='Instagram Username', max_length=100)
    password = forms.CharField(label='Instagram Password', widget=forms.PasswordInput)
