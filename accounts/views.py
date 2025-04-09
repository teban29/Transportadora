from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm, CustomUserChangeForm, CustomPasswordChangeForm

@login_required
@permission_required('auth.add_user', raise_exception=True)
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('user_list')
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
            return redirect('user_list')
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form})

@login_required
@permission_required('auth.delete_user', raise_exception=True)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.is_active = False  # Desactivar en lugar de borrar
        user.save()
        return redirect('user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})

@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = CustomPasswordChangeForm(user)
    return render(request, 'accounts/user_password.html', {'form': form})

@login_required
@permission_required('auth.view_user', raise_exception=True)
def user_list(request):
    users = User.objects.all().order_by('-is_active', 'username')
    return render(request, 'accounts/user_list.html', {'users': users})