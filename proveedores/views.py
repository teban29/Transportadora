from django.shortcuts import render, redirect
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

