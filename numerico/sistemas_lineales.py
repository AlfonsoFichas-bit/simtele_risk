import time
import numpy as np

# ==========================================
# 1. TEORÍA DE ERRORES TRANSVERSAL
# ==========================================
def calcular_metricas_error(x_aprox, x_ref, A=None, b=None):
    x_aprox = np.array(x_aprox, dtype=float)
    x_ref = np.array(x_ref, dtype=float)

    # Protección contra overflow / NaN
    if not np.all(np.isfinite(x_aprox)):
        return {
            "error_abs": 1e9,
            "error_rel": 1e9,
            "error_porc": 1e9,
            "residual": 1e9,
        }

    # Norma infinito para vectores (máximo valor absoluto)
    err_abs = float(np.linalg.norm(x_aprox - x_ref, ord=np.inf))
    norm_ref = float(np.linalg.norm(x_ref, ord=np.inf))
    err_rel = (err_abs / norm_ref) if norm_ref > 1e-15 else 0.0
    err_porc = err_rel * 100.0

    residual = 0.0
    if A is not None and b is not None:
        A_mat = np.array(A, dtype=float)
        b_vec = np.array(b, dtype=float)
        residual = float(np.linalg.norm(A_mat @ x_aprox - b_vec, ord=np.inf))

    return {
        "error_abs": round(err_abs, 8),
        "error_rel": round(err_rel, 8),
        "error_porc": round(err_porc, 6),
        "residual": round(residual, 8),
    }


def info_condicionamiento(A):
    """Calcula el número de condición de A en norma infinito y verifica si es SPD."""
    A_mat = np.array(A, dtype=float)
    cond = float(np.linalg.cond(A_mat, p=np.inf))
    es_simetrica = bool(np.allclose(A_mat, A_mat.T, atol=1e-8))

    # Verificar si es Definida Positiva (autovalores > 0)
    if es_simetrica:
        try:
            autovalores = np.linalg.eigvalsh(A_mat)
            es_spd = bool(np.all(autovalores > 0))
        except np.linalg.LinAlgError:
            es_spd = False
    else:
        es_spd = False

    return {
        "condicion_inf": round(cond, 4),
        "es_spd": es_spd,
        "es_simetrica": es_simetrica,
    }


# ==========================================
# 2. SOLUCIÓN EXACTA / REFERENCIA Y LU
# ==========================================
def solucion_referencia(A, b):
    A_mat = np.array(A, dtype=float)
    b_vec = np.array(b, dtype=float)
    sol = np.linalg.solve(A_mat, b_vec)
    return [round(float(v), 8) for v in sol]


def metodo_lu(A, b, x_ref):
    """Factorización LU de Doolittle (A = L * U con L unitaria inferior)."""
    t0 = time.perf_counter()
    A_mat = np.array(A, dtype=float)
    b_vec = np.array(b, dtype=float)
    n = len(b_vec)

    L = np.eye(n, dtype=float)
    U = A_mat.copy()

    # Eliminación Gaussiana sin pivoteo (adecuado para matrices SPD y diagonal dominantes)
    for i in range(n):
        if abs(U[i, i]) < 1e-14:
            raise ValueError(f"Pivote nulo o casi nulo en U[{i},{i}]")
        for k in range(i + 1, n):
            factor = U[k, i] / U[i, i]
            L[k, i] = factor
            U[k, i:] -= factor * U[i, i:]

    # Sustitución hacia adelante: L * y = b
    y = np.zeros(n, dtype=float)
    for i in range(n):
        y[i] = b_vec[i] - np.dot(L[i, :i], y[:i])

    # Sustitución hacia atrás: U * x = y
    x = np.zeros(n, dtype=float)
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - np.dot(U[i, i + 1:], x[i + 1:])) / U[i, i]

    t_ms = (time.perf_counter() - t0) * 1000
    metricas = calcular_metricas_error(x, x_ref, A, b)

    return {
        "metodo": "Factorización LU",
        "convergio": True,
        "tiempo_ms": round(t_ms, 4),
        "solucion": [round(float(v), 6) for v in x],
        "L": np.round(L, 4).tolist(),
        "U": np.round(U, 4).tolist(),
        "iteraciones": [
            {
                "numero": 1,
                "aproximacion": [round(float(v), 6) for v in x],
                **metricas,
            }
        ],
        "resumen_error": metricas,
    }


