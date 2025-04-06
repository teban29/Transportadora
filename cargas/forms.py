from django import forms
from .models import Carga, Producto, InventarioCarga
from proveedores.models import Proveedor
from django.core.exceptions import ValidationError

class CargaForm(forms.ModelForm):
    class Meta:
        model = Carga
        fields = ['proveedor', 'remision', 'observaciones', 'archivo_factura']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'archivo_factura': forms.FileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png'})
        }
        labels = {
            'archivo_factura': 'Factura (PDF o imagen)'
        }

    def __init__(self, *args, **kwargs):
        cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
        
        if cliente:
            self.fields['proveedor'].queryset = cliente.proveedores.all()
            self.fields['proveedor'].label_from_instance = lambda obj: f"{obj.nombre}"

        # Mejoras en la presentación de los campos
        self.fields['remision'].widget.attrs.update({
            'placeholder': 'Número único de remisión',
            'autocomplete': 'off'
        })
        self.fields['observaciones'].widget.attrs.update({
            'placeholder': 'Observaciones adicionales...'
        })

    def clean_remision(self):
        remision = self.cleaned_data.get('remision')
        
        if not remision:
            raise ValidationError("El número de remisión es obligatorio")
            
        # Verificar si la remisión ya existe
        if Carga.objects.filter(remision=remision).exists():
            carga_existente = Carga.objects.get(remision=remision)
            raise ValidationError(
                f"La remisión {remision} ya está registrada para la carga {carga_existente.nombre}"
            )
            
        return remision

    def clean_archivo_factura(self):
        archivo = self.cleaned_data.get('archivo_factura')
        
        if archivo:
            # Validar extensión del archivo
            ext = archivo.name.split('.')[-1].lower()
            if ext not in ['pdf', 'jpg', 'jpeg', 'png']:
                raise ValidationError("Formato no soportado. Suba un PDF o imagen")
            
            # Validar tamaño del archivo (ejemplo: 5MB máximo)
            if archivo.size > 5 * 1024 * 1024:
                raise ValidationError("El archivo es demasiado grande (máx. 5MB)")
                
        return archivo

class ProductoForm(forms.Form):
    nombre = forms.CharField(max_length=255, required=True)
    cantidad = forms.IntegerField(min_value=1, required=True)