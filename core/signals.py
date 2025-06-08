from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    EvaluacionTrabajador, EvaluacionVenta,
    PesoEvaluacion, ResultadoTotal, TipoEvaluacion
)

def _recalcula(usuario):
    puesto = usuario.puesto
    if not puesto: return
    # 1) último TRABAJADOR
    et = EvaluacionTrabajador.objects.filter(
        evaluado=usuario, estado='COMPLETADA'
    ).order_by('-fecha_creacion').first()
    pt = et.puntaje_total if et else 0
    # 2) última VENTA
    ev = EvaluacionVenta.objects.filter(
        trabajador=usuario, estado='COMPLETADA'
    ).order_by('-fecha').first()
    pc = ev.puntaje_total if ev else 0
    # 3) (opcional) auto
    pa = 0
    # 4) pesos para este puesto
    pesos = {p.tipo:p.peso for p in PesoEvaluacion.objects.filter(puesto=puesto)}
    total = (
        pesos.get(TipoEvaluacion.EVALUACION_TRABAJADOR,0)*pt +
        pesos.get(TipoEvaluacion.EVALUACION_CLIENTE,0)*pc +
        pesos.get(TipoEvaluacion.AUTOEVALUACION,0)*pa
    )
    rt,cre = ResultadoTotal.objects.get_or_create(
        trabajador=usuario,
        defaults={'puntaje_total':total,'fecha_ejecucion':timezone.now().date()}
    )
    if not cre:
        rt.puntaje_total=total
        rt.fecha_ejecucion=timezone.now().date()
        rt.save()

@receiver(post_save, sender=EvaluacionTrabajador)
@receiver(post_delete, sender=EvaluacionTrabajador)
def _on_trab(sender, instance, **kwargs):
    if getattr(instance,'estado','')=='COMPLETADA' or kwargs.get('signal') is post_delete:
        _recalcula(instance.evaluado)

@receiver(post_save, sender=EvaluacionVenta)
@receiver(post_delete, sender=EvaluacionVenta)
def _on_venta(sender, instance, **kwargs):
    if getattr(instance,'estado','')=='COMPLETADA' or kwargs.get('signal') is post_delete:
        _recalcula(instance.trabajador)
