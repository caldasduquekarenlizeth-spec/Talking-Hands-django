import os
import re
from django import forms
from .models import Perfil, Modulo, Leccion, Ejercicio, Senna, Logro

class formsPerfiles(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['nombre', 'email', 'puntos_xp', 'rol']

class formsEditarPerfilPropio(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['nombre', 'foto']
        labels = {
            'nombre': 'Nombre de Usuario',
            'foto': 'Foto de Perfil',
        }

class formsModulos(forms.ModelForm):
    class Meta:
        model = Modulo
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Abecedario en LSC'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'style': 'resize: none;',
                'placeholder': 'Describe el contenido del módulo...'
            }),
        }
        
    # Función para verificar la correcta entrada de información al campo Nombre.
    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        
        if len(nombre) < 5 or len(nombre) > 35:
            raise forms.ValidationError("El nombre debe tener entre 5 y 35 caracteres.")
        
        #Permitir letras, tildes y Ñ. (Usando la librería re para utilizar expresiones regulares como verificación de entrada de datos)
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s]+$', nombre):
            raise forms.ValidationError("El nombre no puede contener caracteres especiales.")
        
        if nombre.replace(' ', '').isdigit():
            raise forms.ValidationError("El nombre no puede estar compuesto únicamente por números.")
        
        return nombre
    
    # Función para verificar la correcta entrada de información al campo Descripción.
    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get('descripcion') or '').strip()
        
        if not descripcion:
            raise forms.ValidationError("La descripción es obligatoria.")
        
        if len(descripcion) < 5 or len(descripcion) > 255:
            raise forms.ValidationError("La descripción debe tener entre 5 y 255 caracteres")
        
        return descripcion
        
        
            
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
        fields = ['leccion', 'pregunta', 'tipo', 'opciones', 'opcion_correcta']
        widgets = {
            'leccion': forms.Select(attrs={'class': 'form-control'}),
            'pregunta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: ¿Qué seña corresponde a la letra A?'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'opciones': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'opcion_correcta': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['leccion'].empty_label = "-- Selecciona una Lección --"
        self.fields['opcion_correcta'].empty_label = "-- Selecciona la Seña Correcta --"

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
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Hola'
            }),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.webp,.gif'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'style': 'resize: none;',
                'placeholder': 'Explica cómo realizar la seña...'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True
        self.fields['categoria'].required = True
        self.fields['imagen'].required = True
        self.fields['descripcion'].required = True
        if hasattr(self.fields['categoria'], 'empty_label'):
            self.fields['categoria'].empty_label = "-- Selecciona una Categoria --"
            
    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        
        # Verificar longitud
        if len(nombre) < 1 or len(nombre) > 50:
            raise forms.ValidationError("El nombre es obligatorio y debe tener entre 1 y 50 caracteres.")
        
        # Verificar contenido (Solo letras, tildes y espacios)
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', nombre):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        
        return nombre
    
    def clean_categoria(self):
        categoria = self.cleaned_data.get('categoria')
        if not categoria:
            raise forms.ValidationError("Debes seleccionar una categoría.")
        return categoria
    
    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        
        if not imagen:
            raise forms.ValidationError("La imagen de la seña es obligatoria.")
        
        # Validar extensión
        extensiones_Validas = ['.jpg','.jpeg','.png','.webp','.gif']
        ext = os.path.splitext(imagen.name)[1].lower()
        if ext not in extensiones_Validas:
            raise forms.ValidationError("Formato no permitido. Solo se aceptan imágenes en formato .jpg, .jpeg, .png, .webp o .gif.")
        
        # Validar tamaño máximo (El tamaño de los archivos se lee en Bytes por lo que hay que realizar una operación matemática para poder especficar las 5MB de tamaño máximo.)
        max_size = 5 * 1024 * 1024
        if imagen.size > max_size:
            raise forms.ValidationError("La imagen no puede superar los 5 MB.")
        
        return imagen
    
    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get('descripcion') or '').strip()

        if not descripcion:
            raise forms.ValidationError("La descripción es obligatoria.")

        if len(descripcion) < 5 or len(descripcion) > 255:
            raise forms.ValidationError("La descripción debe tener entre 5 y 255 caracteres.")

        return descripcion

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
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Primer Paso en LSC'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'style': 'resize: none;',
                'placeholder': 'Describe cómo desbloquear este logro...'
            }),
            'puntos_xp': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Ej: 50'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True
        self.fields['descripcion'].required = True
        self.fields['puntos_xp'].required = True
        self.fields['tipo'].required = True

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()

        if len(nombre) < 3:
            raise forms.ValidationError("El nombre del logro debe tener al menos 3 caracteres.")

        if nombre.replace(' ', '').isdigit():
            raise forms.ValidationError("El nombre del logro no puede contener solo números.")

        return nombre

    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get('descripcion') or '').strip()

        if not descripcion:
            raise forms.ValidationError("La descripción del logro es obligatoria.")

        return descripcion

    def clean_puntos_xp(self):
        puntos_xp = self.cleaned_data.get('puntos_xp')

        if puntos_xp is None or puntos_xp <= 0:
            raise forms.ValidationError("Los puntos XP deben ser mayores a 0.")

        return puntos_xp