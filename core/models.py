from django.db import models
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Puesto(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

# En tu modelo Usuario (ya existente), agregas:


class Usuario(AbstractUser):
    # Solo para clientes
    ROL_TIPOS = [
        ('cliente', 'Cliente'),
        ('trabajador', 'Trabajador'),
    ]
    rol = models.CharField(
        max_length=20, choices=ROL_TIPOS, blank=True, null=True)

    # Roles administrativos: trabajador, gerente
    rol_admin = models.ForeignKey(
        Rol, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')

    puesto = models.ForeignKey(
        Puesto, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.rol_admin:
            return f"{self.username} ({self.rol_admin.nombre})"
        elif self.rol:
            return f"{self.username} ({self.get_rol_display()})"
        else:
            return self.username


class Cliente(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, null=True, blank=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() if self.user else "Cliente sin usuario"


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre


class Venta(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    tiempo_inicio = models.DateTimeField(editable=False, null=True, blank=True)
    tiempo_fin = models.DateTimeField(null=True, blank=True)
    duracion_venta = models.DurationField(
        null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        now = timezone.now()
        if not self.pk:
            self.tiempo_inicio = now
        self.tiempo_fin = now
        if self.tiempo_inicio:
            self.duracion_venta = self.tiempo_fin - self.tiempo_inicio
        super().save(*args, **kwargs)

    @property
    def total(self):
        return sum(detalle.subtotal for detalle in self.detalleventa_set.all())

    @property
    def duracion_segundos(self):
        if self.duracion_venta:
            return int(self.duracion_venta.total_seconds())
        return 0

    def __str__(self):
        return f'Venta #{self.id} - {self.cliente}'


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        if not self.precio_unitario:
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        try:
            return self.cantidad * self.precio_unitario
        except (TypeError, ValueError):
            return 0

# # Evaluaciones (referencia)
# class Evaluacion(models.Model):
#     TIPO_CHOICES = [
#         ('auto', 'Autoevaluación'),
#         ('cliente', 'Evaluación de Cliente'),
#         ('gerente', 'Evaluación de Gerente'),
#     ]
#     evaluador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluaciones_hechas')
#     evaluado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluaciones_recibidas')
#     tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
#     puntaje = models.DecimalField(max_digits=5, decimal_places=2)
#     comentarios = models.TextField(blank=True, null=True)
#     fecha = models.DateField(auto_now_add=True)


class PreguntaEvaluacion(models.Model):
    texto = models.CharField(max_length=255)
    orden = models.PositiveIntegerField()

    def __str__(self):
        return self.texto

# class EvaluacionVenta(models.Model):
#     venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
#     trabajador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Usuario con rol trabajador
#     cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
#     fecha = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Evaluación venta #{self.venta.id} - Cliente: {self.cliente} - Trabajador: {self.trabajador}"

# class RespuestaEvaluacion(models.Model):
#     evaluacion = models.ForeignKey(EvaluacionVenta, on_delete=models.CASCADE)
#     pregunta = models.ForeignKey(PreguntaEvaluacion, on_delete=models.CASCADE)
#     puntuacion = models.PositiveSmallIntegerField()  # Valor 1 a 5

#     class Meta:
#         unique_together = ('evaluacion', 'pregunta')

#     def __str__(self):
#         return f"{self.pregunta.texto}: {self.puntuacion} estrellas"


class Incidencia(models.Model):
    empleado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    descripcion = models.TextField()
    estado = models.CharField(max_length=50)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Incidencia de {self.empleado} - {self.estado}"

# 3


class Criterio(models.Model):
    nombre = models.CharField(max_length=100, default='Sin nombre')
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    puesto = models.ForeignKey(
        Puesto, on_delete=models.SET_NULL, null=True, blank=True)

    rango_min = models.IntegerField()
    rango_max = models.IntegerField()

    def __str__(self):
        return f"{self.nombre}: {self.descripcion} ({self.rango_min}-{self.rango_max})"

    @property
    def puntaje(self):
        total = self.indicadores.aggregate(
            total=models.Sum('max_puntaje'))['total']
        return total or 0


class Indicador(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    criterio = models.ForeignKey(
        Criterio, on_delete=models.CASCADE, related_name='indicadores', default=0)

    max_puntaje = models.IntegerField(default=5)

    def __str__(self):
        return f"{self.nombre} ({self.criterio.nombre})"

# class Evaluacion(models.Model):
#     TIPO_CHOICES = [
#         ('auto', 'Autoevaluación'),
#         ('cliente', 'Evaluación de Cliente'),
#         ('gerente', 'Evaluación de Gerente'),
#     ]
#     evaluador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluaciones_hechas')
#     evaluado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluaciones_recibidas')
#     tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
#     puntaje_total = models.DecimalField(max_digits=5, decimal_places=2, default=0)
#     criterio_obtenido = models.ForeignKey(Criterio, null=True, blank=True, on_delete=models.SET_NULL)
#     comentarios = models.TextField(blank=True, null=True)
#     fecha = models.DateField(auto_now_add=True)

#     def __str__(self):
#         return f"Evaluacion {self.tipo} de {self.evaluado} por {self.evaluador}"

# class RespuestaEvaluacion(models.Model):
#     evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='respuestas')
#     indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE, null=True, blank=True)
#     puntaje = models.IntegerField(default=0)

#     def __str__(self):
#         return f"{self.indicador.nombre}: {self.puntaje}"


class EvaluacionVenta(models.Model):

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROGRESO', 'En progreso'),
        ('COMPLETADA', 'Completada'),
    ]

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    trabajador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'rol': 'trabajador'})
    # rol trabajador
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='PENDIENTE')

    def __str__(self):
        return f"Evaluación venta #{self.venta.id} - Cliente: {self.cliente} - Trabajador: {self.trabajador}"
    
    ###
    
    @property
    def puntaje_total(self):
        agg = self.respuestas.aggregate(total=Sum('puntaje'))['total']
        return agg or 0



class RespuestaEvaluacionVenta(models.Model):

    evaluacion = models.ForeignKey(
        EvaluacionVenta, on_delete=models.CASCADE, related_name='respuestas', default=1)
    indicador = models.ForeignKey(
        Indicador, on_delete=models.CASCADE, default=1)
    puntaje = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.indicador.nombre}: {self.puntaje}"


# 333

class EvaluacionTrabajador(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROGRESO', 'En progreso'),
        ('COMPLETADA', 'Completada'),
    ]

    evaluador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluaciones_realizadas')
    evaluado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluaciones_recibidas')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    # Valor por defecto para las nuevas evaluaciones
    fecha_activacion = models.DateTimeField(default=timezone.now)
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='PENDIENTE')
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Evaluación de {self.evaluador.get_full_name()} a {self.evaluado.get_full_name()}"

    def save(self, *args, **kwargs):
        # Si la fecha de activación es futura, no permita guardar la evaluación hasta esa fecha
        if self.fecha_activacion > timezone.now():
            raise ValueError(
                "No se puede crear una evaluación antes de la fecha de activación.")
        super().save(*args, **kwargs)
    ##### agrege 
    @property
    def puntaje_por_criterio(self):
        """
        Agrupa las respuestas por criterio y suma sus puntajes.
        Devuelve un dict { criterio_nombre: suma_puntaje }.
        """
        qs = self.respuestas.values(
            'indicador__criterio__nombre'
        ).annotate(total=Sum('puntaje'))
        return {
            entry['indicador__criterio__nombre']: entry['total'] or 0
            for entry in qs
        }

    # @property
    # def puntaje_total(self):
    #     """
    #     Suma todos los subtotales por criterio para devolver un único puntaje.
    #     """
    #     return sum(self.puntaje_por_criterio.values())
    @property
    def puntaje_total(self):
        agg = self.respuestas.aggregate(total=Sum('puntaje'))['total']
        return agg or 0


class RespuestaEvaluacionTrabajador(models.Model):
    evaluacion = models.ForeignKey(
        EvaluacionTrabajador, on_delete=models.CASCADE, related_name='respuestas')
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE)
    puntaje = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.indicador.nombre}: {self.puntaje}"


