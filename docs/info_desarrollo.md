# SIMTELE-RISK — Requisitos de desarrollo

Aplicación web integrada con **4 módulos obligatorios**. Cada módulo ejecuta **3 escenarios**: NORMAL, ESTRÉS y MAL CONDICIONADO. Teoría de errores transversal en todos los módulos (no es un módulo aparte).

## Métodos numéricos obligatorios (cobertura mínima global)

| Familia | Métodos requeridos | Evidencia mínima |
| --- | --- | --- |
| Errores (transversal) | Absoluto, relativo (si procede), porcentual, residual, sensibilidad | Tablas de error por CADA módulo; comparación bajo perturbaciones |
| Sistemas lineales | Jacobi, Gauss-Seidel, LU, gradiente conjugado, solución directa de referencia | A x = b de tamaño ≥ 4; residuo, condición, iteraciones y errores |
| Interpolación | Lagrange, Newton (diferencias divididas), splines cúbicos | Mismos nodos; puntos ocultados; curvas superpuestas |
| Raíces | Bisección, Newton-Raphson, secante | Intervalo/semillas, raíz, iteraciones, error o residual |
| Integración | Trapecio compuesto, Simpson 1/3 compuesto, Romberg | Integral, valor analítico o referencia, refinamiento y errores |
| EDO | RK2 (variante declarada), RK4 | Condición inicial, paso, tabla temporal, solución de referencia y errores |

No hace falta ejecutar todas las familias en cada módulo, pero el sistema completo debe incluir TODOS los métodos.

### Asignación de métodos por módulo

- **Módulo 1 (Detención de emergencia):** EDO RK2/RK4 sobre dx/dt = v, dv/dt = -a(v,t); integración de v(t) con trapecio, Simpson, Romberg; raíces para v(t) = 0 con bisección, Newton, secante (si hay formulación continua).
- **Módulo 2 (Deterioro/mantenimiento):** Raíces sobre D(t) - D_umbral = 0; sistemas lineales (Jacobi, Gauss-Seidel, LU, gradiente conjugado sobre matriz SPD) para calibrar coeficientes; integración opcional de la tasa de deterioro.
- **Módulo 3 (Oscilaciones por viento):** EDO RK2/RK4 sobre x' = v, v' = (F(t) - c·v - k·x)/m; integración de |x(t)| o x(t)² con trapecio, Simpson, Romberg; sistemas lineales auxiliares de calibración opcionales.
- **Módulo 4 (Reconstrucción de sensores):** Interpolación obligatoria (Lagrange, Newton, splines cúbicos); sistemas lineales auxiliares de calibración; raíces para cruce de umbral sobre la curva interpolada.

## Escenarios por módulo (3 × 4)

| Escenario | Definición |
| --- | --- |
| NORMAL | Parámetros nominales sintéticos, datos consistentes, configuración numérica adecuada |
| ESTRÉS | Pasos mayores/menores, perturbaciones más intensas, más puntos o más tiempo de simulación |
| MAL CONDICIONADO | κ(A) elevado, nodos desfavorables, raíz múltiple/derivada pequeña o sensibilidad demostrable |

Reglas: distinguir mal condicionamiento de falta de convergencia; evitar matrices no SPD en gradiente conjugado; justificar condiciones de convergencia de los iterativos.

## Pantallas / funciones de la aplicación

| Pantalla | Contenido imprescindible |
| --- | --- |
| Inicio | Cuatro tarjetas: Detención, Deterioro, Oscilaciones, Sensores |
| Módulo del caso | Modelo, parámetros con validaciones, selector de escenario (NORMAL/ESTRÉS/MAL CONDICIONADO) |
| Resultados | Métodos aplicables, tablas de iteraciones, error, comparación gráfica |
| Interpretación | Conclusión matemática y conclusión del caso, claramente separadas |
| Historial | Buscar, abrir, visualizar y relanzar simulaciones guardadas |

Debe existir un panel general de comparación y navegación de vuelta al historial desde cada módulo. Mínimo **2 gráficos útiles por módulo**: uno de solución/escenario y otro de error/convergencia/comparación.

## Modelo de datos obligatorio

Entidades mínimas:

| Entidad | Campos |
| --- | --- |
| caso_estudio | id, nombre, modelo_version |
| escenario | id, caso_id, tipo (NORMAL/ESTRÉS/MAL_CONDICIONADO), parámetros_json, fuente_datos |
| simulacion | id, escenario_id, fecha, usuario/equipo opcional, estado |
| ejecucion_metodo | id, simulacion_id, metodo, tolerancia, paso, max_iter, convergio, tiempo_ms |
| iteracion_resultado | id, ejecucion_id, numero, aproximacion_json, residual, error_abs, error_rel |
| resultado_resumen | id, ejecucion_id, referencia, valor_json, metrica_error_json, interpretacion |

Se debe entregar: DER, modelo relacional y script SQL o migraciones.

## Persistencia (requisito verificable)

- Guardar una ejecución completa: entrada, escenario, método, iteraciones, resultados y errores.
- Recuperarla después de reiniciar la aplicación (no solo memoria/temporal).
- Prueba obligatoria: ejecutar → guardar → cerrar/actualizar → recuperar parámetros, iteraciones y gráficos → recalcular → coincidir dentro de la tolerancia.
- El historial debe permitir buscar, abrir, visualizar y relanzar.

## Cálculos y evidencias que el código debe producir

- Tablas de iteraciones o refinamiento (paso, subintervalos, tolerancia), valor aproximado y criterio de parada.
- Errores por método y escenario (sin dividir por cero), residuales, sensibilidad ante perturbaciones y convergencia.
- Referencia analítica cuando exista; si no, solución independiente de alta precisión justificada.
- Comparación de métodos aplicables entre sí, por escenario.
- Manejo de no convergencia (max_iter, tolerancia) y registro del estado (convergio true/false, tiempo en ms).
- Funciones de prueba con solución analítica cuando sea posible (ej. v(t)=v0-at; D(t)=D0+αt+βt²; oscilador subamortiguado; y(t)=sin(t) o e^(-t)).

## Entregables técnicos por semana

- **Semana 1:** errores transversal + sistemas lineales implementados; prototipo web con 4 módulos visibles; DER inicial; repo GitHub con README.
- **Semana 2:** interpolación, raíces, integración y EDO; 4 módulos ejecutan al menos NORMAL con tablas, errores y 2 gráficos; escenarios ESTRÉS y MAL CONDICIONADO; BD funcional con guardar/recuperar.
- **Semana 3:** 3 escenarios × 4 módulos; comparación completa; persistencia comprobada; recuperación de experimento histórico en vivo.

## Restricciones

- Escenarios y datos 100% sintéticos, sin conexión a sistemas reales.
- El diseño visual no compensa algoritmos incorrectos; la prioridad es el cálculo correcto y verificable.
- Trabajo individual permite diseño austero, pero no reduce alcance matemático ni rúbrica.
- Defensa: cada participante cambia parámetros, ejecuta, recupera un experimento e interpreta resultados.
