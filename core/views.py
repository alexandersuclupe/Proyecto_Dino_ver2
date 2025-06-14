import csv
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from openpyxl import Workbook
from .models import AutoevaluacionTrabajador, RespuestaAutoevaluacionTrabajador, TipoEvaluacion, Venta, Usuario, Cliente, EvaluacionVenta, EvaluacionTrabajador, Criterio, RespuestaEvaluacionTrabajador, Rol, RespuestaEvaluacionVenta, Indicador, PeriodoEvaluacion, PesoEvaluacion, ResultadoTotal, Trabajador
from .forms import CriterioForm, FiltroEvaluacionForm, IndicadorFormSet
from .forms import AutoevaluacionForm, AutoevaluacionTrabajadorForm, RespuestaAutoevaluacionFormSet, RespuestaForm, TrabajadorForm
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
from datetime import datetime, date, time
from django.utils.timezone import is_aware
from django.db.models import Sum


def gracias_encuesta(request):
    return render(request, 'gracias.html')


def index(request):
    return render(request, 'index.html')

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
                        # ← aquí el nombre exacto
                        return redirect('cliente_panel')
                    else:
                        messages.error(
                            request, 'No tienes permisos de cliente.')
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
        cliente=cliente, estado="COMPLETADA"
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
# @login_required
# def evaluar_venta(request, venta_id):
#     # # Validar rol cliente
#     # if not hasattr(request.user, 'rol') or request.user.rol != 'cliente':
#     #     return render(request, 'error.html', {
#     #         'mensaje': 'No tienes permisos para acceder a esta página. Debes ser un cliente registrado.'
#     #     })

#     # Obtener cliente asociado
#     try:
#         cliente = Cliente.objects.get(user=request.user)
#     except Cliente.DoesNotExist:
#         return render(request, 'error.html', {
#             'mensaje': 'No tienes un perfil de cliente asociado. Por favor contacta al administrador.'
#         })

#     # Obtener venta que pertenece a ese cliente
#     try:
#         venta = Venta.objects.get(id=venta_id, cliente=cliente)
#     except Venta.DoesNotExist:
#         return render(request, 'error.html', {
#             'mensaje': 'No se encontró la venta solicitada o no te pertenece.'
#         })

#     trabajador = venta.usuario
#     indicadores = Indicador.objects.filter(criterio__nombre="atencion")

#     if request.method == 'POST':
#         form = EvaluacionVentaForm(request.POST, indicadores=indicadores)
#         if form.is_valid():
#             evaluacion, creada = EvaluacionVenta.objects.update_or_create(
#             venta=venta,
#             cliente=cliente,
#             trabajador=trabajador,
#             defaults={'estado': 'COMPLETADA'}
#         )
#         # (Opcional) refrescar sus respuestas…
#         for indicador in indicadores:
#             puntaje = int(form.cleaned_data[f'indicador_{indicador.id}'])
#             RespuestaEvaluacionVenta.objects.update_or_create(
#                 evaluacion=evaluacion,
#                 indicador=indicador,
#                 defaults={'puntaje': puntaje}
#             )
#         return render(request, 'evaluacion_venta_ex.html')
#     else:
#         form = EvaluacionVentaForm(indicadores=indicadores)

