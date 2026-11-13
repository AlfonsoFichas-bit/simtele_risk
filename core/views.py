import json
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from inertia import inertia

from numerico.sistemas_lineales import (
    ESCENARIOS_MODULO_2,
    calcular_metricas_error,
    info_condicionamiento,
    metodo_gauss_seidel,
    metodo_gradiente_conjugado,
    metodo_jacobi,
    metodo_lu,
    solucion_referencia,
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


@transaction.atomic
def ejecutar_y_persistir(tipo_escenario: str = "NORMAL", tolerancia: float = 1e-6, max_iter: int = 100):
    """Ejecuta los 4 métodos de sistemas lineales y persiste la corrida en la BD."""
    if tipo_escenario not in ESCENARIOS_MODULO_2:
        tipo_escenario = "NORMAL"

    datos_esc = ESCENARIOS_MODULO_2[tipo_escenario]
    A = datos_esc["A"]
    b = datos_esc["b"]
    x_exacta = datos_esc["x_exacta"]

    # Información de condicionamiento y simetría
    cond_info = info_condicionamiento(A)

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

    # 2. Escenario
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
            },
            "fuente_datos": "Calibración sintética de desgaste en poleas (4x4 SPD)",
        },
    )

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

        # Interpretación matemática y física
        if res["metodo"] == "Factorización LU":
            interpretacion = (
                f"Método directo exacto (descomposición L·U de Doolittle). "
                f"Resuelve el sistema en un solo ciclo sin iterar. Tiempo: {res['tiempo_ms']} ms. "
                f"Residuo residual ||Ax-b||: {res['resumen_error']['residual']:.2e}."
            )
        elif res["metodo"] == "Jacobi":
            interpretacion = (
                f"Método iterativo simultáneo. Convergencia: {'Exitosa' if res['convergio'] else 'No convergió/Límite de iteraciones'} "
                f"en {len(res['iteraciones'])} iteraciones. Error relativo final: {res['resumen_error']['error_rel']:.2e}."
            )
        elif res["metodo"] == "Gauss-Seidel":
            interpretacion = (
                f"Método iterativo sucesivo (actualización inmediata de variables). Convergencia: {'Exitosa' if res['convergio'] else 'No alcanzada'} "
                f"en {len(res['iteraciones'])} iteraciones con residuo {res['resumen_error']['residual']:.2e}."
            )
        else:  # Gradiente Conjugado
            interpretacion = (
                f"Método de subespacios de Krylov para matrices Simétricas Definidas Positivas (SPD). "
                f"Convergencia teórica garantizada en máximo n={len(b)} pasos exactos. "
                f"Completó {len(res['iteraciones'])} iteraciones. Error relativo: {res['resumen_error']['error_rel']:.2e}."
            )

        ResultadoResumen.objects.create(
            ejecucion=ejec,
            referencia=x_ref,
            valor_json=res["solucion"],
            metrica_error_json=res["resumen_error"],
            interpretacion=interpretacion,
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
        "solucion_referencia": x_ref,
        "metodos": metodos_resultados,
    }


def reconstruir_desde_simulacion(sim: Simulacion):
    """Reconstruye el payload de visualización a partir de una simulación guardada."""
    esc = sim.escenario
    params = esc.parametros_json
    A = params.get("A", [])
    b = params.get("b", [])
    x_exacta = params.get("x_exacta", [])
    cond_info = params.get("condicion", info_condicionamiento(A) if A else {})

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

        metodos_list.append({
            "metodo": ejec.metodo,
            "convergio": ejec.convergio,
            "tiempo_ms": ejec.tiempo_ms,
            "solucion": resumen.valor_json if resumen else (iteraciones_data[-1]["aproximacion"] if iteraciones_data else []),
            "iteraciones": iteraciones_data,
            "resumen_error": resumen_error,
            "interpretacion": resumen.interpretacion if resumen else "",
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
        "solucion_referencia": x_ref or [],
        "metodos": metodos_list,
    }


@inertia("Dashboard")
def index(request: HttpRequest) -> dict[str, object]:
    """Ruta principal '/': Renderiza la vista Inertia Dashboard.vue."""
    # Verificar si ya existe al menos una simulación en la BD; si no, generar la inicial NORMAL
    ultima_sim = Simulacion.objects.order_by("-fecha").first()
    if ultima_sim:
        datos_corrida = reconstruir_desde_simulacion(ultima_sim)
    else:
        datos_corrida = ejecutar_y_persistir(tipo_escenario="NORMAL", tolerancia=1e-6, max_iter=100)

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
        "corrida": datos_corrida,
        "ultimas_simulaciones": ultimas,
    }


def ejecutar_modulo_2(request: HttpRequest) -> HttpResponse:
    """Ruta '/modulo-2/ejecutar' (POST o GET):

    Recibe escenario y tolerancia, ejecuta y persiste la simulación.
    """
    if request.method == "POST":
        # Manejar tanto JSON como Form data
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
        # GET query params
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
    ultimas = get_ultimas_simulaciones(limit=5)

    # Si la petición es Inertia, renderizamos Dashboard con los nuevos datos
    from inertia import render
    return render(
        request,
        "Dashboard",
        props={
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
            "corrida": datos_corrida,
            "ultimas_simulaciones": ultimas,
        },
    )


def recargar_simulacion_view(request: HttpRequest, simulacion_id: int) -> HttpResponse:
    """Ruta '/modulo-2/recargar/<simulacion_id>': Carga una simulación histórica en Dashboard."""
    sim = get_object_or_404(Simulacion, id=simulacion_id)
    datos_corrida = reconstruir_desde_simulacion(sim)
    ultimas = get_ultimas_simulaciones(limit=5)

    from inertia import render
    return render(
        request,
        "Dashboard",
        props={
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
            "corrida": datos_corrida,
            "ultimas_simulaciones": ultimas,
        },
    )


def health(request: HttpRequest) -> JsonResponse:
    """Liveness probe."""
    return JsonResponse({"status": "ok"})
