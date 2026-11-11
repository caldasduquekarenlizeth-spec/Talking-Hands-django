from django.contrib import admin
from .models import Modulo, Leccion, Senna, Ejercicio, Logro, Perfil

# Register your models here.
admin.site.register(Modulo)
admin.site.register(Leccion)
admin.site.register(Senna)
admin.site.register(Ejercicio)
admin.site.register(Logro)
admin.site.register(Perfil)