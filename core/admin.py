from django.contrib import admin
from jsonschema import ValidationError
from .models import AutoevaluacionTrabajador, Cliente,Producto, RespuestaAutoevaluacionTrabajador, Venta, DetalleVenta, Usuario, EvaluacionTrabajador, Criterio, Indicador, RespuestaEvaluacionTrabajador, EvaluacionVenta, RespuestaEvaluacionVenta, Puesto ,PeriodoEvaluacion ,ResultadoTotal ,PesoEvaluacion , Trabajador
from django import forms
from django.contrib.auth.admin import UserAdmin

###################################### CLIENTE #########################################
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
    duracion_segundos = forms.IntegerField(
        widget=forms.HiddenInput(), required=False)

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
    list_display = (
        'id', 'cliente', 'usuario', 'fecha',
        'tiempo_inicio', 'tiempo_fin',
        'duracion_venta_formateada', 'get_total'
    )
    readonly_fields = ('tiempo_inicio', 'tiempo_fin')
    inlines = [DetalleVentaInline]
    list_per_page = 5

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Solo para el campo 'usuario', mostramos Trabajadores con puesto 'vendedor'
        if db_field.name == "usuario":
            kwargs["queryset"] = Trabajador.objects.filter(
                puesto__nombre__iexact='vendedor'
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            # Creamos EvaluacionVenta al guardar por primera vez
            evaluacion = EvaluacionVenta.objects.create(
                venta=obj,
                trabajador=obj.usuario,   # obj.usuario es un Trabajador
                cliente=obj.cliente,
            )
            for indicador in Indicador.objects.all():
                RespuestaEvaluacionVenta.objects.create(
                    evaluacion=evaluacion,
                    indicador=indicador,
                    puntaje=0
                )

    def get_total(self, obj):
        return obj.total
    get_total.short_description = 'Total'

    def duracion_venta_formateada(self, obj):
        if obj.duracion_venta:
            total_sec = int(obj.duracion_venta.total_seconds())
            mins, secs = divmod(total_sec, 60)
            hrs, mins = divmod(mins, 60)
            return f'{hrs}h {mins}m {secs}s'
        return "No calculado"
    duracion_venta_formateada.short_description = 'Duración de la venta'


class UsuarioAdmin(UserAdmin):
    # Especificar los campos que se deben mostrar en el listado de usuarios
    list_display = ('username', 'email', 'nombre_completo')

    # Método para mostrar el nombre completo
    def nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    nombre_completo.short_description = 'Nombre Completo'  # Encabezado personalizado en la interfaz

    # Los campos que se mostrarán al crear/editar un usuario
    fieldsets = (
        (None, {'fields': ('username', 'password')}),  # Campos para autenticación
        ('Información personal', {'fields': ('first_name', 'last_name', 'email')}),  # Datos personales
        #('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser')}),  # Permisos del usuario
        #('Fechas importantes', {'fields': ('last_login', 'date_joined')}),  # Fechas
    )

    # Los campos que se mostrarán al agregar un nuevo usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'is_active', 'is_staff')}
        ),
    )

    # Permitir búsqueda por username o email
    search_fields = ('username', 'email')  

    # Ordenar por username
    ordering = ('username',)  

# Registrar el modelo Usuario con su configuración de administración personalizada
admin.site.register(Usuario, UsuarioAdmin)

################################ TRABAJADOR #################################
@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'puesto', 'telefono', 'direccion')

    def nombre_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    nombre_completo.short_description = 'Nombre completo'

    def correo(self, obj):
        return obj.user.email
    list_per_page = 5

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


# @admin.register(Criterio)
# class CriterioAdmin(admin.ModelAdmin):
#     list_display = ('nombre', 'descripcion', 'puesto',
#                     'rango_min', 'rango_max')
#     list_filter = ('puesto',)

@admin.register(Criterio)
class CriterioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'mostrar_puestos', 'rango_min', 'rango_max')
    list_filter = ('puestos',)  # Filtro para el campo puestos (relación many to many)
    search_fields = ('nombre', 'descripcion')  # Permitir búsqueda por nombre y descripción

    # Método para mostrar los puestos asociados
    def mostrar_puestos(self, obj):
        return ", ".join([puesto.nombre for puesto in obj.puestos.all()])
    mostrar_puestos.short_description = 'Puestos'
    
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
    list_display = ('id', 'cliente', 'trabajador', 'estado', 'fecha')
    list_filter = ('estado',)


class RespuestaEvaluacionTrabajadorInline(admin.TabularInline):
    model = RespuestaEvaluacionTrabajador
    readonly_fields = ('indicador', 'puntaje')
    extra = 0
    can_delete = False

    def mostrar_indicador(self, obj):
        return obj.indicador.nombre
    mostrar_indicador.short_description = 'Indicador'


