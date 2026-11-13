import json
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from inertia import inertia, render

from numerico.sistemas_lineales import (
    ESCENARIOS_MODULO_2,
    calcular_metricas_error,
    info_condicionamiento,
    analizar_sensibilidad,
    metodo_gauss_seidel,
    metodo_gradiente_conjugado,
    metodo_jacobi,
    metodo_lu,
    solucion_referencia,
)
from numerico.escenarios_definicion import (
    ESCENARIOS_MODULO_1,
    ESCENARIOS_MODULO_3,
    ESCENARIOS_MODULO_4,
)

from .models import (
    CasoEstudio,
    EjecucionMetodo,
    Escenario,
    IteracionResultado,
    ResultadoResumen,
    Simulacion,
)


def get_modulos_obligatorios():
    """Retorna los 4 módulos obligatorios del sistema SIMTELE-RISK."""
    return [
        {
            "id": 1,
            "numero": "Módulo 1",
            "titulo": "Detención de Emergencia de Cabinas",
            "ecuacion": "dx/dt = v,  dv/dt = -a(v, t)",
            "descripcion": "Modelado de dinámica de desaceleración y frenado de emergencia en tramos de alta pendiente ante falla de tracción.",
            "metodos": [
                "EDO (RK2, RK4)",
                "Integración (Trapecio, Simpson 1/3, Romberg)",
                "Raíces (Bisección, Newton, Secante)",
            ],
            "activo": False,
            "estado": "Modelado Matemático Completo - Algoritmos Semana 2",
            "badge_color": "amber",
        },
        {
            "id": 2,
            "numero": "Módulo 2",
            "titulo": "Deterioro Mecánico y Mantenimiento",
            "ecuacion": "A·x = b  (Calibración) | D(t) - D_umbral = 0",
            "descripcion": "Calibración acoplada de tasas de desgaste en poleas y cable mediante sistemas de ecuaciones lineales simétricos.",
            "metodos": [
                "Factorización LU",
                "Método de Jacobi",
                "Método de Gauss-Seidel",
                "Gradiente Conjugado (SPD)",
                "Solución Directa de Referencia",
            ],
            "activo": True,
            "estado": "Módulo 2: Sistemas Lineales Operativo - Semana 1",
            "badge_color": "emerald",
        },
        {
            "id": 3,
            "numero": "Módulo 3",
            "titulo": "Oscilaciones por Viento",
            "ecuacion": "m·x'' + c·x' + k·x = F(t)",
            "descripcion": "Respuesta aeroelástica y resonancia del sistema de suspensión de cabinas bajo ráfagas de viento lateral.",
            "metodos": [
                "EDO (RK2, RK4)",
                "Integración Numérica (Trapecio, Simpson, Romberg)",
            ],
            "activo": False,
            "estado": "Modelado Matemático Completo - Algoritmos Semana 2",
            "badge_color": "amber",
        },
        {
            "id": 4,
            "numero": "Módulo 4",
            "titulo": "Reconstrucción de Señales de Sensores",
            "ecuacion": "P_n(x) = ∑ y_i L_i(x)  o  Splines Cúbicos S_i(x)",
            "descripcion": "Reconstrucción de pérdidas de telemetría y vibraciones en torres intermedias mediante interpolación polinómica.",
            "metodos": [
                "Interpolación de Lagrange",
                "Newton (Diferencias Divididas)",
                "Splines Cúbicos",
                "Raíces de Cruce de Umbral",
            ],
            "activo": False,
            "estado": "Modelado Matemático Completo - Algoritmos Semana 2",
            "badge_color": "amber",
        },
    ]


def get_ultimas_simulaciones(limit=5):
    """Consulta las últimas N simulaciones guardadas con sus relaciones."""
    sims = (
        Simulacion.objects.select_related("escenario", "escenario__caso")
        .prefetch_related("ejecuciones")
        .order_by("-fecha")[:limit]
    )
    resultado = []
    for s in sims:
        resultado.append({
            "id": s.id,
            "fecha": s.fecha.strftime("%Y-%m-%d %H:%M:%S"),
            "escenario_tipo": s.escenario.tipo,
            "escenario_nombre": s.escenario.get_tipo_display(),
            "usuario": s.usuario,
            "estado": s.estado,
            "metodos_count": s.ejecuciones.count(),
        })
    return resultado


