from django.db import models

# Create your models here.

class Cliente(models.Model):
    nombre = models.CharField(max_length=255)
    email = models.EmailField()
    telefono = models.CharField(max_length=15)
    ciudad = models.CharField(max_length=255)
    direccion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Nombre: {self.nombre}"
    
