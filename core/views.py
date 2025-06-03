from django.shortcuts import render, get_object_or_404, redirect
from .models import  Venta, Usuario, Cliente, EvaluacionVenta, EvaluacionTrabajador, Criterio, RespuestaEvaluacionTrabajador, Rol ,RespuestaEvaluacionVenta ,Indicador
from .forms import  RespuestaForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import RegistroClienteForm , EvaluacionVentaForm ,EvaluacionTrabajadorForm
from django.contrib.auth.decorators import login_required
from django.db.models import Avg




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

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # Puede ser email o username según tu modelo
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('cliente_panel')  # Redirige al inicio después del login
        else:
            messages.error(request, 'Credenciales inválidas. Intenta nuevamente.')

    return render(request, 'login.html')

def registro_cliente(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroClienteForm()
    return render(request, 'registro_cliente.html', {'form': form})

def admin_dashboard(request):
    return render(request, 'admin_panel.html')
@login_required
def cliente_dashboard(request):

    user = request.user

    if not hasattr(user, 'rol') or user.rol != 'cliente':
        return render(request, 'error.html', {
            'mensaje': 'No tienes permisos para acceder a esta página. Debes ser un cliente.'
        })

    try:
        cliente = Cliente.objects.get(user=user)
    except Cliente.DoesNotExist:
        return render(request, 'error.html', {
            'mensaje': 'No tienes un perfil cliente asociado.'
        })

    evaluaciones_realizadas = EvaluacionVenta.objects.filter(cliente=cliente)\
        .select_related('trabajador', 'venta')

    context = {
        'evaluaciones_realizadas': evaluaciones_realizadas,
    }
    return render(request, 'cliente_panel.html', context)

#####################
# @login_required
# def cliente_panel(request):
#     trabajadores = Usuario.objects.filter(rol='trabajador')
#     return render(request, 'cliente_panel.html', {'trabajadores': trabajadores})

# @login_required
# def evaluar_cliente(request, trabajador_id):
#     trabajador = get_object_or_404(Usuario, id=trabajador_id, rol='trabajador')
#     opciones = [(5, "Excelente", "success"), (4, "Muy Bueno", "primary"), (3, "Bueno", "info"), (2, "Regular", "warning"), (1, "Malo", "danger")]

#     if request.method == 'POST':
#         puntaje = int(request.POST.get('calidad_atencion'))
#         Evaluacion.objects.create(
#             evaluador=request.user,
#             evaluado=trabajador,
#             tipo='cliente',
#             puntaje=puntaje
#         )
#         return redirect('cliente_panel')

#     return render(request, 'encuesta_form.html', {
#         'trabajador': trabajador,
#         'detalle_actividad': 'Venta de Taladro Inalámbrico',
#         'fecha_actividad': '15 Enero 2024',
#         'opciones': opciones,
#     })


# @login_required
# def evaluar_venta(request, venta_id, pregunta_orden=1):
#     venta = get_object_or_404(Venta, id=venta_id)
#     cliente = venta.cliente
#     trabajador = venta.usuario  # Usuario que realizó la venta, rol trabajador esperado

#     preguntas = PreguntaEvaluacion.objects.order_by('orden')
#     total_preguntas = preguntas.count()

#     try:
#         pregunta = preguntas.get(orden=pregunta_orden)
#     except PreguntaEvaluacion.DoesNotExist:
#         # Si no hay más preguntas, redirigir a resumen
#         return redirect('resultado_evaluacion', venta_id=venta.id)

#     evaluacion, created = EvaluacionVenta.objects.get_or_create(
#         venta=venta,
#         cliente=cliente,
#         trabajador=trabajador,
#     )

#     if request.method == 'POST':
#         form = RespuestaForm(request.POST)
#         if form.is_valid():
#             puntuacion = int(form.cleaned_data['puntuacion'])
#             # Guardar o actualizar la respuesta a la pregunta actual
#             RespuestaEvaluacion.objects.update_or_create(
#                 evaluacion=evaluacion,
#                 pregunta=pregunta,
#                 defaults={'puntuacion': puntuacion}
#             )
#             siguiente = pregunta_orden + 1
#             if siguiente > total_preguntas:
#                 return redirect('resultado_evaluacion', venta_id=venta.id)
#             else:
#                 return redirect('evaluar_venta', venta_id=venta.id, pregunta_orden=siguiente)
#     else:
#         # Pre-cargar la respuesta si ya existe para esta pregunta
#         try:
#             respuesta = RespuestaEvaluacion.objects.get(evaluacion=evaluacion, pregunta=pregunta)
#             form = RespuestaForm(initial={'puntuacion': respuesta.puntuacion})
#         except RespuestaEvaluacion.DoesNotExist:
#             form = RespuestaForm()

#     progreso = int((pregunta_orden / total_preguntas) * 100)

#     return render(request, 'evaluacion/pregunta.html', {
#         'venta': venta,
#         'cliente': cliente,
#         'trabajador': trabajador,
#         'pregunta': pregunta,
#         'form': form,
#         'progreso': progreso,
#         'orden_actual': pregunta_orden,
#         'total_preguntas': total_preguntas,
#     })


# @login_required
# def resultado_evaluacion(request, venta_id):
#     venta = get_object_or_404(Venta, id=venta_id)
#     evaluacion = get_object_or_404(EvaluacionVenta, venta=venta)

#     respuestas = evaluacion.respuestaevaluacion_set.select_related('pregunta').order_by('pregunta__orden')

#     promedio = 0
#     if respuestas.exists():
#         promedio = sum(r.puntuacion for r in respuestas) / respuestas.count()

#     return render(request, 'evaluacion/resultado.html', {
#         'venta': venta,
#         'evaluacion': evaluacion,
#         'respuestas': respuestas,
#         'promedio': promedio,
#     })


# @login_required
# def admin_dashboard(request):
#     # Datos básicos
#     total_empleados = Usuario.objects.filter(rol_admin__nombre='Trabajador').count()
#     empleados = Usuario.objects.filter(rol_admin__nombre='Trabajador')
    
#     # # Evaluaciones por tipo
#     # evaluacion_cliente = Evaluacion.objects.filter(tipo='cliente')
#     # evaluacion_gerencial = Evaluacion.objects.filter(tipo='gerente')
#     # autoevaluacion = Evaluacion.objects.filter(tipo='auto')

#     # Calculamos datos para cada tipo de evaluación
#     def get_eval_data(queryset):
#         completadas = queryset.count()
#         # Ejemplo de pendientes, reemplaza según tu lógica:
#         pendientes = 0  # Puedes calcular pendientes si tienes campo para ello
#         promedio = queryset.aggregate(prom=Avg('puntaje'))['prom'] or 0
#         return {
#             'completadas': completadas,
#             'pendientes': pendientes,
#             'promedio': round(promedio, 1),
#         }

#     context = {
#         'total_empleados': total_empleados,
#         'empleados': empleados,
#         'evaluacion_cliente': get_eval_data(evaluacion_cliente),
#         'evaluacion_gerencial': get_eval_data(evaluacion_gerencial),
#         'autoevaluacion': get_eval_data(autoevaluacion),
#         'total_evaluaciones_cliente': evaluacion_cliente.count(),
#         'incidencias_activas': Incidencia.objects.filter(estado='abierta').count(),
#         'roles': Rol.objects.all(),
#         # Agrega otros datos que necesites para las otras pestañas
#     }
#     return render(request, 'admin_panel.html', context)


##################333
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
                cliente=cliente 
                
            )
            for indicador in indicadores:
                puntaje = int(form.cleaned_data[f'indicador_{indicador.id}'])
                RespuestaEvaluacionVenta.objects.create(
                    evaluacion=evaluacion,
                    indicador=indicador,
                    puntaje=puntaje
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

@login_required
def editar_evaluacion_trabajador(request, evaluacion_id):
    evaluacion = get_object_or_404(EvaluacionTrabajador, id=evaluacion_id)
    evaluado = evaluacion.evaluado
    puesto = evaluado.puesto

    # Criterios asignados al puesto del evaluado
    criterios = Criterio.objects.filter(puestos=puesto)
    indicadores = Indicador.objects.filter(criterio__in=criterios)

    # Obtiene las respuestas actuales en un dict {indicador_id: puntaje}
    respuestas_actuales = {r.indicador_id: r.puntaje for r in evaluacion.respuestas.all()}

    if request.method == 'POST':
        form = EvaluacionTrabajadorForm(request.POST, indicadores=indicadores)
        if form.is_valid():
            for indicador in indicadores:
                puntaje = form.cleaned_data.get(f'indicador_{indicador.id}')
                # Actualiza o crea la respuesta
                obj, created = RespuestaEvaluacionTrabajador.objects.update_or_create(
                    evaluacion=evaluacion,
                    indicador=indicador,
                    defaults={'puntaje': puntaje}
                )
            evaluacion.estado = 'COMPLETADA'
            evaluacion.save()
            return redirect('admin_dashboard')  # Ajusta a tu URL de éxito
    else:
        # Prepara datos iniciales para el formulario
        initial_data = {}
        for indicador in indicadores:
            initial_data[f'indicador_{indicador.id}'] = respuestas_actuales.get(indicador.id, 0)

        form = EvaluacionTrabajadorForm(indicadores=indicadores, initial=initial_data)

    context = {
        'form': form,
        'evaluacion': evaluacion,
        'evaluado': evaluado,
        'criterios': criterios,
    }
    return render(request, 'evaluacion_trabajador_form.html', context)