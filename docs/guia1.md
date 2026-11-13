Para asegurar los **6 puntos de hoy** sin trabajar de más, esta es la ruta crítica exacta según la rúbrica de la Semana 1:

1. **Paso 1 (3 pts): Motor numérico en Python** (Teoría de errores transversal + Jacobi, Gauss-Seidel, LU, Gradiente Conjugado y solución exacta) probado con los 3 escenarios del **Módulo 2**.


2. **Paso 2 (1 pt): Modelos de Django (`models.py`) + Vista Inertia** con las 4 tarjetas y el DER.


3. **Paso 3 (2 pts): Planteamiento matemático** de los 4 casos y tablas generadas por el script listas para tu PDF.



Empecemos por el **Paso 1 y el modelo de base de datos**, que es el corazón de la entrega de hoy.

---

### 1. Motor Matemático: Errores + Sistemas Lineales (`numerico/sistemas_lineales.py`)

La consigna exige matrices de tamaño $\ge 4$ y que la matriz sea Simétrica Definida Positiva (SPD) para el Gradiente Conjugado en el Módulo 2. Este código usa `numpy` solo para estructuras y la referencia exacta/condición, implementando los 4 métodos desde cero para que puedas mostrar las iteraciones y errores paso a paso:

```python
import time
import numpy as np

# ==========================================
# 1. TEORÍA DE ERRORES TRANSVERSAL
# ==========================================
def calcular_metricas_error(x_aprox, x_ref, A=None, b=None):
    x_aprox = np.array(x_aprox, dtype=float)
    x_ref = np.array(x_ref, dtype=float)
    
    # Norma infinito para vectores
    err_abs = float(np.linalg.norm(x_aprox - x_ref, ord=np.inf))
    norm_ref = float(np.linalg.norm(x_ref, ord=np.inf))
    err_rel = err_abs / norm_ref if norm_ref > 1e-15 else 0.0
    err_porc = err_rel * 100.0
    
    residual = 0.0
    if A is not None and b is not None:
        A_mat = np.array(A, dtype=float)
        b_vec = np.array(b, dtype=float)
        # Residuo ||Ax - b||_inf
        residual = float(np.linalg.norm(A_mat @ x_aprox - b_vec, ord=np.inf))
        
    return {
        "error_abs": round(err_abs, 8),
        "error_rel": round(err_rel, 8),
        "error_porc": round(err_porc, 6),
        "residual": round(residual, 8)
    }

def info_condicionamiento(A):
    A_mat = np.array(A, dtype=float)
    cond = float(np.linalg.cond(A_mat, p=np.inf))
    es_simetrica = np.allclose(A_mat, A_mat.T)
    # Verificar si es Definida Positiva (autovalores > 0)
    autovalores = np.linalg.eigvalsh(A_mat) if es_simetrica else []
    es_spd = bool(es_simetrica and np.all(autovalores > 0))
    return {"condicion_inf": round(cond, 4), "es_spd": es_spd}

# ==========================================
# 2. SOLUCIÓN EXACTA / REFERENCIA Y LU
# ==========================================
def solucion_referencia(A, b):
    A_mat = np.array(A, dtype=float)
    b_vec = np.array(b, dtype=float)
    return np.linalg.solve(A_mat, b_vec).tolist()

def metodo_lu(A, b, x_ref):
    t0 = time.perf_counter()
    A_mat = np.array(A, dtype=float)
    b_vec = np.array(b, dtype=float)
    n = len(b_vec)
    
    L = np.eye(n)
    U = A_mat.copy()
    
    # Eliminación de Gauss para obtener L y U (Doolittle sin pivoteo para matriz SPD)
    for i in range(n):
        for k in range(i + 1, n):
            factor = U[k, i] / U[i, i]
            L[k, i] = factor
            U[k, i:] -= factor * U[i, i:]
            
    # Sustitución hacia adelante: L * y = b
    y = np.zeros(n)
    for i in range(n):
        y[i] = b_vec[i] - np.dot(L[i, :i], y[:i])
        
    # Sustitución hacia atrás: U * x = y
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - np.dot(U[i, i + 1:], x[i + 1:])) / U[i, i]
        
    t_ms = (time.perf_counter() - t0) * 1000
    metricas = calcular_metricas_error(x, x_ref, A, b)
    
    return {
        "metodo": "Factorización LU",
        "convergio": True,
        "tiempo_ms": round(t_ms, 4),
        "solucion": np.round(x, 6).tolist(),
        "L": np.round(L, 4).tolist(),
        "U": np.round(U, 4).tolist(),
        "iteraciones": [{
            "numero": 1,
            "aproximacion": np.round(x, 6).tolist(),
            **metricas
        }],
        "resumen_error": metricas
    }

# ==========================================
# 3. MÉTODOS ITERATIVOS (Jacobi, GS, GC)
# ==========================================
def metodo_jacobi(A, b, x_ref, tol=1e-6, max_iter=100):
    t0 = time.perf_counter()
    A_mat = np.array(A, dtype=float)
    b_vec = np.array(b, dtype=float)
    n = len(b_vec)
    x = np.zeros(n)
    historial = []
    convergio = False
    
    for k in range(1, max_iter + 1):
        x_new = np.zeros(n)
        for i in range(n):
            suma = np.dot(A_mat[i, :i], x[:i]) + np.dot(A_mat[i, i+1:], x[i+1:])
            x_new[i] = (b_vec[i] - suma) / A_mat[i, i]
            
        metricas = calcular_metricas_error(x_new, x_ref, A_mat, b_vec)
        diff = np.linalg.norm(x_new - x, ord=np.inf)
        x = x_new
        
        historial.append({
            "numero": k,
            "aproximacion": np.round(x, 6).tolist(),
            **metricas
        })
        if diff < tol:
            convergio = True
            break
            
    t_ms = (time.perf_counter() - t0) * 1000
    return {
        "metodo": "Jacobi",
        "convergio": convergio,
        "tiempo_ms": round(t_ms, 4),
        "solucion": np.round(x, 6).tolist(),
        "iteraciones": historial,
        "resumen_error": historial[-1]
    }

def metodo_gauss_seidel(A, b, x_ref, tol=1e-6, max_iter=100):
    t0 = time.perf_counter()
    A_mat = np.array(A, dtype=float)
    b_vec = np.array(b, dtype=float)
    n = len(b_vec)
    x = np.zeros(n)
    historial = []
    convergio = False
    
    for k in range(1, max_iter + 1):
        x_old = x.copy()
        for i in range(n):
            suma = np.dot(A_mat[i, :i], x[:i]) + np.dot(A_mat[i, i+1:], x_old[i+1:])
            x[i] = (b_vec[i] - suma) / A_mat[i, i]
            
        metricas = calcular_metricas_error(x, x_ref, A_mat, b_vec)
        diff = np.linalg.norm(x - x_old, ord=np.inf)
        
        historial.append({
            "numero": k,
            "aproximacion": np.round(x, 6).tolist(),
            **metricas
        })
        if diff < tol:
            convergio = True
            break
            
    t_ms = (time.perf_counter() - t0) * 1000
    return {
        "metodo": "Gauss-Seidel",
        "convergio": convergio,
        "tiempo_ms": round(t_ms, 4),
        "solucion": np.round(x, 6).tolist(),
        "iteraciones": historial,
        "resumen_error": historial[-1]
    }

def metodo_gradiente_conjugado(A, b, x_ref, tol=1e-6, max_iter=100):
    t0 = time.perf_counter()
    A_mat = np.array(A, dtype=float)
    b_vec = np.array(b, dtype=float)
    n = len(b_vec)
    
    x = np.zeros(n)
    r = b_vec - A_mat @ x
    p = r.copy()
    rs_old = np.dot(r, r)
    
    historial = []
    convergio = False
    
    for k in range(1, max_iter + 1):
        Ap = A_mat @ p
        alpha = rs_old / np.dot(p, Ap)
        x = x + alpha * p
        r = r - alpha * Ap
        rs_new = np.dot(r, r)
        
        metricas = calcular_metricas_error(x, x_ref, A_mat, b_vec)
        historial.append({
            "numero": k,
            "aproximacion": np.round(x, 6).tolist(),
            **metricas
        })
        
        if np.sqrt(rs_new) < tol:
            convergio = True
            break
            
        p = r + (rs_new / rs_old) * p
        rs_old = rs_new
        
    t_ms = (time.perf_counter() - t0) * 1000
    return {
        "metodo": "Gradiente Conjugado",
        "convergio": convergio,
        "tiempo_ms": round(t_ms, 4),
        "solucion": np.round(x, 6).tolist(),
        "iteraciones": historial,
        "resumen_error": historial[-1]
    }

# ==========================================
# 4. ESCENARIOS DE PRUEBA (MÓDULO 2 - 4x4 SPD)
# Solución exacta fijada: x* = [1.0, 2.0, 1.5, 0.5]
# ==========================================
ESCENARIOS_MODULO_2 = {
    "NORMAL": {
        "descripcion": "Matriz 4x4 SPD estrictamente diagonal dominante (Calibración de desgaste en 4 poleas)",
        "A": [
            [10.0, -1.0,  2.0,  0.0],
            [-1.0, 11.0, -1.0,  3.0],
            [ 2.0, -1.0, 10.0, -1.0],
            [ 0.0,  3.0, -1.0,  8.0]
        ],
        "x_exacta": [1.0, 2.0, 1.5, 0.5],
        # b = A * x_exacta = [11.0, 21.0, 14.5, 8.5]
        "b": [11.0, 21.0, 14.5, 8.5]
    },
    "ESTRES": {
        "descripcion": "Sistema acoplado con diagonal ajustada y perturbación en el vector de lecturas b",
        "A": [
            [4.0, 1.0, 1.0, 1.0],
            [1.0, 4.0, 1.0, 1.0],
            [1.0, 1.0, 4.0, 1.0],
            [1.0, 1.0, 1.0, 4.0]
        ],
        "x_exacta": [1.0, 2.0, 1.5, 0.5],
        # b exacto = [8.0, 11.0, 9.5, 6.5]
        "b": [8.0, 11.0, 9.5, 6.5]
    },
    "MAL_CONDICIONADO": {
        "descripcion": "Matriz SPD casi singular con alto número de condición kappa(A) (Sensores colineales)",
        "A": [
            [1.00, 0.99, 0.98, 0.97],
            [0.99, 1.00, 0.99, 0.98],
            [0.98, 0.99, 1.00, 0.99],
            [0.97, 0.98, 0.99, 1.00]
        ],
        "x_exacta": [1.0, 2.0, 1.5, 0.5],
        # b = A * x_exacta
        "b": [4.935, 4.965, 4.965, 4.945]
    }
}

```

---

### 2. Modelos de Django (`models.py`) compatibles con SQLite y Neon Postgres

Cumple al 100% con la sección **8. Modelo de datos obligatorio** del PDF (usa `models.JSONField`, que funciona nativo tanto en SQLite3 de desarrollo como en PostgreSQL de Neon Tech):

```python
from django.db import models

class CasoEstudio(models.Model):
    nombre = models.CharField(max_length=120)
    modelo_version = models.CharField(max_length=50, default="v1.0")
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = "caso_estudio"

class Escenario(models.Model):
    TIPO_CHOICES = [
        ("NORMAL", "Normal"),
        ("ESTRES", "Estrés"),
        ("MAL_CONDICIONADO", "Mal Condicionado"),
    ]
    caso = models.ForeignKey(CasoEstudio, on_delete=models.CASCADE, related_name="escenarios")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    parametros_json = models.JSONField()
    fuente_datos = models.CharField(max_length=150, default="Datos sintéticos controlados")

    class Meta:
        db_table = "escenario"

class Simulacion(models.Model):
    escenario = models.ForeignKey(Escenario, on_delete=models.CASCADE, related_name="simulaciones")
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=100, default="Estudiante Informática")
    estado = models.CharField(max_length=30, default="COMPLETADO")

    class Meta:
        db_table = "simulacion"

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

class IteracionResultado(models.Model):
    ejecucion = models.ForeignKey(EjecucionMetodo, on_delete=models.CASCADE, related_name="iteraciones")
    numero = models.IntegerField()
    aproximacion_json = models.JSONField()
    residual = models.FloatField()
    error_abs = models.FloatField()
    error_rel = models.FloatField()

    class Meta:
        db_table = "iteracion_resultado"

class ResultadoResumen(models.Model):
    ejecucion = models.OneToOneField(EjecucionMetodo, on_delete=models.CASCADE, related_name="resumen")
    referencia = models.JSONField()
    valor_json = models.JSONField()
    metrica_error_json = models.JSONField()
    interpretacion = models.TextField()

    class Meta:
        db_table = "resultado_resumen"

```

---
