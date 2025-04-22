from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm, CustomUserChangeForm, CustomPasswordChangeForm
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
import json


@login_required
@permission_required('auth.add_user', raise_exception=True)
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = True  # Asegura que el usuario esté activo
                    user.save()
                    form.save_m2m()  # Necesario para guardar los grupos (relación ManyToMany)
                    messages.success(request, 'Usuario creado exitosamente!')
                    return redirect('user_list')
            except Exception as e:
                messages.error(request, f'Error al crear usuario: {str(e)}')
        else:
            # Muestra errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/user_form.html', {'form': form})

@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado correctamente!')
            return redirect('user_list')
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form})

@login_required
@permission_required('auth.change_user', raise_exception=True)
@require_POST
def toggle_user_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    try:
        data = json.loads(request.body)
        user.is_active = data.get('is_active', False)
        user.save()
        return JsonResponse({
            'success': True,
            'new_status': 'Activo' if user.is_active else 'Inactivo',
            'status_class': 'text-success' if user.is_active else 'text-danger'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contraseña actualizada correctamente!')
            return redirect('user_list')
    else:
        form = CustomPasswordChangeForm(user)
    return render(request, 'accounts/user_password.html', {'form': form})

@login_required
@permission_required('auth.view_user', raise_exception=True)
def user_list(request):
    users = User.objects.all().order_by('-is_active', 'username')
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
@permission_required('auth.delete_user', raise_exception=True)
@require_http_methods(["DELETE", "POST"])
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Prevenir auto-eliminación
    if request.user == user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'No puedes eliminarte a ti mismo'
            }, status=400)
        messages.error(request, 'No puedes eliminarte a ti mismo')
        return redirect('user_list')
    
    try:
        with transaction.atomic():
            # Registra información antes de eliminar (opcional)
            deleted_info = {
                'username': user.username,
                'email': user.email,
                'deleted_by': request.user.username
            }
            
            user.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Usuario eliminado correctamente'
                })
            
            messages.success(request, 'Usuario eliminado correctamente')
            return redirect('user_list')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        messages.error(request, f'Error al eliminar usuario: {str(e)}')
        return redirect('user_list')