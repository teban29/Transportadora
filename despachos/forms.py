from django import forms
from .models import Despacho

class DespachoForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = ['valor_flete', 'observaciones', 'placa_camion', 'nombre_conductor']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

class ItemDespachoForm(forms.Form):
    inventario = forms.IntegerField(widget=forms.HiddenInput())
    cantidad = forms.IntegerField(min_value=1)
    valor_unitario = forms.DecimalField(
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )