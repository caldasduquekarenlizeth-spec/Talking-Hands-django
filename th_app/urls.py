from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path("",views.inicio, name="inicio"),
    path("registro/", views.registro_aprendiz, name="registro"),
    #Para el login y logout se utilizan las vistas predefinidas de django importandolas al principio del archivo y luego usandolas definiendo en la misma líena del path la template que va a incluir el Login y Logout
    path("login/", auth_views.LoginView.as_view(template_name="th_app/aprendiz/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # APRENDIZ
    path("accounts/profile/", views.dashboard_aprendiz, name="dashboard_aprendiz"),
    path("leccion/<int:leccion_id>",views.realizar_leccion,name="realizar_leccion"),
    path("diccionario/", views.diccionario_sennas, name="diccionario_sennas"),
    path("perfil/", views.perfil_y_ranking, name="perfil_y_ranking"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)