############## AUTOEVALUACION #######################
class AutoevaluacionTrabajador(models.Model):
    trabajador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='autoevaluaciones'
    )
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.trabajador} - {self.fecha}"

    # @property
    # def total_puntaje(self):
    #     return sum(res.puntaje for res in self.respuestas.all())
    @property
    def puntaje_por_criterio(self):
        """
        Igual que en EvaluacionTrabajador: agrupa las respuestas de la autoevaluación
        por criterio y suma sus puntajes.
        """
        qs = self.respuestas.values(
            'indicador__criterio__nombre'
        ).annotate(total=Sum('puntaje'))
        return {
            entry['indicador__criterio__nombre']: entry['total'] or 0
            for entry in qs
        }

    # @property
    # def puntaje_total(self):
    #     """
    #     Suma de los subtotales por criterio para esta autoevaluación.
    #     """
    #     return sum(self.puntaje_por_criterio.values())
    @property
    def puntaje_total(self):
        return sum(r.puntaje for r in self.respuestas.all())


class RespuestaAutoevaluacionTrabajador(models.Model):
    autoevaluacion = models.ForeignKey(
        'AutoevaluacionTrabajador',
        related_name='respuestas',
        on_delete=models.CASCADE
    )
    indicador = models.ForeignKey('Indicador', on_delete=models.PROTECT)

    VALORACION_CHOICES = [
        (1, 'Muy malo'),
        (2, 'Malo'),
        (3, 'Regular'),
        (4, 'Bueno'),
        (5, 'Excelente'),
    ]

    valoracion = models.PositiveSmallIntegerField(
        choices=VALORACION_CHOICES,
        default=3
    )

    puntaje = models.PositiveIntegerField(
        default=0)  # Se calcula automáticamente

    def save(self, *args, **kwargs):
        # Asignamos el puntaje igual a la valoración numérica
        self.puntaje = self.valoracion
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.indicador.nombre} - {self.get_valoracion_display()} ({self.puntaje})"


