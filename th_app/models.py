from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
class Modulo(models.Model):
    nombre = models.CharField(max_length=80)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.nombre}"

class Leccion(models.Model):
    nombre = models.CharField(max_length=80)
    descripcion = models.TextField()
    puntos_xp = models.PositiveIntegerField(default=15)
    id_modulo = models.ForeignKey(Modulo, verbose_name=("modulo"), on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} {self.puntos_xp}"

class Ejercicio(models.Model):
    pregunta = models.TextField()
    tipo = models.TextField()
    respuesta_correcta = models.TextField()
    leccion = models.ForeignKey(Leccion, verbose_name="leccion", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.pregunta} - {self.tipo}"
    
class RolUsuario(models.TextChoices):
    APRENDIZ = 'APRENDIZ', 'Aprendiz'
    ADMINISTRADOR = 'ADMIN', 'Administrador'

class Perfil(models.Model):
    nombre = models.CharField(max_length=25)
    email = models.EmailField()
    puntos_xp = models.PositiveIntegerField()
    rol = models.CharField(
         max_length=10,
         choices=RolUsuario.choices,
         default=RolUsuario.APRENDIZ,
    )

    def __str__(self):
        return f"{self.nombre} - {self.puntos_xp}XP"

class Senna(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to="sennas/")
    categoria = models.TextField()

    def __str__(self):
        return f"{self.nombre} - {self.categoria}"


class TipoLogro(models.TextChoices):
    LECCION = "LEC", "Leccion"
    RACHA = "RAC", "Racha"
    SENNAS = "SEN", "Señas"
    NIVEL = "NIV", "Nivel"
    DIFICULTAD = "DIF", "Dificultad"
    EXPLORACION = "EXP", "Exploracion"

class Logro(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField()
    puntos_xp = models.PositiveIntegerField()
    tipo = models.CharField(max_length=3,choices=TipoLogro.choices,default=TipoLogro.NIVEL,)

    def __str__(self):
        return f"{self.nombre}: {self.tipo}"