# ==========================================
# 3. MÉTODOS ITERATIVOS (Jacobi, GS, GC)
# ==========================================
def metodo_jacobi(A, b, x_ref, tol=1e-6, max_iter=100):
    t0 = time.perf_counter()
    A_mat = np.array(A, dtype=float)
    b_vec = np.array(b, dtype=float)
    n = len(b_vec)
    x = np.zeros(n, dtype=float)
    historial = []
    convergio = False

    for k in range(1, max_iter + 1):
        x_new = np.zeros(n, dtype=float)
        for i in range(n):
            suma = np.dot(A_mat[i, :i], x[:i]) + np.dot(A_mat[i, i + 1:], x[i + 1:])
            x_new[i] = (b_vec[i] - suma) / A_mat[i, i]

        if not np.all(np.isfinite(x_new)) or np.linalg.norm(x_new, ord=np.inf) > 1e12:
            historial.append({
                "numero": k,
                "aproximacion": [999999.0] * n,
                "error_abs": 999999.0,
                "error_rel": 999999.0,
                "error_porc": 999999.0,
                "residual": 999999.0,
            })
            break

        metricas = calcular_metricas_error(x_new, x_ref, A_mat, b_vec)
        diff = float(np.linalg.norm(x_new - x, ord=np.inf))
        x = x_new

        historial.append({
            "numero": k,
            "aproximacion": [round(float(v), 6) for v in x],
            **metricas,
        })

        if diff < tol:
            convergio = True
            break

    t_ms = (time.perf_counter() - t0) * 1000
    resumen = historial[-1] if historial else calcular_metricas_error(x, x_ref, A_mat, b_vec)

    return {
        "metodo": "Jacobi",
        "convergio": convergio,
        "tiempo_ms": round(t_ms, 4),
        "solucion": [round(float(v), 6) for v in x],
        "iteraciones": historial,
        "resumen_error": resumen,
    }


def metodo_gauss_seidel(A, b, x_ref, tol=1e-6, max_iter=100):
    t0 = time.perf_counter()
    A_mat = np.array(A, dtype=float)
    b_vec = np.array(b, dtype=float)
    n = len(b_vec)
    x = np.zeros(n, dtype=float)
    historial = []
    convergio = False

    for k in range(1, max_iter + 1):
        x_old = x.copy()
        for i in range(n):
            suma = np.dot(A_mat[i, :i], x[:i]) + np.dot(A_mat[i, i + 1:], x_old[i + 1:])
            x[i] = (b_vec[i] - suma) / A_mat[i, i]

        if not np.all(np.isfinite(x)) or np.linalg.norm(x, ord=np.inf) > 1e12:
            historial.append({
                "numero": k,
                "aproximacion": [999999.0] * n,
                "error_abs": 999999.0,
                "error_rel": 999999.0,
                "error_porc": 999999.0,
                "residual": 999999.0,
            })
            break

        metricas = calcular_metricas_error(x, x_ref, A_mat, b_vec)
        diff = float(np.linalg.norm(x - x_old, ord=np.inf))

        historial.append({
            "numero": k,
            "aproximacion": [round(float(v), 6) for v in x],
            **metricas,
        })

        if diff < tol:
            convergio = True
            break

    t_ms = (time.perf_counter() - t0) * 1000
    resumen = historial[-1] if historial else calcular_metricas_error(x, x_ref, A_mat, b_vec)

    return {
        "metodo": "Gauss-Seidel",
        "convergio": convergio,
        "tiempo_ms": round(t_ms, 4),
        "solucion": [round(float(v), 6) for v in x],
        "iteraciones": historial,
        "resumen_error": resumen,
    }


