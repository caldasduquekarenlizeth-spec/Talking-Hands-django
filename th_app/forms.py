from django import forms
from .models import Perfil

class formsPerfiles(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['nombre', 'email', 'puntos_xp', 'rol']
