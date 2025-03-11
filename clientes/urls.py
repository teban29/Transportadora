from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='clientes'),
    path('crear_cliente/', views.crear_cliente, name='crear_cliente'),
    path('editar_cliente/<int:id>/', views.crear_cliente, name='editar_cliente'),
    path('eliminar_cliente/<int:id>/', views.eliminar_cliente, name='eliminar_cliente'),
]