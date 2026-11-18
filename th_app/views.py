import csv
import random
from django.db import models
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from .models import Perfil, Modulo, Leccion, Ejercicio, Senna, Logro, ActividadAdmin
from .forms import (
    formsPerfiles,
    formsModulos,
    formsLecciones,
    formsEjercicios,
    formsSennas,
    formsLogros,
    formsEditarPerfilPropio,
)


# ==========================================
# UTILIDADES Y AUDITORÍA
# ==========================================

def registrar_actividad(accion, entidad, detalle, perfil=None):
    if perfil is None:
        perfil = Perfil.objects.filter(rol='ADMIN').first() or Perfil.objects.first()

    ActividadAdmin.objects.create(
        perfil=perfil,
        accion=accion,
        entidad=entidad,
        detalle=detalle
    )


# ==========================================
# VISTAS PÚBLICAS Y AUTENTICACIÓN
# ==========================================

def inicio(request):
    return render(request, "th_app/index.html")


def registro_aprendiz(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Ese nombre de usuario ya está en uso.")
            return redirect("registro")

        user = User.objects.create_user(username=username, email=email, password=password)

        Perfil.objects.create(
            usuario=user,
            nombre=username[:25],
            email=email,
            puntos_xp=0,
            rol='APRENDIZ'
        )

        login(request, user)
        messages.success(request, f"¡Bienvenido {username}! Ya puedes empezar a aprender lengua de señas colombiana.")
        return redirect("dashboard_aprendiz")

    return render(request, "th_app/aprendiz/register.html")


# ==========================================
# VISTAS DE ADMINISTRACIÓN (PANEL ADMIN)
# ==========================================

def dashboard(request):
    total_usuarios = Perfil.objects.count()
    total_modulos = Modulo.objects.count()
    total_sennas = Senna.objects.count()
    total_logros = Logro.objects.count()
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
    if request.method == 'POST' and form.is_valid():
        perfil = form.save()
        registrar_actividad('CREAR', 'Perfil', f'Creaste el perfil "{perfil.nombre}"')
        messages.success(request, 'Perfil creado exitosamente.')
        return redirect('listar_perfiles')

    return render(request, 'th_app/crear_perfil.html', {
        'form': form,
        'titulo': "Crear Nuevo Perfil",
    })


def editar_perfil(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    form = formsPerfiles(request.POST or None, instance=perfil)
    form.fields['email'].disabled = True
    if request.method == 'POST' and form.is_valid():
        perfil = form.save()
        registrar_actividad('EDITAR', 'Perfil', f'Editaste el perfil "{perfil.nombre}"')
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('listar_perfiles')

    return render(request, 'th_app/crear_perfil.html', {
        'form': form,
        'titulo': f"Editar a {perfil.nombre}",
    })


def eliminar_perfil(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)
    if request.method == 'POST':
        nombre_perfil = perfil.nombre
        perfil.delete()
        registrar_actividad('ELIMINAR', 'Perfil', f'Eliminaste el perfil "{nombre_perfil}"')
        messages.success(request, 'Perfil eliminado correctamente')
        return redirect('listar_perfiles')

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
    if request.method == 'POST' and form.is_valid():
        modulo = form.save()
        registrar_actividad('CREAR', 'Módulo', f'Creaste el módulo "{modulo.nombre}"')
        messages.success(request, 'Modulo creado exitosamente.')
        return redirect('listar_modulos')

    return render(request, 'th_app/crear_modulo.html', {
        'form': form,
        'titulo': "Crear Nuevo Modulo",
    })


def editar_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)
    form = formsModulos(request.POST or None, instance=modulo)
    if request.method == 'POST' and form.is_valid():
        modulo = form.save()
        registrar_actividad('EDITAR', 'Modulo', f'Editaste el modulo "{modulo.nombre}"')
        messages.success(request, 'Modulo actualizado exitosamente.')
        return redirect('listar_modulos')

    return render(request, 'th_app/crear_modulo.html', {
        'form': form,
        'titulo': f"Editar a {modulo.nombre}",
    })


def eliminar_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)
    if request.method == 'POST':
        nombre_modulo = modulo.nombre
        modulo.delete()
        registrar_actividad('ELIMINAR', 'modulo', f'Eliminaste el modulo "{nombre_modulo}"')
        messages.success(request, 'Modulo eliminado correctamente')
        return redirect('listar_modulos')

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
    modulo = get_object_or_404(Modulo, id=modulo_id) if modulo_id else None

    if request.method == 'POST':
        form = formsLecciones(request.POST)
        if form.is_valid():
            leccion = form.save()
            registrar_actividad('CREAR', 'Leccion', f'Creaste la leccion "{leccion.nombre}"')
            messages.success(request, 'Leccion creada exitosamente.')
            return redirect('ver_lecciones', modulo_id=leccion.id_modulo.id)
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
    modulo_id = leccion.id_modulo.id
    if request.method == 'POST':
        nombre_leccion = leccion.nombre
        leccion.delete()
        registrar_actividad('ELIMINAR', 'Leccion', f'Eliminaste la leccion "{nombre_leccion}"')
        messages.success(request, 'Leccion eliminada correctamente')
        return redirect('ver_lecciones', modulo_id=modulo_id)

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
    leccion = get_object_or_404(Leccion, id=leccion_id) if leccion_id else None

    if request.method == 'POST':
        form = formsEjercicios(request.POST)
        if form.is_valid():
            ejercicio = form.save()
            registrar_actividad('CREAR', 'Ejercicio', f'Creaste el ejercicio "{ejercicio.pregunta[:40]}"')
            messages.success(request, 'Ejercicio creado exitosamente.')
            return redirect('ver_ejercicios', leccion_id=ejercicio.leccion.id)
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
            registrar_actividad('EDITAR', 'Ejercicio', f'Editaste el ejercicio "{ejercicio.pregunta[:40]}"')
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
        texto_ejercicio = ejercicio.pregunta[:40]
        ejercicio.delete()
        registrar_actividad('ELIMINAR', 'Ejercicio', f'Eliminaste el ejercicio "{texto_ejercicio}"')
        messages.success(request, 'Ejercicio eliminado correctamente.')
        return redirect('ver_ejercicios', leccion_id=leccion_id)

    return render(request, 'th_app/eliminar_ejercicio.html', {'ejercicio': ejercicio})


def listar_sennas(request):
    query = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()

    sennas = Senna.objects.all()

    if query:
        sennas = sennas.filter(
            models.Q(nombre__icontains=query) | models.Q(descripcion__icontains=query)
        )
    if categoria and categoria != 'Todas':
        sennas = sennas.filter(categoria__iexact=categoria)

    categorias = Senna.objects.values_list('categoria', flat=True).distinct()

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
        return redirect('listar_sennas')

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


def ver_perfil(request):
    perfil = Perfil.objects.filter(rol='ADMIN').first() or Perfil.objects.first()

    if not perfil:
        perfil = Perfil.objects.create(
            nombre="Admin1",
            email="admin@talkinghands.com",
            puntos_xp=0,
            rol="ADMIN"
        )
    actividades = ActividadAdmin.objects.all()[:10]

    return render(request, 'th_app/perfil.html', {
        'perfil': perfil,
        'actividades': actividades,
    })


def editar_perfil_propio(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)

    if request.method == 'POST':
        form = formsEditarPerfilPropio(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            registrar_actividad('EDITAR', 'Módulo', f'Actualizaste la información de tu perfil "{perfil.nombre}"')
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('ver_perfil')
    else:
        form = formsEditarPerfilPropio(instance=perfil)

    return render(request, 'th_app/editar_perfil.html', {
        'form': form,
        'perfil': perfil,
    })


def cambiar_contrasena(request):
    usuario = request.user if request.user.is_authenticated else (
        User.objects.filter(is_superuser=True).first() or User.objects.first()
    )

    if not usuario:
        messages.error(request, 'No hay ningún usuario administrador registrado en el sistema.')
        return redirect('ver_perfil')

    if request.method == 'POST':
        form = PasswordChangeForm(usuario, request.POST)
        if form.is_valid():
            user = form.save()
            if request.user.is_authenticated:
                update_session_auth_hash(request, user)
            registrar_actividad('EDITAR', 'Módulo', 'Actualizaste tu contraseña de administrador')
            messages.success(request, 'Tu contraseña ha sido actualizada exitosamente.')
            return redirect('ver_perfil')
    else:
        form = PasswordChangeForm(usuario)

    return render(request, 'th_app/cambiar_contrasena.html', {'form': form})


def gestion_auditoria(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'exportar_sennas':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="respaldo_sennas_th.csv"'
            writer = csv.writer(response)
            writer.writerow(['ID', 'Nombre', 'Categoría', 'Descripción'])
            for s in Senna.objects.all():
                writer.writerow([s.id, s.nombre, s.categoria, s.descripcion])
            registrar_actividad('CREAR', 'Seña', 'Descargaste un respaldo CSV del catálogo de señas')
            return response

        elif accion == 'limpiar_historial':
            ActividadAdmin.objects.all().delete()
            registrar_actividad('ELIMINAR', 'Módulo', 'Reiniciaste el historial de actividad')
            messages.success(request, 'Historial de actividad vaciado correctamente.')
            return redirect('ver_perfil')

    total_registros = ActividadAdmin.objects.count()
    return render(request, 'th_app/gestion_auditoria.html', {'total_registros': total_registros})


def config_sistema(request):
    modo_mantenimiento = request.session.get('modo_mantenimiento', False)

    if request.method == 'POST':
        nuevo_estado = 'modo_mantenimiento' in request.POST
        request.session['modo_mantenimiento'] = nuevo_estado
        estado_texto = "activado" if nuevo_estado else "desactivado"
        registrar_actividad('EDITAR', 'Módulo', f'Modo mantenimiento {estado_texto}')
        messages.success(request, f'Modo mantenimiento {estado_texto} correctamente.')
        return redirect('config_sistema')

    return render(request, 'th_app/config_sistema.html', {
        'modo_mantenimiento': modo_mantenimiento
    })


def ver_ranking(request):
    aprendices = Perfil.objects.filter(rol='APRENDIZ').order_by('-puntos_xp', 'nombre')

    return render(request, 'th_app/ranking.html', {
        'aprendices': aprendices,
    })


# ==========================================
# VISTAS DEL APRENDIZ (RAMA GABRIEL)
# ==========================================

@login_required
def dashboard_aprendiz(request):
    if request.user.is_staff:
        return redirect("panel_admin")

    perfil, _ = Perfil.objects.get_or_create(
        usuario=request.user,
        defaults={
            "nombre": request.user.username[:25],
            "email": request.user.email or "",
            "puntos_xp": 0,
            "rol": "APRENDIZ",
        }
    )

    ranking = Perfil.objects.order_by("-puntos_xp")[:10]
    modulos = Modulo.objects.all()
    completadas_ids = set(perfil.lecciones_completadas.values_list("id", flat=True))

    modulos_ruta = []
    anterior_completado = True

    for modulo in modulos:
        lecciones = list(Leccion.objects.filter(id_modulo=modulo))
        total_lecciones = len(lecciones)
        completadas_modulo = sum(1 for l in lecciones if l.id in completadas_ids)

        if total_lecciones > 0:
            porcentaje = int((completadas_modulo / total_lecciones) * 100)
        else:
            porcentaje = 0

        completado = (total_lecciones > 0 and completadas_modulo == total_lecciones)

        siguiente_leccion = next((l for l in lecciones if l.id not in completadas_ids), None)
        if not siguiente_leccion and lecciones:
            siguiente_leccion = lecciones[0]

        modulos_ruta.append({
            "modulo": modulo,
            "porcentaje": porcentaje,
            "completadas": completadas_modulo,
            "total": total_lecciones,
            "esta_completado": completado,
            "desbloqueado": anterior_completado,
            "siguiente_leccion": siguiente_leccion,
        })

        anterior_completado = completado

    context = {
        "perfil": perfil,
        "modulos_ruta": modulos_ruta,
        "lecciones_completadas_ids": list(completadas_ids),
        "ranking": ranking,
    }
    return render(request, "th_app/aprendiz/dashboard.html", context)


def ranking(request):
    ranking = Perfil.objects.order_by("-puntos_xp")

    context = {
        "ranking": ranking,
    }
    return render(request, "th_app/aprendiz/ranking.html", context)


@login_required
def realizar_leccion(request, leccion_id):
    leccion = get_object_or_404(Leccion, id=leccion_id)
    perfil = get_object_or_404(Perfil, usuario=request.user)

    if request.method == "POST":
        ejercicios = Ejercicio.objects.filter(leccion=leccion).select_related('opcion_correcta')
        aciertos = 0
        total_ejercicios = ejercicios.count()
        resultados_detalle = []

        for ejercicio in ejercicios:
            respuesta_id = request.POST.get(f"ejercicio_{ejercicio.id}")
            es_correcta = False

            if respuesta_id and ejercicio.opcion_correcta:
                es_correcta = str(ejercicio.opcion_correcta.id) == str(respuesta_id)

            if es_correcta:
                aciertos += 1

            resultados_detalle.append({
                "pregunta": ejercicio.pregunta,
                "es_correcta": es_correcta,
                "opcion_correcta": ejercicio.opcion_correcta,
            })

        aprobado = (aciertos == total_ejercicios) if total_ejercicios > 0 else False
        xp_ganado = 0

        if aprobado:
            puntos_base = getattr(leccion, 'puntos_xp', 20)
            if not perfil.lecciones_completadas.filter(id=leccion.id).exists():
                perfil.puntos_xp += puntos_base
                perfil.lecciones_completadas.add(leccion)
                xp_ganado = puntos_base
            else:
                perfil.puntos_xp += 5
                xp_ganado = 5

            perfil.save()
            verificar_logros(perfil)

        context_resultado = {
            "leccion": leccion,
            "aciertos": aciertos,
            "total": total_ejercicios,
            "aprobado": aprobado,
            "xp_ganado": xp_ganado,
            "resultados": resultados_detalle,
            "perfil": perfil,
        }
        return render(request, "th_app/aprendiz/resultado_leccion.html", context_resultado)

    ejercicios = list(
        Ejercicio.objects.filter(leccion=leccion)
        .prefetch_related('opciones')
        .select_related('opcion_correcta')
        .order_by('?')
    )

    for ejercicio in ejercicios:
        opciones_lista = list(ejercicio.opciones.all())
        random.shuffle(opciones_lista)
        ejercicio.opciones_aleatorias = opciones_lista

    context = {
        "leccion": leccion,
        "ejercicios": ejercicios,
        "perfil": perfil
    }
    return render(request, "th_app/aprendiz/leccion_practica.html", context)


def verificar_logros(perfil):
    logros_disponibles = Logro.objects.filter(puntos_xp__lte=perfil.puntos_xp).exclude(
        id__in=perfil.logros_obtenidos.values_list("id", flat=True)
    )
    for logro in logros_disponibles:
        perfil.logros_obtenidos.add(logro)


@login_required
def diccionario_sennas(request):
    query = request.GET.get("q", "").strip()
    categoria_actual = request.GET.get("categoria", "").strip()

    sennas = Senna.objects.all()

    if query:
        sennas = sennas.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )
    if categoria_actual:
        sennas = sennas.filter(categoria__iexact=categoria_actual)

    categorias = Senna.objects.values_list("categoria", flat=True).distinct()

    context = {
        "sennas": sennas,
        "categorias": categorias,
        "query": query,
        "categoria_actual": categoria_actual,
    }
    return render(request, "th_app/aprendiz/diccionario.html", context)


@login_required
def perfil_y_ranking(request):
    perfil = get_object_or_404(Perfil, usuario=request.user)
    todos_los_logros = Logro.objects.all()
    logros_desbloqueados_ids = perfil.logros_obtenidos.values_list("id", flat=True)
    ranking = Perfil.objects.order_by("-puntos_xp")[:10]

    context = {
        "perfil": perfil,
        "todos_los_logros": todos_los_logros,
        "logros_desbloqueados_ids": list(logros_desbloqueados_ids),
        "ranking": ranking,
    }
    return render(request, "th_app/aprendiz/perfil.html", context)