#     return render(request, 'evaluacion_venta_form.html', {
#         'form': form,
#         'venta': venta,
#         'trabajador': trabajador,
#         'cliente': cliente
#     })
@login_required
def evaluar_venta(request, evaluacion_id):
    # 1) Recupero la evaluación (y compruebo que el cliente sea el suyo)
    evaluacion = get_object_or_404(
        EvaluacionVenta,
        id=evaluacion_id,
        cliente__user=request.user
    )

    # 2) Datos relacionados
    venta      = evaluacion.venta
    cliente    = evaluacion.cliente
    trabajador = evaluacion.trabajador

    # 3) Indicadores del criterio “atencion”
    indicadores = Indicador.objects.filter(criterio__nombre="atencion")

    if request.method == 'POST':
        form = EvaluacionVentaForm(request.POST, indicadores=indicadores)
        if form.is_valid():
            # 4) Marcar COMPLETADA y borrar viejas respuestas
            evaluacion.estado = 'COMPLETADA'
            evaluacion.save()
            RespuestaEvaluacionVenta.objects.filter(
                evaluacion=evaluacion
            ).delete()

            # 5) Crear exactamente las nuevas
            for indicador in indicadores:
                puntaje = int(form.cleaned_data[f'indicador_{indicador.id}'])
                RespuestaEvaluacionVenta.objects.create(
                    evaluacion=evaluacion,
                    indicador=indicador,
                    puntaje=puntaje
                )

            return render(request, 'evaluacion_venta_ex.html', {
                'evaluacion': evaluacion
            })

    else:
        form = EvaluacionVentaForm(indicadores=indicadores)

    return render(request, 'evaluacion_venta_form.html', {
        'form':       form,
        'evaluacion': evaluacion,
        'venta':      venta,
        'trabajador': trabajador,
        'cliente':    cliente,
    })