@admin.register(EvaluacionTrabajador)
class EvaluacionTrabajadorAdmin(admin.ModelAdmin):
    change_form_template = "admin/change_form.html"
    #inlines = [RespuestaEvaluacionTrabajadorInline]

    list_display = (
        'id',
        'evaluador',
        'evaluado',
        'estado',
        'fecha_creacion',
        'fecha_activacion',
    )
    list_filter = (
        'estado',
        'fecha_activacion',
    )
    search_fields = (
        'evaluador__username',
        'evaluado__username',
        'observaciones',
    )
    date_hierarchy = 'fecha_creacion'
    ordering = ('-fecha_creacion',)

    readonly_fields = (
        'id',
        'fecha_creacion',
    )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        ev = self.get_object(request, object_id)

        # 1) Agrupar respuestas por criterio
        agrupado = {}
        for r in ev.respuestas.select_related('indicador__criterio').all():
            crit = r.indicador.criterio
            agrupado.setdefault(crit, []).append(r)

        # 2) Construir una lista de tuplas (criterio, total, lista_de_respuestas)
        grouped_list = [
            (crit, sum(r.puntaje for r in respuestas), respuestas)
            for crit, respuestas in agrupado.items()
        ]

        # 3) Calcular el gran total
        grand_total = sum(total for (_, total, _) in grouped_list)

        extra_context = extra_context or {}
        extra_context.update({
            'grouped_list': grouped_list,
            'grand_total':  grand_total,
        })
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

###########################################################


class RespuestaAutoevaluacionForm(forms.ModelForm):
    class Meta:
        model = RespuestaAutoevaluacionTrabajador
        fields = '__all__'

    def clean_puntaje(self):
        puntaje = self.cleaned_data.get('puntaje')
        if puntaje is not None and puntaje > 5:
            raise ValidationError('El puntaje máximo permitido es 5.')
        return puntaje

    # También se puede limitar el widget para facilitar
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'puntaje' in self.fields:
            self.fields['puntaje'].widget.attrs.update({'max': 5, 'min': 0})

# Ahora el inline que usa este formulario


class RespuestaAutoevaluacionInline(admin.TabularInline):
    model = RespuestaAutoevaluacionTrabajador
    form = RespuestaAutoevaluacionForm
    extra = 0
    can_delete = False

# Modificación del admin de AutoevaluacionTrabajador


@admin.register(AutoevaluacionTrabajador)
class AutoevaluacionTrabajadorAdmin(admin.ModelAdmin):
    list_display = ('trabajador', 'fecha',
                    'mostrar_indicadores', 'total_puntaje')
    inlines = [RespuestaAutoevaluacionInline]

    def mostrar_indicadores(self, obj):
        indicadores = [
            f"{resp.indicador.nombre} ({resp.valoracion})" for resp in obj.respuestas.all()]
        return ", ".join(indicadores) if indicadores else "Sin indicadores"
    mostrar_indicadores.short_description = 'Indicadores'

    def total_puntaje(self, obj):
        return sum(resp.puntaje for resp in obj.respuestas.all())
    total_puntaje.short_description = 'Puntaje Total'


#################################### PEESOS #######################################33

# ——— Admin para PeriodoEvaluacion ———
@admin.register(PeriodoEvaluacion)
class PeriodoEvaluacionAdmin(admin.ModelAdmin):
    list_display  = ('puesto', 'fecha_inicio', 'fecha_fin', 'esta_activo')
    list_filter   = ('puesto',)
    search_fields = ('puesto__nombre',)
    ordering      = ('puesto', 'fecha_inicio')
    date_hierarchy = 'fecha_inicio'

    def esta_activo(self, obj):
        return obj.esta_activo()
    esta_activo.boolean = True
    esta_activo.short_description = 'Activo ahora?'

# ——— Admin para PesoEvaluacion ———
@admin.register(PesoEvaluacion)
class PesoEvaluacionAdmin(admin.ModelAdmin):
    list_display  = ('puesto', 'get_tipo_display', 'peso')
    list_filter   = ('puesto', 'tipo')
    search_fields = ('puesto__nombre',)
    ordering      = ('puesto', 'tipo')

# ——— Admin para ResultadoTotal ———
@admin.register(ResultadoTotal)
class ResultadoTotalAdmin(admin.ModelAdmin):
    list_display  = ('trabajador', 'fecha_ejecucion', 'puntaje_total')
    list_filter = ('trabajador__puesto',)  # Filtrar por el puesto del trabajador
    
    date_hierarchy = 'fecha_ejecucion'
    ordering      = ('-fecha_ejecucion',)

