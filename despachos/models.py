from django.db import models
from cargas.models import InventarioCarga
from clientes.models import Cliente
import random
import string
from django.db.models import F

# Create your models here.

class EstadoDespacho(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
class Despacho(models.Model):
    ESTADOS = (
        ('BODEGA', 'En bodega'),
        ('RUTA', 'En ruta'),
        ('ENTREGADO', 'Entregado'),
    )
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='despachos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    guia = models.CharField(max_length=20, unique=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BODEGA')
    valor_flete = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Despacho {self.guia} - {self.cliente.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.guia:
            # Generar guía con iniciales del cliente + 8 dígitos aleatorios
            iniciales = self.cliente.nombre[:3].upper()
            numeros = ''.join(random.choices(string.digits, k=8))
            self.guia = f"{iniciales}-{numeros}"
            
            # Verificar que la guía no exista
            while Despacho.objects.filter(guia=self.guia).exists():
                numeros = ''.join(random.choices(string.digits, k=8))
                self.guia = f"{iniciales}-{numeros}"
                
        super().save(*args, **kwargs)
        
class ItemDespacho(models.Model):
    despacho = models.ForeignKey(Despacho, on_delete=models.CASCADE, related_name='items')
    inventario = models.ForeignKey(InventarioCarga, on_delete=models.CASCADE, related_name='items_despacho')
    cantidad = models.PositiveIntegerField()
    
    def clean(self):
        """Validación adicional antes de guardar"""
        super().clean()
        self.inventario.verificar_disponibilidad(self.cantidad)
    
    def save(self, *args, **kwargs):
        """Sobrescribimos save para incluir validación"""
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.cantidad} x {self.inventario.producto.nombre} para {self.despacho.guia}"
    
    class Meta:
        verbose_name_plural = "Items de despacho"