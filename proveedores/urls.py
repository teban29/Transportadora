from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='proveedores'),
    path('crear_proveedor/', views.crear_proveedor, name='crear_proveedor'),
]