from django.db import models


class CasoEstudio(models.Model):
    nombre = models.CharField(max_length=120)
    modelo_version = models.CharField(max_length=50, default="v1.0")
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = "caso_estudio"
        verbose_name = "Caso de Estudio"
        verbose_name_plural = "Casos de Estudio"

    def __str__(self):
        return f"{self.nombre} ({self.modelo_version})"


class Escenario(models.Model):
    TIPO_CHOICES = [
        ("NORMAL", "Normal"),
        ("ESTRES", "Estrés"),
        ("MAL_CONDICIONADO", "Mal Condicionado"),
    ]
    caso = models.ForeignKey(CasoEstudio, on_delete=models.CASCADE, related_name="escenarios")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    parametros_json = models.JSONField(help_text="Parámetros numéricos en formato JSON")
    fuente_datos = models.CharField(max_length=150, default="Datos sintéticos controlados")

    class Meta:
        db_table = "escenario"
        verbose_name = "Escenario"
        verbose_name_plural = "Escenarios"

    def __str__(self):
        return f"{self.caso.nombre} - {self.get_tipo_display()}"


class Simulacion(models.Model):
    escenario = models.ForeignKey(Escenario, on_delete=models.CASCADE, related_name="simulaciones")
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=100, default="Estudiante Informática")
    estado = models.CharField(max_length=30, default="COMPLETADO")

    class Meta:
        db_table = "simulacion"
        ordering = ["-fecha"]
        verbose_name = "Simulación"
        verbose_name_plural = "Simulaciones"

    def __str__(self):
        return f"Simulación #{self.pk} [{self.escenario.tipo}] - {self.fecha.strftime('%Y-%m-%d %H:%M')}"


class EjecucionMetodo(models.Model):
    simulacion = models.ForeignKey(Simulacion, on_delete=models.CASCADE, related_name="ejecuciones")
    metodo = models.CharField(max_length=60)
    tolerancia = models.FloatField(default=1e-6)
    paso = models.FloatField(null=True, blank=True)
    max_iter = models.IntegerField(default=100)
    convergio = models.BooleanField(default=True)
    tiempo_ms = models.FloatField()

    class Meta:
        db_table = "ejecucion_metodo"
        verbose_name = "Ejecución de Método"
        verbose_name_plural = "Ejecuciones de Método"

    def __str__(self):
        return f"{self.metodo} (Sim #{self.simulacion_id}) - Convergió: {self.convergio}"


class IteracionResultado(models.Model):
    ejecucion = models.ForeignKey(EjecucionMetodo, on_delete=models.CASCADE, related_name="iteraciones")
    numero = models.IntegerField()
    aproximacion_json = models.JSONField()
    residual = models.FloatField()
    error_abs = models.FloatField()
    error_rel = models.FloatField()

    class Meta:
        db_table = "iteracion_resultado"
        ordering = ["numero"]
        verbose_name = "Iteración de Resultado"
        verbose_name_plural = "Iteraciones de Resultado"

    def __str__(self):
        return f"Iter {self.numero} - Ejecución #{self.ejecucion_id}"


class ResultadoResumen(models.Model):
    ejecucion = models.OneToOneField(EjecucionMetodo, on_delete=models.CASCADE, related_name="resumen")
    referencia = models.JSONField()
    valor_json = models.JSONField()
    metrica_error_json = models.JSONField()
    interpretacion = models.TextField()

    class Meta:
        db_table = "resultado_resumen"
        verbose_name = "Resumen de Resultado"
        verbose_name_plural = "Resúmenes de Resultados"

    def __str__(self):
        return f"Resumen Ejecución #{self.ejecucion_id}"
