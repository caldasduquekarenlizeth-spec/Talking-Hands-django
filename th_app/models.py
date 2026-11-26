from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Modulo(models.Model):
    nombre = models.CharField(max_length=80)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.nombre}"


class Leccion(models.Model):
    nombre = models.CharField(max_length=80)
    descripcion = models.TextField()
    puntos_xp = models.PositiveIntegerField(default=15)
    id_modulo = models.ForeignKey(Modulo, verbose_name="modulo", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} {self.puntos_xp}"


class Senna(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to="sennas/")
    categoria = models.TextField()

    def __str__(self):
        return f"{self.nombre} - {self.categoria}"


class Ejercicio(models.Model):
    TIPO_CHOICES = [
        ('seleccion_multiple', 'Selección Múltiple'),
        ('emparejar', 'Emparejar'),
        ('completar', 'Completar'),
    ]

    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE, related_name='ejercicios')
    pregunta = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='seleccion_multiple')
    opciones = models.ManyToManyField(
        Senna,
        related_name='ejercicios_donde_es_opcion',
        help_text="Selecciona exactamente 3 señas como opciones"
    )
    opcion_correcta = models.ForeignKey(
        Senna,
        on_delete=models.CASCADE,
        related_name='ejercicios_donde_es_correcta',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Ejercicio"
        verbose_name_plural = "Ejercicios"

    def __str__(self):
        return f"{self.pregunta} ({self.leccion.nombre})"

    def clean(self):
        super().clean()
        if self.pk and self.opcion_correcta:
            if not self.opciones.filter(pk=self.opcion_correcta.pk).exists():
                raise ValidationError({
                    'opcion_correcta': 'La opción correcta debe ser una de las señas seleccionadas en las opciones.'
                })


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
    tipo = models.CharField(
        max_length=3,
        choices=TipoLogro.choices,
        default=TipoLogro.NIVEL,
    )

    def __str__(self):
        return f"{self.nombre}: {self.tipo}"


class RolUsuario(models.TextChoices):
    APRENDIZ = 'APRENDIZ', 'Aprendiz'
    ADMINISTRADOR = 'ADMIN', 'Administrador'


class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil", null=True, blank=True)
    nombre = models.CharField(max_length=25)
    email = models.EmailField()
    puntos_xp = models.PositiveIntegerField(default=0)
    rol = models.CharField(
        max_length=10,
        choices=RolUsuario.choices,
        default=RolUsuario.APRENDIZ,
    )
    foto = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    lecciones_completadas = models.ManyToManyField(Leccion, blank=True)
    logros_obtenidos = models.ManyToManyField(Logro, blank=True)
    xp_diario = models.IntegerField(default=0)
    fecha_ultimo_xp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre or self.usuario} - {self.puntos_xp}XP"
    
    def obtener_xp_hoy(self):
        """Retorna el XP ganado hoy. Y reinicia la cuenta al cambiar el día"""
        hoy = timezone.localdate()
        if self.fecha_ultimo_xp != hoy:
            return 0
        return self.xp_diario
    
    def sumar_xp(self, cantidad):
        """Suma XP total y XP diario"""
        hoy = timezone.localdate()
        if self.fecha_ultimo_xp != hoy:
            self.xp_diario = 0
            self.fecha_ultimo_xp = hoy
        
        self.puntos_xp += cantidad
        self.xp_diario += cantidad
        self.save(update_fields=['puntos_xp', 'xp_diario', 'fecha_ultimo_xp'])


class ActividadAdmin(models.Model):
    ACCIONES = [
        ('CREAR', 'Crear'),
        ('EDITAR', 'Editar'),
        ('ELIMINAR', 'Eliminar'),
    ]

    ENTIDADES = [
        ('Módulo', 'Módulo'),
        ('Lección', 'Lección'),
        ('Ejercicio', 'Ejercicio'),
        ('Seña', 'Seña'),
        ('Logro', 'Logro'),
    ]

    perfil = models.ForeignKey(
        Perfil,
        on_delete=models.CASCADE,
        related_name='actividades',
        null=True,
        blank=True
    )
    accion = models.CharField(max_length=10, choices=ACCIONES)
    entidad = models.CharField(max_length=20, choices=ENTIDADES)
    detalle = models.CharField(max_length=150)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.detalle} ({self.entidad})"