def metodo_gradiente_conjugado(A, b, x_ref, tol=1e-6, max_iter=100):
    t0 = time.perf_counter()
    A_mat = np.array(A, dtype=float)
    b_vec = np.array(b, dtype=float)
    n = len(b_vec)

    x = np.zeros(n, dtype=float)
    r = b_vec - A_mat @ x
    p = r.copy()
    rs_old = float(np.dot(r, r))

    historial = []
    convergio = False

    for k in range(1, max_iter + 1):
        Ap = A_mat @ p
        pAp = float(np.dot(p, Ap))

        if abs(pAp) < 1e-15:
            # División por cero potencial si p es casi nulo o A no es definida positiva
            break

        alpha = rs_old / pAp
        x = x + alpha * p
        r = r - alpha * Ap
        rs_new = float(np.dot(r, r))

        metricas = calcular_metricas_error(x, x_ref, A_mat, b_vec)
        historial.append({
            "numero": k,
            "aproximacion": [round(float(v), 6) for v in x],
            **metricas,
        })

        if np.sqrt(max(0.0, rs_new)) < tol:
            convergio = True
            break

        if rs_old < 1e-15:
            break

        p = r + (rs_new / rs_old) * p
        rs_old = rs_new

    t_ms = (time.perf_counter() - t0) * 1000
    resumen = historial[-1] if historial else calcular_metricas_error(x, x_ref, A_mat, b_vec)

    return {
        "metodo": "Gradiente Conjugado",
        "convergio": convergio,
        "tiempo_ms": round(t_ms, 4),
        "solucion": [round(float(v), 6) for v in x],
        "iteraciones": historial,
        "resumen_error": resumen,
    }


# ==========================================
# 4. ESCENARIOS DE PRUEBA (MÓDULO 2 - 4x4 SPD)
# Solución de referencia fijada: x* = [1.0, 2.0, 1.5, 0.5]
# ==========================================
ESCENARIOS_MODULO_2 = {
    "NORMAL": {
        "nombre": "Normal - Matriz SPD Diagonal Dominante",
        "descripcion": "Calibración de desgaste en 4 poleas con acoplamiento simétrico y estricta diagonal dominante.",
        "A": [
            [10.0, -1.0,  2.0,  0.0],
            [-1.0, 11.0, -1.0,  3.0],
            [ 2.0, -1.0, 10.0, -1.0],
            [ 0.0,  3.0, -1.0,  8.0]
        ],
        "x_exacta": [1.0, 2.0, 1.5, 0.5],
        "b": [11.0, 21.0, 14.5, 8.5]
    },
    "ESTRES": {
        "nombre": "Estrés - Matriz SPD Acoplada Uniforme",
        "descripcion": "Alta interacción entre poleas con diagonal débilmente dominante y respuesta acoplada.",
        "A": [
            [4.0, 1.0, 1.0, 1.0],
            [1.0, 4.0, 1.0, 1.0],
            [1.0, 1.0, 4.0, 1.0],
            [1.0, 1.0, 1.0, 4.0]
        ],
        "x_exacta": [1.0, 2.0, 1.5, 0.5],
        "b": [8.0, 11.0, 9.5, 6.5]
    },
    "MAL_CONDICIONADO": {
        "nombre": "Mal Condicionado - Matriz SPD Casi Singular",
        "descripcion": "Sensores cuasi-colineales de deformación con alto número de condición kappa(A) > 1000.",
        "A": [
            [1.00, 0.99, 0.98, 0.97],
            [0.99, 1.00, 0.99, 0.98],
            [0.98, 0.99, 1.00, 0.99],
            [0.97, 0.98, 0.99, 1.00]
        ],
        "x_exacta": [1.0, 2.0, 1.5, 0.5],
        "b": [4.935, 4.965, 4.965, 4.945]
    }
}
