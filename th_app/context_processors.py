from .models import Perfil, ActividadAdmin

def datos_globales_admin(request):
    perfil = Perfil.objects.filter(rol='ADMIN').first() or Perfil.objects.first()
    ultimas_actividades = ActividadAdmin.objects.all()[:4]
    
    return {
        'perfil_nav': perfil,
        'ultimas_actividades_nav': ultimas_actividades,
    }