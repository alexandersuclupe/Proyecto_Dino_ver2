from django.shortcuts import render, get_object_or_404, redirect
from .models import Venta, EncuestaSatisfaccion
from .forms import EncuestaSatisfaccionForm
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.contrib import messages




def encuesta_satisfaccion(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)

    if EncuestaSatisfaccion.objects.filter(venta=venta).exists():
        return render(request, 'gracias.html')

    if request.method == 'POST':
        form = EncuestaSatisfaccionForm(request.POST)
        if form.is_valid():
            encuesta = form.save(commit=False)
            encuesta.venta = venta
            encuesta.trabajador = venta.usuario  # Asumiendo que 'usuario' es el trabajador
            encuesta.save()
            return redirect('gracias_encuesta')
    else:
        form = EncuestaSatisfaccionForm()

    return render(request, 'encuesta_form.html', {
        'form': form,
        'venta': venta,
        'trabajador': venta.usuario  # ✅ Aquí se añade al contexto
    })

def gracias_encuesta(request):
    return render(request, 'gracias.html')

def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # Puede ser email o username según tu modelo
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')  # Redirige al inicio después del login
        else:
            messages.error(request, 'Credenciales inválidas. Intenta nuevamente.')

    return render(request, 'login.html')
