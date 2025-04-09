from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from cargas.models import Carga
from despachos.models import Despacho
from clientes.models import Cliente
from proveedores.models import Proveedor

@login_required
def home(request):
    # Fechas para filtros
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    
    # Métricas principales
    total_clientes = Cliente.objects.count()
    total_proveedores = Proveedor.objects.count()
    
    # Estadísticas de cargas (optimizadas con select_related)
    cargas_recientes = Carga.objects.select_related('cliente').order_by('-fecha')[:5]
    total_cargas_mes = Carga.objects.filter(fecha__date__gte=inicio_mes).count()
    cargas_por_cliente = Carga.objects.values('cliente__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # Estadísticas de despachos (optimizadas)
    despachos_recientes = Despacho.objects.select_related('cliente').order_by('-fecha_creacion')[:5]
    total_despachos_mes = Despacho.objects.filter(fecha_creacion__date__gte=inicio_mes).count()
    estados_despachos = Despacho.objects.values('estado').annotate(
        total=Count('id')
    )
    
    context = {
        'hoy': hoy,
        'total_clientes': total_clientes,
        'total_proveedores': total_proveedores,
        'cargas_recientes': cargas_recientes,
        'total_cargas_mes': total_cargas_mes,
        'cargas_por_cliente': cargas_por_cliente,
        'despachos_recientes': despachos_recientes,
        'total_despachos_mes': total_despachos_mes,
        'estados_despachos': estados_despachos,
    }
    return render(request, 'main/home.html', context)