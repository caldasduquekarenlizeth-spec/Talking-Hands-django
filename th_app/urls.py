from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # ==========================================
    # RUTAS PÚBLICAS Y AUTENTICACIÓN
    # ==========================================
    path('', views.inicio, name='inicio'),
    path('registro/', views.registro_aprendiz, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='th_app/aprendiz/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # ==========================================
    # RUTAS DEL APRENDIZ
    # ==========================================
    path('accounts/profile/', views.dashboard_aprendiz, name='dashboard_aprendiz'),
    path('leccion/<int:leccion_id>/', views.realizar_leccion, name='realizar_leccion'),
    path('diccionario/', views.diccionario_sennas, name='diccionario_sennas'),
    path('aprendiz/perfil/', views.perfil_y_ranking, name='perfil_y_ranking'),
    path('aprendiz/ranking/', views.ranking, name='ranking'),

    # ==========================================
    # RUTAS DE ADMINISTRACIÓN (PANEL ADMIN)
    # ==========================================
    path('panel-admin/', views.dashboard, name='panel_admin'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Perfiles (Admin)
    path('perfiles/', views.listar_perfiles, name='listar_perfiles'),
    path('perfil/crear/', views.crear_perfil, name='crear_perfil'),
    path('perfil/editar/<int:perfil_id>/', views.editar_perfil, name='editar_perfil'),
    path('perfil/eliminar/<int:perfil_id>/', views.eliminar_perfil, name='eliminar_perfil'),

    # Módulos
    path('modulos/', views.listar_modulos, name='listar_modulos'),
    path('modulos/crear/', views.crear_modulo, name='crear_modulo'),
    path('modulos/editar/<int:modulo_id>/', views.editar_modulo, name='editar_modulo'),
    path('modulos/eliminar/<int:modulo_id>/', views.eliminar_modulo, name='eliminar_modulo'),

    # Lecciones
    path('lecciones/<int:modulo_id>/', views.ver_lecciones, name='ver_lecciones'),
    path('lecciones/crear/', views.crear_leccion, name='crear_leccion'),
    path('lecciones/editar/<int:leccion_id>/', views.editar_leccion, name='editar_leccion'),
    path('lecciones/eliminar/<int:leccion_id>/', views.eliminar_leccion, name='eliminar_leccion'),

    # Ejercicios
    path('ejercicios/<int:leccion_id>/ejercicios/', views.ver_ejercicios, name='ver_ejercicios'),
    path('ejercicios/crear/', views.crear_ejercicio, name='crear_ejercicio'),
    path('ejercicios/editar/<int:ejercicio_id>/', views.editar_ejercicio, name='editar_ejercicio'),
    path('ejercicio/eliminar/<int:ejercicio_id>/', views.eliminar_ejercicio, name='eliminar_ejercicio'),

    # Señas
    path('sennas/', views.listar_sennas, name='listar_sennas'),
    path('sennas/crear/', views.crear_senna, name='crear_senna'),
    path('sennas/editar/<int:senna_id>/', views.editar_senna, name='editar_senna'),
    path('sennas/eliminar/<int:senna_id>/', views.eliminar_senna, name='eliminar_senna'),

    # Logros
    path('logros/', views.listar_logros, name='listar_logros'),
    path('logros/crear/', views.crear_logro, name='crear_logro'),
    path('logros/editar/<int:logro_id>/', views.editar_logro, name='editar_logro'),
    path('logros/eliminar/<int:logro_id>/', views.eliminar_logro, name='eliminar_logro'),

    # Perfil propio y configuración del Admin
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    path('mi-perfil/editar/<int:perfil_id>/', views.editar_perfil_propio, name='editar_perfil_propio'),
    path('perfil/cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('perfil/auditoria/', views.gestion_auditoria, name='gestion_auditoria'),
    path('perfil/estado-sistema/', views.config_sistema, name='config_sistema'),
    path('ranking/', views.ver_ranking, name='ver_ranking'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)