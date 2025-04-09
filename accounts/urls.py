from django.contrib.auth import views as auth_views  # ¡Esta línea falta!
from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_list, name='user_list'),
    path('create/', views.user_create, name='user_create'),
    path('<int:pk>/edit/', views.user_update, name='user_update'),
    path('<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('<int:pk>/password/', views.user_password, name='user_password'),
    
    # URLs de autenticación (corregidas)
    path('login/', auth_views.LoginView.as_view(template_name='main/registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]