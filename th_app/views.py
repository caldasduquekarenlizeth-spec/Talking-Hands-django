from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from .models import Perfil, Modulo, Leccion, Ejercicio, Senna, Logro, ActividadAdmin
from .forms import formsPerfiles, formsModulos, formsLecciones, formsEjercicios, formsSennas, formsLogros

# Create your views here.

def registrar_actividad(accion, entidad, detalle):
    ActividadAdmin.objects.create(
        accion=accion,
        entidad=entidad,
        detalle=detalle
    )

def dashboard(request):
    # Conteos para las tarjetas de resumen
    total_usuarios = Perfil.objects.count()
    total_modulos = Modulo.objects.count()
    total_sennas = Senna.objects.count()
    total_logros = Logro.objects.count()

    # Obtener los últimos 5 usuarios registrados (ordenados por ID descendente)
    ultimos_usuarios = Perfil.objects.all().order_by('-id')[:5]

    context = {
        'total_usuarios': total_usuarios,
        'total_modulos': total_modulos,
        'total_sennas': total_sennas,
        'total_logros': total_logros,
        'ultimos_usuarios': ultimos_usuarios,
    }
    return render(request, 'th_app/inicio_admin.html', context)


def listar_perfiles(request):
    query = request.GET.get('q', '').strip()
    if query:
        perfiles = Perfil.objects.filter(
            models.Q(nombre__icontains=query) | models.Q(email__icontains=query)
        )
    else:
        perfiles = Perfil.objects.all()

    return render(request, 'th_app/listar_perfiles.html', {
        'perfiles': perfiles,
        'query': query
    })

def crear_perfil(request):
    form = formsPerfiles(request.POST or None)
    if request.method == 'POST'and form.is_valid(): 
            perfil = form.save()
            registrar_actividad('CREAR', 'Perfil', f'Creaste el perfil "{perfil.nombre}"')
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
        perfil = form.save()
        registrar_actividad('EDITAR', 'Perfil', f'Editaste el perfil "{perfil.nombre}"')
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('listar_perfiles')
    context = {
         'form': form,
         'titulo': f"Editar a {perfil.nombre}",
    }
    return render(request, 'th_app/crear_perfil.html', context)

def eliminar_perfil(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    if request.method == 'POST':
        nombre_perfil = perfil.nombre
        perfil.delete()
        registrar_actividad('ELIMINAR', 'Perfil', f'Eliminaste el perfil "{nombre_perfil}"')
        messages.success(request, 'Perfil eliminado correctamente')
        return redirect ('listar_perfiles')

    return render(request, 'th_app/eliminar_perfil.html', {'perfil': perfil})

def listar_modulos(request):
    query = request.GET.get('q', '').strip()
    if query:
        modulos = Modulo.objects.filter(
            models.Q(nombre__icontains=query) | models.Q(descripcion__icontains=query)
        )
    else:
        modulos = Modulo.objects.all()

    return render(request, 'th_app/listar_modulos.html', {
        'modulos': modulos,
        'query': query
    })

def crear_modulo(request):
    form = formsModulos(request.POST or None)
    if request.method == 'POST'and form.is_valid(): 
            modulo = form.save()
            registrar_actividad('CREAR', 'Módulo', f'Creaste el módulo "{modulo.nombre}"')
            messages.success(request, 'Modulo creado exitosamente.')
            return redirect('listar_modulos')
    context = {
         'form': form,
         'titulo': "Crear Nuevo Modulo",
    }
    
    return render(request, 'th_app/crear_modulo.html', context)

def editar_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)
    form = formsModulos(request.POST or None, instance=modulo)  
    if request.method == 'POST' and form.is_valid():
        modulo = form.save()
        registrar_actividad('EDITAR', 'Modulo', f'Editaste el modulo "{modulo.nombre}"')
        messages.success(request, 'Modulo actualizado exitosamente.')
        return redirect('listar_modulos')
    context = {
         'form': form,
         'titulo': f"Editar a {modulo.nombre}",
    }
    return render(request, 'th_app/crear_modulo.html', context)

def eliminar_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)
    if request.method == 'POST':
        nombre_modulo = modulo.nombre
        modulo.delete()
        registrar_actividad('ELIMINAR', 'modulo', f'Eliminaste el modulo "{nombre_modulo}"')
        messages.success(request, 'Modulo eliminado correctamente')
        return redirect ('listar_modulos')

    return render(request, 'th_app/eliminar_modulo.html', {'modulo': modulo})

def ver_lecciones(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)
    lecciones = Leccion.objects.filter(id_modulo=modulo).order_by('id')

    return render(request, 'th_app/listar_lecciones.html', {
        'modulo': modulo,
        'lecciones': lecciones,
    })

