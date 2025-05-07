from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from cargas.models import InventarioCarga, Carga
from clientes.models import Cliente
from .models import Despacho, ItemDespacho
from .forms import DespachoForm, ItemDespachoForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, F, Sum, Prefetch
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json



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
    items = despacho.items.all().annotate(
        total_item=F('cantidad')*F('valor_unitario')) 
    
    total_despacho = items.aggregate(total=Sum('total_item'))['total'] or 0
        
    context = {
        'despacho': despacho,
        'items': items,
        'total_despacho': total_despacho
    }
    return render(request, 'despachos/detalle_despacho.html', context)


def crear_despacho(request, cliente_nombre):
    cliente = get_object_or_404(Cliente, nombre=cliente_nombre)
    
    cargas_con_inventario = Carga.objects.filter(
        cliente=cliente
    ).prefetch_related(
        Prefetch('inventario', 
               queryset=InventarioCarga.objects.annotate(
                   disponible=F('cantidad') - Coalesce(
                       Sum('items_despacho__cantidad'), 
                       0
                   )
               ).filter(
                   disponible__gt=0
               ).select_related('producto'))
    ).order_by('-fecha')
    
    if request.method == 'POST':
        despacho_form = DespachoForm(request.POST)
        
        if despacho_form.is_valid():
            despacho = despacho_form.save(commit=False)
            despacho.cliente = cliente
            
            try:
                with transaction.atomic():
                    despacho.save()
                    items_data = []
                    
                    # Procesar items del formulario
                    for key, value in request.POST.items():
                        if key.startswith('items-') and key.endswith('-inventario'):
                            prefix = key.split('-')[1]
                            inventario_id = value
                            cantidad = request.POST.get(f'items-{prefix}-cantidad', '0')
                            valor_unitario = request.POST.get(f'items-{prefix}-valor_unitario', '0')
                            
                            if inventario_id and cantidad.isdigit():
                                cantidad = int(cantidad)
                                valor_unitario = float(valor_unitario) if valor_unitario.replace('.', '', 1).isdigit() else 0 
                                if cantidad > 0:
                                    items_data.append((inventario_id, cantidad, valor_unitario))
                    
                    if not items_data:
                        raise ValueError('Debe agregar al menos un producto')
                    
                    # Crear items si todo está bien
                    for inventario_id, cantidad, valor_unitario in items_data:
                        inventario = InventarioCarga.objects.get(id=inventario_id)
                        ItemDespacho.objects.create(
                            despacho=despacho,
                            inventario=inventario,
                            cantidad=cantidad,
                            valor_unitario=valor_unitario
                        )
                    
                    messages.success(request, 'Despacho creado exitosamente!')
                    return redirect('detalle_despacho', pk=despacho.pk)
            
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error al crear despacho: {str(e)}')
    
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


@require_http_methods(["GET", "POST"])
def seguimiento_despacho(request):
    """Vista para ingresar la guía de despacho"""
    guia = ''
    error = None
    
    if request.method == 'POST':
        guia = request.POST.get('guia', '').strip()
        if guia:
            if Despacho.objects.filter(guia=guia).exists():
                return redirect('detalle-seguimiento', guia=guia)  # Cambiado aquí
            error = "No se encontró un despacho con esta guía"
    
    return render(request, 'despachos/seguimiento.html', {
        'guia': guia,
        'error': error
    })
    
def detalle_seguimiento(request, guia):
    """Vista que muestra los detalles del despacho"""
    despacho = get_object_or_404(Despacho, guia=guia)
    items = despacho.items.select_related('inventario__producto')
    
    return render(request, 'despachos/detalle_seguimiento.html', {
        'despacho': despacho,
        'items': items
    })
    

