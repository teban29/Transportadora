from django.db import models
from django.db.models import Max
from clientes.models import Cliente
from proveedores.models import Proveedor
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from django.core.exceptions import ValidationError


# Create your models here.


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre
    

class Carga(models.Model):
    nombre = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cargas')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='cargas')
    fecha = models.DateTimeField(auto_now_add=True)
    remision = models.CharField(unique=True, max_length=20)
    observaciones = models.TextField(blank=True, null=True) 
    archivo_factura = models.FileField(upload_to='facturas/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.nombre:
            prefijo = self.cliente.nombre[:3].upper()
            ultima_carga = Carga.objects.filter(cliente=self.cliente).aggregate(Max('nombre'))
            ultimo_numero = int(ultima_carga['nombre__max'][-3:]) if ultima_carga['nombre__max'] else 0
            nuevo_numero = ultimo_numero + 1
            self.nombre = f"{prefijo}{nuevo_numero:03d}"
            
        super().save(*args, **kwargs)
    
class InventarioCarga(models.Model):
    carga = models.ForeignKey(Carga, on_delete=models.CASCADE, related_name='inventario')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    codigo_barras = models.CharField(max_length=100, blank=True, null=True)
    fecha_generacion_codigo = models.DateTimeField(blank=True, null=True)
    
    @property
    def cantidad_disponible(self):
        """Calcula dinámicamente la cantidad disponible"""
        total_despachado = self.items_despacho.aggregate(
            total=Sum('cantidad')
        )['total'] or 0
        return max(0, self.cantidad - total_despachado)
    
    def verificar_disponibilidad(self, cantidad, despacho_actual=None):
        """Verifica disponibilidad considerando un despacho existente"""
        try:
            cantidad = int(cantidad)
            if cantidad <= 0:
                raise ValidationError("La cantidad debe ser mayor a cero")
            
            # Si estamos editando un despacho existente
            if despacho_actual:
                # Obtenemos la cantidad ya asignada a este despacho
                cantidad_actual = self.items_despacho.filter(
                    despacho=despacho_actual
                ).aggregate(
                    total=Sum('cantidad')
                )['total'] or 0
                
                # La nueva cantidad disponible es:
                # (cantidad total) - (despachado en otros despachos) + (ya asignado a este despacho)
                disponible = (self.cantidad - 
                            (self.items_despacho.exclude(despacho=despacho_actual)
                             .aggregate(total=Sum('cantidad'))['total'] or 0) + 
                            cantidad_actual)
            else:
                # Para nuevo despacho, disponible es simplemente cantidad total - despachado
                disponible = self.cantidad_disponible
            
            if cantidad > disponible:
                raise ValidationError(
                    f"No hay suficiente stock. Disponible: {disponible}"
                )
            return True
                
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Cantidad inválida: {str(e)}")