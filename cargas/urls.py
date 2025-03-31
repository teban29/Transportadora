# cargas/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('registrar_carga/<int:cliente_id>/', views.registrar_carga, name='registrar_carga'),
    path('detalle_carga/<int:carga_id>/', views.detalle_carga, name='detalle_carga'),
    path('producto/<int:inventario_id>/codigo-barras/', views.generar_codigo_barras_producto, name='generar_codigo_barras_producto'),
    path('api/verificar-remision/', views.verificar_remision, name='verificar_remision'),
]