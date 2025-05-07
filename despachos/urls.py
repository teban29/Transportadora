from django.urls import path
from . import views


urlpatterns = [
    path('', views.lista_despachos, name='lista_despachos'),
    path('cliente/<str:cliente_nombre>/', views.lista_despachos, name='lista_despachos_cliente'),
    path('<int:pk>/', views.detalle_despacho, name='detalle_despacho'),
    path('crear/cliente/<str:cliente_nombre>/', views.crear_despacho, name='crear_despacho'),
    path('editar/<int:pk>/', views.editar_despacho, name='editar_despacho'),
    path('<int:pk>/cambiar-estado/<str:nuevo_estado>/', views.cambiar_estado_despacho, name='cambiar_estado_despacho'),
    
    #escaneo de códigos de barras
    path('<str:cliente_nombre>/escanear/', views.validar_codigo_barras, name='validar_codigo'),
    
    #URLS para seguimiento de despachos
    path('seguimiento/', views.seguimiento_despacho, name='seguimiento-despacho'),
    path('seguimiento/<str:guia>/', views.detalle_seguimiento, name='detalle-seguimiento'),\
    
]