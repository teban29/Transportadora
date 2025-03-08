from django.shortcuts import render
from .models import Cliente
from .forms import ClienteForm

# Create your views here.

def index(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/index.html', {'clientes': clientes})

