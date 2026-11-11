from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Modulo, Leccion, Ejercicio, Senna, Logro, Perfil
import random

# Create your views here.
# Vista del Index.html
def inicio(request):
    return render(request, "th_app/index.html")


# Registro nuevo aprendiz
def registro_aprendiz(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Ese nombre de usuario ya está en uso.")
            return redirect("registro")

        # Crea usuario con el modelo predefinido de Django
        user = User.objects.create_user(username=username, email=email, password=password)

        #Crea el perfil con su cantidad de puntos de XP en 0
        Perfil.objects.create(
            usuario = user,
            email = email,
            puntos_xp = 0
        )

        login(request, user)
        messages.success(request, f"¡Bienvenido {username}! Comienza a aprender la lengua de señas colombiana iniciando sesión.")
        return redirect("dashboard_aprendiz")
    return render(request, "th_app/aprendiz/register.html")




# DASHBOARD APRENDIZ (Página que se mostrará cuando el usuario inicie sesión)
@login_required
def dashboard_aprendiz(request):

    # Redirigir al usuario al panel de administrador en caso de serlo
    if request.user.is_staff:
        return redirect("panel_admin")

    perfil, _ = Perfil.objects.get_or_create(
        usuario = request.user,
        defaults={"puntos_xp": 0}
    )

    # prefetch_related es un método que optimiza las consultas en la base de datos
    modulos = Modulo.objects.prefetch_related("leccion_set").all()
    lecciones_completadas_ids = perfil.lecciones_completadas.values_list("id", flat=True)

    context = {
        "perfil": perfil,
        "modulos": modulos,
        "lecciones_completadas_ids": list(lecciones_completadas_ids),
    }
    return render (request, "th_app/aprendiz/dashboard.html", context)



# VISTA DE LECCIONES Y MODULOS
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
            if 'verificar_logros' in globals():
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

    # --- PETICIÓN GET (Carga de la pantalla con ejercicios y opciones) ---
    ejercicios = list(
        Ejercicio.objects.filter(leccion=leccion)
        .prefetch_related('opciones')
        .select_related('opcion_correcta')
        .order_by('?')
    )

    # Asignamos las opciones desordenadas a cada ejercicio para el render inicial
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



# Función para desbloquear los logros de XP automáticamente
def verificar_logros(perfil):
    # Desbloquea logros cuyo requisito de puntos_xp haya sido alcanzado por el aprendiz
    logros_disponibles = Logro.objects.filter(puntos_xp__lte=perfil.puntos_xp).exclude(
        id__in=perfil.logros_obtenidos.values_list("id", flat=True)
    )
    for logro in logros_disponibles:
        perfil.logros_obtenidos.add(logro)



# Función para permitir la búsqueda de señas usando la librería Q
@login_required
def diccionario_sennas(request):
    query = request.GET.get("q", "").strip()
    categoria_actual = request.GET.get("categoria", "").strip()

    sennas = Senna.objects.all()

    # Permite realizar búsquedas por nombre o por descripción de la seña
    if query:
        sennas = sennas.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )
    if categoria_actual:
        sennas = sennas.filter(categoria__iexact=categoria_actual)

    # Obtener lista única de categorías para botones de filtro
    categorias = Senna.objects.values_list("categoria", flat=True).distinct()

    context = {
        "sennas": sennas,
        "categorias": categorias,
        "query": query,
        "categoria_actual": categoria_actual,
    }
    return render(request, "th_app/aprendiz/diccionario.html", context)



# PERFIL DEL APRENDIZ (RANKING)
@login_required
def perfil_y_ranking(request):
    perfil = get_object_or_404(Perfil, usuario=request.user)
    todos_los_logros = Logro.objects.all()
    logros_desbloqueados_ids = perfil.logros_obtenidos.values_list("id", flat=True)

    # Top 10 aprendices con más XP
    ranking = Perfil.objects.order_by("-puntos_xp")[:10]

    context = {
        "perfil": perfil,
        "todos_los_logros": todos_los_logros,
        "logros_desbloqueados_ids": list(logros_desbloqueados_ids),
        "ranking": ranking,
    }
    return render(request, "th_app/aprendiz/perfil.html", context)