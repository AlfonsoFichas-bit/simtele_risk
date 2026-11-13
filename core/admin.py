from django.contrib import admin
from .models import (
    CasoEstudio,
    Escenario,
    Simulacion,
    EjecucionMetodo,
    IteracionResultado,
    ResultadoResumen,
)

admin.site.register(CasoEstudio)
admin.site.register(Escenario)
admin.site.register(Simulacion)
admin.site.register(EjecucionMetodo)
admin.site.register(IteracionResultado)
admin.site.register(ResultadoResumen)
