from django.db import models

# Create your models here.

class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre}"