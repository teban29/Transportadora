from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import Cliente
from proveedores.models import Proveedor

class ClienteForm(forms.ModelForm):
    proveedores = forms.ModelMultipleChoiceField(
        queryset=Proveedor.objects.all(),
        widget=FilteredSelectMultiple("Proveedores", is_stacked=False),
        required=False
    )
    
    class Meta:
        model = Cliente
        fields = ['nit', 'nombre', 'email', 'telefono', 'ciudad', 'direccion', 'proveedores']

class ClienteFormEditar(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nit', 'nombre', 'email', 'telefono', 'ciudad', 'direccion']