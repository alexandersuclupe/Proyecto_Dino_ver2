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
from core.views import login_view , evaluar_venta ,editar_evaluacion_trabajador
from django.contrib.auth.views import LogoutView




urlpatterns = [
    path('admin/', admin.site.urls),

    # Eliminamos encuesta_satisfaccion antigua
    # path('encuesta/<int:venta_id>/', views.encuesta_satisfaccion, name='encuesta_satisfaccion'),
    # path('gracias/', views.gracias_encuesta, name='gracias_encuesta'),

    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('registrar/', views.registro_cliente, name='registro_cliente'),

    path('cliente/dashboard/', views.cliente_dashboard, name='cliente_panel'),
    path('evaluar_cliente/<int:venta_id>/', views.evaluar_venta, name='evaluar_venta'),

    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    #path('clientes/', views.cliente_panel, name='cliente_panel'),

    # Nueva ruta para evaluación paso a paso por venta
   # path('evaluar/<int:venta_id>/', views.evaluar_venta, name='evaluar_venta_default'),  # Inicia en pregunta 1
   # path('evaluar/<int:venta_id>/<int:pregunta_orden>/', views.evaluar_venta, name='evaluar_venta'),

    # Ruta para mostrar resultado resumen de evaluación
    #path('resultado/<int:venta_id>/', views.resultado_evaluacion, name='resultado_evaluacion'),

    # Comentamos la antigua evaluación por trabajador simple
    # path('evaluar/<int:trabajador_id>/', views.evaluar_cliente, name='evaluar_cliente'),

    path('admin_panel/', views.admin_dashboard, name='admin_dashboard'),

    path('evaluacion_trabajador/<int:evaluacion_id>/', views.editar_evaluacion_trabajador, name='editar_evaluacion_trabajador'),

]
