"""
URL configuration for ventas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core import views
from core.views import index  # ← Aquí va la importación
from core.views import login_view , evaluar_venta ,editar_evaluacion_trabajador,seguimiento_trabajador
from django.contrib.auth.views import LogoutView




urlpatterns = [
    path('admin/', admin.site.urls),

    # Eliminamos encuesta_satisfaccion antigua
    # path('encuesta/<int:venta_id>/', views.encuesta_satisfaccion, name='encuesta_satisfaccion'),
    # path('gracias/', views.gracias_encuesta, name='gracias_encuesta'),

    path('', views.index, name='index'),
    #path('login/', views.login_view, name='login'),
        # login “normal” (clientes y trabajadores)
    path('login/', views.login_view, name='login'),
    # login exclusivo para colaboradores (trabajadores)
    path('login/colaborador/', 
         views.login_view, 
         {'is_colaborador': True}, 
         name='login_colaborador'),
         
    path('registrar/', views.registro_cliente, name='registro_cliente'),
    path('autoevaluacion/nueva/', views.crear_autoevaluacion, name='crear_autoevaluacion'),
    path('autoevaluacion/lista/', views.lista_autoevaluaciones, name='lista_autoevaluaciones'),
    path('evaluacion_exitosa/', views.evaluacion_exitosa, name='evaluacion_exitosa'),
    path('historial/', views.historial_evaluaciones, name='historial_evaluaciones'),
    path('exportar/', views.exportar_evaluaciones_excel, name='exportar_evaluaciones_excel'),
    path('evaluacion/<str:tipo>/<int:id>/', views.ver_evaluacion, name='ver_evaluacion'),
    path('autoevaluacion/lista/', views.lista_autoevaluaciones, name='lista_autoevaluaciones'),
    path('autoevaluacion/realizar/', views.realizar_autoevaluacion, name='realizar_autoevaluacion'),
    path('autoevaluacion/ver/<int:pk>/', views.ver_autoevaluacion, name='ver_autoevaluacion'),
    path('cliente/dashboard/', views.cliente_dashboard, name='cliente_panel'),

    path('cliente/reporte_venta/<int:evaluacion_id>/', 
         views.reporte_evaluacion_venta, 
         name='reporte_evaluacion_venta'),
   
    #path('evaluar_cliente/<int:venta_id>/', views.evaluar_venta, name='evaluar_venta'),
    
    path('evaluar_cliente/<int:venta_id>/', views.evaluar_venta, name='evaluar_venta'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    #path('clientes/', views.cliente_panel, name='cliente_panel'),

    # Nueva ruta para evaluación paso a paso por venta
   # path('evaluar/<int:venta_id>/', views.evaluar_venta, name='evaluar_venta_default'),  # Inicia en pregunta 1
   # path('evaluar/<int:venta_id>/<int:pregunta_orden>/', views.evaluar_venta, name='evaluar_venta'),

    # Ruta para mostrar resultado resumen de evaluación
    #path('resultado/<int:venta_id>/', views.resultado_evaluacion, name='resultado_evaluacion'),
     path('criterios/',                    views.lista_criterios,   name='lista_criterios'),
    path('criterios/nuevo/',              views.nuevo_criterio,   name='nuevo_criterio'),
    path('criterios/<int:pk>/editar/',    views.editar_criterio,  name='editar_criterio'),
    path('criterios/<int:pk>/eliminar/',  views.eliminar_criterio,name='eliminar_criterio'),
    path('criterios/<int:pk>/',           views.detalle_criterio, name='detalle_criterio'),

    # Comentamos la antigua evaluación por trabajador simple
    # path('evaluar/<int:trabajador_id>/', views.evaluar_cliente, name='evaluar_cliente'),

    path('admin_panel/', views.admin_dashboard, name='admin_dashboard'),

    path('evaluacion_trabajador/<int:evaluacion_id>/', views.editar_evaluacion_trabajador, name='editar_evaluacion_trabajador'),
    # path('evaluaciones/', views.mostrar_evaluaciones, name='mostrar_evaluaciones'),
    # path('evaluaciones/', views.evaluar_trabajadores, name='evaluar_trabajadores'),
    # path('guardar_evaluacion/<int:evaluacion_id>/', views.guardar_evaluacion, name='guardar_evaluacion'),
      path(
        'evaluaciones/',
        views.lista_evaluaciones,
        name='lista_evaluaciones'
    ),

    path('empleados/', views.gestion_empleados, name='gestion_empleados'),
    path('empleados/agregar/', views.agregar_empleado, name='agregar_empleado'),
    path('empleados/editar/<int:id>/', views.editar_empleado, name='editar_empleado'),
    path('empleados/eliminar/<int:id>/', views.eliminar_empleado, name='eliminar_empleado'),
    path('empleado/<int:trabajador_id>/resultado/', views.calcular_resultado_final, name='resultado_total'),
    path('reporte_evaluacion/<int:evaluacion_id>/', views.reporte_evaluacion, name='reporte_evaluacion'),

    path('seguimiento/', views.seguimiento_trabajador, name='seguimiento_trabajador'),

]