def crear_leccion(request):
    modulo_id = request.GET.get('modulo')
    modulo = None
    if modulo_id:
        modulo = get_object_or_404(Modulo, id=modulo_id)

    if request.method == 'POST':
            form = formsLecciones(request.POST)
            if form.is_valid():
                leccion = form.save()
                registrar_actividad('CREAR', 'Leccion', f'Creaste la leccion "{leccion.nombre}"')
                messages.success(request, 'Leccion creada exitosamente.')
                return redirect('listar_lecciones')
    else:
        initial_data = {'id_modulo': modulo} if modulo else {}
        form = formsLecciones(initial=initial_data)
    
    return render(request, 'th_app/crear_leccion.html', {
        'form': form,
        'modulo': modulo,
        'titulo': "Crear Nueva Lección",
    })

def editar_leccion(request, leccion_id):
    leccion = get_object_or_404(Leccion, id=leccion_id)
    modulo = leccion.id_modulo  
    
    if request.method == 'POST':
        form = formsLecciones(request.POST, instance=leccion)
        if form.is_valid():
            leccion = form.save()
            registrar_actividad('EDITAR', 'Leccion', f'Editaste la leccion "{leccion.nombre}"')
            messages.success(request, 'Leccion actualizada exitosamente.')
            return redirect('ver_lecciones', modulo_id=modulo.id)
    else:
        form = formsLecciones(instance=leccion)
    return render(request, 'th_app/crear_leccion.html', {
        'form': form,
        'modulo': modulo,
        'titulo': f"Editar a {leccion.nombre}",
    })

def eliminar_leccion(request, leccion_id):
    leccion = get_object_or_404(Leccion, id=leccion_id)
    if request.method == 'POST':
        nombre_leccion = leccion.nombre
        leccion.delete()
        registrar_actividad('ELIMINAR', 'Leccion', f'Eliminaste la leccion "{nombre_leccion}"')
        messages.success(request, 'Leccion eliminada correctamente')
        return redirect ('listar_lecciones')

    return render(request, 'th_app/eliminar_leccion.html', {'leccion': leccion})

def ver_ejercicios(request, leccion_id):
    leccion = get_object_or_404(Leccion, id=leccion_id)
    ejercicios = Ejercicio.objects.filter(leccion=leccion).order_by('id')

    return render(request, 'th_app/listar_ejercicios.html', {
        'leccion': leccion,
        'ejercicios': ejercicios,
    })

def crear_ejercicio(request):
    leccion_id = request.GET.get('leccion')
    leccion = None
    if leccion_id:
        leccion = get_object_or_404(Leccion, id=leccion_id)

    if request.method == 'POST':
        form = formsEjercicios(request.POST)
        if form.is_valid():
            ejercicio = form.save()
            registrar_actividad('CREAR', 'Ejercicio', f'Creaste el ejercicio "{ejercicio.nombre}"')
            messages.success(request, 'Ejercicio creado exitosamente.')
            return redirect('ver_lecciones_modulo', modulo_id=ejercicio.leccion.id_modulo.id)
    else:
        initial_data = {'leccion': leccion} if leccion else {}
        form = formsEjercicios(initial=initial_data)

    return render(request, 'th_app/crear_ejercicio.html', {
        'form': form,
        'leccion': leccion
    })

def editar_ejercicio(request, ejercicio_id):
    ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
    leccion = ejercicio.leccion  
    
    if request.method == 'POST':
        form = formsEjercicios(request.POST, instance=ejercicio)
        if form.is_valid():
            ejercicio = form.save()
            registrar_actividad('EDITAR', 'Ejercicio', f'Editaste el ejercicio "{ejercicio.nombre}"')
            messages.success(request, 'Ejercicio actualizado exitosamente.')
            return redirect('ver_ejercicios', leccion_id=leccion.id)
    else:
        form = formsEjercicios(instance=ejercicio)

    return render(request, 'th_app/crear_ejercicio.html', {
        'form': form,
        'leccion': leccion,
        'titulo': f"Editar Ejercicio: {ejercicio.pregunta[:30]}...",
    })

def eliminar_ejercicio(request, ejercicio_id):
    ejercicio = get_object_or_404(Ejercicio, id=ejercicio_id)
    leccion_id = ejercicio.leccion.id

    if request.method == 'POST':
        nombre_ejercicio = ejercicio.nombre
        ejercicio.delete()
        registrar_actividad('ELIMINAR', 'Ejercicio', f'Eliminaste el ejercicio "{nombre_ejercicio}"')
        messages.success(request, 'Ejercicio eliminado correctamente.')
        return redirect('ver_ejercicios_leccion', leccion_id=leccion_id)

    return render(request, 'th_app/eliminar_ejercicio.html', {'ejercicio': ejercicio})