@login_required
def editar_evaluacion_trabajador(request, evaluacion_id):
    evaluacion = get_object_or_404(EvaluacionTrabajador, id=evaluacion_id)
    usuario_evaluado = evaluacion.evaluado  # Este es un objeto Usuario

    # Obtener el puesto desde el perfil Trabajador vinculado al Usuario
    try:
        perfil = usuario_evaluado.trabajador
        puesto_evaluado = perfil.puesto
    except (Trabajador.DoesNotExist, AttributeError):
        puesto_evaluado = None

    # Filtrar criterios asociados a ese puesto
    criterios = Criterio.objects.filter(puestos=puesto_evaluado) if puesto_evaluado else Criterio.objects.none()

    # Obtener los indicadores de esos criterios
    indicadores = Indicador.objects.filter(criterio__in=criterios)

    # Precargar respuestas previas
    respuestas_actuales = {
        r.indicador_id: r.puntaje
        for r in evaluacion.respuestas.all()
    }

    if request.method == 'POST':
        form = EvaluacionTrabajadorForm(request.POST, indicadores=indicadores)
        if form.is_valid():
            for indicador in indicadores:
                puntaje = int(form.cleaned_data.get(f'indicador_{indicador.id}', 0))
                RespuestaEvaluacionTrabajador.objects.update_or_create(
                    evaluacion=evaluacion,
                    indicador=indicador,
                    defaults={'puntaje': puntaje}
                )
            evaluacion.estado = 'COMPLETADA'
            evaluacion.save()
            return redirect('admin_dashboard')  # Ajusta esto a tu URL deseada
    else:
        initial_data = {
            f'indicador_{ind.id}': respuestas_actuales.get(ind.id, 0)
            for ind in indicadores
        }
        form = EvaluacionTrabajadorForm(indicadores=indicadores, initial=initial_data)

    return render(request, 'evaluacion_trabajador_form.html', {
        'form':       form,
        'evaluacion': evaluacion,
        'evaluado':   usuario_evaluado,
        'criterios':  criterios,
        'puesto':     puesto_evaluado,
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
    user = request.user

    # 1) Intentar conseguir el perfil de Trabajador
    try:
        perfil = user.trabajador
    except (Trabajador.DoesNotExist, AttributeError):
        # Si el usuario no tiene perfil de Trabajador, no puede ver evaluaciones
        return render(request, 'sin_permiso.html', status=403)

    puesto = perfil.puesto
    puesto_nombre = puesto.nombre.lower() if puesto else ''

    # 2) Cargar el periodo activo para ese puesto
    periodo = PeriodoEvaluacion.objects.filter(puesto=puesto).first()
    periodo_activo = periodo.esta_activo() if periodo else False

    # 3) Filtrar empleados según rol (puesto) del evaluador
    if puesto_nombre == 'supervisor':
        # Sólo vendedores, cajeros y almacenistas
        candidatos = ['vendedor', 'cajero', 'almacen']
        empleados = Trabajador.objects.filter(
            puesto__nombre__in=candidatos
        ).exclude(user=user)

    elif puesto_nombre == 'gerente':
        # Sólo supervisores
        empleados = Trabajador.objects.filter(puesto__nombre__iexact='supervisor')

    else:
        # Resto no evalúan
        empleados = Trabajador.objects.none()

    # 4) Pre-crear evaluaciones pendientes
    for emp in empleados:
        EvaluacionTrabajador.objects.get_or_create(
            evaluador=user,
            evaluado=emp.user,
            defaults={
                'fecha_activacion': periodo.fecha_inicio if periodo else timezone.now(),
                'estado': 'PENDIENTE'
            }
        )

    # 5) Recuperar y renderizar
    evaluaciones = EvaluacionTrabajador.objects.filter(evaluador=user)
    return render(request, 'lista_evaluaciones.html', {
        'evaluaciones':   evaluaciones,
        'periodo':        periodo,
        'periodo_activo': periodo_activo,
    })


@login_required
def gestion_empleados(request):
    query = request.GET.get('q', '')
    qs = Trabajador.objects.select_related('user')
    if query:
        qs = qs.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
    paginator = Paginator(qs, 6)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'empleados/lista.html', {
        'empleados': page_obj,
        'query': query
    })

# @login_required
# def agregar_empleado(request):
#     if request.method == 'POST':
#         form = EmpleadoForm(request.POST)
#         if form.is_valid():
#             empleado = form.save(commit=False)
#             empleado.rol = 'trabajador'
#             empleado.set_password('123456')  # Contraseña por defecto (puedes mejorar esto)
#             empleado.save()
#             return redirect('gestion_empleados')
#     else:
#         form = EmpleadoForm()
#     return render(request, 'empleados/formulario.html', {'form': form, 'titulo': 'Agregar nuevo empleado'})


@login_required
def agregar_empleado(request):
    if request.method == 'POST':
        form = TrabajadorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Registro exitoso.')
            return redirect('gestion_empleados')
    else:
        form = TrabajadorForm()

    return render(
        request,
        'empleados/formulario.html',
        {
            'form': form,
            'titulo': 'Agregar nuevo trabajador'
        }
    )


# @login_required
# def editar_empleado(request, id):
#     empleado = get_object_or_404(Usuario, id=id)
#     form = EmpleadoForm(request.POST or None, instance=empleado)
#     if form.is_valid():
#         form.save()
#         return redirect('gestion_empleados')
#     return render(request, 'empleados/formulario.html', {'form': form, 'titulo': 'Editar Empleado'})

@login_required
def editar_empleado(request, id):
    trabajador = get_object_or_404(Trabajador, id=id)
    form = TrabajadorForm(request.POST or None, instance=trabajador)

    if form.is_valid():
        form.save()
        return redirect('gestion_empleados')
    return render(request, 'empleados/formulario.html', {
        'form':   form,
        'titulo': 'Editar trabajador'
    })


def eliminar_empleado(request, id):
    empleado = get_object_or_404(Trabajador, id=id)  # Obtener el empleado con el ID proporcionado
    empleado.delete()  # Eliminar el empleado
    return redirect('gestion_empleados')  # Redirigir a la lista de empleados después de eliminar

# para calcular los pesos de los trabajadores


@login_required
@only_trabajador
def calcular_resultado_final(request, trabajador_id):
    # 1) Perfil de Trabajador
    perfil = get_object_or_404(Trabajador, id=trabajador_id)
    usuario_id = perfil.user_id

    # Determinamos si es vendedor
    puesto_lower = perfil.puesto.nombre.lower() if perfil.puesto else ''
    es_vendedor  = (puesto_lower == 'vendedor')

    # 2) Pesos según el puesto
    pesos = {
        peso.tipo: peso.peso
        for peso in PesoEvaluacion.objects.filter(puesto_id=perfil.puesto_id)
    }

    # 3) Autoevaluaciones
    auto_qs = AutoevaluacionTrabajador.objects.filter(trabajador_id=trabajador_id)
    auto_puntaje = sum(
        r.puntaje
        for a in auto_qs
        for r in a.respuestas.all()
    ) if auto_qs.exists() else 0

    # 4) Evaluaciones de cliente — sólo si es vendedor
    if es_vendedor:
        cliente_qs = EvaluacionVenta.objects.filter(
            trabajador_id=trabajador_id,
            estado="COMPLETADA"
        )
        cliente_puntaje = sum(
            r.puntaje
            for e in cliente_qs
            for r in e.respuestas.all()
        ) if cliente_qs.exists() else 0
    else:
        cliente_puntaje = 0

    # 5) Evaluaciones internas
    interno_qs = EvaluacionTrabajador.objects.filter(
        evaluado_id=usuario_id,
        estado="COMPLETADA"
    )
    interno_puntaje = sum(
        r.puntaje
        for e in interno_qs
        for r in e.respuestas.all()
    ) if interno_qs.exists() else 0

    # 6) Cálculo total: si no es vendedor, el peso "CLIE" simplemente no suma nada
    total = (
        auto_puntaje    * pesos.get("AUTO", 0) +
        cliente_puntaje * pesos.get("CLIE", 0) +
        interno_puntaje * pesos.get("TRAB", 0)
    )

    # 7) Guardar/actualizar ResultadoTotal
    ResultadoTotal.objects.update_or_create(
        trabajador_id=trabajador_id,
        defaults={"puntaje_total": total}
    )

    # 8) Leyenda
    if total >= 80:
        leyenda = "Aprobado"
    elif total >= 50:
        leyenda = "En proceso"
    else:
        leyenda = "En riesgo"

    return render(request, "empleados/resultado_total.html", {
        "trabajador":       perfil,
        "es_vendedor":      es_vendedor,
        "puntaje_autoeval": auto_puntaje,
        "puntaje_cliente":  cliente_puntaje,
        "puntaje_interno":  interno_puntaje,
        "peso_auto":        pesos.get("AUTO", 0),
        "peso_cliente":     pesos.get("CLIE", 0),
        "peso_interno":     pesos.get("TRAB", 0),
        "total":            total,
        "leyenda":          leyenda,
    })


@login_required
def lista_criterios(request):
    criterios = Criterio.objects.all()
    return render(request, 'criterios/lista_criterios.html', {
        'criterios': criterios
    })

@login_required
def nuevo_criterio(request):
    if request.method == 'POST':
        form    = CriterioForm(request.POST)
        formset = IndicadorFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            criterio = form.save()
            formset.instance = criterio    # asociamos el formset al nuevo criterio
            formset.save()                 # ¡guardamos los indicadores!
            return redirect('detalle_criterio', pk=criterio.pk)
    else:
        form    = CriterioForm()
        formset = IndicadorFormSet()
    return render(request, 'criterios/form_criterio.html', {
        'form':    form,
        'formset': formset,
        'titulo':  'Nuevo criterio e indicadores'
    })

@login_required
def editar_criterio(request, pk):
    criterio = get_object_or_404(Criterio, pk=pk)

    if request.method == 'POST':
        # 1) Asociamos POST al form de Criterio (edición)
        form    = CriterioForm(request.POST, instance=criterio)
        # 2) Y al formset de Indicadores, vinculándolo al mismo criterio
        formset = IndicadorFormSet(request.POST, instance=criterio)

        if form.is_valid() and formset.is_valid():
            # 3) Guardamos primero el criterio
            form.save()
            # 4) ¡MUY IMPORTANTE!: guardamos los indicadores (nuevos, modificados o borrados)
            formset.save()

            # 5) Redirigimos a la vista de detalle, donde se verán los indicadores actualizados
            return redirect('detalle_criterio', pk=criterio.pk)

    else:
        form    = CriterioForm(instance=criterio)
        formset = IndicadorFormSet(instance=criterio)

    return render(request, 'criterios/form_criterio.html', {
        'form':    form,
        'formset': formset,
        'titulo':  'Editar criterio e indicadores'
    })

@login_required
def detalle_criterio(request, pk):
    criterio    = get_object_or_404(Criterio, pk=pk)
    # Usa el related_name que tengas en el modelo Indicator->criterio.
    # Si en tu modelo pusiste related_name="indicadores":
    indicadores = criterio.indicadores.all()
    return render(request, 'criterios/detalle_criterio.html', {
        'criterio':    criterio,
        'indicadores': indicadores,
    })

@login_required
def eliminar_criterio(request, pk):
    criterio = get_object_or_404(Criterio, pk=pk)
    if request.method == 'POST':
        criterio.delete()
        return redirect('lista_criterios')
    return render(request, 'criterios/confirmar_eliminacion.html', {
        'criterio': criterio
    })



def normalizar_fecha(fecha):
    if isinstance(fecha, datetime):
        if is_aware(fecha):
            return fecha.replace(tzinfo=None)
        return fecha
    elif isinstance(fecha, date):
        return datetime.combine(fecha, time.min)
    return None



@login_required
def historial_evaluaciones(request):
 
    form        = FiltroEvaluacionForm(request.GET or None)
    tipo_filtro = request.GET.get('tipo', 'todas')
    busqueda    = request.GET.get('buscar', '').lower().strip()

    user              = request.user
    puesto_usuario    = getattr(getattr(user, 'trabajador', None), 'puesto', None)
    nombre_puesto     = (puesto_usuario.nombre.lower() if puesto_usuario else '')
    es_supervisor     = user.is_superuser or nombre_puesto == 'supervisor'

    evaluaciones = []

    # AUTOEVALUACIONES
    auto_qs = AutoevaluacionTrabajador.objects.select_related('trabajador')
    if not es_supervisor:
        auto_qs = auto_qs.filter(trabajador=user)
    if tipo_filtro in ['todas', 'AUTO']:
        for auto in auto_qs:
            if busqueda in str(auto.trabajador).lower():
                evaluaciones.append({
                    'id'                : auto.id,
                    'evaluado'          : auto.trabajador,
                    'evaluador'         : auto.trabajador,
                    'fecha'             : auto.fecha,
                    'tipo'              : 'AUTO',
                    'get_tipo_display'  : TIPO_CHOICES['AUTO'],
                    'puntaje'           : auto.puntaje_total,
                    'estado'            : 'Completada',
                })

    # EVALUACIONES TRABAJADOR
    et_qs = EvaluacionTrabajador.objects.select_related('evaluador', 'evaluado') \
                                        .filter(estado__iexact='Completada')
    if not es_supervisor:
        et_qs = et_qs.filter(evaluado=user)
    if tipo_filtro in ['todas', 'TRAB']:
        for e in et_qs:
            if busqueda in str(e.evaluado).lower() or busqueda in str(e.evaluador).lower():
                evaluaciones.append({
                    'id'                : e.id,  
                    'evaluado'          : e.evaluado,
                    'evaluador'         : e.evaluador,
                    'fecha'             : e.fecha_creacion,
                    'tipo'              : 'TRAB',
                    'get_tipo_display'  : TIPO_CHOICES['TRAB'],
                    'puntaje'           : e.puntaje_total,
                    'estado'            : 'Completada',
                })

    # EVALUACIONES CLIENTE
    ev_qs = EvaluacionVenta.objects.select_related('trabajador', 'cliente') \
                                   .filter(estado__iexact='Completada')
    if not es_supervisor:
        trabajador_inst = getattr(user, 'trabajador', None)
        ev_qs = ev_qs.filter(trabajador=trabajador_inst)
    if tipo_filtro in ['todas', 'CLIE']:
        for ev in ev_qs:
            if busqueda in str(ev.trabajador).lower() or busqueda in str(ev.cliente).lower():
                evaluaciones.append({
                    'id'                : ev.id,
                    'evaluado'          : ev.trabajador,
                    'evaluador'         : ev.cliente,
                    'fecha'             : ev.fecha,
                    'tipo'              : 'CLIE',
                    'get_tipo_display'  : TIPO_CHOICES['CLIE'],
                    'puntaje'           : ev.puntaje_total,
                    'estado'            : 'Completada',
                })

    # Ordenar por fecha descendente
    evaluaciones.sort(key=lambda x: normalizar_fecha(x['fecha']), reverse=True)

    context = {
        'evaluaciones' : evaluaciones,
        'form'         : form,
        'tipo_filtro'  : tipo_filtro,
        'busqueda'     : request.GET.get('buscar', ''),
        'TipoEvaluacion': TipoEvaluacion  # para el <select> del filtro
    }
    return render(request, 'historial.html', context)

from core.models import (
    AutoevaluacionTrabajador,
    EvaluacionTrabajador,
    EvaluacionVenta,
)

def exportar_evaluaciones_excel(request):
    user = request.user
    try:
        trabajador = Trabajador.objects.get(user=user)
    except Trabajador.DoesNotExist:
        trabajador = None

    es_admin = user.is_superuser or (
        trabajador and trabajador.puesto and trabajador.puesto.nombre.lower() == "supervisor"
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Evaluaciones"
    ws.append(['Evaluado', 'Evaluador', 'Fecha', 'Tipo', 'Puntaje', 'Estado'])

    auto_qs = AutoevaluacionTrabajador.objects.select_related('trabajador')
    if not es_admin:
        auto_qs = auto_qs.filter(trabajador=user)        

    for auto in auto_qs:
        puntaje = auto.respuestas.aggregate(
            total=Sum('puntaje')
        )['total'] or 0
        ws.append([
            str(auto.trabajador),
            str(auto.trabajador),
            auto.fecha.strftime('%Y-%m-%d'),
            "Autoevaluación",
            puntaje,
            "COMPLETADA",
        ])

    trab_qs = (
        EvaluacionTrabajador.objects
        .filter(estado='COMPLETADA')
        .select_related('evaluado', 'evaluador')
    )
    if not es_admin:
        trab_qs = trab_qs.filter(evaluado=user)          

    for ev in trab_qs:
        ws.append([
            str(ev.evaluado),
            str(ev.evaluador),
            ev.fecha_creacion.strftime('%Y-%m-%d'),
            "Evaluación del Trabajador",
            ev.puntaje_total,
            ev.estado,
        ])

    cli_qs = (
        EvaluacionVenta.objects
        .filter(estado='COMPLETADA')
        .select_related('trabajador', 'cliente')
    )
    if not es_admin and trabajador:
        cli_qs = cli_qs.filter(trabajador=trabajador)     

    for ev in cli_qs:
        ws.append([
            str(ev.trabajador),
            str(ev.cliente),
            ev.fecha.strftime('%Y-%m-%d'),
            "Evaluación del Cliente",
            ev.puntaje_total,
            ev.estado,
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="evaluaciones_completadas.xlsx"'
    wb.save(response)
    return response


def ver_evaluacion(request, tipo, id):
    try:
        if tipo == 'AUTO':
            evaluacion = AutoevaluacionTrabajador.objects.get(id=id)
        elif tipo == 'TRAB':
            evaluacion = EvaluacionTrabajador.objects.get(id=id)
        elif tipo == 'CLIE':
            evaluacion = EvaluacionVenta.objects.get(id=id)
        else:
            return HttpResponse("Tipo de evaluación no válido", status=400)

        return render(request, 'ver_evaluacion.html', {'evaluacion': evaluacion, 'tipo': tipo})

    except (AutoevaluacionTrabajador.DoesNotExist, EvaluacionTrabajador.DoesNotExist, EvaluacionVenta.DoesNotExist):
        raise Http404(f"Evaluación no encontrada: No {tipo} con ID {id}")