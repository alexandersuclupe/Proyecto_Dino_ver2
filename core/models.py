from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


# Cliente
class Cliente(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name()

# Producto
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre

# Venta
class Venta(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    tiempo_inicio = models.DateTimeField(editable=False, null=True, blank=True)
    tiempo_fin = models.DateTimeField(null=True, blank=True)
    duracion_venta = models.DurationField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        now = timezone.now()

        # Si es nueva venta (no tiene ID), se registra el tiempo de inicio
        if not self.pk:
            self.tiempo_inicio = now

        # Siempre se registra el tiempo de fin al guardar
        self.tiempo_fin = now

        # Solo calcula la duración si tiempo_inicio ya está definido
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
        return f'Venta #{self.id} - {self.cliente.nombre}'
# Detalle de Venta
class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # Al guardar, toma el precio del producto si aún no se asignó
        if not self.precio_unitario:
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        try:
                return self.cantidad * self.precio_unitario
        except (TypeError, ValueError):
            return 0

class EncuestaSatisfaccion(models.Model):
    venta = models.OneToOneField('Venta', on_delete=models.CASCADE)
    trabajador = models.ForeignKey(User, on_delete=models.CASCADE, null=True)


    cordialidad = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    resolucion_dudas = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    tiempo_atencion = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    recomendacion = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Encuesta para venta #{self.venta.id}"