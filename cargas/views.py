from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import IntegrityError
from .forms import CargaForm
from .utils import generar_codigo_barras_unico
from clientes.models import Cliente
from proveedores.models import Proveedor
from .models import Carga, InventarioCarga, Producto
from django.contrib.auth.decorators import login_required
import logging
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.db.models import Q
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


@login_required

def historial_cargas(request):
    # Obtener todas las cargas ordenadas por fecha descendente
    cargas = Carga.objects.select_related('cliente', 'proveedor').order_by('-fecha')
    
    # Aplicar filtros
    cliente_id = request.GET.get('cliente')
    proveedor_id = request.GET.get('proveedor')
    fecha = request.GET.get('fecha')
    busqueda = request.GET.get('q')
    
    if cliente_id:
        cargas = cargas.filter(cliente_id=cliente_id)
    if proveedor_id:
        cargas = cargas.filter(proveedor_id=proveedor_id)
    if fecha:
        try:
            fecha_date = datetime.strptime(fecha, '%Y-%m-%d').date()
            cargas = cargas.filter(fecha__date=fecha_date)
        except ValueError:
            pass
    if busqueda:
        cargas = cargas.filter(
            Q(nombre__icontains=busqueda) |
            Q(remision__icontains=busqueda) |
            Q(observaciones__icontains=busqueda)
        )
    
    context = {
        'cargas': cargas,
        'clientes': Cliente.objects.all().order_by('nombre'),
        'proveedores': Proveedor.objects.all().order_by('nombre'),
        'query_params': request.GET.urlencode().replace('page=', '')  # Para paginación
    }
    return render(request, 'cargas/historial_cargas.html', context)

@require_GET
def verificar_remision(request):
    remision = request.GET.get('remision', '').strip()
    cliente_id = request.GET.get('cliente_id', '').strip()
    logger.debug(f"Verificando remisión: {remision} para cliente: {cliente_id}")
    
    if not remision:
        return JsonResponse({'error': 'Remisión no proporcionada'}, status=400)
    
    try:
        if cliente_id:
            carga_existente = Carga.objects.filter(remision=remision, cliente_id=cliente_id).first()
        else:
            carga_existente = None
            
        response_data = {
            'exists': carga_existente is not None,
            'remision': remision,
            'existing_url': reverse('detalle_carga', args=[carga_existente.id]) if carga_existente else '',
        }
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error verificando remisión: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def registrar_carga(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        carga_form = CargaForm(request.POST, request.FILES, cliente=cliente)
        
        try:
            if carga_form.is_valid():
                remision = carga_form.cleaned_data.get('remision')
                
                # Verificación de remisión duplicada
                if Carga.objects.filter(remision=remision, cliente=cliente).exists():
                    carga_existente = Carga.objects.get(remision=remision, cliente=cliente)
                    messages.error(
                        request,
                        f'❌ Error: La remisión {remision} ya está registrada para este cliente en la carga {carga_existente.nombre}',
                        extra_tags='danger'
                    )
                    return render(request, 'cargas/registrar_carga.html', {
                        'carga_form': carga_form,
                        'cliente': cliente,
                    })
                
                # Guardar la carga
                carga = carga_form.save(commit=False)
                carga.cliente = cliente
                carga.save()
                
                # Procesar productos - CORRECCIÓN CLAVE AQUÍ
                nombres_productos = request.POST.getlist('nombre')
                cantidades_productos = request.POST.getlist('cantidad')
                
                for nombre, cantidad in zip(nombres_productos, cantidades_productos):
                    if nombre and cantidad:  # Solo si ambos campos tienen valores
                        # Crear o obtener el producto
                        producto, created = Producto.objects.get_or_create(nombre=nombre)
                        # Crear relación en InventarioCarga
                        InventarioCarga.objects.create(
                            carga=carga,
                            producto=producto,
                            cantidad=cantidad
                        )
                
                messages.success(request, '✅ Carga registrada exitosamente!')
                return redirect('detalle_carga', carga_id=carga.id)
                
        except IntegrityError as e:
            messages.error(
                request,
                '❌ Error crítico al registrar la carga. Por favor intente nuevamente.',
                extra_tags='danger'
            )
            # Opcional: Log del error para debugging
            print(f"Error de integridad: {str(e)}")
    
    else:
        carga_form = CargaForm(cliente=cliente)
    
    return render(request, 'cargas/registrar_carga.html', {
        'carga_form': carga_form,
        'cliente': cliente,
    })

@login_required
def detalle_carga(request, carga_id):
    carga = get_object_or_404(Carga, id=carga_id)  # Usar get() para obtener una única carga
    inventario = carga.inventario.all()  # Obtener el inventario de la carga
    return render(request, 'cargas/detalle_carga.html', {'carga': carga, 'inventario': inventario})

@login_required
def generar_codigo_barras_producto(request, inventario_id):
    inventario = get_object_or_404(InventarioCarga, id=inventario_id)
    
    try:
        pdf_buffer = generar_codigo_barras_unico(inventario)
        response = HttpResponse(
            pdf_buffer.getvalue(),
            content_type='application/pdf'
        )
        filename = f"CODIGO_{inventario.producto.nombre}_{inventario.carga.nombre}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        return HttpResponse(f"Error generando código: {str(e)}", status=500)


@require_GET
def verificar_inventario_disponible(request):
    """ Verificar si el inventario de la carga está disponible para el despacho """
    
    inventario_id = request.GET.get('inventario_id')
    cantidad_requerida = int(request.GET.get('cantidad', 0))
    
    inventario = get_object_or_404(InventarioCarga, id=inventario_id)
    disponible = inventario.cantidad_disponible()
    
    return JsonResponse({
        'disponible': disponible,
        'suficiente': disponible >= cantidad_requerida,
        'producto': inventario.producto.nombre,
        'carga' : inventario.carga.nombre,
        })