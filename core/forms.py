from django import forms
from .models import AutoevaluacionTrabajador, Cliente, Indicador, RespuestaAutoevaluacionTrabajador, TipoEvaluacion, Trabajador
from django.contrib.auth import get_user_model
from django import forms
from .models import Criterio, Indicador
from django.forms import inlineformset_factory
User = get_user_model()
from core.models import Usuario
import random
import string
SPECIAL_CHARS = "!@#$%^&*"



class RegistroClienteForm(forms.ModelForm):
    username = forms.CharField(label='Nombre de usuario')
    email = forms.EmailField(label='Correo electrónico')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    first_name = forms.CharField(label='Nombre')
    last_name = forms.CharField(label='Apellidos')

    class Meta:
        model = Cliente
        fields = ['direccion', 'telefono']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        user.rol = 'cliente'  # Asegúrate de asignar el rol si es obligatorio
        if commit:
            user.save()

        cliente = super().save(commit=False)
        cliente.user = user
        if commit:
            cliente.save()
        return cliente
    
class RespuestaForm(forms.Form):
    puntuacion = forms.ChoiceField(
        label="Califica la pregunta",
        choices=[(1, '⭐ Malo'), (2, '⭐⭐ Regular'), (3, '⭐⭐⭐ Bueno'), (4, '⭐⭐⭐⭐ Muy Bueno'), (5, '⭐⭐⭐⭐⭐ Excelente')],
        widget=forms.RadioSelect
    )

#######3
class EvaluacionVentaForm(forms.Form):
    comentarios = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Comentarios adicionales (opcional)',
            'rows': 3,
            'style': 'resize: vertical; height: 80px; padding-right: 0px'
        }),
        required=False,
        label="Comentarios adicionales"
    )

    def __init__(self, *args, indicadores=None, **kwargs):
        super().__init__(*args, **kwargs)
        if indicadores:
            for indicador in indicadores:
                choices = [(i, '★' * i) for i in range(1, indicador.max_puntaje + 1)]
                self.fields[f'indicador_{indicador.id}'] = forms.ChoiceField(
                    label=indicador.nombre,
                    choices=choices,
                    widget=forms.RadioSelect,
                    required=True,
                )
                # Aquí asignamos la descripción para usarla en el template
                self.fields[f'indicador_{indicador.id}'].widget.attrs['descripcion'] = indicador.descripcion or "Sin descripción."

class CriterioForm(forms.ModelForm):
    class Meta:
            model = Criterio
            fields = ['nombre', 'descripcion', 'puesto', 'rango_min', 'rango_max']

IndicadorFormSet = inlineformset_factory(
    Criterio, Indicador,
    fields=['nombre', 'descripcion', 'max_puntaje'],
    extra=1, can_delete=True
)





class EvaluacionTrabajadorForm(forms.Form):
    def __init__(self, *args, indicadores=None, **kwargs):
        super().__init__(*args, **kwargs)
        if indicadores:
            for indicador in indicadores:
                self.fields[f'indicador_{indicador.id}'] = forms.IntegerField(
                    label=indicador.nombre,
                    min_value=0,
                    max_value=getattr(indicador, 'puntaje_maximo', 10),  # ejemplo, que tengas ese atributo
                    required=True,
                )

class AutoevaluacionTrabajadorForm(forms.ModelForm):
    class Meta:
        model = AutoevaluacionTrabajador
        fields = ['trabajador']

