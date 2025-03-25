from django.shortcuts import render, redirect, get_object_or_404
from .models import Proveedor
from .forms import ProveedorForm

# Create your views here.

def index(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'proveedores/index.html', {'proveedores': proveedores})


def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            return redirect('proveedores')
        
    else:
        form = ProveedorForm()
            
    return render(request, 'proveedores/crear_proveedor.html', {'form':form})

def detalle_proveedor(request, nombre):
    proveedor = get_object_or_404(Proveedor, nombre=nombre)
    return render(request, 'proveedores/detalle_proveedor.html', {'proveedor': proveedor})

def editar_proveedor(request, nombre):
    proveedor = get_object_or_404(Proveedor, nombre=nombre)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            proveedor = form.save()
            return redirect('proveedores')
        
    else:
        form = ProveedorForm(instance=proveedor)
            
    return render(request, 'proveedores/editar_proveedor.html', {'form':form})
    

def eliminar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, id=id)
    proveedor.delete()
    return redirect('proveedores')