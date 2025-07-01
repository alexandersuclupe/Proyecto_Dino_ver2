from core.models import (
    AutoevaluacionTrabajador,
    EvaluacionTrabajador,
    EvaluacionVenta,
)
import csv
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from openpyxl import Workbook
from .models import AutoevaluacionTrabajador, RespuestaAutoevaluacionTrabajador, TipoEvaluacion, Venta, Usuario, Cliente, EvaluacionVenta, EvaluacionTrabajador, Criterio, RespuestaEvaluacionTrabajador, Rol, RespuestaEvaluacionVenta, Indicador, PeriodoEvaluacion, PesoEvaluacion, ResultadoTotal, Trabajador
from .forms import CriterioForm, FiltroEvaluacionForm, IndicadorFormSet
from .forms import AutoevaluacionForm, AutoevaluacionTrabajadorForm, RespuestaAutoevaluacionFormSet, RespuestaForm, TrabajadorForm ,PeriodoEvaluacionForm
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
            # Mensajes específicos según el fallo
            try:
                # Comprobar si el usuario existe en el modelo personalizado
                user = Usuario.objects.get(username=u)
                if not user.check_password(p):
                    messages.error(request, 'Contraseña incorrecta.')
            except Usuario.DoesNotExist:
                messages.error(
                    request, 'No hay usuario con perfil trabajador.')
            except Exception as e:
                # Si ocurre algún otro error
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


# @login_required(login_url='login')
# @only_trabajador
# def admin_dashboard(request):
#     return render(request, 'admin_panel.html')

@login_required(login_url='login')
@only_trabajador
def admin_dashboard(request):
    # 1) Total de empleados
    total_empleados = Trabajador.objects.count()

    # 2) Evaluaciones pendientes
    pendientes = EvaluacionVenta.objects.filter(estado='PENDIENTE').count()

    # 3) Promedio general de puntajes
    promedio_general = ResultadoTotal.objects.aggregate(
        avg=Avg('puntaje_total'))['avg'] or 0

    # 4) Empleados destacados (por ejemplo, los con puntaje ≥ 80)
    empleados_destacados = ResultadoTotal.objects.filter(
        puntaje_total__gte=80).count()

    # (Opcional) diferencias vs mes anterior — ajusta tu lógica real
    diff_total_empleados = "+2 vs mes anterior"
    diff_pendientes = "-3 vs mes anterior"
    diff_promedio = "+0.3 vs mes anterior"
    diff_destacados = "+1 vs mes anterior"

    # (Opcional) datos para gráficas
    chart_monthly_data = {
        'labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
        'datasets': [{
            'label': 'Evaluaciones',
            'data': [12, 18, 22, 19, 24, 20],
        }]
    }
    chart_trend_data = {
        'labels': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
        'datasets': [{
            'label': 'Promedio',
            'data': [3.8, 4.0, 4.1, 4.2, 4.3, 4.2],
        }]
    }

    return render(request, 'admin_panel.html', {
        'total_empleados':      total_empleados,
        'diff_total_empleados': diff_total_empleados,
        'evaluaciones_pendientes': pendientes,
        'diff_pendientes':      diff_pendientes,
        'promedio_general':     promedio_general,
        'diff_promedio':        diff_promedio,
        'empleados_destacados': empleados_destacados,
        'diff_destacados':      diff_destacados,
        'chart_monthly_data':   chart_monthly_data,
        'chart_trend_data':     chart_trend_data,
    })


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


############################################################
@login_required
def evaluar_venta(request, venta_id):
    # # Validar rol cliente
    # if not hasattr(request.user, 'rol') or request.user.rol != 'cliente':
    #     return render(request, 'error.html', {
    #         'mensaje': 'No tienes permisos para acceder a esta página. Debes ser un cliente registrado.'
    #     })

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
            evaluacion, creada = EvaluacionVenta.objects.update_or_create(
            venta=venta,
            cliente=cliente,
            trabajador=trabajador,
            defaults={'estado': 'COMPLETADA'}
        )
        # (Opcional) refrescar sus respuestas…
        for indicador in indicadores:
            puntaje = int(form.cleaned_data[f'indicador_{indicador.id}'])
            RespuestaEvaluacionVenta.objects.update_or_create(
                evaluacion=evaluacion,
                indicador=indicador,
                defaults={'puntaje': puntaje}
            )
        return render(request, 'evaluacion_venta_ex.html')
    else:
        form = EvaluacionVentaForm(indicadores=indicadores)

    return render(request, 'evaluacion_venta_form.html', {
        'form': form,
        'venta': venta,
        'trabajador': trabajador,
        'cliente': cliente
    })

# @login_required
# def evaluar_venta(request, evaluacion_id):
#     # 1) Recupero la evaluación (y compruebo que el cliente sea el suyo)
#     evaluacion = get_object_or_404(
#         EvaluacionVenta,
#         id=evaluacion_id,
#         cliente__user=request.user  # Verifica que el cliente está asociado con el usuario logueado
#     )

#     # 2) Datos relacionados
#     venta = evaluacion.venta
#     cliente = evaluacion.cliente
#     trabajador = evaluacion.trabajador

#     # 3) Indicadores del criterio "atencion"
#     indicadores = Indicador.objects.filter(criterio__nombre="atencion")

#     if request.method == 'POST':
#         form = EvaluacionVentaForm(request.POST, indicadores=indicadores)
#         if form.is_valid():
#             # 4) Marcar la evaluación como COMPLETADA y eliminar las respuestas anteriores
#             evaluacion.estado = 'COMPLETADA'
#             evaluacion.save()

#             # Borrar las respuestas anteriores de la evaluación
#             RespuestaEvaluacionVenta.objects.filter(
#                 evaluacion=evaluacion
#             ).delete()

#             # 5) Crear nuevas respuestas para cada indicador evaluado
#             for indicador in indicadores:
#                 puntaje = int(form.cleaned_data[f'indicador_{indicador.id}'])
#                 RespuestaEvaluacionVenta.objects.create(
#                     evaluacion=evaluacion,
#                     indicador=indicador,
#                     puntaje=puntaje
#                 )

#             # Redirige al reporte de evaluación
#             return render(request, 'evaluacion_venta_ex.html', {
#                 'evaluacion': evaluacion,
#                 'venta': venta,
#                 'cliente': cliente,
#                 'trabajador': trabajador,
#             })

#     else:
#         form = EvaluacionVentaForm(indicadores=indicadores)

#     return render(request, 'evaluacion_venta_form.html', {
#         'form': form,
#         'evaluacion': evaluacion,
#         'venta': venta,
#         'trabajador': trabajador,
#         'cliente': cliente,
#     })
# reporte ######################33

@login_required
def reporte_evaluacion_venta(request, evaluacion_id):
    evaluacion = get_object_or_404(EvaluacionVenta, id=evaluacion_id)
    usuario_evaluado = evaluacion.trabajador  # Este es un objeto Trabajador

    # Filtrar el criterio específico de "Atención"
    criterios = Criterio.objects.filter(nombre="atencion")

    # Obtener los indicadores de esos criterios
    indicadores = Indicador.objects.filter(criterio__in=criterios)

    # Obtener las respuestas de la evaluación de los indicadores
    respuestas_actuales = RespuestaEvaluacionVenta.objects.filter(
        evaluacion=evaluacion, indicador__in=indicadores)

    # Crear un diccionario con las respuestas para pasarlo a la plantilla
    respuestas_dict = {
        respuesta.indicador.id: respuesta.puntaje for respuesta in respuestas_actuales
    }

    # Calcular el puntaje total (sumando las respuestas)
    puntaje_total = sum(respuestas_dict.values())

    # Retornar el reporte
    return render(request, 'cliente/cliente_reporte_venta.html', {
        'evaluacion': evaluacion,
        'evaluado': usuario_evaluado,
        'criterios': criterios,
        'respuestas': respuestas_dict,  # Pasar las respuestas a la plantilla
        'puntaje_total': puntaje_total,  # Pasar el puntaje total a la plantilla
    })

# @login_required
# def editar_evaluacion_trabajador(request, evaluacion_id):
#     evaluacion = get_object_or_404(EvaluacionTrabajador, id=evaluacion_id)
#     usuario_evaluado = evaluacion.evaluado  # Este es un objeto Usuario

#     # Obtener el puesto desde el perfil Trabajador vinculado al Usuario
#     try:
#         perfil = usuario_evaluado.trabajador
#         puesto_evaluado = perfil.puesto
#     except (Trabajador.DoesNotExist, AttributeError):
#         puesto_evaluado = None

#     # Filtrar criterios asociados a ese puesto
#     criterios = Criterio.objects.filter(
#         puestos=puesto_evaluado) if puesto_evaluado else Criterio.objects.none()

#     # Obtener los indicadores de esos criterios
#     indicadores = Indicador.objects.filter(criterio__in=criterios)

#     # Precargar respuestas previas
#     respuestas_actuales = {
#         r.indicador_id: r.puntaje
#         for r in evaluacion.respuestas.all()
#     }

#     # Crear un diccionario con los puntajes actuales para cada indicador
#     initial_data = {
#         # Usamos el valor por defecto 0 si no hay respuesta
#         f'indicador_{ind.id}': respuestas_actuales.get(ind.id, 0)
#         for ind in indicadores
#     }

#     # Si la evaluación ya está completada, redirigir a la vista de reporte
#     if evaluacion.estado == 'COMPLETADA':
#         return redirect('reporte_evaluacion', evaluacion_id=evaluacion.id)

#     if request.method == 'POST':
#         form = EvaluacionTrabajadorForm(request.POST, indicadores=indicadores)
#         if form.is_valid():
#             # Guardar las respuestas seleccionadas
#             for indicador in indicadores:
#                 puntaje = int(form.cleaned_data.get(
#                     f'indicador_{indicador.id}', 0))
#                 RespuestaEvaluacionTrabajador.objects.update_or_create(
#                     evaluacion=evaluacion,
#                     indicador=indicador,
#                     defaults={'puntaje': puntaje}
#                 )
#             evaluacion.estado = 'COMPLETADA'
#             evaluacion.save()
#             # Redirige al reporte
#             return redirect('reporte_evaluacion', evaluacion_id=evaluacion.id)

#     else:
#         form = EvaluacionTrabajadorForm(
#             indicadores=indicadores, initial=initial_data)

