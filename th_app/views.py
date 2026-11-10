from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Modulo, Leccion, Ejercicio, Senna, Logro, Perfil

# Create your views here.
# Registro nuevo aprendiz
def registro_aprendiz(request):
    if request.method == "POST":
        username = request.POST.get("username")
        nombre = request.POST.get("nombre")
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
            nombre = nombre or username,
            email = email,
            puntos_xp = 0
        )

        login(request, user)
        messages.success(request, f"¡Bienvenido {nombre}! Comienza a aprender la lengua de señas colombiana iniciando sesión.")
        return redirect("dashboard_aprendiz")
    return render(request, "th_app/aprendiz/registro.html")




# DASHBOARD APRENDIZ 
@login_required
def dashboard_aprendiz(request):

    # Redirigir al usuario al panel de administrador en caso de serlo
    if request.User.is_staff:
        return redirect("panel_admin")

    perfil, _ = Perfil.objects.get_or_create(
        usuario = request.user,
        defaults={"nombre": request.user.username, "email": request.user.email, "puntos_xp": 0}
    )

    # prefetch_related es un método que optimiza las consultas en la base de datos
    modulos = Modulo.objects.prefetch_related("lecciones").all()
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
    ejercicios = leccion.objects.all()
    perfil = get_object_or_404(Perfil, usuario=request.user)

    if request.method == "POST":
        aciertos = 0
        total_ejercicios = ejercicios.count()
        resultados_detalle = []

        for ejercicio in ejercicios:
            respuesta_usuario = request.POST.get(f"El ejercicio_{ejercicio.id}", "").strip()
            es_correcta = respuesta_usuario.lower() == ejercicio.respuesta_correcta.strip().lower()

            if es_correcta:
                aciertos += 1

            resultados_detalle.append({
                "pregunta": ejercicio.pregunta,
                "respuesta_usuario": respuesta_usuario,
                "respuesta_correcta": ejercicio.respuesta_correcta,
                "es_correcta": es_correcta,
            })

        # Condicional para dar como aprobada la lección
        aprobado = (aciertos == total_ejercicios) if total_ejercicios > 0 else False
        xp_ganado = 0

        if aprobado:
            # Si la lección se completa por primera vez otorga el puntaje completo.
            if not perfil.lecciones_completadas.filter(id=leccion.id).exists():
                perfil.puntos_xp += leccion.puntos_xp
                perfil.lecciones_completadas.add(leccion)
                xp_ganado = leccion.puntos_xp
            # Si se completa otra vez una lección solo se otorgarán 5 puntos
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



# PERFIL DEL APRENDIZ
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
    return render(request, "th_app/aprendiz/perfil_ranking.html", context)