class PuntajeIndicador(models.Model):
    indicador = models.ForeignKey(
        'Indicador', on_delete=models.CASCADE, related_name="puntajes")
    malo = models.FloatField(default=0.0)
    regular = models.FloatField(default=0.0)
    bueno = models.FloatField(default=0.0)

    class Meta:
        app_label = 'core'

    def __str__(self):
        return f'Puntajes para {self.indicador.nombre}'


#######################################################################

# al inicio de tu models.py, junto a Puesto:
class TipoEvaluacion(models.TextChoices):
    AUTOEVALUACION = 'AUTO', 'Autoevaluación'
    EVALUACION_TRABAJADOR = 'TRAB', 'Evaluación Trabajador'
    EVALUACION_CLIENTE = 'CLIE', 'Evaluación Cliente'


class PesoEvaluacion(models.Model):
    puesto = models.ForeignKey(
        Puesto,
        on_delete=models.CASCADE,
        related_name='pesos_evaluacion'
    )
    tipo = models.CharField(max_length=4, choices=TipoEvaluacion.choices)
    peso = models.FloatField(
        help_text="Decimal entre 0 y 1, e.g. 0.5"
    )

    class Meta:
        unique_together = ('puesto', 'tipo')
        verbose_name = 'Peso de Evaluación'

    def __str__(self):
        return f"{self.puesto.nombre} – {self.get_tipo_display()}: {self.peso}"


class PeriodoEvaluacion(models.Model):
    puesto = models.ForeignKey(
        Puesto,
        on_delete=models.CASCADE,
        related_name='periodos_evaluacion'
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        unique_together = ('puesto', 'fecha_inicio', 'fecha_fin')

    def esta_activo(self):
        hoy = timezone.now().date()
        return self.fecha_inicio <= hoy <= self.fecha_fin

    def __str__(self):
        return f"{self.puesto.nombre}: {self.fecha_inicio} → {self.fecha_fin}"


class ResultadoTotal(models.Model):
    trabajador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resultados_totales'
    )
    fecha_ejecucion = models.DateField(auto_now_add=True)
    puntaje_total = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-fecha_ejecucion']

    def __str__(self):
        return f"{self.trabajador.username} @ {self.fecha_ejecucion}: {self.puntaje_total:.2f}"
