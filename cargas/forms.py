from django import forms
from .models import Carga, Producto, InventarioCarga
from proveedores.models import Proveedor

class CargaForm(forms.ModelForm):
    class Meta:
        model = Carga
        fields = ['proveedor']

    def __init__(self, *args, **kwargs):
        cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
        
        if cliente:
            self.fields['proveedor'].queryset = cliente.proveedores.all()

class ProductoForm(forms.Form):
    nombre = forms.CharField(max_length=255, required=True)
    cantidad = forms.IntegerField(min_value=1, required=True)