def _props_dashboard(corrida):
    """Genera el diccionario de props unificado para la vista Dashboard de Inertia."""
    ultimas = get_ultimas_simulaciones(limit=5)
    return {
        "titulo": "SIMTELE-RISK | Sistema de Simulación Numérica por Cable",
        "modulos": get_modulos_obligatorios(),
        "escenarios_disponibles": [
            {
                "clave": k,
                "nombre": v["nombre"],
                "descripcion": v["descripcion"],
            }
            for k, v in ESCENARIOS_MODULO_2.items()
        ],
        "escenarios_modulos": {
            1: ESCENARIOS_MODULO_1,
            3: ESCENARIOS_MODULO_3,
            4: ESCENARIOS_MODULO_4,
        },
        "corrida": corrida,
        "ultimas_simulaciones": ultimas,
    }


def _generar_interpretacion_doble(metodo_nombre: str, tipo_escenario: str, res: dict):
    """Genera la conclusión numérica y la conclusión del caso aplicado para cada método."""
    resumen_err = res.get("resumen_error", {})
    residual = resumen_err.get("residual", 0.0)
    tiempo_ms = res.get("tiempo_ms", 0.0)
    convergio = res.get("convergio", False)
    num_iters = len(res.get("iteraciones", []))
    criterio = res.get("criterio_parada", "")

    # 1. Conclusión Numérica
    if metodo_nombre == "Factorización LU":
        interp_num = (
            f"Método directo exacto por descomposición L·U (Doolittle). "
            f"Resuelve el sistema por sustitución directa hacia adelante y hacia atrás sin iterar en {tiempo_ms} ms. "
            f"Residuo final ||Ax-b||_inf = {residual:.2e}. Criterio: {criterio}."
        )
    elif metodo_nombre == "Jacobi":
        interp_num = (
            f"Método iterativo simultáneo. Convergencia: {'SÍ' if convergio else 'NO (límite de iteraciones)'} "
            f"en {num_iters} iteraciones. Criterio de parada: {criterio}. Residuo final: {residual:.2e}."
        )
    elif metodo_nombre == "Gauss-Seidel":
        interp_num = (
            f"Método iterativo sucesivo (actualización inmediata de variables). "
            f"Convergencia: {'SÍ' if convergio else 'NO (límite de iteraciones)'} en {num_iters} iteraciones. "
            f"Criterio de parada: {criterio}. Residuo final: {residual:.2e}."
        )
    else:  # Gradiente Conjugado
        interp_num = (
            f"Método de subespacios de Krylov para matrices Simétricas Definidas Positivas (SPD). "
            f"Convergencia: {'SÍ' if convergio else 'NO'} en {num_iters} iteraciones (cota teórica <= n=4). "
            f"Criterio de parada: {criterio}. Residuo final: {residual:.2e}."
        )

    # 2. Conclusión del Caso Aplicado
    if tipo_escenario == "MAL_CONDICIONADO":
        interp_caso = (
            "Matriz cuasi-singular (κ = 792.0) por sensores de deformación cuasi-colineales en las poleas. "
            "Jacobi y Gauss-Seidel divergen/fallan por pérdida de dominancia diagonal estricta (|a_ii| < sum |a_ij|), "
            "mientras que Gradiente Conjugado converge con precisión porque la matriz conserva la propiedad "
            "Simétrica Definida Positiva (SPD) con todos sus autovalores estrictamente positivos."
        )
    elif tipo_escenario == "ESTRES":
        interp_caso = (
            "Mayor acoplamiento inter-poleas con dominancia diagonal débil. "
            "La alta interacción física entre apoyos ralentiza sustancialmente la tasa de contracción espectral "
            "de Jacobi y Gauss-Seidel (requiriendo más iteraciones que en condiciones nominales), "
            "evidenciando la necesidad de calibración con amortiguamiento inter-ejes."
        )
    else:  # NORMAL
        interp_caso = (
            "Sistema bien condicionado (κ = 3.14) con estricta dominancia diagonal en los sensores de carga. "
            "Calibración nominal óptima de las 4 poleas con convergencia monótona y rápida en todos los algoritmos."
        )

    return {"numerica": interp_num, "caso": interp_caso}


@transaction.atomic
def ejecutar_y_persistir(tipo_escenario: str = "NORMAL", tolerancia: float = 1e-6, max_iter: int = 100):
    """Ejecuta los 4 métodos de sistemas lineales, analiza sensibilidad y persiste la corrida en la BD."""
    if tipo_escenario not in ESCENARIOS_MODULO_2:
        tipo_escenario = "NORMAL"

    datos_esc = ESCENARIOS_MODULO_2[tipo_escenario]
    A = datos_esc["A"]
    b = datos_esc["b"]
    x_exacta = datos_esc["x_exacta"]

    # Información de condicionamiento y simetría
    cond_info = info_condicionamiento(A)

    # Análisis de sensibilidad ante perturbación δb
    sensibilidad_info = analizar_sensibilidad(A, b)

    # Solución de referencia de alta precisión
    x_ref = solucion_referencia(A, b)

    # Ejecución de los 4 métodos numéricos
    res_lu = metodo_lu(A, b, x_ref)
    res_jacobi = metodo_jacobi(A, b, x_ref, tol=tolerancia, max_iter=max_iter)
    res_gs = metodo_gauss_seidel(A, b, x_ref, tol=tolerancia, max_iter=max_iter)
    res_gc = metodo_gradiente_conjugado(A, b, x_ref, tol=tolerancia, max_iter=max_iter)

    metodos_resultados = [res_lu, res_jacobi, res_gs, res_gc]

    # Persistencia en Base de Datos (6 entidades obligatorias)
    # 1. CasoEstudio
    caso, _ = CasoEstudio.objects.get_or_create(
        nombre="Deterioro mecánico y mantenimiento",
        defaults={
            "modelo_version": "v1.0",
            "descripcion": "Calibración de desgaste en poleas y vida útil residual de cable tractor",
        },
    )

    # 2. Escenario con parámetros, condición y sensibilidad
    escenario, _ = Escenario.objects.get_or_create(
        caso=caso,
        tipo=tipo_escenario,
        defaults={
            "parametros_json": {
                "nombre": datos_esc["nombre"],
                "descripcion": datos_esc["descripcion"],
                "A": A,
                "b": b,
                "x_exacta": x_exacta,
                "condicion": cond_info,
                "sensibilidad": sensibilidad_info,
            },
            "fuente_datos": "Calibración sintética de desgaste en poleas (4x4 SPD)",
        },
    )

    # Actualizar parámetros si el escenario ya existía para asegurar que contiene la sensibilidad
    params = escenario.parametros_json or {}
    params["nombre"] = datos_esc["nombre"]
    params["descripcion"] = datos_esc["descripcion"]
    params["A"] = A
    params["b"] = b
    params["x_exacta"] = x_exacta
    params["condicion"] = cond_info
    params["sensibilidad"] = sensibilidad_info
    escenario.parametros_json = params
    escenario.save(update_fields=["parametros_json"])

    # 3. Simulacion
    simulacion = Simulacion.objects.create(
        escenario=escenario,
        usuario="Estudiante Informática",
        estado="COMPLETADO",
    )

    # 4. EjecucionMetodo, 5. IteracionResultado, 6. ResultadoResumen
    for res in metodos_resultados:
        ejec = EjecucionMetodo.objects.create(
            simulacion=simulacion,
            metodo=res["metodo"],
            tolerancia=tolerancia,
            paso=None,
            max_iter=max_iter,
            convergio=res["convergio"],
            tiempo_ms=res["tiempo_ms"],
        )

        # Iteraciones
        iteraciones_objs = [
            IteracionResultado(
                ejecucion=ejec,
                numero=it["numero"],
                aproximacion_json=it["aproximacion"],
                residual=it["residual"],
                error_abs=it["error_abs"],
                error_rel=it["error_rel"],
            )
            for it in res["iteraciones"]
        ]
        IteracionResultado.objects.bulk_create(iteraciones_objs)

        # Interpretación doble serializada en JSON
        interpretacion_dict = _generar_interpretacion_doble(res["metodo"], tipo_escenario, res)
        res["interpretacion"] = interpretacion_dict

        ResultadoResumen.objects.create(
            ejecucion=ejec,
            referencia=x_ref,
            valor_json=res["solucion"],
            metrica_error_json=res["resumen_error"],
            interpretacion=json.dumps(interpretacion_dict, ensure_ascii=False),
        )

    return {
        "simulacion_id": simulacion.id,
        "tipo_escenario": tipo_escenario,
        "tolerancia": tolerancia,
        "max_iter": max_iter,
        "datos_escenario": {
            "nombre": datos_esc["nombre"],
            "descripcion": datos_esc["descripcion"],
            "A": A,
            "b": b,
            "x_exacta": x_exacta,
            "condicion_inf": cond_info["condicion_inf"],
            "es_spd": cond_info["es_spd"],
            "es_simetrica": cond_info["es_simetrica"],
        },
        "sensibilidad": sensibilidad_info,
        "solucion_referencia": x_ref,
        "metodos": metodos_resultados,
    }