class RespuestaAutoevaluacionForm(forms.ModelForm):
    class Meta:
        model = RespuestaAutoevaluacionTrabajador
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Indicador no editable
        self.fields['indicador'].disabled = True
        # Puntaje visible pero no editable
        self.fields['puntaje'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        valoracion = cleaned_data.get('valoracion')

        # Mapea la valoración al puntaje correcto
        puntaje_map = {
            'Malo': 1,
            'Regular': 3,
            'Bueno': 5,
        }
        cleaned_data['puntaje'] = puntaje_map.get(valoracion, 0)
        return cleaned_data
    
class AutoevaluacionForm(forms.Form):
    def __init__(self, indicadores, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for indicador in indicadores:
            self.fields[f'indicador_{indicador.id}'] = forms.ChoiceField(
                choices=[(str(i), str(i)) for i in range(1, 6)],
                widget=forms.RadioSelect,
                label=indicador.nombre
            )
            
RespuestaAutoevaluacionFormSet = forms.modelformset_factory(
    RespuestaAutoevaluacionTrabajador,
    form=RespuestaAutoevaluacionForm,  # tu form personalizado para cada respuesta
    extra=0,  # o el número de formularios extra que quieras
    can_delete=False,
)

############################33 1er form de trabajador ############################333
# class EmpleadoForm(forms.ModelForm):
#     class Meta:
#         model = Usuario
#         fields = ['username', 'first_name', 'last_name', 'email', 'puesto', 'rol_admin']
#         widgets = {
#             'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
#             'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
#             'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo'}),
#             'puesto': forms.Select(attrs={'class': 'form-select'}),
#             'rol_admin': forms.Select(attrs={'class': 'form-select'}),
#         }

class TrabajadorForm(forms.ModelForm):
    # Campos de usuario
    username   = forms.CharField(
        label='Nombre de usuario',
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Usuario'})
    )
    email      = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class':'form-control','placeholder':'Correo'})
    )
    password   = forms.CharField(
        label='Contraseña inicial',
        widget=forms.TextInput(attrs={'class':'form-control','readonly':'readonly'})
    )
    first_name = forms.CharField(
        label='Nombre',
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Nombre'})
    )
    last_name  = forms.CharField(
        label='Apellidos',
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Apellidos'})
    )

    class Meta:
        model = Trabajador
        fields = [
            'username','email','password','first_name','last_name',
            'puesto','direccion','telefono'
        ]
        widgets = {
            'puesto':    forms.Select(attrs={'class':'form-select'}),
            'direccion': forms.TextInput(attrs={'class':'form-control','placeholder':'Dirección'}),
            'telefono':  forms.TextInput(attrs={'class':'form-control','placeholder':'Teléfono'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si es edición (instance.pk existe), quitamos el campo password
        if self.instance.pk:
            self.fields.pop('password', None)
            # Precargamos datos del user existente
            u = self.instance.user
            self.fields['username'].initial   = u.username
            self.fields['email'].initial      = u.email
            self.fields['first_name'].initial = u.first_name
            self.fields['last_name'].initial  = u.last_name
            return

        # En creación: generamos contraseña aleatoria 3 mayúsculas + 5 dígitos + 1 especial
        letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(3))
        digits  = ''.join(random.choice(string.digits) for _ in range(5))
        special = random.choice(SPECIAL_CHARS)
        self.fields['password'].initial = f"{letters}{digits}{special}"

    def save(self, commit=True):
        data = self.cleaned_data

        # 1) Crear o actualizar User
        if self.instance.pk:
            # Edición: actualiza usuario existente
            user = self.instance.user
            user.username   = data['username']
            user.email      = data['email']
            user.first_name = data['first_name']
            user.last_name  = data['last_name']
        else:
            # Creación: crea nuevo user con la contraseña generada
            user = User.objects.create_user(
                username   = data['username'],
                email      = data['email'],
                password   = data['password'],
                first_name = data['first_name'],
                last_name  = data['last_name'],
            )

        if commit:
            user.save()

        # 2) Guardar Trabajador
        trabajador = super().save(commit=False)
        trabajador.user = user
        if commit:
            trabajador.save()
        return trabajador
    
class FiltroEvaluacionForm(forms.Form):
    buscar = forms.CharField(required=False, label='Buscar')
    tipo = forms.ChoiceField(
        required=False,
        choices=[('todas', 'Todas las evaluaciones')] + list(TipoEvaluacion.choices),
        label='Tipo'
    )