from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, 
    UserChangeForm,
    PasswordChangeForm
)
from django.contrib.auth.models import User, Group

class CustomUserCreationForm(UserCreationForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'groups')

class CustomUserChangeForm(UserChangeForm):
    password = None  # Eliminamos el campo de password del formulario

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'groups')

class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = User