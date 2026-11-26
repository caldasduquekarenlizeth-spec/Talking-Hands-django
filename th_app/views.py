import csv, re, random
from django.db import models, transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from .models import Perfil, Modulo, Leccion, Ejercicio, Senna, Logro, ActividadAdmin, TipoLogro
from django.contrib.auth.password_validation import validate_password
from .forms import (
    formsPerfiles,
    formsModulos,
    formsLecciones,
    formsEjercicios,
    formsSennas,
    formsLogros,
    formsEditarPerfilPropio,
)


def es_administrador(user):
    if not user.is_authenticated:
        return False
    return (
        user.is_staff
        or user.is_superuser
        or user.groups.filter(name='Administrador').exists()
        or (hasattr(user, 'perfil') and user.perfil.rol == 'ADMIN')
    )


def solo_admin(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not es_administrador(request.user):
            messages.error(request, "No tienes permisos para acceder al panel de administración.")
            return redirect('dashboard_aprendiz')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

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
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        # 1. Validar Usuario (Username): 5-25 chars, alfanumérico + '_', no solo números
        if not (5 <= len(username) <= 25):
            messages.error(request, "El usuario debe tener entre 5 y 25 caracteres.")
            return redirect("registro")
        if not re.match(r"^[a-zA-Z0-9_]+$", username) or username.isdigit():
            messages.error(request, "El usuario solo puede contener letras, números y guion bajo (_), y no puede ser únicamente numérico.")
            return redirect("registro")
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Ese nombre de usuario ya está en uso.")
            return redirect("registro")

        # 2. Validar Correo electrónico: obligatorio, formato válido y único
        if not email:
            messages.error(request, "El correo electrónico es obligatorio.")
            return redirect("registro")
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Ingresa un correo electrónico válido.")
            return redirect("registro")
        if User.objects.filter(email__iexact=email).exists() or Perfil.objects.filter(email__iexact=email).exists():
            messages.error(request, "Ese correo electrónico ya está registrado.")
            return redirect("registro")

        # 3. Validar Contraseña: 6-25 chars, 1 mayúscula, 1 minúscula, 1 número y 1 carácter especial
        if not (6 <= len(password) <= 25):
            messages.error(request, "La contraseña debe tener entre 6 y 25 caracteres.")
            return redirect("registro")
        if (not re.search(r"[A-Z]", password) or
            not re.search(r"[a-z]", password) or
            not re.search(r"\d", password) or
            not re.search(r"[^a-zA-Z0-9]", password)):
            messages.error(request, "La contraseña debe incluir al menos una mayúscula, una minúscula, un número y un carácter especial.")
            return redirect("registro")
        
        # 3b. Bloquear secuencias obvias y palabras comunes
        secuencias_prohibidas = ['12345', '123456', 'qwerty', 'asdfgh', 'abcde', 'password', 'contrasena', 'admin', 'talkinghands']
        if any(seq in password.lower() for seq in secuencias_prohibidas):
            messages.error(request, "La contraseña contiene secuencias o palabras demasiado predecibles (ej. 123456, qwerty).")
            return redirect("registro")

        # 3c. Ejecutar los validadores oficiales de seguridad de Django (lista de contraseñas comunes y similitud con usuario/correo)
        try:
            usuario_temporal = User(username=username, email=email)
            validate_password(password, user=usuario_temporal)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect("registro")
        
        # 4. Creación atómica de User + Grupo + Perfil
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
            grupo_aprendiz, _ = Group.objects.get_or_create(name='Aprendiz')
            user.groups.add(grupo_aprendiz)

            Perfil.objects.create(
                usuario=user,
                nombre=username,
                email=email,
                puntos_xp=0,
                rol='APRENDIZ'
            )

        login(request, user)
        messages.success(request, f"¡Bienvenido {username}! Ya puedes empezar a aprender Lengua de Señas Colombiana.")
        return redirect("dashboard_aprendiz")

    return render(request, "th_app/aprendiz/register.html")


def cerrar_sesion(request):
    # Consumir y limpiar cualquier mensaje pendiente antes de cerrar sesión
    list(messages.get_messages(request))
    logout(request)
    return redirect('login')

# ==========================================
# VISTAS DE ADMINISTRACIÓN (PANEL ADMIN)
# ==========================================
@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
def eliminar_perfil(request, perfil_id):
    perfil = get_object_or_404(Perfil, id=perfil_id)

    # Evita que el administrador elimine su propia cuenta activa por accidente
    if perfil.usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propio perfil de administrador mientras tienes sesión iniciada.')
        return redirect('listar_perfiles')

    if request.method == 'POST':
        nombre_perfil = perfil.nombre
        usuario = perfil.usuario

        # 1. Borramos sus actividades vinculadas para evitar bloqueos de llave foránea
        ActividadAdmin.objects.filter(perfil=perfil).delete()

        # 2. Eliminamos el User (que borra en cascada el Perfil) o solo el Perfil si no tiene User
        if usuario:
            usuario.delete()
        else:
            perfil.delete()

        registrar_actividad('ELIMINAR', 'Perfil', f'Eliminaste el perfil "{nombre_perfil}"')
        messages.success(request, 'Perfil eliminado correctamente.')
        return redirect('listar_perfiles')

    return render(request, 'th_app/eliminar_perfil.html', {'perfil': perfil})

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
def eliminar_modulo(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)
    if request.method == 'POST':
        nombre_modulo = modulo.nombre
        modulo.delete()
        registrar_actividad('ELIMINAR', 'modulo', f'Eliminaste el modulo "{nombre_modulo}"')
        messages.success(request, 'Modulo eliminado correctamente')
        return redirect('listar_modulos')

    return render(request, 'th_app/eliminar_modulo.html', {'modulo': modulo})

@solo_admin
def ver_lecciones(request, modulo_id):
    modulo = get_object_or_404(Modulo, id=modulo_id)
    lecciones = Leccion.objects.filter(id_modulo=modulo).order_by('id')

    return render(request, 'th_app/listar_lecciones.html', {
        'modulo': modulo,
        'lecciones': lecciones,
    })

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
def ver_ejercicios(request, leccion_id):
    leccion = get_object_or_404(Leccion, id=leccion_id)
    ejercicios = Ejercicio.objects.filter(leccion=leccion).order_by('id')

    return render(request, 'th_app/listar_ejercicios.html', {
        'leccion': leccion,
        'ejercicios': ejercicios,
    })

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
def eliminar_logro(request, logro_id):
    logro = get_object_or_404(Logro, id=logro_id)

    if request.method == 'POST':
        nombre_logro = logro.nombre
        logro.delete()
        registrar_actividad('ELIMINAR', 'Logro', f'Eliminaste el logro "{nombre_logro}"')
        messages.success(request, 'Logro eliminado correctamente.')
        return redirect('listar_logros')

    return render(request, 'th_app/eliminar_logro.html', {'logro': logro})

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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

@solo_admin
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
    # Si el usuario pertenece al grupo Administrador o tiene rol ADMIN, va a su panel
    if es_administrador(request.user):
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

    # Filtramos solo aprendices para que los administradores no aparezcan en el podio
    ranking = Perfil.objects.filter(rol="APRENDIZ").order_by("-puntos_xp")[:10]
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

@login_required
def ranking(request):
    if es_administrador(request.user):
        return redirect("clasificacion_admin")
    ranking = Perfil.objects.filter(rol='APRENDIZ').order_by("-puntos_xp", "nombre")

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
    # Excluir los logros que el usuario ya tiene
    obtenidos_ids = perfil.logros_obtenidos.values_list("id", flat=True)
    logros_pendientes = Logro.objects.exclude(id__in=obtenidos_ids)

    # Métricas actuales del aprendiz
    xp_actual = perfil.puntos_xp
    lecciones_count = perfil.lecciones_completadas.count()
    racha_actual = getattr(perfil, "racha_dias", 0)
    # Señas aprendidas
    sennas_count = getattr(perfil, "sennas_aprendidas", perfil.lecciones_completadas).count()
    # Nivel (cada 25 xp sube un nivel)
    nivel_actual = (xp_actual // 25) + 1

    for logro in logros_pendientes:
        tipo = (getattr(logro, "tipo", "") or "").lower().strip()
        # Toma el valor meta del campo numérico que haya en Logro (puntos_xp, meta o requisito)
        requisito = getattr(logro, "meta", None) or getattr(logro, "puntos_xp", 0)
        cumple = False

        if tipo in "LECCION":
            cumple = lecciones_count >= requisito
        elif tipo == "RACHA":
            cumple = racha_actual >= requisito
        elif tipo in ["SEN", "Señas"]:
            cumple = sennas_count >= requisito
        elif tipo == ["NIV","Nivel"]:
            cumple = nivel_actual >= requisito
        elif tipo == ["DIF","Dificultad"]:
            # Se desbloquea si alcanza el XP requerido en algunas lecciones
            cumple = xp_actual >= requisito
        elif tipo in ["EXP", "Exploracion"]:
            # Ej: ha visitado el diccionario o completado su primera lección
            cumple = lecciones_count >= max(1, requisito)
        else:
            # Respaldo por defecto: comparación directa por puntos_xp
            cumple = xp_actual >= logro.puntos_xp

        if cumple:
            perfil.logros_obtenidos.add(logro)


@login_required
def mis_logros(request):
    perfil = get_object_or_404(Perfil, usuario=request.user)
    
    # Ejecutamos la verificación antes de mostrar para asegurar que estén al día
    verificar_logros(perfil)

    categoria_actual = request.GET.get("tipo", "").strip()
    todos_los_logros = Logro.objects.all()

    if categoria_actual:
        todos_los_logros = todos_los_logros.filter(tipo__iexact=categoria_actual)

    obtenidos_ids = set(perfil.logros_obtenidos.values_list("id", flat=True))
    total_general = Logro.objects.count()
    total_obtenidos = len(obtenidos_ids)
    porcentaje_logros = int((total_obtenidos / total_general) * 100) if total_general > 0 else 0

    context = {
        "perfil": perfil,
        "logros": todos_los_logros,
        "obtenidos_ids": obtenidos_ids,
        "total_general": total_general,
        "total_obtenidos": total_obtenidos,
        "porcentaje_logros": porcentaje_logros,
        "tipos_choices": TipoLogro.choices,
        "categoria_actual": categoria_actual,
    }
    return render(request, "th_app/aprendiz/logros.html", context)

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
    ranking = Perfil.objects.filter(rol='APRENDIZ').order_by("-puntos_xp", "nombre")[:10]

    context = {
        "perfil": perfil,
        "todos_los_logros": todos_los_logros,
        "logros_desbloqueados_ids": list(logros_desbloqueados_ids),
        "ranking": ranking,
    }
    return render(request, "th_app/aprendiz/perfil.html", context)