#     return render(request, 'evaluacion_trabajador_form.html', {
#         'form': form,
#         'evaluacion': evaluacion,
#         'evaluado': usuario_evaluado,
#         'criterios': criterios,
#         'puesto': puesto_evaluado,
#         'initial_data': initial_data,  # Pasamos el diccionario con los puntajes iniciales
#     })
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

    # Filtrar criterios asociados a ese puesto, excluyendo aquellos que comienzan con "auto" o "autoevaluacion"
    criterios = Criterio.objects.filter(
        puestos=puesto_evaluado).exclude(
        nombre__istartswith='auto'
    ).exclude(
        nombre__istartswith='autoevaluacion'
    ) if puesto_evaluado else Criterio.objects.none()

    # Obtener los indicadores de esos criterios
    indicadores = Indicador.objects.filter(criterio__in=criterios)

    # Precargar respuestas previas
    respuestas_actuales = {
        r.indicador_id: r.puntaje
        for r in evaluacion.respuestas.all()
    }

    # Crear un diccionario con los puntajes actuales para cada indicador
    initial_data = {
        # Usamos el valor por defecto 0 si no hay respuesta
        f'indicador_{ind.id}': respuestas_actuales.get(ind.id, 0)
        for ind in indicadores
    }

    # Si la evaluación ya está completada, redirigir a la vista de reporte
    if evaluacion.estado == 'COMPLETADA':
        return redirect('reporte_evaluacion', evaluacion_id=evaluacion.id)

    if request.method == 'POST':
        form = EvaluacionTrabajadorForm(request.POST, indicadores=indicadores)
        if form.is_valid():
            # Guardar las respuestas seleccionadas
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
            # Redirige al reporte
            return redirect('reporte_evaluacion', evaluacion_id=evaluacion.id)

    else:
        form = EvaluacionTrabajadorForm(
            indicadores=indicadores, initial=initial_data)

    return render(request, 'evaluacion_trabajador_form.html', {
        'form': form,
        'evaluacion': evaluacion,
        'evaluado': usuario_evaluado,
        'criterios': criterios,
        'puesto': puesto_evaluado,
        'initial_data': initial_data,  # Pasamos el diccionario con los puntajes iniciales
    })


# @login_required
# def reporte_evaluacion(request, evaluacion_id):
#     evaluacion = get_object_or_404(EvaluacionTrabajador, id=evaluacion_id)
#     usuario_evaluado = evaluacion.evaluado  # Este es un objeto Usuario

#     # Obtener el puesto desde el perfil Trabajador vinculado al Usuario
#     try:
#         perfil = usuario_evaluado.trabajador
#         puesto_evaluado = perfil.puesto
#     except (Trabajador.DoesNotExist, AttributeError):
#         puesto_evaluado = None

#     # Filtrar criterios asociados a ese puesto
#     criterios = Criterio.objects.filter(
#         puestos=puesto_evaluado) if puesto_evaluado else Criterio.objects.none()

#     # Obtener los indicadores de esos criterios
#     indicadores = Indicador.objects.filter(criterio__in=criterios)

#     # Obtener las respuestas de la evaluación de los indicadores
#     respuestas_actuales = RespuestaEvaluacionTrabajador.objects.filter(
#         evaluacion=evaluacion)

#     # Crear un diccionario con las respuestas para pasarlo a la plantilla
#     respuestas_dict = {
#         respuesta.indicador_id: respuesta.puntaje for respuesta in respuestas_actuales
#     }

#     # Calcular el puntaje total
#     puntaje_total = sum(respuestas_dict.values())

