from django import forms
from .models import EncuestaSatisfaccion
from .models import Cliente  # Asegúrate de tener este modelo
from django.contrib.auth.models import User



class EncuestaSatisfaccionForm(forms.ModelForm):
    OPCIONES = [(i, str(i)) for i in range(1, 6)]

    cordialidad = forms.ChoiceField(
        label='¿Qué tan cordial fue el trabajador al atenderlo?',
        choices=OPCIONES,
        widget=forms.RadioSelect
    )
    resolucion_dudas = forms.ChoiceField(
        label='¿El trabajador resolvió sus dudas adecuadamente?',
        choices=OPCIONES,
        widget=forms.RadioSelect
    )
    tiempo_atencion = forms.ChoiceField(
        label='¿Está satisfecho con el tiempo de atención?',
        choices=OPCIONES,
        widget=forms.RadioSelect
    )
    recomendacion = forms.ChoiceField(
        label='¿Recomendaría ser atendido nuevamente por este trabajador?',
        choices=OPCIONES,
        widget=forms.RadioSelect
    )

    class Meta:
        model = EncuestaSatisfaccion
        fields = ['cordialidad', 'resolucion_dudas', 'tiempo_atencion', 'recomendacion', 'comentario']
        labels = {
            'comentario': 'Comentario adicional (opcional)',
        }


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
        cliente = super().save(commit=False)
        cliente.user = user
        if commit:
            cliente.save()
        return cliente