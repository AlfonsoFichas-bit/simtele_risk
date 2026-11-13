"""Catálogo declarativo de escenarios para los Módulos 1, 3 y 4 de SIMTELE-RISK.

Cada módulo expone los escenarios NORMAL, ESTRES y MAL_CONDICIONADO con sus
parámetros gobernantes, formulación matemática y supuestos físicos de modelado.
"""

ESCENARIOS_MODULO_1 = {
    "NORMAL": {
        "nombre": "Normal - Desaceleración Nominal en Pendiente Media",
        "descripcion": "Frenado de servicio y emergencia controlado con pendiente media y fricción constante.",
        "parametros": {
            "v0": 6.0,
            "masa_kg": 3200.0,
            "pendiente_grados": 15.0,
            "desaceleracion_nominal": 1.8,
            "coef_arrastre_kd": 0.35,
            "t_simulacion": 5.0,
            "paso_tiempo": 0.05,
        },
        "supuestos": [
            "Desaceleración mecánica de zapatas constante tras tiempo de respuesta.",
            "Resistencia aerodinámica cuadrática respecto a la velocidad.",
            "Contacto de cable continuo sin rebotes longitudinales.",
        ],
    },
    "ESTRES": {
        "nombre": "Estrés - Tramo de Máxima Pendiente y Falla Parcial",
        "descripcion": "Desaceleración en tramo de alta inclinación (35°) con cabina a carga máxima y fuerza de frenado reducida en 40%.",
        "parametros": {
            "v0": 8.5,
            "masa_kg": 4500.0,
            "pendiente_grados": 35.0,
            "desaceleracion_nominal": 1.05,
            "coef_arrastre_kd": 0.42,
            "t_simulacion": 9.0,
            "paso_tiempo": 0.02,
        },
        "supuestos": [
            "Freno de emergencia hidráulico secundario operando con presión degradada.",
            "Efecto de gravedad contrarresta sustancialmente la fuerza de retención.",
            "Requerimiento de detección precisa del punto de detención exacta v(t)=0.",
        ],
    },
    "MAL_CONDICIONADO": {
        "nombre": "Mal Condicionado - Desaceleración Asintótica Cuasi-Nula",
        "descripcion": "Comportamiento exponencial a bajas velocidades donde dv/dt tiende a 0, generando alta sensibilidad en raíces y pasos temporales.",
        "parametros": {
            "v0": 5.0,
            "masa_kg": 3500.0,
            "pendiente_grados": 5.0,
            "desaceleracion_nominal": 0.08,
            "coef_asintotico": 0.02,
            "t_simulacion": 25.0,
            "paso_tiempo": 0.01,
        },
        "supuestos": [
            "Derivada dv/dt ≈ 0 en proximidad al reposo (raíz con pendiente cuasi-horizontal).",
            "Elevado número de condición temporal ante perturbaciones en el paso de integración EDO.",
            "Método de Newton susceptible a división por derivadas infinitesimales.",
        ],
    },
}

ESCENARIOS_MODULO_3 = {
    "NORMAL": {
        "nombre": "Normal - Oscilador Subamortiguado Bajo Brisa Lateral",
        "descripcion": "Respuesta dinámica amortiguada de cabina suspendida bajo ráfagas suaves alejadas de la frecuencia propia.",
        "parametros": {
            "masa_kg": 2800.0,
            "coef_amortiguamiento_c": 420.0,
            "rigidez_k": 8500.0,
            "fuerza_viento_F0": 1200.0,
            "frecuencia_forzada_omega": 0.85,
            "t_max": 20.0,
            "paso_tiempo": 0.05,
        },
        "supuestos": [
            "Péndulo simple equivalente para oscilaciones laterales de cabina.",
            "Régimen subamortiguado con razón de amortiguamiento zeta < 1.",
            "Viento modelado como fuerza armónica periódica pura.",
        ],
    },
    "ESTRES": {
        "nombre": "Estrés - Ráfagas Turbulentas de Alta Energía",
        "descripcion": "Impacto de ráfagas intensas con frecuencia cercana a la natural y amortiguamiento aerodinámico degradado.",
        "parametros": {
            "masa_kg": 3600.0,
            "coef_amortiguamiento_c": 210.0,
            "rigidez_k": 8200.0,
            "fuerza_viento_F0": 3900.0,
            "frecuencia_forzada_omega": 1.42,
            "t_max": 35.0,
            "paso_tiempo": 0.01,
        },
        "supuestos": [
            "Amplitud máxima cercana a límites de seguridad geométrica de la torre.",
            "Pérdida de eficiencia en amortiguadores de vibración de la pinza.",
            "Integración de energía cinética acumulada durante 35 segundos.",
        ],
    },
    "MAL_CONDICIONADO": {
        "nombre": "Mal Condicionado - Resonancia Crítica con Disipación Cuasi-Nula",
        "descripcion": "Excitación armónica con frecuencia exactamente igual a la natural (omega = omega_0) y amortiguamiento mínimo, generando divergencia lineal.",
        "parametros": {
            "masa_kg": 3000.0,
            "coef_amortiguamiento_c": 8.0,
            "rigidez_k": 8400.0,
            "fuerza_viento_F0": 1800.0,
            "frecuencia_forzada_omega": 1.67332,
            "t_max": 40.0,
            "paso_tiempo": 0.005,
        },
        "supuestos": [
            "Frecuencia de forzamiento idéntica a la frecuencia propia no amortiguada.",
            "Ecuación diferencial rígida (stiff) ante pasos de tiempo no suficientemente finos.",
            "Sensibilidad extrema en la integral de energía acumulada mediante Romberg.",
        ],
    },
}

ESCENARIOS_MODULO_4 = {
    "NORMAL": {
        "nombre": "Normal - Muestreo Equidistante Regular",
        "descripcion": "Reconstrucción continua de aceleraciones con nodos uniformemente distribuidos en sensor de torre.",
        "parametros": {
            "num_nodos": 7,
            "t_inicial": 0.0,
            "t_final": 6.0,
            "tasa_perdida_pct": 0.0,
            "tipo_polinomio": "Cúbico Natural",
            "ruido_amplitud": 0.01,
        },
        "supuestos": [
            "Lecturas de acelerómetros triaxiales con sincronización temporal exacta.",
            "Interpolación mediante splines cúbicos con curvatura mínima en los extremos.",
            "Condiciones de suavidad C2 garantizadas en toda la trayectoria.",
        ],
    },
    "ESTRES": {
        "nombre": "Estrés - Ráfaga de Pérdida de Telemetría (Laguna Central)",
        "descripcion": "Reconstrucción con 14 puntos donde se pierde un bloque contiguo del 35% de datos por falla de enlace.",
        "parametros": {
            "num_nodos": 14,
            "t_inicial": 0.0,
            "t_final": 10.0,
            "intervalo_laguna": [3.5, 6.8],
            "tasa_perdida_pct": 35.0,
            "ruido_amplitud": 0.05,
        },
        "supuestos": [
            "Pérdida prolongada de comunicación inalámbrica en tramo entre torres.",
            "Polinomio de Newton de orden elevado sobre nodos dispersos.",
            "Cálculo de error de interpolación mediante puntos de control ocultos.",
        ],
    },
    "MAL_CONDICIONADO": {
        "nombre": "Mal Condicionado - Fenómeno de Runge y Nodos Agrupados",
        "descripcion": "Muestreo con nodos de alta proximidad temporal generando matriz de Vandermonde mal condicionada y oscilaciones de Runge en bordes.",
        "parametros": {
            "num_nodos": 11,
            "t_inicial": -1.0,
            "t_final": 1.0,
            "separacion_minima": 0.002,
            "funcion_base": "1 / (1 + 25*t^2)",
            "condicion_vandermonde": 8.5e7,
        },
        "supuestos": [
            "Distribución desfavorable de nodos equidistantes en polinomio de alto grado.",
            "Oscilaciones divergentes en los extremos del intervalo [-1, 1].",
            "Sensibilidad numérica extrema ante pequeños errores de redondeo en diferencias divididas.",
        ],
    },
}
