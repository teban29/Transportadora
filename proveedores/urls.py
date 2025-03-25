from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='proveedores'),
    path('crear_proveedor/', views.crear_proveedor, name='crear_proveedor'),
    path('<str:nombre>/', views.detalle_proveedor, name='detalle_proveedor'),
    path('<str:nombre>/editar/', views.editar_proveedor, name='editar_proveedor'), 
    path('<int:id>/eliminar/', views.eliminar_proveedor, name='eliminar_proveedor'),
]