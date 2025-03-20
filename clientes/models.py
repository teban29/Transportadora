from django.db import models
from proveedores.models import Proveedor

# Create your models here.

class Cliente(models.Model):
    nit = models.CharField(max_length=255, default="", unique=True, blank=False)
    nombre = models.CharField(max_length=255, blank=False)
    email = models.EmailField()
    telefono = models.CharField(max_length=15)
    ciudad = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    proveedores = models.ManyToManyField(Proveedor, related_name="clientes", blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Nombre: {self.nombre}"
    
