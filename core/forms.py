from django import forms
from .models import Cliente  # Asegúrate de tener este modelo
from django.contrib.auth import get_user_model
User = get_user_model()




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
        widget=forms.Textarea(attrs={'placeholder': 'Comentarios adicionales (opcional)'}),
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