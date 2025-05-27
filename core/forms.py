from django import forms
from .models import EncuestaSatisfaccion
from .models import Cliente  # Asegúrate de tener este modelo


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

