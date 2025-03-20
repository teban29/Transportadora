from django.db import models
from django.db.models import Max
from clientes.models import Cliente
from proveedores.models import Proveedor

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
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (CARGA:{self.carga.id})"
    