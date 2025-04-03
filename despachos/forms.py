from django import forms
from .models import Despacho

class DespachoForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = ['valor_flete', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

class ItemDespachoForm(forms.Form):
    inventario = forms.IntegerField(widget=forms.HiddenInput())
    cantidad = forms.IntegerField(min_value=1)