def reconstruir_desde_simulacion(sim: Simulacion):
    """Reconstruye el payload de visualización a partir de una simulación guardada."""
    esc = sim.escenario
    params = esc.parametros_json or {}
    A = params.get("A", [])
    b = params.get("b", [])
    x_exacta = params.get("x_exacta", [])
    cond_info = params.get("condicion", info_condicionamiento(A) if A else {})
    sensibilidad_info = params.get("sensibilidad") or (analizar_sensibilidad(A, b) if A and b else {})

    metodos_list = []
    x_ref = None

    for ejec in sim.ejecuciones.select_related("resumen").prefetch_related("iteraciones").all():
        resumen = getattr(ejec, "resumen", None)
        if resumen and x_ref is None:
            x_ref = resumen.referencia

        iteraciones_data = [
            {
                "numero": it.numero,
                "aproximacion": it.aproximacion_json,
                "residual": it.residual,
                "error_abs": it.error_abs,
                "error_rel": it.error_rel,
                "error_porc": round(it.error_rel * 100.0, 6),
            }
            for it in ejec.iteraciones.all()
        ]

        resumen_error = resumen.metrica_error_json if resumen else (iteraciones_data[-1] if iteraciones_data else {})

        # Normalizar interpretación (JSON nuevo vs texto legado)
        raw_interp = resumen.interpretacion if resumen else ""
        try:
            interp_obj = json.loads(raw_interp)
            if not isinstance(interp_obj, dict) or "numerica" not in interp_obj:
                interp_obj = {"numerica": str(raw_interp), "caso": ""}
        except Exception:
            interp_obj = {"numerica": str(raw_interp), "caso": ""}

        metodos_list.append({
            "metodo": ejec.metodo,
            "convergio": ejec.convergio,
            "tiempo_ms": ejec.tiempo_ms,
            "solucion": resumen.valor_json if resumen else (iteraciones_data[-1]["aproximacion"] if iteraciones_data else []),
            "iteraciones": iteraciones_data,
            "resumen_error": resumen_error,
            "interpretacion": interp_obj,
        })

    if x_ref is None and A and b:
        x_ref = solucion_referencia(A, b)

    return {
        "simulacion_id": sim.id,
        "tipo_escenario": esc.tipo,
        "tolerancia": sim.ejecuciones.first().tolerancia if sim.ejecuciones.exists() else 1e-6,
        "max_iter": sim.ejecuciones.first().max_iter if sim.ejecuciones.exists() else 100,
        "datos_escenario": {
            "nombre": params.get("nombre", f"Escenario {esc.get_tipo_display()}"),
            "descripcion": params.get("descripcion", ""),
            "A": A,
            "b": b,
            "x_exacta": x_exacta,
            "condicion_inf": cond_info.get("condicion_inf", 0),
            "es_spd": cond_info.get("es_spd", False),
            "es_simetrica": cond_info.get("es_simetrica", False),
        },
        "sensibilidad": sensibilidad_info,
        "solucion_referencia": x_ref or [],
        "metodos": metodos_list,
    }