def listar_sennas(request):
    query = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()

    sennas = Senna.objects.all()

    if query:
        sennas = Senna.objects.filter(
            models.Q(nombre__icontains=query) | models.Q(descripcion__icontains=query)
        )
    if categoria and categoria != 'Todas':
        sennas = sennas.filter(categoria_iexact=categoria)

    categorias = Senna.objects.values_list('categoria',flat=True).distinct()

    return render(request, 'th_app/listar_sennas.html', {
        'sennas': sennas,
        'query': query,
        'categoria_actual': categoria or 'Todas',
        'categoria': categorias,
    })

def crear_senna(request):
    if request.method == 'POST':
        form = formsSennas(request.POST, request.FILES)
        if form.is_valid():
            senna = form.save()
            registrar_actividad('CREAR', 'Seña', f'Creaste la seña "{senna.nombre}"')
            messages.success(request, 'Seña creada exitosamente.')
            return redirect('listar_sennas')
    else:
        form = formsSennas()

    return render(request, 'th_app/crear_senna.html', {
        'form': form,
        'titulo': 'Nueva Seña'
    })

def editar_senna(request, senna_id):
    senna = get_object_or_404(Senna, id=senna_id)

    if request.method == 'POST':
        form = formsSennas(request.POST, request.FILES, instance=senna)
        if form.is_valid():
            senna = form.save()
            registrar_actividad('EDITAR', 'Seña', f'Editaste la seña "{senna.nombre}"')
            messages.success(request, 'Seña actualizada exitosamente.')
            return redirect('listar_sennas')
    else:
        form = formsSennas(instance=senna)

    return render(request, 'th_app/crear_senna.html', {
        'form': form,
        'senna': senna,
        'titulo': f'Editar Seña: {senna.nombre}'
    })

def eliminar_senna(request, senna_id):
    senna = get_object_or_404(Senna, id=senna_id)
    if request.method == 'POST':
        if senna.imagen:
            senna.imagen.delete(save=False)
        nombre_sena = senna.nombre
        senna.delete()
        registrar_actividad('ELIMINAR', 'Seña', f'Eliminaste la seña "{nombre_sena}"')
        messages.success(request, 'Seña eliminada correctamente')
        return redirect ('listar_sennas')

    return render(request, 'th_app/eliminar_senna.html', {'senna': senna})

def listar_logros(request):
    logros = Logro.objects.all().order_by('id')
    total_logros = logros.count()
    puntaje_maximo = logros.aggregate(total_xp=Sum('puntos_xp'))['total_xp'] or 0
    total_lecciones = Leccion.objects.count()

    return render(request, 'th_app/listar_logros.html', {
        'logros': logros,
        'total_logros': total_logros,
        'puntaje_maximo': puntaje_maximo,
        'total_lecciones': total_lecciones,
    })

def crear_logro(request):
    if request.method == 'POST':
        form = formsLogros(request.POST)
        if form.is_valid():
            logro = form.save()
            registrar_actividad('CREAR', 'Logro', f'Creaste el logro "{logro.nombre}"')
            messages.success(request, 'Logro creado exitosamente.')
            return redirect('listar_logros')
    else:
        form = formsLogros()

    return render(request, 'th_app/crear_logro.html', {
        'form': form,
        'titulo': 'Crear Nuevo Logro'
    })

def editar_logro(request, logro_id):
    logro = get_object_or_404(Logro, id=logro_id)

    if request.method == 'POST':
        form = formsLogros(request.POST, instance=logro)
        if form.is_valid():
            logro = form.save()
            registrar_actividad('EDITAR', 'Logro', f'Editaste el logro "{logro.nombre}"')
            messages.success(request, 'Logro actualizado exitosamente.')
            return redirect('listar_logros')
    else:
        form = formsLogros(instance=logro)

    return render(request, 'th_app/crear_logro.html', {
        'form': form,
        'logro': logro,
        'titulo': f'Editar Logro: {logro.nombre}'
    })

def eliminar_logro(request, logro_id):
    logro = get_object_or_404(Logro, id=logro_id)

    if request.method == 'POST':
        nombre_logro = logro.nombre
        logro.delete()
        registrar_actividad('ELIMINAR', 'Logro', f'Eliminaste el logro "{nombre_logro}"')
        messages.success(request, 'Logro eliminado correctamente.')
        return redirect('listar_logros')

    return render(request, 'th_app/eliminar_logro.html', {'logro': logro})