@csrf_exempt
def escanear_codigo_barras(request, cliente_nombre):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            codigo = data.get('codigo')
            
            # Parsear el código según el formato que generamos (cliente|producto|carga|remisión)
            partes = codigo.split('|')
            if len(partes) != 4:
                return JsonResponse({'error': 'Formato de código inválido'}, status=400)
            
            cliente, producto_nombre, carga_nombre, remision = partes
            
            # Verificar que el cliente coincida
            cliente_obj = get_object_or_404(Cliente, nombre=cliente)
            if cliente_obj.nombre != cliente_nombre:
                return JsonResponse({'error': 'El producto no pertenece a este cliente'}, status=400)
            
            # Buscar el inventario correspondiente
            inventario = InventarioCarga.objects.filter(
                carga__nombre=carga_nombre,
                carga__remision=remision,
                producto__nombre=producto_nombre
            ).annotate(
                disponible=F('cantidad') - Coalesce(Sum('items_despacho__cantidad'), 0)
            ).first()
            
            if not inventario:
                return JsonResponse({'error': 'Producto no encontrado en inventario'}, status=404)
            
            if inventario.disponible <= 0:
                return JsonResponse({'error': 'No hay unidades disponibles'}, status=400)
            
            # Devolver los datos del producto
            return JsonResponse({
                'inventario_id': inventario.id,
                'producto': inventario.producto.nombre,
                'carga': inventario.carga.nombre,
                'disponible': inventario.disponible,
                'remision': inventario.carga.remision
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def editar_despacho(request, pk):
    despacho = get_object_or_404(Despacho, pk=pk)
    cliente = despacho.cliente
    
    if request.method == 'POST':
        despacho_form = DespachoForm(request.POST, instance=despacho)
        
        if despacho_form.is_valid():
            try:
                with transaction.atomic():
                    despacho = despacho_form.save()
                    items_data = []
                    items_a_eliminar = list(despacho.items.all())
                    
                    # Procesar items del formulario
                    for key, value in request.POST.items():
                        if key.startswith('items-') and key.endswith('-inventario'):
                            prefix = key.split('-')[1]
                            inventario_id = value
                            cantidad = request.POST.get(f'items-{prefix}-cantidad', '0')
                            valor_unitario = request.POST.get(f'items-{prefix}-valor_unitario', '0')
                            item_id = request.POST.get(f'items-{prefix}-id', '')
                            
                            if inventario_id and cantidad.isdigit():
                                cantidad = int(cantidad)
                                valor_unitario = float(valor_unitario) if valor_unitario.replace('.', '', 1).isdigit() else 0
                                
                                if cantidad > 0:
                                    items_data.append({
                                        'id': item_id,
                                        'inventario_id': inventario_id,
                                        'cantidad': cantidad,
                                        'valor_unitario': valor_unitario
                                    })
                    
                    if not items_data:
                        raise ValueError('Debe agregar al menos un producto')
                    
                    # Validar todos los items primero
                    for item_data in items_data:
                        inventario = InventarioCarga.objects.get(id=item_data['inventario_id'])
                        if item_data['id']:
                            item = ItemDespacho.objects.get(id=item_data['id'])
                            # Verificar el cambio neto
                            if item.inventario_id == int(item_data['inventario_id']):
                                diferencia = item_data['cantidad'] - item.cantidad
                                if diferencia > 0:
                                    inventario.verificar_disponibilidad(diferencia, despacho)
                            else:
                                # Cambió de inventario - validar todo
                                inventario.verificar_disponibilidad(item_data['cantidad'], despacho)
                        else:
                            inventario.verificar_disponibilidad(item_data['cantidad'], despacho)
                    
                    # Procesar cambios
                    for item_data in items_data:
                        inventario = InventarioCarga.objects.get(id=item_data['inventario_id'])
                        
                        if item_data['id']:
                            item = ItemDespacho.objects.get(id=item_data['id'])
                            items_a_eliminar.remove(item)
                            
                            # Actualizar el item
                            item.cantidad = item_data['cantidad']
                            item.valor_unitario = item_data['valor_unitario']
                            item.inventario = inventario
                            item.save()
                        else:
                            ItemDespacho.objects.create(
                                despacho=despacho,
                                inventario=inventario,
                                cantidad=item_data['cantidad'],
                                valor_unitario=item_data['valor_unitario']
                            )
                    
                    # Eliminar items que ya no están
                    for item in items_a_eliminar:
                        item.delete()
                    
                    messages.success(request, 'Despacho actualizado exitosamente!')
                    return redirect('detalle_despacho', pk=despacho.pk)
            
            except Exception as e:
                messages.error(request, f'Error al actualizar despacho: {str(e)}')
    
    # Obtener cargas con inventario disponible o ya en este despacho
    cargas_con_inventario = Carga.objects.filter(
        cliente=cliente
    ).prefetch_related(
        Prefetch('inventario', 
            queryset=InventarioCarga.objects.annotate(
                disponible=Coalesce(
                    F('cantidad') - Sum('items_despacho__cantidad', 
                    filter=~Q(items_despacho__despacho=despacho)),
                    F('cantidad')
                )
            ).filter(
                Q(disponible__gt=0) | Q(items_despacho__despacho=despacho)
            ).distinct()
        )
    ).distinct()
    
    context = {
        'despacho_form': DespachoForm(instance=despacho),
        'despacho': despacho,
        'cliente': cliente,
        'cargas_con_inventario': cargas_con_inventario,
        'items_actuales': despacho.items.select_related('inventario', 'inventario__producto').all()
    }
    return render(request, 'despachos/editar_despacho.html', context)