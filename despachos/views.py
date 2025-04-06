from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from cargas.models import InventarioCarga, Carga
from clientes.models import Cliente
from .models import Despacho, ItemDespacho
from .forms import DespachoForm, ItemDespachoForm
from django.core.paginator import Paginator
from django.db import transaction


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
    items = despacho.items.all()  # Esto usa el related_name='items' del ForeignKey
    
    context = {
        'despacho': despacho,
        'items': items
    }
    return render(request, 'despachos/detalle_despacho.html', context)


def crear_despacho(request, cliente_nombre):
    cliente = get_object_or_404(Cliente, nombre=cliente_nombre)
    cargas_con_inventario = Carga.objects.filter(
        cliente=cliente
    ).prefetch_related(
        'inventario__producto'
    ).order_by('-fecha')
    
    if request.method == 'POST':
        despacho_form = DespachoForm(request.POST)
        
        if despacho_form.is_valid():
            despacho = despacho_form.save(commit=False)
            despacho.cliente = cliente
            
            try:
                with transaction.atomic():  # Transacción atómica
                    # Guardamos primero el despacho
                    despacho.save()
                    
                    items_creados = False
                    items_data = []
                    
                    # Procesamos los items del formulario
                    for key, value in request.POST.items():
                        if key.startswith('items-') and key.endswith('-inventario'):
                            prefix = key.split('-')[1]
                            inventario_id = value
                            cantidad_str = request.POST.get(f'items-{prefix}-cantidad', '0')
                            
                            if inventario_id and cantidad_str.isdigit():
                                cantidad = int(cantidad_str)
                                if cantidad > 0:
                                    items_data.append((inventario_id, cantidad))
                    
                    # Validamos que haya al menos un producto
                    if not items_data:
                        raise ValueError('Debe agregar al menos un producto')
                    
                    # Procesamos los items validados
                    for inventario_id, cantidad in items_data:
                        inventario = get_object_or_404(InventarioCarga, id=inventario_id)
                        
                        # Validación de stock disponible
                        if cantidad > inventario.cantidad_disponible:
                            raise ValueError(
                                f'No hay suficiente stock de {inventario.producto.nombre}. '
                                f'Disponible: {inventario.cantidad_disponible}, '
                                f'Solicitado: {cantidad}'
                            )
                        
                        # Restamos del inventario
                        inventario.restar_stock(cantidad)
                        
                        # Creamos el item de despacho
                        ItemDespacho.objects.create(
                            despacho=despacho,
                            inventario=inventario,
                            cantidad=cantidad
                        )
                        items_creados = True
                    
                    messages.success(request, 'Despacho creado exitosamente!')
                    return redirect('detalle_despacho', pk=despacho.pk)
            
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('crear_despacho', cliente_nombre=cliente.nombre)
            
            except Exception as e:
                messages.error(
                    request, 
                    f'Error al crear el despacho: {str(e)}. '
                    'Por favor intente nuevamente.'
                )
                return redirect('crear_despacho', cliente_nombre=cliente.nombre)
    
    else:
        despacho_form = DespachoForm()
    
    context = {
        'despacho_form': despacho_form,
        'cliente': cliente,
        'cargas_con_inventario': cargas_con_inventario
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