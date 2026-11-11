from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

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
    id_modulo = models.ForeignKey(Modulo, verbose_name=("lecciones"), on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} {self.puntos_xp}"

class Ejercicio(models.Model):
    TIPO_CHOICES = [
        ('seleccion_multiple', 'Selección Múltiple'),
        ('emparejar', 'Emparejar'),
        ('completar', 'Completar'),
    ]

    leccion = models.ForeignKey('Leccion', on_delete=models.CASCADE, related_name='ejercicios')
    pregunta = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='seleccion_multiple')
    opciones = models.ManyToManyField('Senna', related_name='ejercicios_donde_es_opcion',help_text="Selecciona exactamente 3 señas como opciones")
    opcion_correcta = models.ForeignKey('Senna', on_delete=models.CASCADE, related_name='ejercicios_donde_es_correcta', null=True, blank=True)

    class Meta:
        verbose_name = "Ejercicio"
        verbose_name_plural = "Ejercicios"

    def __str__(self):
        return f"{self.pregunta} ({self.leccion.nombre})"

    def clean(self):
        super().clean()
        # Valida que si el ejercicio ya tiene id (en edición) la opción correcta esté entre las opciones
        if self.pk and self.opcion_correcta:
            if not self.opciones.filter(pk=self.opcion_correcta.pk).exists():
                raise ValidationError({
                    'opcion_correcta': 'La opción correcta debe ser una de las señas seleccionadas en las opciones.'
                })


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
    tipo = models.CharField(max_length=3,
                            choices=TipoLogro.choices,
                            default=TipoLogro.NIVEL,
                            )

    def __str__(self):
        return f"{self.nombre}: {self.tipo}"

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil", null=True, blank=True)
    email = models.EmailField()
    puntos_xp = models.PositiveIntegerField()
    lecciones_completadas = models.ManyToManyField(Leccion, blank=True)
    logros_obtenidos = models.ManyToManyField(Logro, blank=True)

    def __str__(self):
        return f"{self.usuario} - {self.puntos_xp}XP"