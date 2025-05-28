from django.contrib import admin
from .models import Cliente, Producto, Venta, DetalleVenta
from django import forms


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

# # Registro de otros modelos
# admin.site.register(Cliente)
# admin.site.register(Producto)
