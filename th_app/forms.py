from django import forms
from .models import Perfil, Modulo, Leccion, Ejercicio, Senna, Logro

class formsPerfiles(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['nombre', 'email', 'puntos_xp', 'rol']

class formsModulos(forms.ModelForm):
    class Meta:
        model = Modulo
        fields = ['nombre', 'descripcion']


from django import forms
from .models import Leccion, Modulo

class formsLecciones(forms.ModelForm):
    class Meta:
        model = Leccion
        fields = ['nombre', 'descripcion', 'puntos_xp', 'id_modulo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegura que el selector muestre el nombre de cada módulo
        self.fields['id_modulo'].queryset = Modulo.objects.all()
        self.fields['id_modulo'].empty_label = "-- Selecciona un Módulo --"

TIPOS_EJERCICIO = [
    ('', '-- Selecciona el tipo de ejercicio --'),
    ('SELECCION_MULTIPLE', 'Selección Múltiple'),
    ('RECONOCIMIENTO_SENNA', 'Reconocimiento de Seña'),
    ('COMPLETAR', 'Completar la Frase'),
]

class formsEjercicios(forms.ModelForm):
    class Meta:
        model = Ejercicio
        fields = ['pregunta', 'tipo', 'respuesta_correcta', 'leccion']
        labels = {
            'pregunta': 'Pregunta / Enunciado del Ejercicio',
            'tipo': 'Tipo de Ejercicio',
            'respuesta_correcta': 'Respuesta Correcta',
            'leccion': 'Lección Asociada',
        }
        widgets = {
            'tipo': forms.Select(choices=TIPOS_EJERCICIO),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['leccion'].queryset = Leccion.objects.all()
        self.fields['leccion'].empty_label = "-- Selecciona una Lección --"

CATEGORIAS_SENNA = [
    ('', '-- Selecciona una categoría --'),
    ('Alfabeto', 'Alfabeto'),
    ('Saludos', 'Saludos'),
    ('Colores', 'Colores'),
    ('Familia', 'Familia'),
    ('Números', 'Números'),
    ('General', 'General'),
]

class formsSennas(forms.ModelForm):
    class Meta:
        model = Senna
        fields = ['nombre', 'descripcion', 'imagen', 'categoria']
        labels = {
            'nombre': 'Nombre / Palabra de la Seña',
            'descripcion': 'Descripción o Instrucción',
            'imagen': 'Imagen de la Seña',
            'categoria': 'Categoría',
        }
        widgets = {
            'categoria': forms.Select(choices=CATEGORIAS_SENNA),
        }

class formsLogros(forms.ModelForm):
    class Meta:
        model = Logro
        fields = ['nombre', 'descripcion', 'puntos_xp', 'tipo']
        labels = {
            'nombre': 'Nombre del Logro',
            'descripcion': 'Descripción o Condición',
            'puntos_xp': 'Puntos XP Otorgados',
            'tipo': 'Tipo / Categoría del Logro',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Racha de 7 días'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej. Practicaste una semana sin interrupción.'}),
            'puntos_xp': forms.NumberInput(attrs={'min': 0, 'placeholder': 'Ej. 150'}),
        }