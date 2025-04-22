from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, 
    UserChangeForm,
    PasswordChangeForm
)
from django.contrib.auth.models import User, Group

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'groups')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].help_text = None
        self.fields['groups'].widget.attrs.update({
            'style': 'display: none;'  # Ocultamos el widget original
        })

class CustomUserChangeForm(UserChangeForm):
    password = None  # Eliminamos el campo de password del formulario

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'groups')

class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = User