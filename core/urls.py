from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("modulo-2/ejecutar", views.ejecutar_modulo_2, name="ejecutar_modulo_2"),
    path("modulo-2/recargar/<int:simulacion_id>/", views.recargar_simulacion_view, name="recargar_simulacion"),
    path("health", views.health, name="health"),
]
