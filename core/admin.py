from django.contrib import admin
from .models import Cliente, Producto, Venta, DetalleVenta, Usuario, EvaluacionTrabajador ,Criterio ,Indicador , RespuestaEvaluacionTrabajador ,EvaluacionVenta ,RespuestaEvaluacionVenta ,Puesto
from django import forms
from django.contrib.auth.admin import UserAdmin


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'correo', 'direccion', 'telefono')
    list_filter = ('direccion',)

    def nombre_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    nombre_completo.short_description = 'Nombre completo'

    def correo(self, obj):
        return obj.user.email
    list_per_page = 5


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'precio', 'stock')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('nombre',)
    list_per_page = 5


class VentaAdminForm(forms.ModelForm):
    # Campo oculto para recibir segundos
    duracion_segundos = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Venta
        fields = '__all__'


# Inline para mostrar detalles dentro de la venta
class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    readonly_fields = ('precio_unitario', 'get_subtotal')

    def get_subtotal(self, obj):
        return obj.subtotal
    get_subtotal.short_description = 'Subtotal'

# Admin de Venta


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'usuario', 'fecha', 'tiempo_inicio', 'tiempo_fin', 'duracion_venta_formateada', 'get_total')
    readonly_fields = ('tiempo_inicio', 'tiempo_fin')
    exclude = ('usuario',)  # oculta el campo 'usuario' del formulario
    inlines = [DetalleVentaInline]
    list_per_page = 5

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # solo cuando es una nueva venta
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

    def get_total(self, obj):
        return obj.total
    get_total.short_description = 'Total'

    def duracion_venta_formateada(self, obj):
        if obj.duracion_venta:
            total_seconds = int(obj.duracion_venta.total_seconds())
            minutos, segundos = divmod(total_seconds, 60)
            horas, minutos = divmod(minutos, 60)
            return f'{horas}h {minutos}m {segundos}s'
        return "No calculado"
    duracion_venta_formateada.short_description = 'Duración de la venta'

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ('username', 'email', 'rol')  # agregué 'puesto' para mostrar
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('rol', 'puesto')}),  # Reemplaza 'area' por 'puesto'
    )


# @admin.register(Evaluacion)
# class EvaluacionAdmin(admin.ModelAdmin):
#     list_display = ('tipo', 'evaluador', 'evaluado', 'puntaje', 'fecha')
#     list_filter = ('tipo', 'fecha')






# # Registro de otros modelos
# admin.site.register(Cliente)
# admin.site.register(Producto)

@admin.register(Puesto)
class PuestoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(Criterio)
class CriterioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    filter_horizontal = ('puestos',)  # Para mejor selección de puestos en interfaz
    search_fields = ('nombre',)

@admin.register(Indicador)
class IndicadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'get_criterio_nombre', 'max_puntaje')
    list_filter = ('criterio',)
    search_fields = ('nombre',)

    def get_criterio_nombre(self, obj):
        return obj.criterio.nombre
    get_criterio_nombre.short_description = 'Criterio'
    get_criterio_nombre.admin_order_field = 'criterio__nombre'



    ##############

class RespuestaEvaluacionVentaInline(admin.TabularInline):
    model = RespuestaEvaluacionVenta
    extra = 0
    readonly_fields = ('mostrar_indicador', 'puntaje')
    fields = ('mostrar_indicador', 'puntaje')
    can_delete = False

    def mostrar_indicador(self, obj):
        return obj.indicador.nombre
    mostrar_indicador.short_description = 'Indicador'


@admin.register(EvaluacionVenta)
class EvaluacionVentaAdmin(admin.ModelAdmin):
    inlines = [RespuestaEvaluacionVentaInline]
    list_display = ('id', 'cliente', 'trabajador', 'fecha')


class RespuestaEvaluacionTrabajadorInline(admin.TabularInline):
    model = RespuestaEvaluacionTrabajador
    readonly_fields = ('indicador', 'puntaje')
    extra = 0
    can_delete = False

@admin.register(EvaluacionTrabajador)
class EvaluacionTrabajadorAdmin(admin.ModelAdmin):
    list_display = ('id', 'evaluador', 'evaluado', 'estado', 'fecha_creacion')
    list_filter = ('estado',)
    inlines = [RespuestaEvaluacionTrabajadorInline]