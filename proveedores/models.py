from django.db import models

# Create your models here.

class Proveedor(models.Model):
    nit = models.CharField(default='',max_length=255, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=255)
    contacto = models.CharField(default='',max_length=255, null=True,blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre}"