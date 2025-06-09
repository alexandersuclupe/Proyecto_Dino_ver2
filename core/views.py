from django.shortcuts import render, get_object_or_404, redirect
from .models import AutoevaluacionTrabajador, RespuestaAutoevaluacionTrabajador, Venta, Usuario, Cliente, EvaluacionVenta, EvaluacionTrabajador, Criterio, RespuestaEvaluacionTrabajador, Rol, RespuestaEvaluacionVenta, Indicador, PeriodoEvaluacion
from .forms import EmpleadoForm
from .forms import AutoevaluacionForm, AutoevaluacionTrabajadorForm, RespuestaAutoevaluacionFormSet, RespuestaForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import RegistroClienteForm, EvaluacionVentaForm, EvaluacionTrabajadorForm
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from .decorators import only_trabajador, only_cliente


# def encuesta_satisfaccion(request, venta_id):
#     venta = get_object_or_404(Venta, id=venta_id)

#     if EncuestaSatisfaccion.objects.filter(venta=venta).exists():
#         return render(request, 'gracias.html')

#     if request.method == 'POST':
#         form = EncuestaSatisfaccionForm(request.POST)
#         if form.is_valid():
#             encuesta = form.save(commit=False)
#             encuesta.venta = venta
#             encuesta.trabajador = venta.usuario  # Asumiendo que 'usuario' es el trabajador
#             encuesta.save()
#             return redirect('gracias_encuesta')
#     else:
#         form = EncuestaSatisfaccionForm()

#     return render(request, 'encuesta_form.html', {
#         'form': form,
#         'venta': venta,
#         'trabajador': venta.usuario  # ✅ Aquí se añade al contexto
#     })

def gracias_encuesta(request):
    return render(request, 'gracias.html')


def index(request):
    return render(request, 'index.html')

# login inicial ###############3
# def login_view(request):
#     if request.method == 'POST':
#         # Puede ser email o username según tu modelo
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             # Redirige al inicio después del login
#             return redirect('cliente_panel')
#         else:
#             messages.error(
#                 request, 'Credenciales inválidas. Intenta nuevamente.')

#     return render(request, 'login.html')

############## login con trabajador ################################


def login_view(request, is_colaborador=False):
    """
    Si is_colaborador=True, mostramos sólo el login de trabajadores
    y ocultamos el enlace de registro en la plantilla.
    """
    context = {'is_colaborador': is_colaborador}

    if request.method == 'POST':
        u = request.POST['username']
        p = request.POST['password']
        user = authenticate(request, username=u, password=p)

        if user:
            # Si estoy en modo colaborador, obligo a que sea trabajador
            if is_colaborador:
                if hasattr(user, 'trabajador'):
                    login(request, user)
                    return redirect('admin_dashboard')
                else:
                    messages.error(
                        request, 'No tienes permisos de colaborador.')
            else:
                # modo “normal”: dejo que entren clientes y trabajadores

                if user and not is_colaborador:
                    if hasattr(user, 'cliente'):
                        login(request, user)
                        return redirect('cliente_panel')    # ← aquí el nombre exacto
                    else:
                        messages.error(request, 'No tienes permisos de cliente.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'login.html', context)


def registro_cliente(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroClienteForm()
    return render(request, 'registro_cliente.html', {'form': form})


@login_required(login_url='login')
@only_trabajador
def admin_dashboard(request):
    return render(request, 'admin_panel.html')


@login_required(login_url='login')
@only_cliente
def cliente_dashboard(request):
    
    cliente = request.user.cliente

    evaluaciones_realizadas = EvaluacionVenta.objects.filter(
        cliente=cliente, estado="COMPLETADO"
    )
    ventas_pendientes = EvaluacionVenta.objects.filter(
        cliente=cliente, estado="PENDIENTE"
    )

    context = {
        'evaluaciones_realizadas': evaluaciones_realizadas,
        'ventas_pendientes': ventas_pendientes,
        'total_pendientes': ventas_pendientes.count(),
    }
    return render(request, 'cliente_panel.html', context)


#############################################################
@login_required
def evaluar_venta(request, venta_id):
    # Validar rol cliente
    if not hasattr(request.user, 'rol') or request.user.rol != 'cliente':
        return render(request, 'error.html', {
            'mensaje': 'No tienes permisos para acceder a esta página. Debes ser un cliente registrado.'
        })

    # Obtener cliente asociado
    try:
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        return render(request, 'error.html', {
            'mensaje': 'No tienes un perfil de cliente asociado. Por favor contacta al administrador.'
        })

    # Obtener venta que pertenece a ese cliente
    try:
        venta = Venta.objects.get(id=venta_id, cliente=cliente)
    except Venta.DoesNotExist:
        return render(request, 'error.html', {
            'mensaje': 'No se encontró la venta solicitada o no te pertenece.'
        })

    trabajador = venta.usuario
    indicadores = Indicador.objects.filter(criterio__nombre="atencion")

    if request.method == 'POST':
        form = EvaluacionVentaForm(request.POST, indicadores=indicadores)
        if form.is_valid():
            evaluacion = EvaluacionVenta.objects.create(
                venta=venta,
                trabajador=trabajador,
                cliente=cliente,
                estado='COMPLETADO'

            )
            for indicador in indicadores:
                puntaje = int(form.cleaned_data[f'indicador_{indicador.id}'])
                RespuestaEvaluacionVenta.objects.create(
                    evaluacion=evaluacion,
                    indicador=indicador,
                    puntaje=puntaje
                )
            evaluacion.estado = 'COMPLETADO'
            evaluacion.save()
            return render(request, 'evaluacion_venta_ex.html')
    else:
        form = EvaluacionVentaForm(indicadores=indicadores)

    return render(request, 'evaluacion_venta_form.html', {
        'form': form,
        'venta': venta,
        'trabajador': trabajador,
        'cliente': cliente
    })


@login_required
def editar_evaluacion_trabajador(request, evaluacion_id):
    evaluacion = get_object_or_404(EvaluacionTrabajador, id=evaluacion_id)
    evaluado = evaluacion.evaluado
    # Si es FK, está bien. Si es M2M, tomar el primero: evaluado.puesto.first()
    puesto = evaluado.puesto

    # Obtener criterios asignados al puesto del evaluado
    criterios = Criterio.objects.filter(puesto=puesto)

    # Obtener indicadores relacionados a esos criterios
    indicadores = Indicador.objects.filter(criterio__in=criterios)

    # Obtener respuestas previas para precargar el formulario
    respuestas_actuales = {
        r.indicador_id: r.puntaje for r in evaluacion.respuestas.all()}

    if request.method == 'POST':
        form = EvaluacionTrabajadorForm(request.POST, indicadores=indicadores)
        if form.is_valid():
            for indicador in indicadores:
                puntaje = int(form.cleaned_data.get(
                    f'indicador_{indicador.id}', 0))
                RespuestaEvaluacionTrabajador.objects.update_or_create(
                    evaluacion=evaluacion,
                    indicador=indicador,
                    defaults={'puntaje': puntaje}
                )
            evaluacion.estado = 'COMPLETADA'
            evaluacion.save()
            return redirect('admin_dashboard')  # Cambia según tu ruta deseada
    else:
        initial_data = {f'indicador_{ind.id}': respuestas_actuales.get(
            ind.id, 0) for ind in indicadores}
        form = EvaluacionTrabajadorForm(
            indicadores=indicadores, initial=initial_data)

    return render(request, 'evaluacion_trabajador_form.html', {
        'form': form,
        'evaluacion': evaluacion,
        'evaluado': evaluado,
        'criterios': criterios,
        'puesto': puesto,
    })


# 333

def mostrar_evaluaciones(request):
    # Obtener todas las evaluaciones de trabajadores
    evaluaciones = EvaluacionTrabajador.objects.all()

    # Paginación (mostrar 10 evaluaciones por página)
    paginator = Paginator(evaluaciones, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pasar las evaluaciones al contexto
    context = {
        'page_obj': page_obj
    }

    return render(request, 'mostrar_evaluaciones.html', context)


@login_required
def evaluar_trabajadores(request):
    # Filtrar trabajadores con puestos específicos
    trabajadores = Usuario.objects.filter(rol='trabajador').exclude(
        puesto__nombre__in=['gerente', 'supervisor'])

    # Crear un listado de evaluaciones pendientes para cada trabajador
    evaluaciones_pendientes = []
    for trabajador in trabajadores:
        # Filtrar las evaluaciones pendientes para el evaluador actual
        evaluaciones = EvaluacionTrabajador.objects.filter(
            evaluador=request.user, evaluado=trabajador, estado='PENDIENTE')

        if evaluaciones.exists():
            evaluaciones_pendientes.append({
                'trabajador': trabajador,
                'evaluaciones': evaluaciones
            })

    context = {
        'evaluaciones_pendientes': evaluaciones_pendientes
    }
    return render(request, 'evaluaciones_pendientes.html', context)


@login_required
def guardar_evaluacion(request, evaluacion_id):
    # Obtener la evaluación específica
    evaluacion = get_object_or_404(EvaluacionTrabajador, id=evaluacion_id)

    # Verificar que el evaluador es el que está logueado (supervisor)
    if evaluacion.evaluador != request.user:
        return redirect('error')  # Redirigir si no es el supervisor

    if request.method == 'POST':
        # Guardar las respuestas de evaluación
        for indicador in evaluacion.evaluado.puesto.criterios.all().indicadores.all():
            puntaje = request.POST.get(f'puntaje_{indicador.id}')
            if puntaje:
                RespuestaEvaluacionTrabajador.objects.create(
                    evaluacion=evaluacion,
                    indicador=indicador,
                    puntaje=puntaje
                )

        # Cambiar el estado de la evaluación a 'COMPLETADA'
        evaluacion.estado = 'COMPLETADA'
        evaluacion.save()

        # Redirigir al listado de evaluaciones o mostrar un mensaje de éxito
        return redirect('mostrar_evaluaciones')

    return render(request, 'evaluacion_trabajador_form.html', {'evaluacion': evaluacion})


def crear_autoevaluacion(request):

    indicadores = Indicador.objects.all()

    if request.method == 'POST':
        form = AutoevaluacionTrabajadorForm(request.POST)
        formset = RespuestaAutoevaluacionFormSet(request.POST, queryset=None)
        if form.is_valid() and formset.is_valid():
            autoevaluacion = form.save(commit=False)
            autoevaluacion.evaluador = request.user
            autoevaluacion.save()
            for form_indicador in formset:
                respuesta = form_indicador.save(commit=False)
                respuesta.autoevaluacion = autoevaluacion
                respuesta.save()
            return redirect('lista_autoevaluaciones')
    else:
        form = AutoevaluacionTrabajadorForm()
        formset = RespuestaAutoevaluacionFormSet(queryset=None)

    return render(request, 'crear_autoevaluacion.html', {
        'form': form,
        'formset': formset,
        'indicadores': indicadores
    })


def lista_autoevaluaciones(request):
    autoevaluaciones = AutoevaluacionTrabajador.objects.all()
    return render(request, 'lista_autoevaluaciones.html', {'autoevaluaciones': autoevaluaciones})


@login_required
def realizar_autoevaluacion(request):
    indicadores = Indicador.objects.all()

    if request.method == 'POST':
        form = AutoevaluacionForm(indicadores, request.POST)
        if form.is_valid():
            evaluacion = AutoevaluacionTrabajador.objects.create(
                trabajador=request.user
            )
            for key, valoracion in form.cleaned_data.items():
                indicador_id = int(key.replace('indicador_', ''))
                puntaje = int(valoracion)
                RespuestaAutoevaluacionTrabajador.objects.create(
                    autoevaluacion=evaluacion,
                    indicador_id=indicador_id,
                    valoracion=valoracion,  # Guarda '1', '2', ..., '5'
                    puntaje=puntaje
                )
            return redirect('evaluacion_exitosa')
    else:
        form = AutoevaluacionForm(indicadores)

    return render(request, 'realizar_autoevaluacion.html', {
        'form': form,
        'trabajador': request.user,
        'indicadores': indicadores,
        'titulo': f'Autoevaluación - {request.user.get_full_name() or request.user.username}'
    })


def guardar_autoevaluacion(request):
    if request.method == 'POST':
        trabajador = request.user
        autoeval = AutoevaluacionTrabajador.objects.create(
            trabajador=trabajador)

        for key, valoracion in request.POST.items():
            if key.startswith('indicador_'):
                indicador_id = int(key.split('_')[1])
                respuesta = RespuestaAutoevaluacionTrabajador(
                    autoevaluacion=autoeval,
                    indicador_id=indicador_id,
                    valoracion=valoracion
                )
                respuesta.save()  # Importantísimo para que se calcule el puntaje automáticamente


def evaluacion_exitosa(request):
    return render(request, 'evaluacion_exitosa.html')


@login_required
def autoevaluacion_view(request):
    trabajador = request.user

    print(
        f"Usuario: {trabajador} - Rol: {getattr(trabajador, 'rol', 'No tiene rol')}")
    indicadores = Indicador.objects.all()
    print(f"Indicadores encontrados: {indicadores.count()}")

    # Opcionalmente comentar el filtro de rol para pruebas:
    # if not trabajador.is_authenticated or trabajador.rol != 'trabajador':
    #     messages.error(request, "No tienes permiso para acceder a esta página.")
    #     return redirect('pagina_inicio')

    if request.method == 'POST':
        # tu lógica para guardar respuestas aquí
        pass

    return render(request, 'realizar_autoevaluacion.html', {
        'trabajador': trabajador,
        'indicadores': indicadores,
    })

#####################################


@login_required
def lista_evaluaciones(request):
    usuario = request.user

    # 1) cargar periodo
    periodo = PeriodoEvaluacion.objects.filter(puesto=usuario.puesto).first()
    periodo_activo = periodo.esta_activo() if periodo else False

    # 2) filtrar según rol del evaluador
    puesto_nombre = usuario.puesto.nombre.lower() if usuario.puesto else ''

    if puesto_nombre == 'supervisor':
        # Supervisor ve a todos los trabajadores excepto supervisores/gerentes (y a sí mismo)
        empleados = Usuario.objects.filter(rol='trabajador')\
            .exclude(
                Q(puesto__nombre__iexact='supervisor') |
                Q(puesto__nombre__iexact='gerente') |
                Q(pk=usuario.pk)
        )

    elif puesto_nombre == 'gerente':
        # Gerente ve SOLO a los Supervisores
        empleados = Usuario.objects.filter(
            rol='trabajador',
            puesto__nombre__iexact='supervisor'
        )

    else:
        # Resto de usuarios no evalúan
        empleados = Usuario.objects.none()

    # 3) pre-crear evaluaciones pendientes
    for emp in empleados:
        EvaluacionTrabajador.objects.get_or_create(
            evaluador=usuario,
            evaluado=emp,
            defaults={
                'fecha_activacion': periodo.fecha_inicio if periodo else timezone.now(),
                'estado': 'PENDIENTE'
            }
        )

    # 4) recuperarlas para el template
    evaluaciones = EvaluacionTrabajador.objects.filter(evaluador=usuario)

    return render(request, 'lista_evaluaciones.html', {
        'evaluaciones':   evaluaciones,
        'periodo':        periodo,
        'periodo_activo': periodo_activo,
    })

from django.db.models import Q

@login_required
def gestion_empleados(request):
    query = request.GET.get('q', '')
    lista_empleados = Usuario.objects.filter(rol='trabajador')

    if query:
        lista_empleados = lista_empleados.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    paginator = Paginator(lista_empleados, 6)  # 6 empleados por página
    page = request.GET.get('page')
    empleados = paginator.get_page(page)

    return render(request, 'empleados/lista.html', {
        'empleados': empleados,
        'query': query
    })


@login_required
def agregar_empleado(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            empleado = form.save(commit=False)
            empleado.rol = 'trabajador'
            empleado.set_password('123456')  # Contraseña por defecto (puedes mejorar esto)
            empleado.save()
            return redirect('gestion_empleados')
    else:
        form = EmpleadoForm()
    return render(request, 'empleados/formulario.html', {'form': form, 'titulo': 'Agregar nuevo empleado'})

@login_required
def editar_empleado(request, id):
    empleado = get_object_or_404(Usuario, id=id)
    form = EmpleadoForm(request.POST or None, instance=empleado)
    if form.is_valid():
        form.save()
        return redirect('gestion_empleados')
    return render(request, 'empleados/formulario.html', {'form': form, 'titulo': 'Editar Empleado'})

@login_required
def eliminar_empleado(request, id):
    empleado = get_object_or_404(Usuario, id=id)
    empleado.delete()
    return redirect('gestion_empleados')