@inertia("Dashboard")
def index(request: HttpRequest) -> dict[str, object]:
    """Ruta principal '/': Renderiza la vista Inertia Dashboard.vue."""
    ultima_sim = Simulacion.objects.order_by("-fecha").first()
    if ultima_sim:
        datos_corrida = reconstruir_desde_simulacion(ultima_sim)
    else:
        datos_corrida = ejecutar_y_persistir(tipo_escenario="NORMAL", tolerancia=1e-6, max_iter=100)

    return _props_dashboard(datos_corrida)


def ejecutar_modulo_2(request: HttpRequest) -> HttpResponse:
    """Ruta '/modulo-2/ejecutar' (POST o GET):

    Recibe escenario y tolerancia, ejecuta y persiste la simulación.
    """
    if request.method == "POST":
        if request.content_type == "application/json":
            try:
                body = json.loads(request.body.decode("utf-8"))
            except Exception:
                body = {}
            tipo_escenario = body.get("escenario", "NORMAL")
            tolerancia = float(body.get("tolerancia", 1e-6))
            max_iter = int(body.get("max_iter", 100))
        else:
            tipo_escenario = request.POST.get("escenario", "NORMAL")
            tolerancia = float(request.POST.get("tolerancia", 1e-6))
            max_iter = int(request.POST.get("max_iter", 100))
    else:
        tipo_escenario = request.GET.get("escenario", "NORMAL")
        tolerancia = float(request.GET.get("tolerancia", 1e-6))
        max_iter = int(request.GET.get("max_iter", 100))

    if tipo_escenario not in ESCENARIOS_MODULO_2:
        tipo_escenario = "NORMAL"

    datos_corrida = ejecutar_y_persistir(
        tipo_escenario=tipo_escenario,
        tolerancia=tolerancia,
        max_iter=max_iter,
    )
    return render(request, "Dashboard", props=_props_dashboard(datos_corrida))


def recargar_simulacion_view(request: HttpRequest, simulacion_id: int) -> HttpResponse:
    """Ruta '/modulo-2/recargar/<simulacion_id>': Carga una simulación histórica en Dashboard."""
    sim = get_object_or_404(Simulacion, id=simulacion_id)
    datos_corrida = reconstruir_desde_simulacion(sim)
    return render(request, "Dashboard", props=_props_dashboard(datos_corrida))


@require_POST
def relanzar_simulacion_view(request: HttpRequest, simulacion_id: int) -> HttpResponse:
    """Ruta 'POST /modulo-2/relanzar/<simulacion_id>/': Re-ejecuta una simulación histórica y crea un nuevo registro."""
    sim_orig = get_object_or_404(Simulacion, id=simulacion_id)
    tipo_escenario = sim_orig.escenario.tipo
    primera_ejec = sim_orig.ejecuciones.first()
    tolerancia = primera_ejec.tolerancia if primera_ejec else 1e-6
    max_iter = primera_ejec.max_iter if primera_ejec else 100

    datos_corrida = ejecutar_y_persistir(
        tipo_escenario=tipo_escenario,
        tolerancia=tolerancia,
        max_iter=max_iter,
    )
    return render(request, "Dashboard", props=_props_dashboard(datos_corrida))


def health(request: HttpRequest) -> JsonResponse:
    """Liveness probe."""
    return JsonResponse({"status": "ok"})
