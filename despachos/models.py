from django.db import models
from cargas.models import InventarioCarga
from clientes.models import Cliente
import random
import string
from django.db.models import F, Sum
from django.core.exceptions import ValidationError

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
    placa_camion = models.CharField(max_length=20, default='')
    nombre_conductor = models.CharField(max_length=50, blank=True, null=True, default='')
    
    
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
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    
    def clean(self):
        """Validación adicional antes de guardar"""
        super().clean()
        
        if not self.pk or (self.pk and self.inventario_id != ItemDespacho.objects.get(pk=self.pk).inventario_id):
            self.inventario.verificar_disponibilidad(self.cantidad)
            
        else:
            original = ItemDespacho.objects.get(pk=self.pk)
            diferencia = self.cantidad - original.cantidad
            if diferencia > 0:
                self.inventario.verificar_disponibilidad(diferencia)
    
    @property
    def valor_total(self):
        """Devuelve el valor total del item despacho"""
        return self.cantidad * self.valor_unitario
    
    def save(self, *args, **kwargs):
            """Sobrescribimos save para incluir validación"""
            # Primero validamos
            self.clean()
            
            # Si es una actualización, necesitamos manejar el cambio de cantidades
            if self.pk:
                original = ItemDespacho.objects.get(pk=self.pk)
                # Si cambió el inventario, debemos "devolver" la cantidad original
                if original.inventario_id != self.inventario_id:
                    original.inventario.cantidad += original.cantidad
                    original.inventario.save()
                    # Y restar del nuevo inventario
                    self.inventario.cantidad -= self.cantidad
                    self.inventario.save()
                # Si solo cambió la cantidad
                elif original.cantidad != self.cantidad:
                    diferencia = self.cantidad - original.cantidad
                    self.inventario.cantidad -= diferencia
                    self.inventario.save()
            else:
                # Para items nuevos, simplemente restamos del inventario
                self.inventario.cantidad -= self.cantidad
                self.inventario.save()
            
            super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Al eliminar un item, devolvemos la cantidad al inventario"""
        self.inventario.cantidad += self.cantidad
        self.inventario.save()
        super().delete(*args, **kwargs)
        
    def __str__(self):
        return f"{self.cantidad} x {self.inventario.producto.nombre} para {self.despacho.guia}"
    
    class Meta:
        verbose_name_plural = "Items de despacho"