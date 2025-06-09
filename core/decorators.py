# core/decorators.py

from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

from core.models import Cliente


def only_trabajador(view_func):
    return user_passes_test(lambda u: hasattr(u, 'trabajador'), login_url='login_colaborador')(view_func)

def only_cliente(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        # 1) Si no está autenticado, lo mandamos al login
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder.')
            return redirect('login')

        # 2) Si no tiene perfil de cliente, también al login
        try:
            _ = request.user.cliente
        except Cliente.DoesNotExist:
            messages.error(request, 'No tienes permisos de cliente.')
            return redirect('login')

        # 3) Todo OK, llamamos a la vista
        return view_func(request, *args, **kwargs)

    return _wrapped