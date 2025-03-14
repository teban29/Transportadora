from django.urls import path
from . import views

urlpatterns = [
    path('registrar_carga/<int:cliente_id>/', views.registrar_carga, name='registrar_carga'),
    path('detalle_carga/<int:carga_id>/', views.detalle_carga, name='detalle_carga'),  # Usar carga_id
]