#     return render(request, 'reporte_evaluacion.html', {
#         'evaluacion': evaluacion,
#         'evaluado': usuario_evaluado,
#         'criterios': criterios,
#         'respuestas': respuestas_dict,  # Pasar las respuestas a la plantilla
#         'puntaje_total': puntaje_total,  # Pasar el puntaje total a la plantilla
#     })
@login_required
def reporte_evaluacion(request, evaluacion_id):
    evaluacion = get_object_or_404(EvaluacionTrabajador, id=evaluacion_id)
    usuario_evaluado = evaluacion.evaluado  # Este es un objeto Usuario

    # Obtener el puesto desde el perfil Trabajador vinculado al Usuario
    try:
        perfil = usuario_evaluado.trabajador
        puesto_evaluado = perfil.puesto
    except (Trabajador.DoesNotExist, AttributeError):
        puesto_evaluado = None

    # Filtrar criterios asociados a esa evaluación, basándonos en los indicadores
    criterios = Criterio.objects.filter(
        indicadores__respuestaevaluaciontrabajador__evaluacion=evaluacion
    ).distinct()

    # Obtener los indicadores de esos criterios
    indicadores = Indicador.objects.filter(criterio__in=criterios)

    # Obtener las respuestas de la evaluación de los indicadores
    respuestas_actuales = RespuestaEvaluacionTrabajador.objects.filter(
        evaluacion=evaluacion, indicador__in=indicadores)

    # Crear un diccionario con las respuestas para pasarlo a la plantilla
    respuestas_dict = {
        respuesta.indicador_id: respuesta.puntaje for respuesta in respuestas_actuales
    }

    # Calcular el puntaje total
    puntaje_total = sum(respuestas_dict.values())

    return render(request, 'reporte_evaluacion.html', {
        'evaluacion': evaluacion,
        'evaluado': usuario_evaluado,
        'criterios': criterios,  # Solo los criterios asociados a la evaluación
        'respuestas': respuestas_dict,  # Pasar las respuestas a la plantilla
        'puntaje_total': puntaje_total,  # Pasar el puntaje total a la plantilla
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

    usuario = request.user                      

    try:
        trabajador = Trabajador.objects.get(user=usuario)
    except Trabajador.DoesNotExist:
        messages.error(request, "Este usuario no está asociado a un trabajador.")
        return redirect('evaluacion_exitosa')


    try:
        mes = int(request.GET.get('mes', timezone.now().month))
    except ValueError:
        mes = timezone.now().month

    if AutoevaluacionTrabajador.objects.filter(
        trabajador=usuario,       
        fecha__month=mes
    ).exists():
        messages.error(request, "Ya has realizado una autoevaluación este mes.")
        return redirect('evaluacion_exitosa')

    puesto = trabajador.puesto
    if not puesto:
        messages.error(request, "No se ha definido un puesto para este usuario.")
        return redirect('evaluacion_exitosa')

    criterios = (
        Criterio.objects
        .filter(
            puestos=puesto,
            estado='Activo',
            nombre__startswith='Autoevaluación'
        )
        .prefetch_related('indicadores')
    )

    if request.method == 'POST':
  
        autoeval = AutoevaluacionTrabajador.objects.create(trabajador=usuario)

        for criterio in criterios:
            for indicador in criterio.indicadores.all():
                valor = request.POST.get(f'indicador_{indicador.id}')
                if valor and valor.isdigit():
                    RespuestaAutoevaluacionTrabajador.objects.create(
                        autoevaluacion=autoeval,
                        indicador=indicador,
                        valoracion=int(valor)
                    )
        return redirect('evaluacion_exitosa')

    return render(
        request,
        'realizar_autoevaluacion.html',
        {
            'trabajador': trabajador,  
            'criterios' : criterios,
            'mes'       : mes,
        }
    )
    return render(request, 'realizar_autoevaluacion.html', context)

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
                respuesta.save()  


def evaluacion_exitosa(request):
    return render(request, 'evaluacion_exitosa.html')

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

# @login_required
# def lista_evaluaciones(request):
#     user = request.user

#     # 1) Intentar conseguir el perfil de Trabajador
#     try:
#         perfil = user.trabajador
#     except (Trabajador.DoesNotExist, AttributeError):
#         # Si el usuario no tiene perfil de Trabajador, no puede ver evaluaciones
#         return render(request, 'sin_permiso.html', status=403)

#     puesto = perfil.puesto
#     puesto_nombre = puesto.nombre.lower() if puesto else ''

#     # 2) Cargar el periodo activo para ese puesto
#     periodo = PeriodoEvaluacion.objects.filter(puesto=puesto,estado="Activo").first()
#     periodo_activo = periodo is not None

#     # 3) Filtrar empleados según rol (puesto) del evaluador
#     if puesto_nombre == 'supervisor':
#         candidatos = ['vendedor', 'cajero', 'almacen']
#         empleados = Trabajador.objects.filter(
#             puesto__nombre__in=candidatos
#         ).exclude(user=user)

#     elif puesto_nombre == 'gerente':
#         empleados = Trabajador.objects.filter(
#             puesto__nombre__iexact='supervisor')
#     else:
#         empleados = Trabajador.objects.none()

#     # 4) Pre-crear evaluaciones pendientes
#     for emp in empleados:
#         EvaluacionTrabajador.objects.get_or_create(
#             evaluador=user,
#             evaluado=emp.user,
#             defaults={
#                 'fecha_activacion': periodo.fecha_inicio if periodo else timezone.now(),
#                 'estado': 'PENDIENTE'
#             }
#         )

#     # 5) Recuperar los filtros desde la URL
#     estado = request.GET.get('estado', '')
#     trabajador = request.GET.get('trabajador', '')

#     # 6) Filtrar evaluaciones por estado y trabajador
#     evaluaciones = EvaluacionTrabajador.objects.filter(evaluador=user)

#     if estado:
#         evaluaciones = evaluaciones.filter(estado=estado)

#     if trabajador:
#         evaluaciones = evaluaciones.filter(
#             evaluado__username__icontains=trabajador)

#     # 7) Renderizar la plantilla
#     return render(request, 'lista_evaluaciones.html', {
#         'evaluaciones':   evaluaciones,
#         'periodo':        periodo,
#         'periodo_activo': periodo_activo,
#         'estado': estado,
#         'trabajador': trabajador,
#     })

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
    periodo = PeriodoEvaluacion.objects.filter(puesto=puesto, estado="Activo").first()

    # Verificar si existe un periodo activo
    periodo_activo = periodo is not None

    if not periodo_activo:
        # Si el periodo no está activo, redirigir o mostrar un mensaje
        return render(request, 'sin_periodo_activo.html')  # Asegúrate de crear esta plantilla

    # 3) Filtrar empleados según rol (puesto) del evaluador
    if puesto_nombre == 'supervisor':
        candidatos = ['vendedor', 'cajero', 'almacen']
        empleados = Trabajador.objects.filter(
            puesto__nombre__in=candidatos
        ).exclude(user=user)

    elif puesto_nombre == 'gerente':
        # Filtrar solo supervisores para los gerentes
        empleados = Trabajador.objects.filter(
            puesto__nombre__iexact='supervisor'  # Comparación insensible a mayúsculas/minúsculas
        ).exclude(user=user)  # Excluir al propio gerente

    else:
        empleados = Trabajador.objects.none()

    # 4) Pre-crear evaluaciones pendientes (para nuevas fechas de activación)
    for emp in empleados:
        # Verificar si ya existe una evaluación para ese periodo y ese trabajador
        evaluacion_existente = EvaluacionTrabajador.objects.filter(
            evaluador=user,
            evaluado=emp.user,
            fecha_activacion=periodo.fecha_inicio).first()

        # Si no existe una evaluación para esta fecha, crearla
        if not evaluacion_existente:
            nueva_evaluacion = EvaluacionTrabajador.objects.create(
                evaluador=user,
                evaluado=emp.user,
                fecha_activacion=periodo.fecha_inicio,  # Nueva fecha de activación
                estado='PENDIENTE'  # El estado inicial
            )
            nueva_evaluacion.save()  # Guardar la nueva evaluación

    # 5) Recuperar los filtros desde la URL
    estado = request.GET.get('estado', '')
    trabajador = request.GET.get('trabajador', '')

    # 6) Filtrar evaluaciones por estado y trabajador
    evaluaciones = EvaluacionTrabajador.objects.filter(evaluador=user)

    if estado:
        evaluaciones = evaluaciones.filter(estado=estado)

    if trabajador:
        evaluaciones = evaluaciones.filter(
            evaluado__username__icontains=trabajador)

    # 7) Renderizar la plantilla
    return render(request, 'lista_evaluaciones.html', {
        'evaluaciones': evaluaciones,
        'periodo': periodo,
        'periodo_activo': periodo_activo,
        'estado': estado,
        'trabajador': trabajador,
    })



# @login_required
# def lista_evaluaciones(request):
#     user = request.user

#     # 1) Intentar conseguir el perfil de Trabajador
#     try:
#         perfil = user.trabajador
#     except (Trabajador.DoesNotExist, AttributeError):
#         # Si el usuario no tiene perfil de Trabajador, no puede ver evaluaciones
#         return render(request, 'sin_permiso.html', status=403)

#     puesto = perfil.puesto
#     puesto_nombre = puesto.nombre.lower() if puesto else ''

#     # 2) Cargar el periodo activo para ese puesto
#     # 2) Cargar el periodo activo para ese puesto
#     periodo = PeriodoEvaluacion.objects.filter(puesto=puesto, estado="Activo").first()

#     # Verificar si existe un periodo activo
#     periodo_activo = periodo is not None

#     if not periodo_activo:
#         # Si el periodo no está activo, redirigir o mostrar un mensaje
#         return render(request, 'sin_periodo_activo.html')  # Asegúrate de crear esta plantilla

#     # 3) Filtrar empleados según rol (puesto) del evaluador
#     if puesto_nombre == 'supervisor':
#         candidatos = ['vendedor', 'cajero', 'almacen']
#         empleados = Trabajador.objects.filter(
#             puesto__nombre__in=candidatos
#         ).exclude(user=user)

#     elif puesto_nombre == 'gerente':
#         empleados = Trabajador.objects.filter(
#             puesto__nombre__iexact='supervisor')
#     else:
#         empleados = Trabajador.objects.none()

#     # 4) Pre-crear evaluaciones pendientes
#     for emp in empleados:
#         EvaluacionTrabajador.objects.get_or_create(
#             evaluador=user,
#             evaluado=emp.user,
#             defaults={
#                 'fecha_activacion': periodo.fecha_inicio if periodo else timezone.now(), 
#                 'estado': 'PENDIENTE'
#             }
#         )

#     # 5) Recuperar los filtros desde la URL
#     estado = request.GET.get('estado', '')
#     trabajador = request.GET.get('trabajador', '')

#     # 6) Filtrar evaluaciones por estado y trabajador
#     evaluaciones = EvaluacionTrabajador.objects.filter(evaluador=user)

#     if estado:
#         evaluaciones = evaluaciones.filter(estado=estado)

#     if trabajador:
#         evaluaciones = evaluaciones.filter(
#             evaluado__username__icontains=trabajador)

#     # 7) Renderizar la plantilla
#     return render(request, 'lista_evaluaciones.html', {
#         'evaluaciones': evaluaciones,
#         'periodo': periodo,
#         'periodo_activo': periodo_activo,
#         'estado': estado,
#         'trabajador': trabajador,
#     })


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
    # Obtener el empleado con el ID proporcionado
    empleado = get_object_or_404(Trabajador, id=id)
    empleado.delete()  # Eliminar el empleado
    # Redirigir a la lista de empleados después de eliminar
    return redirect('gestion_empleados')

# para calcular los pesos de los trabajadores


@login_required
@only_trabajador
def calcular_resultado_final(request, trabajador_id):
    # Obtener el trabajador y su puesto
    trab = get_object_or_404(Trabajador, id=trabajador_id)
    usuario = trab.user

    # Obtener el puesto del trabajador
    puesto_trabajador = trab.puesto

    # Consultar los pesos de las evaluaciones según el puesto del trabajador
    try:
        peso_auto = PesoEvaluacion.objects.get(puesto=puesto_trabajador, tipo='AUTO').peso
        peso_cliente = PesoEvaluacion.objects.get(puesto=puesto_trabajador, tipo='CLIE').peso
        peso_interno = PesoEvaluacion.objects.get(puesto=puesto_trabajador, tipo='TRAB').peso
    except PesoEvaluacion.DoesNotExist:
        # Si no existe el peso para el tipo de evaluación, asignar valores predeterminados
        peso_auto = 0.30
        peso_cliente = 0.40
        peso_interno = 0.30

    # Obtener los puntajes de las evaluaciones
    auto_puntaje = AutoevaluacionTrabajador.objects.filter(trabajador=usuario).aggregate(
        total=Sum('respuestas__puntaje'))['total'] or 0

    cliente_puntaje = EvaluacionVenta.objects.filter(trabajador=trab, estado='COMPLETADA').aggregate(
        total=Sum('respuestas__puntaje'))['total'] or 0

    interno_puntaje = EvaluacionTrabajador.objects.filter(evaluado=usuario, estado='COMPLETADA').aggregate(
        total=Sum('respuestas__puntaje'))['total'] or 0

    # Calcular el total ponderado
    total = round(
        auto_puntaje * peso_auto +
        cliente_puntaje * peso_cliente +
        interno_puntaje * peso_interno,
        2
    )

    # Asignar la leyenda según el puntaje total
    if total >= 80:
        leyenda = 'Aprobado'
    elif total >= 50:
        leyenda = 'En proceso'
    else:
        leyenda = 'En riesgo'

    # Retornar la plantilla con los datos
    return render(
        request,
        'empleados/resultado_total.html',
        {
            'trabajador': trab,
            'puntaje_autoeval': auto_puntaje,
            'puntaje_cliente': cliente_puntaje,
            'puntaje_interno': interno_puntaje,
            'peso_auto': peso_auto * 100,
            'peso_cliente': peso_cliente * 100,
            'peso_interno': peso_interno * 100,
            'total': total,
            'leyenda': leyenda,
        }
    )


# @login_required
# def lista_criterios(request):
#     criterios = Criterio.objects.all()
#     return render(request, 'criterios/lista_criterios.html', {
#         'criterios': criterios
#     })
@login_required
def lista_criterios(request):
    criterios = Criterio.objects.all()

    # Filtrar por nombre del criterio
    nombre_criterio = request.GET.get('nombre', '')
    if nombre_criterio:
        criterios = criterios.filter(nombre__icontains=nombre_criterio)

    # Filtrar por puesto
    puesto_criterio = request.GET.get('puesto', '')
    if puesto_criterio:
        criterios = criterios.filter(puestos__nombre__icontains=puesto_criterio)

    return render(request, 'criterios/lista_criterios.html', {
        'criterios': criterios,
        'nombre_criterio': nombre_criterio,
        'puesto_criterio': puesto_criterio
    })

@login_required
def nuevo_criterio(request):
    if request.method == 'POST':
        form = CriterioForm(request.POST)
        formset = IndicadorFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            criterio = form.save()
            formset.instance = criterio    # asociamos el formset al nuevo criterio
            formset.save()                 # ¡guardamos los indicadores!
            return redirect('detalle_criterio', pk=criterio.pk)
    else:
        form = CriterioForm()
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
        form = CriterioForm(request.POST, instance=criterio)
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
        form = CriterioForm(instance=criterio)
        formset = IndicadorFormSet(instance=criterio)

    return render(request, 'criterios/form_criterio.html', {
        'form':    form,
        'formset': formset,
        'titulo':  'Editar criterio e indicadores'
    })


@login_required
def detalle_criterio(request, pk):
    criterio = get_object_or_404(Criterio, pk=pk)
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


TIPO_CHOICES = {
    'AUTO': 'Autoevaluación',
    'TRAB': 'Evaluación del Trabajador',
    'CLIE': 'Evaluación del Cliente',
}


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
    form = FiltroEvaluacionForm(request.GET or None)
    tipo_filtro = request.GET.get('tipo', 'todas')
    busqueda = request.GET.get('buscar', '').lower().strip()

    user = request.user
    trabajador = getattr(user, 'trabajador', None)
    puesto_usuario = getattr(trabajador, 'puesto', None)
    nombre_puesto = (puesto_usuario.nombre.lower() if puesto_usuario else '')

    es_gerente = nombre_puesto == 'gerente'
    ver_solo_propias = nombre_puesto in [
        'supervisor', 'cajero', 'almacen', 'vendedor']

    evaluaciones = []

    # AUTOEVALUACIONES
    auto_qs = AutoevaluacionTrabajador.objects.select_related('trabajador')
    if ver_solo_propias:
        auto_qs = auto_qs.filter(trabajador=user)
    if tipo_filtro in ['todas', 'AUTO']:
        for auto in auto_qs:
            if busqueda in str(auto.trabajador).lower():
                evaluaciones.append({
                    'id': auto.id,
                    'evaluado': auto.trabajador,
                    'evaluador': auto.trabajador,
                    'fecha': auto.fecha,
                    'tipo': 'AUTO',
                    'get_tipo_display': TIPO_CHOICES['AUTO'],
                    'puntaje': auto.puntaje_total,
                    'estado': 'Completada',
                })

    # EVALUACIONES TRABAJADOR
    et_qs = EvaluacionTrabajador.objects.select_related('evaluador', 'evaluado') \
                                        .filter(estado__iexact='Completada')
    if ver_solo_propias:
        et_qs = et_qs.filter(evaluado=user)
    if tipo_filtro in ['todas', 'TRAB']:
        for e in et_qs:
            if busqueda in str(e.evaluado).lower() or busqueda in str(e.evaluador).lower():
                evaluaciones.append({
                    'id': e.id,
                    'evaluado': e.evaluado,
                    'evaluador': e.evaluador,
                    'fecha': e.fecha_creacion,
                    'tipo': 'TRAB',
                    'get_tipo_display': TIPO_CHOICES['TRAB'],
                    'puntaje': e.puntaje_total,
                    'estado': 'Completada',
                })

    # EVALUACIONES CLIENTE
    ev_qs = EvaluacionVenta.objects.select_related('trabajador', 'cliente') \
                                   .filter(estado__iexact='Completada')
    if ver_solo_propias:
        ev_qs = ev_qs.filter(trabajador=trabajador)
    if tipo_filtro in ['todas', 'CLIE']:
        for ev in ev_qs:
            if busqueda in str(ev.trabajador).lower() or busqueda in str(ev.cliente).lower():
                evaluaciones.append({
                    'id': ev.id,
                    'evaluado': ev.trabajador,
                    'evaluador': ev.cliente,
                    'fecha': ev.fecha,
                    'tipo': 'CLIE',
                    'get_tipo_display': TIPO_CHOICES['CLIE'],
                    'puntaje': ev.puntaje_total,
                    'estado': 'Completada',
                })

    # Ordenar por fecha descendente
    evaluaciones.sort(key=lambda x: normalizar_fecha(x['fecha']), reverse=True)

    context = {
        'evaluaciones': evaluaciones,
        'form': form,
        'tipo_filtro': tipo_filtro,
        'busqueda': request.GET.get('buscar', ''),
        'TipoEvaluacion': TipoEvaluacion  # para el <select> del filtro
    }
    return render(request, 'historial.html', context)


def exportar_evaluaciones_excel(request):
    user = request.user
    try:
        trabajador = Trabajador.objects.get(user=user)
    except Trabajador.DoesNotExist:
        trabajador = None

    es_admin = user.is_superuser or (
        trabajador and trabajador.puesto and trabajador.puesto.nombre.lower() == "gerente"
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


@login_required
def lista_autoevaluaciones(request):
    user = request.user
    ahora = timezone.localtime()
    anio_actual = ahora.year
    mes_actual = ahora.month

    # Obtener el trabajador vinculado al usuario
    try:
        trabajador = user.trabajador
    except Trabajador.DoesNotExist:
        trabajador = None

    # Obtener autoevaluaciones del usuario
    autoevaluaciones = AutoevaluacionTrabajador.objects.filter(trabajador=user)

    autoevaluaciones_por_mes = {}
    for autoeval in autoevaluaciones:
        mes = autoeval.fecha_creacion.month
        autoevaluaciones_por_mes[mes] = autoeval

    meses_nombres = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    lista = []
    for mes in range(6, 13):  # Junio a Diciembre
        if mes in autoevaluaciones_por_mes:
            autoeval = autoevaluaciones_por_mes[mes]
            estado = "Completada"
            fecha_creacion_local = timezone.localtime(autoeval.fecha_creacion)
            fecha_limite = fecha_creacion_local.replace(day=28)
            lista.append({
                'mes': meses_nombres[mes - 1],
                'mes_numero': mes,
                'estado': estado,
                'autoevaluacion': autoeval,
                'fecha_completada': fecha_creacion_local,
                'mes_previo': meses_nombres[mes - 1],
                'fecha_limite': fecha_limite
            })
        else:
            estado = "No disponible"
            fecha_limite = ahora.replace(month=mes, day=28)

            # Verificar si hay un periodo de evaluación activo
            if trabajador and trabajador.puesto:
                try:
                    periodo = PeriodoEvaluacion.objects.get(
                        puesto=trabajador.puesto,
                        fecha_inicio__year=anio_actual,
                        fecha_inicio__month=mes
                    )
                    hoy = date.today()
                    if periodo.fecha_inicio <= hoy <= periodo.fecha_fin:
                        estado = "Disponible"
                        fecha_limite = periodo.fecha_fin
                except PeriodoEvaluacion.DoesNotExist:
                    pass

            lista.append({
                'mes': meses_nombres[mes - 1],
                'mes_numero': mes,
                'estado': estado,
                'autoevaluacion': None,
                'fecha_completada': None,
                'mes_previo': meses_nombres[mes - 1],
                'fecha_limite': fecha_limite
            })

    total = len(lista)
    disponibles = sum(1 for item in lista if item['estado'] == 'Disponible')
    completadas = sum(1 for item in lista if item['estado'] == 'Completada')

    return render(request, 'lista_autoevaluaciones.html', {
        'lista': lista,
        'total': total,
        'disponibles': disponibles,
        'completadas': completadas,
        'ahora': ahora,
    })


def ver_autoevaluacion(request, pk):
    evaluacion = get_object_or_404(
        AutoevaluacionTrabajador, pk=pk, trabajador=request.user)
    return render(request, 'ver_autoevaluacion.html', {'evaluacion': evaluacion})


########################################################################################33
@login_required
def seguimiento_trabajador(request):
    form = FiltroEvaluacionForm(request.GET or None)
    tipo_filtro = request.GET.get('tipo', 'todas')
    busqueda = request.GET.get('buscar', '').lower().strip()

    # Asignar el mes de junio como valor por defecto si no se proporciona
    mes_filtro = request.GET.get('mes', datetime.today().strftime('%Y-06'))  # Por defecto, junio de este año
    trabajador_filtro = request.GET.get('trabajador')  # Obtenemos el trabajador filtrado

    # Si el trabajador_filtro está presente, lo filtramos
    if trabajador_filtro:
        trabajador = Trabajador.objects.get(id=trabajador_filtro)
    else:
        trabajador = None

    evaluaciones = []

    # Filtrar las evaluaciones por mes si se proporciona
    mes_year_month = None  # Inicializamos como None
    try:
        mes_year_month = datetime.strptime(mes_filtro, "%Y-%m")  # Convertir el mes a datetime
    except ValueError:
        mes_year_month = None  # Si el formato no es válido, se asegura que sea None

    # Filtrar las autoevaluaciones
    auto_qs = AutoevaluacionTrabajador.objects.select_related('trabajador')
    if trabajador:
        auto_qs = auto_qs.filter(trabajador=trabajador)
    if tipo_filtro in ['todas', 'AUTO']:
        for auto in auto_qs:
            if busqueda in str(auto.trabajador).lower():
                if mes_year_month:
                    puntaje_total = ResultadoTotal.objects.filter(
                        trabajador=auto.trabajador,
                        fecha_ejecucion__year=mes_year_month.year,
                        fecha_ejecucion__month=mes_year_month.month
                    ).aggregate(Sum('puntaje_total'))['puntaje_total__sum'] or 0
                else:
                    puntaje_total = 0  # Si no hay mes, se coloca 0 como puntaje
                evaluaciones.append({
                    'id': auto.id,
                    'evaluado': auto.trabajador,
                    'evaluador': auto.trabajador,
                    'fecha': auto.fecha,
                    'tipo': 'AUTO',
                    'get_tipo_display': 'AUTO',
                    'puntaje': puntaje_total,
                    'estado': 'Completada',
                })

    # Filtrar las evaluaciones de trabajadores
    et_qs = EvaluacionTrabajador.objects.select_related('evaluador', 'evaluado').filter(estado__iexact='Completada')
    if trabajador:
        et_qs = et_qs.filter(evaluado=trabajador)
    if tipo_filtro in ['todas', 'TRAB']:
        for e in et_qs:
            if busqueda in str(e.evaluado).lower() or busqueda in str(e.evaluador).lower():
                if mes_year_month:
                    puntaje_total = ResultadoTotal.objects.filter(
                        trabajador=e.evaluado,
                        fecha_ejecucion__year=mes_year_month.year,
                        fecha_ejecucion__month=mes_year_month.month
                    ).aggregate(Sum('puntaje_total'))['puntaje_total__sum'] or 0
                else:
                    puntaje_total = 0  # Si no hay mes, se coloca 0 como puntaje
                evaluaciones.append({
                    'id': e.id,
                    'evaluado': e.evaluado,
                    'evaluador': e.evaluador,
                    'fecha': e.fecha_creacion,
                    'tipo': 'TRAB',
                    'get_tipo_display': 'TRAB',
                    'puntaje': puntaje_total,
                    'estado': 'Completada',
                })

    # Filtrar las evaluaciones de clientes
    ev_qs = EvaluacionVenta.objects.select_related('trabajador', 'cliente').filter(estado__iexact='Completada')
    if trabajador:
        ev_qs = ev_qs.filter(trabajador=trabajador)
    if tipo_filtro in ['todas', 'CLIE']:
        for ev in ev_qs:
            if busqueda in str(ev.trabajador).lower() or busqueda in str(ev.cliente).lower():
                if mes_year_month:
                    puntaje_total = ResultadoTotal.objects.filter(
                        trabajador=ev.trabajador,
                        fecha_ejecucion__year=mes_year_month.year,
                        fecha_ejecucion__month=mes_year_month.month
                    ).aggregate(Sum('puntaje_total'))['puntaje_total__sum'] or 0
                else:
                    puntaje_total = 0  # Si no hay mes, se coloca 0 como puntaje
                evaluaciones.append({
                    'id': ev.id,
                    'evaluado': ev.trabajador,
                    'evaluador': ev.cliente,
                    'fecha': ev.fecha,
                    'tipo': 'CLIE',
                    'get_tipo_display': 'CLIE',
                    'puntaje': puntaje_total,
                    'estado': 'Completada',
                })

    # Ordenar por fecha descendente
    evaluaciones.sort(key=lambda x: x['fecha'], reverse=True)

    # Para pasar los trabajadores al formulario
    trabajadores = Trabajador.objects.all()

    context = {
        'evaluaciones': evaluaciones,
        'form': form,
        'trabajadores': trabajadores,  # Para mostrar en el filtro
        'tipo_filtro': tipo_filtro,
        'busqueda': request.GET.get('buscar', ''),
        'mes_filtro': mes_filtro,
    }
    return render(request, 'seguimiento_trabajador.html', context)
########################################################################33

####################### programar evaluaciones ############################################


@login_required
def programar_periodo_evaluacion(request):
    if request.method == 'POST':
        form = PeriodoEvaluacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Periodo de evaluación programado exitosamente.")
            return redirect('lista_periodos')
        else:
            # Si el formulario no es válido, mostrar los mensajes de error
            for message in form.errors.get('__all__', []):
                messages.error(request, message)
            return render(request, 'periodo/programar_periodo.html', {'form': form})
    else:
        form = PeriodoEvaluacionForm()

    return render(request, 'periodo/programar_periodo.html', {'form': form})


@login_required
def lista_periodos(request):
    periodos = PeriodoEvaluacion.objects.all()
    return render(request, 'periodo/listar_periodos.html', {'periodos': periodos})

