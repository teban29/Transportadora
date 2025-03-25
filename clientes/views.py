from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente
from .forms import ClienteForm
from cargas.models import Carga
from proveedores.models import Proveedor

# Create your views here.

def index(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/index.html', {'clientes': clientes})


def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            
            # Obtener todos los proveedores seleccionados
            proveedores_seleccionados = request.POST.getlist('proveedores[]')  # Usar getlist para múltiples valores
            cliente.proveedores.set(proveedores_seleccionados)  # Asignar los proveedores al cliente
            
            return redirect('clientes')
    else:
        form = ClienteForm()
    
    # Obtener todos los proveedores para mostrar en el template
    proveedores = Proveedor.objects.all()
    
    return render(request, 'clientes/crear_cliente.html', {
        'form': form,
        'proveedores': proveedores,
    })          
    

def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    proveedores = Proveedor.objects.all()
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()
            proveedores_seleccionados = request.POST.getlist('proveedores[]')
            cliente.proveedores.set(proveedores_seleccionados)
            return redirect('clientes')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'clientes/editar_cliente.html', {
        'form': form,
        'cliente': cliente,
        'proveedores': proveedores,
    })

def detalle_cliente(request, nombre):
    cliente = get_object_or_404(Cliente, nombre=nombre)
    cargas = Carga.objects.filter(cliente=cliente)
    
    orden = request.GET.get('orden')
    if orden == 'antiguo':
        cargas = cargas.order_by('fecha')
    else:
        cargas = cargas.order_by('-fecha')
        
    fecha = request.GET.get('fecha')
    if fecha:
        cargas = cargas.filter(fecha__date=fecha)
        
    buscar = request.GET.get('buscar')
    if buscar:
        cargas = cargas.filter(nombre__icontains=buscar)
    
    
    return render(request, 'clientes/detalle_cliente.html', {'cliente': cliente, 'cargas':cargas})

def eliminar_cliente(request, id):
    cliente = Cliente.objects.get(id=id)
    cliente.delete()
    return redirect('clientes')

