from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import IntegrityError
from .forms import CargaForm
from .utils import generar_codigo_barras_unico
from clientes.models import Cliente
from .models import Carga, InventarioCarga, Producto

import logging
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


logger = logging.getLogger(__name__)

@require_GET
def verificar_remision(request):
    remision = request.GET.get('remision', '').strip()
    logger.debug(f"Verificando remisión: {remision}")
    
    if not remision:
        return JsonResponse({'error': 'Remisión no proporcionada'}, status=400)
    
    try:
        carga_existente = Carga.objects.filter(remision=remision).first()
        response_data = {
            'exists': carga_existente is not None,
            'remision': remision,
            'existing_url': reverse('detalle_carga', args=[carga_existente.id]) if carga_existente else '',
        }
        return JsonResponse(response_data)
    
    except Exception as e:
        logger.error(f"Error verificando remisión: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def registrar_carga(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        carga_form = CargaForm(request.POST, request.FILES, cliente=cliente)
        
        try:
            if carga_form.is_valid():
                remision = carga_form.cleaned_data.get('remision')
                
                # Verificación de remisión duplicada
                if Carga.objects.filter(remision=remision).exists():
                    carga_existente = Carga.objects.get(remision=remision)
                    messages.error(
                        request,
                        f'❌ Error: La remisión {remision} ya está registrada en la carga {carga_existente.nombre}',
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

    
def detalle_carga(request, carga_id):
    carga = get_object_or_404(Carga, id=carga_id)  # Usar get() para obtener una única carga
    inventario = carga.inventario.all()  # Obtener el inventario de la carga
    return render(request, 'cargas/detalle_carga.html', {'carga': carga, 'inventario': inventario})


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

