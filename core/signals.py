from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    EvaluacionTrabajador, EvaluacionVenta,
    PesoEvaluacion, ResultadoTotal, TipoEvaluacion,Trabajador
)
from django.db.models.signals import pre_delete


# @receiver(post_save, sender=EvaluacionTrabajador)
# def _recalcula(sender, instance, **kwargs):
#     # `instance.evaluado` es un User
#     usuario = instance.evaluado

#     # 1) Obtener el perfil Trabajador
#     try:
#         perfil = usuario.trabajador      # OneToOneField desde User → Trabajador
#     except (Trabajador.DoesNotExist, AttributeError):
#         return  # si no existe perfil, salimos

#     # 2) Sacar el puesto
#     puesto = perfil.puesto
#     if not puesto:
#         return

#     # 3) Última EvaluacionTrabajador completada
#     et = EvaluacionTrabajador.objects.filter(
#         evaluado=usuario, estado='COMPLETADA'
#     ).order_by('-fecha_creacion').first()
#     pt = et.puntaje_total if et else 0

#     # 4) Última EvaluacionVenta completada (usando el perfil Trabajador)
#     ev = EvaluacionVenta.objects.filter(
#         trabajador=perfil,        # ✔️ pasamos `perfil`, no `usuario`
#         estado='COMPLETADA'
#     ).order_by('-fecha').first()
#     pc = ev.puntaje_total if ev else 0

#     # 5) Autoevaluación (si aplica)
#     pa = 0

#     # 6) Pesos para este puesto
#     pesos_qs = PesoEvaluacion.objects.filter(puesto=puesto)
#     pesos = {p.tipo: p.peso for p in pesos_qs}

#     total = (
#         pesos.get(TipoEvaluacion.EVALUACION_TRABAJADOR, 0) * pt +
#         pesos.get(TipoEvaluacion.EVALUACION_CLIENTE,   0) * pc +
#         pesos.get(TipoEvaluacion.AUTOEVALUACION,       0) * pa
#     )

#     # 7) Crear o actualizar ResultadoTotal también con `perfil`
#     rt, creado = ResultadoTotal.objects.get_or_create(
#         trabajador=perfil,        # ✔️ aquí también `perfil`
#         defaults={
#             'puntaje_total':   total,
#             'fecha_ejecucion': timezone.now().date()
#         }
#     )
#     if not creado:
#         rt.puntaje_total   = total
#         rt.fecha_ejecucion = timezone.now().date()
#         rt.save()

def _recalcula(perfil: Trabajador):
    """
    Recalcula y guarda el ResultadoTotal de un Trabajador,
    sumando evaluación interna, de cliente y (si existiera) autoevaluación.
    """
    # --- 1) Puntaje de la última EvaluacionTrabajador completada ---
    et = (
        EvaluacionTrabajador.objects
        .filter(evaluado=perfil.user, estado='COMPLETADA')
        .order_by('-fecha_creacion')
        .first()
    )
    pt = et.puntaje_total if et else 0

    # --- 2) Puntaje de la última EvaluacionVenta completada ---
    ev = (
        EvaluacionVenta.objects
        .filter(trabajador=perfil, estado='COMPLETADA')
        .order_by('-fecha')
        .first()
    )
    pc = ev.puntaje_total if ev else 0

    # --- 3) Autoevaluación (si la tuvieras) ---
    pa = 0

    # --- 4) Pesos según el puesto del trabajador ---
    pesos = {
        p.tipo: p.peso
        for p in PesoEvaluacion.objects.filter(puesto=perfil.puesto)
    }

    total = (
        pesos.get(TipoEvaluacion.EVALUACION_TRABAJADOR, 0) * pt +
        pesos.get(TipoEvaluacion.EVALUACION_CLIENTE,     0) * pc +
        pesos.get(TipoEvaluacion.AUTOEVALUACION,         0) * pa
    )

    # --- 5) Crear o actualizar el ResultadoTotal ---
    rt, creado = ResultadoTotal.objects.get_or_create(
        trabajador=perfil,
        defaults={
            'puntaje_total':   total,
            'fecha_ejecucion': timezone.now().date()
        }
    )
    if not creado:
        rt.puntaje_total   = total
        rt.fecha_ejecucion = timezone.now().date()
        rt.save()

@receiver(post_save, sender=EvaluacionTrabajador)
@receiver(post_delete, sender=EvaluacionTrabajador)
def _on_trab(sender, instance, **kwargs):
    """
    Dispara recálculo cuando una EvaluacionTrabajador cambia a COMPLETADA o se borra.
    """
    signal = kwargs.get('signal')
    if signal is post_delete or instance.estado == 'COMPLETADA':
        try:
            perfil = instance.evaluado.trabajador
        except (Trabajador.DoesNotExist, AttributeError):
            return
        _recalcula(perfil)

@receiver(post_save, sender=EvaluacionVenta)
@receiver(post_delete, sender=EvaluacionVenta)
def _on_venta(sender, instance, **kwargs):
    perfil = instance.trabajador
    if getattr(instance, 'estado', '') == 'COMPLETADA' or kwargs.get('signal') is post_delete:
        _recalcula(perfil)

