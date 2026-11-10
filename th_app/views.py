from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Perfil, Modulo, Leccion, Ejercicio, Senna, Logro
from .forms import formsPerfiles

# Create your views here.

def listar_perfiles(request):
    perfiles = Perfil.objects.all()
    return render(request, 'th_app/listar_perfiles.html', {'perfiles': perfiles})

def crear_perfil(request):
    form = formsPerfiles(request.POST or None)
    if request.method == 'POST'and form.is_valid(): 
            form.save()
            messages.success(request, 'Perfil creado exitosamente.')
            return redirect('listar_perfiles')
    context = {
         'form': form,
         'titulo': "Crear Nuevo Perfil",
    }
    
    return render(request, 'th_app/crear_perfil.html', context)

def editar_perfil(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    form = formsPerfiles(request.POST or None, instance=perfil)
    form.fields['email'].disabled = True  
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('listar_perfiles')
    context = {
         'form': form,
         'titulo': f"Editar a {perfil.nombre}",
    }
    return render(request, 'th_app/crear_perfil.html', context)