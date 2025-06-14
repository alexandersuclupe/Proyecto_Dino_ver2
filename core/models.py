from django.db import models
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.models import AbstractUser
from django.conf import settings


### --- ROLES Y USUARIOS --- ###

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


class Usuario(AbstractUser):
    ROL_TIPOS = [
        ('cliente', 'Cliente'),
        ('trabajador', 'Trabajador'),
    ]
    rol = models.CharField(max_length=20, choices=ROL_TIPOS, blank=True, null=True)
    rol_admin = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    puesto = models.ForeignKey(Puesto, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.rol_admin:
            return f"{self.username} ({self.rol_admin.nombre})"
        elif self.rol:
            return f"{self.username} ({self.get_rol_display()})"
        return self.username


### --- CLIENTES Y TRABAJADORES --- ###

class Cliente(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cliente', null=True, blank=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() if self.user else "Cliente sin usuario"


class Trabajador(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trabajador', null=True, blank=True)
    puesto = models.ForeignKey(Puesto, on_delete=models.SET_NULL, null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
# <- NUEVO: campo para guardar la contraseña inicial
   # initial_password = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.puesto.nombre}"

    
### --- PRODUCTOS Y VENTAS --- ###

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre


class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Trabajador, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)

    tiempo_inicio = models.DateTimeField(editable=False, null=True, blank=True)
    tiempo_fin = models.DateTimeField(null=True, blank=True)
    duracion_venta = models.DurationField(null=True, blank=True, editable=False)

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
        return int(self.duracion_venta.total_seconds()) if self.duracion_venta else 0

    def __str__(self):
        return f'Venta #{self.id} - {self.cliente}'


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Solo asigna el precio si no fue especificado y hay producto
        if self.precio_unitario is None and self.producto:
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        if self.cantidad is not None and self.precio_unitario is not None:
            return self.cantidad * self.precio_unitario
        return 0


### --- EVALUACIÓN GENERAL --- ###

class TipoEvaluacion(models.TextChoices):
    AUTOEVALUACION = 'AUTO', 'Autoevaluación'
    EVALUACION_TRABAJADOR = 'TRAB', 'Evaluación Trabajador'
    EVALUACION_CLIENTE = 'CLIE', 'Evaluación Cliente'


class Criterio(models.Model):
    nombre = models.CharField(max_length=100, default='Sin nombre')
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    puesto = models.ForeignKey(Puesto, on_delete=models.SET_NULL, null=True, blank=True)
    rango_min = models.IntegerField()
    rango_max = models.IntegerField()

    def __str__(self):
        return f"{self.nombre} ({self.rango_min}-{self.rango_max})"

    @property
    def puntaje(self):
        return self.indicadores.aggregate(total=models.Sum('max_puntaje'))['total'] or 0


class Indicador(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    criterio = models.ForeignKey(Criterio, on_delete=models.CASCADE, related_name='indicadores')
    max_puntaje = models.IntegerField(default=5)

    def __str__(self):
        return f"{self.nombre} ({self.criterio.nombre})"


### --- AUTOEVALUACIÓN --- ###

class AutoevaluacionTrabajador(models.Model):
    trabajador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='autoevaluaciones')
    fecha = models.DateField(auto_now_add=True)

    @property
    def puntaje_total(self):
        return sum(r.puntaje for r in self.respuestas.all())

    def __str__(self):
        return f"{self.trabajador} - {self.fecha}"


class RespuestaAutoevaluacionTrabajador(models.Model):
    autoevaluacion = models.ForeignKey(AutoevaluacionTrabajador, related_name='respuestas', on_delete=models.CASCADE)
    indicador = models.ForeignKey(Indicador, on_delete=models.PROTECT)

    VALORACION_CHOICES = [(i, str(i)) for i in range(1, 6)]

    valoracion = models.PositiveSmallIntegerField(choices=VALORACION_CHOICES, default=3)
    puntaje = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        self.puntaje = self.valoracion
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.indicador.nombre} - {self.get_valoracion_display()} ({self.puntaje})"


### --- EVALUACIÓN CLIENTE --- ###

class EvaluacionVenta(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROGRESO', 'En progreso'),
        ('COMPLETADA', 'Completada'),
    ]
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    @property
    def puntaje_total(self):
        return self.respuestas.aggregate(total=Sum('puntaje'))['total'] or 0

    def __str__(self):
        return f"Evaluación venta #{self.venta.id} - {self.cliente}"


class RespuestaEvaluacionVenta(models.Model):
    evaluacion = models.ForeignKey(EvaluacionVenta, on_delete=models.CASCADE, related_name='respuestas')
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE)
    puntaje = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.indicador.nombre}: {self.puntaje}"


### --- EVALUACIÓN DEL GERENTE --- ###

class EvaluacionTrabajador(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROGRESO', 'En progreso'),
        ('COMPLETADA', 'Completada'),
    ]
    evaluador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluaciones_realizadas')
    evaluado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='evaluaciones_recibidas')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_activacion = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    observaciones = models.TextField(blank=True, null=True)

    @property
    def puntaje_total(self):
        return self.respuestas.aggregate(total=Sum('puntaje'))['total'] or 0

    def __str__(self):
        return f"Evaluación de {self.evaluador.get_full_name()} a {self.evaluado.get_full_name()}"


class RespuestaEvaluacionTrabajador(models.Model):
    evaluacion = models.ForeignKey(EvaluacionTrabajador, on_delete=models.CASCADE, related_name='respuestas')
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE)
    puntaje = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.indicador.nombre}: {self.puntaje}"


### --- PESOS Y PERÍODOS --- ###

class PesoEvaluacion(models.Model):
    puesto = models.ForeignKey(Puesto, on_delete=models.CASCADE, related_name='pesos_evaluacion')
    tipo = models.CharField(max_length=4, choices=TipoEvaluacion.choices)
    peso = models.FloatField(help_text="Decimal entre 0 y 1 (e.g. 0.4)")

    class Meta:
        unique_together = ('puesto', 'tipo')

    def __str__(self):
        return f"{self.puesto.nombre} – {self.get_tipo_display()}: {self.peso}"


class PeriodoEvaluacion(models.Model):
    puesto = models.ForeignKey(Puesto, on_delete=models.CASCADE, related_name='periodos_evaluacion')
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
    trabajador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resultados_totales')
    fecha_ejecucion = models.DateField(auto_now_add=True)
    puntaje_total = models.FloatField(default=0.0)

    def get_clasificacion(self):
        if self.puntaje_total >= 80:
            return "Aprobado"
        elif self.puntaje_total >= 50:
            return "En proceso"
        return "En riesgo"

    def __str__(self):
        return f"{self.trabajador.username} @ {self.fecha_ejecucion}: {self.puntaje_total:.2f}"

class Evaluacion(models.Model):
    evaluador = models.CharField(max_length=100)
    evaluado = models.CharField(max_length=100)
    tipo = models.CharField(max_length=4, choices=TipoEvaluacion.choices)
    puntaje = models.DecimalField(max_digits=5, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.evaluado}"