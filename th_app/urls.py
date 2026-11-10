from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_perfiles, name='listar_perfiles'),
    path('perfil/crear/', views.crear_perfil, name='crear_perfil'),
    path('perfil/editar/<int:perfil_id>/', views.editar_perfil, name='editar_perfil'),
]