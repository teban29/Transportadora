from django.shortcuts import render, redirect, get_object_or_404
from .models import Carga, InventarioCarga, Producto
from .forms import CargaForm
from clientes.models import Cliente


# Create your views here.

def registrar_carga(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        carga_form = CargaForm(request.POST, cliente=cliente)
        
        if carga_form.is_valid():
            # Guardar la carga
            carga = carga_form.save(commit=False)
            carga.cliente = cliente
            carga.save()
            
            # Procesar los productos
            productos = zip(
                request.POST.getlist('nombre'),
                request.POST.getlist('cantidad')
            )
            
            for nombre, cantidad in productos:
                if nombre and cantidad:  # Ignorar campos vacíos
                    producto, created = Producto.objects.get_or_create(nombre=nombre)
                    InventarioCarga.objects.create(
                        carga=carga,
                        producto=producto,
                        cantidad=cantidad
                    )
            
            return redirect('detalle_cliente', nombre=cliente.nombre)
    else:
        carga_form = CargaForm(cliente=cliente)
    
    return render(request, 'cargas/registrar_carga.html', {
        'carga_form': carga_form,
        'cliente': cliente,
    })
    
    
def detalle_carga(request, carga_id):
    carga = get_object_or_404(Carga, id=carga_id)  # Usar get() para obtener una única carga
    inventario = carga.inventario.all()  # Obtener el inventario de la carga
    return render(request, 'cargas/detalle_carga.html', {'carga': carga, 'inventario': inventario})
