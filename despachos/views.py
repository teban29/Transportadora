from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from cargas.models import InventarioCarga
from clientes.models import Cliente
from .models import Despacho, ItemDespacho
from .forms import DespachoForm, ItemDespachoForm
from django.core.paginator import Paginator


def lista_despachos(request, cliente_nombre=None):
    """Lista todos los despachos, con filtro opcional por cliente"""
    despachos = Despacho.objects.all().order_by('-fecha_creacion')
    cliente = None
    estados = Despacho.ESTADOS
    
    # Filtro por cliente
    if cliente_nombre:
        cliente = get_object_or_404(Cliente, nombre=cliente_nombre)
        despachos = despachos.filter(cliente=cliente)
    
    # Filtro por estado
    estado_filter = request.GET.get('estado')
    if estado_filter:
        despachos = despachos.filter(estado=estado_filter)
    
    # Estadísticas (solo cuando se filtra por cliente)
    stats = {
        'total_despachos': 0,
        'en_bodega': 0,
        'en_ruta': 0,
        'entregados': 0
    }
    
    if cliente:
        stats['total_despachos'] = despachos.count()
        stats['en_bodega'] = despachos.filter(estado='BODEGA').count()
        stats['en_ruta'] = despachos.filter(estado='RUTA').count()
        stats['entregados'] = despachos.filter(estado='ENTREGADO').count()
    
    # Paginación
    paginator = Paginator(despachos, 15)  # 15 items por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'despachos': page_obj,
        'cliente': cliente,
        'clientes': Cliente.objects.all(),
        'estados': estados,
        **stats
    }
    return render(request, 'despachos/lista_despachos.html', context)

def detalle_despacho(request, pk):
    despacho = get_object_or_404(Despacho, pk=pk)
    items = despacho.items.all()
    
    context = {
        'despacho':despacho,
        'items':items
    }
    
    return render(request, 'despachos/detalle_despacho.html', context)

def crear_despacho(request, cliente_nombre):
    """Crea un nuevo despacho para un cliente específico"""
    cliente = get_object_or_404(Cliente, nombre=cliente_nombre)
    inventarios_disponibles = InventarioCarga.objects.filter(
        carga__cliente=cliente
    ).select_related('producto', 'carga')
    
    if request.method == 'POST':
        despacho_form = DespachoForm(request.POST)
        
        if despacho_form.is_valid():
            # Crear el despacho
            despacho = despacho_form.save(commit=False)
            despacho.cliente = cliente
            despacho.save()
            
            # Procesar items del despacho
            for item in request.POST.getlist('items'):
                inventario_id = request.POST.get(f'item_{item}_inventario')
                cantidad = request.POST.get(f'item_{item}_cantidad')
                
                if inventario_id and cantidad:
                    inventario = get_object_or_404(InventarioCarga, id=inventario_id)
                    
                    # Validar cantidad disponible
                    if int(cantidad) > inventario.cantidad_disponible:
                        messages.error(
                            request,
                            f'No hay suficiente stock de {inventario.producto.nombre}. Disponible: {inventario.cantidad_disponible}'
                        )
                        despacho.delete()  # Eliminar el despacho creado
                        return redirect('crear_despacho', cliente_nombre=cliente_nombre)
                    
                    # Crear item de despacho
                    ItemDespacho.objects.create(
                        despacho=despacho,
                        inventario=inventario,
                        cantidad=cantidad
                    )
            
            messages.success(request, 'Despacho creado exitosamente!')
            return redirect('detalle_despacho', pk=despacho.pk)
    else:
        despacho_form = DespachoForm()
    
    context = {
        'despacho_form': despacho_form,
        'cliente': cliente,
        'inventarios_disponibles': inventarios_disponibles
    }
    return render(request, 'despachos/crear_despacho.html', context)

def cambiar_estado_despacho(request, pk, nuevo_estado):
    """Cambia el estado de un despacho"""
    despacho = get_object_or_404(Despacho, pk=pk)
    estados_permitidos = [choice[0] for choice in Despacho.ESTADOS]
    
    if nuevo_estado in estados_permitidos:
        despacho.estado = nuevo_estado
        despacho.save()
        messages.success(request, f'Estado actualizado a: {despacho.get_estado_display()}')
    else:
        messages.error(request, 'Estado no válido')
    
    return redirect('detalle_despacho', pk=pk)