from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='clientes'),
    path('crear_cliente/', views.crear_cliente, name='crear_cliente'),
    path('<int:id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('<int:id>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),
    path('<str:nombre>/', views.detalle_cliente ,name="detalle_cliente")
]