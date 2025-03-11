from django.contrib import admin
from .models import Cliente
from proveedores.models import Proveedor

# Register your models here.

class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre'] 
    filter_horizontal = ['proveedores']

admin.site.register(Cliente, ClienteAdmin)