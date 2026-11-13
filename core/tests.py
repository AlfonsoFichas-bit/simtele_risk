from inertia.test import InertiaTestCase
from core.models import (
    CasoEstudio,
    Escenario,
    Simulacion,
    EjecucionMetodo,
    IteracionResultado,
    ResultadoResumen,
)
from numerico.sistemas_lineales import (
    ESCENARIOS_MODULO_2,
    metodo_lu,
    metodo_jacobi,
    metodo_gauss_seidel,
    metodo_gradiente_conjugado,
    solucion_referencia,
    info_condicionamiento,
    analizar_sensibilidad,
)
from numerico.escenarios_definicion import (
    ESCENARIOS_MODULO_1,
    ESCENARIOS_MODULO_3,
    ESCENARIOS_MODULO_4,
)


class DashboardViewTests(InertiaTestCase):
    def test_index_renders_dashboard_and_creates_initial_simulation(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertComponentUsed("Dashboard")

        props = self.props()
        self.assertIn("modulos", props)
        self.assertEqual(len(props["modulos"]), 4)
        self.assertIn("corrida", props)
        self.assertIn("ultimas_simulaciones", props)

        # Verificar que se persistió en BD
        self.assertTrue(Simulacion.objects.exists())
        self.assertEqual(EjecucionMetodo.objects.count(), 4)
        self.assertTrue(IteracionResultado.objects.exists())
        self.assertEqual(ResultadoResumen.objects.count(), 4)

    def test_ejecutar_modulo_2_post_normal(self):
        response = self.client.post("/modulo-2/ejecutar", {
            "escenario": "NORMAL",
            "tolerancia": 1e-6,
            "max_iter": 100,
        })
        self.assertEqual(response.status_code, 200)
        self.assertComponentUsed("Dashboard")

        props = self.props()
        corrida = props["corrida"]
        self.assertEqual(corrida["tipo_escenario"], "NORMAL")
        self.assertEqual(len(corrida["metodos"]), 4)

    def test_ejecutar_modulo_2_estres_y_mal_condicionado(self):
        for esc in ["ESTRES", "MAL_CONDICIONADO"]:
            response = self.client.post("/modulo-2/ejecutar", {
                "escenario": esc,
                "tolerancia": 1e-5,
                "max_iter": 50,
            })
            self.assertEqual(response.status_code, 200)
            corrida = self.props()["corrida"]
            self.assertEqual(corrida["tipo_escenario"], esc)

    def test_recargar_simulacion_historica(self):
        # Crear una simulación
        self.client.post("/modulo-2/ejecutar", {"escenario": "ESTRES"})
        sim = Simulacion.objects.filter(escenario__tipo="ESTRES").latest("id")

        # Recargarla
        response = self.client.get(f"/modulo-2/recargar/{sim.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertComponentUsed("Dashboard")
        corrida = self.props()["corrida"]
        self.assertEqual(corrida["simulacion_id"], sim.id)
        self.assertEqual(corrida["tipo_escenario"], "ESTRES")
        self.assertIn("sensibilidad", corrida)

    def test_relanzar_simulacion_crea_nueva_con_mismos_parametros(self):
        # Crear simulación original con parámetros específicos
        self.client.post("/modulo-2/ejecutar", {
            "escenario": "ESTRES",
            "tolerancia": 1e-4,
            "max_iter": 40,
        })
        sim_orig = Simulacion.objects.filter(escenario__tipo="ESTRES").latest("id")
        total_antes = Simulacion.objects.count()

        # Relanzar
        response = self.client.post(f"/modulo-2/relanzar/{sim_orig.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertComponentUsed("Dashboard")

        total_despues = Simulacion.objects.count()
        self.assertEqual(total_despues, total_antes + 1)

        sim_nueva = Simulacion.objects.latest("id")
        self.assertNotEqual(sim_nueva.id, sim_orig.id)
        self.assertEqual(sim_nueva.escenario.tipo, sim_orig.escenario.tipo)

        # Tolerancia y max_iter coincidentes
        ejec_orig = sim_orig.ejecuciones.first()
        ejec_nueva = sim_nueva.ejecuciones.first()
        self.assertEqual(ejec_nueva.tolerancia, ejec_orig.tolerancia)
        self.assertEqual(ejec_nueva.max_iter, ejec_orig.max_iter)

    def test_relanzar_404_no_crea_registros(self):
        total_antes = Simulacion.objects.count()
        response = self.client.post("/modulo-2/relanzar/999999/")
        self.assertEqual(response.status_code, 404)
        total_despues = Simulacion.objects.count()
        self.assertEqual(total_despues, total_antes)

    def test_persistencia_seis_entidades_y_sensibilidad_interpretacion(self):
        import json
        self.client.post("/modulo-2/ejecutar", {"escenario": "MAL_CONDICIONADO"})
        sim = Simulacion.objects.filter(escenario__tipo="MAL_CONDICIONADO").latest("id")

        # 1. CasoEstudio
        self.assertIsNotNone(sim.escenario.caso)
        # 2. Escenario
        self.assertEqual(sim.escenario.tipo, "MAL_CONDICIONADO")
        self.assertIn("sensibilidad", sim.escenario.parametros_json)
        self.assertGreater(sim.escenario.parametros_json["sensibilidad"]["factor_amplificacion"], 100.0)

        # 3. Simulacion
        self.assertEqual(sim.estado, "COMPLETADO")

        # 4. EjecucionMetodo
        self.assertEqual(sim.ejecuciones.count(), 4)

        for ejec in sim.ejecuciones.all():
            # 5. IteracionResultado
            self.assertTrue(ejec.iteraciones.exists())
            # 6. ResultadoResumen con interpretacion doble
            self.assertTrue(hasattr(ejec, "resumen"))
            interp_dict = json.loads(ejec.resumen.interpretacion)
            self.assertIn("numerica", interp_dict)
            self.assertIn("caso", interp_dict)
            self.assertIn("dominancia diagonal", interp_dict["caso"])
            self.assertIn("SPD", interp_dict["caso"])

    def test_props_dashboard_unificados_todas_las_rutas(self):
        rutas = ["/", "/modulo-2/ejecutar"]
        claves_esperadas = {"titulo", "modulos", "escenarios_disponibles", "escenarios_modulos", "corrida", "ultimas_simulaciones"}

        for ruta in rutas:
            response = self.client.get(ruta)
            self.assertEqual(response.status_code, 200)
            props = self.props()
            self.assertTrue(claves_esperadas.issubset(set(props.keys())), f"Faltan claves en {ruta}")


class MetodosNumericosTests(InertiaTestCase):
    def test_metodos_convergencia_escenario_normal(self):
        datos = ESCENARIOS_MODULO_2["NORMAL"]
        A = datos["A"]
        b = datos["b"]
        x_exacta = datos["x_exacta"]

        cond = info_condicionamiento(A)
        self.assertTrue(cond["es_spd"])
        self.assertLess(cond["condicion_inf"], 50.0)

        x_ref = solucion_referencia(A, b)
        for i in range(len(x_exacta)):
            self.assertAlmostEqual(x_ref[i], x_exacta[i], places=4)

        # LU
        res_lu = metodo_lu(A, b, x_ref)
        self.assertTrue(res_lu["convergio"])
        self.assertLess(res_lu["resumen_error"]["error_abs"], 1e-4)

        # Jacobi
        res_jac = metodo_jacobi(A, b, x_ref, tol=1e-5, max_iter=100)
        self.assertTrue(res_jac["convergio"])
        self.assertLess(res_jac["resumen_error"]["residual"], 1e-4)

        # Gauss-Seidel
        res_gs = metodo_gauss_seidel(A, b, x_ref, tol=1e-5, max_iter=100)
        self.assertTrue(res_gs["convergio"])
        self.assertLess(res_gs["resumen_error"]["residual"], 1e-4)

        # Gradiente Conjugado
        res_gc = metodo_gradiente_conjugado(A, b, x_ref, tol=1e-5, max_iter=100)
        self.assertTrue(res_gc["convergio"])
        self.assertLess(res_gc["resumen_error"]["residual"], 1e-4)

    def test_consistencia_b_igual_A_por_x_estrella(self):
        import numpy as np
        for clave, esc in ESCENARIOS_MODULO_2.items():
            A = np.array(esc["A"], dtype=float)
            b = np.array(esc["b"], dtype=float)
            x_exacta = np.array(esc["x_exacta"], dtype=float)
            diff = np.max(np.abs(A @ x_exacta - b))
            self.assertLess(diff, 1e-10, f"Inconsistencia en {clave}: ||A @ x* - b|| = {diff}")

    def test_factorizacion_lu_L_por_U_igual_A(self):
        import numpy as np
        for clave in ["NORMAL", "ESTRES"]:
            esc = ESCENARIOS_MODULO_2[clave]
            A = np.array(esc["A"], dtype=float)
            b = np.array(esc["b"], dtype=float)
            res_lu = metodo_lu(A, b, esc["x_exacta"])
            self.assertTrue(res_lu["convergio"])
            L = np.array(res_lu["L"], dtype=float)
            U = np.array(res_lu["U"], dtype=float)
            self.assertTrue(np.allclose(L @ U, A, atol=1e-4), f"L @ U != A en {clave}")

    def test_analisis_sensibilidad_normal_y_mal_condicionado(self):
        sens_norm = analizar_sensibilidad(
            ESCENARIOS_MODULO_2["NORMAL"]["A"],
            ESCENARIOS_MODULO_2["NORMAL"]["b"],
        )
        sens_mal = analizar_sensibilidad(
            ESCENARIOS_MODULO_2["MAL_CONDICIONADO"]["A"],
            ESCENARIOS_MODULO_2["MAL_CONDICIONADO"]["b"],
        )

        self.assertLess(sens_norm["factor_amplificacion"], 10.0)
        self.assertGreater(sens_mal["factor_amplificacion"], 100.0)
        self.assertAlmostEqual(sens_mal["cota_teorica_kappa"], 792.0, delta=0.5)

    def test_criterio_parada_declarado(self):
        esc = ESCENARIOS_MODULO_2["NORMAL"]
        A, b, x_ref = esc["A"], esc["b"], esc["x_exacta"]

        lu = metodo_lu(A, b, x_ref)
        jac = metodo_jacobi(A, b, x_ref)
        gs = metodo_gauss_seidel(A, b, x_ref)
        gc = metodo_gradiente_conjugado(A, b, x_ref)

        self.assertEqual(
            lu["criterio_parada"],
            "Método directo: sin criterio iterativo (sustitución L·y=b, U·x=y)",
        )
        self.assertEqual(jac["criterio_parada"], "||x^(k) - x^(k-1)||_inf < tol")
        self.assertEqual(gs["criterio_parada"], "||x^(k) - x^(k-1)||_inf < tol")
        self.assertEqual(gc["criterio_parada"], "||r^(k)||_2 < tol")

    def test_fallo_seguro_pivote_nulo_y_diagonal_nula(self):
        A_piv_nulo = [[0.0, 1.0], [1.0, 1.0]]
        b_vec = [1.0, 2.0]
        x_ref = [1.0, 1.0]

        res_lu = metodo_lu(A_piv_nulo, b_vec, x_ref)
        self.assertFalse(res_lu["convergio"])
        self.assertIn("error", res_lu)
        self.assertIn("Pivote nulo", res_lu["error"])

        res_jac = metodo_jacobi(A_piv_nulo, b_vec, x_ref)
        self.assertFalse(res_jac["convergio"])
        self.assertIn("error", res_jac)
        self.assertIn("diagonal nulo", res_jac["error"])

        res_gs = metodo_gauss_seidel(A_piv_nulo, b_vec, x_ref)
        self.assertFalse(res_gs["convergio"])
        self.assertIn("error", res_gs)
        self.assertIn("diagonal nulo", res_gs["error"])

    def test_escenarios_declarativos_modulos_1_3_4(self):
        import json
        modulos = [
            ("Módulo 1", ESCENARIOS_MODULO_1),
            ("Módulo 3", ESCENARIOS_MODULO_3),
            ("Módulo 4", ESCENARIOS_MODULO_4),
        ]
        tipos_esperados = {"NORMAL", "ESTRES", "MAL_CONDICIONADO"}

        for nombre_mod, d in modulos:
            self.assertEqual(
                set(d.keys()),
                tipos_esperados,
                f"{nombre_mod} no contiene exactamente los tres tipos de escenario",
            )
            for tipo, esc in d.items():
                self.assertIn("nombre", esc)
                self.assertIn("descripcion", esc)
                self.assertIn("parametros", esc)
                self.assertIn("supuestos", esc)
                # Serialización a JSON garantizada
                serialized = json.dumps(esc["parametros"])
                self.assertTrue(len(serialized) > 0)
                json_completo = json.dumps(esc)
                self.assertTrue(len(json_completo) > 0)

    def test_escenarios_modulo_2_estructura_homogenea(self):
        import json
        tipos_esperados = {"NORMAL", "ESTRES", "MAL_CONDICIONADO"}
        self.assertEqual(set(ESCENARIOS_MODULO_2.keys()), tipos_esperados)
        for tipo, esc in ESCENARIOS_MODULO_2.items():
            self.assertIn("nombre", esc)
            self.assertIn("descripcion", esc)
            self.assertIn("parametros", esc)
            self.assertIn("supuestos", esc)
            serialized = json.dumps(esc["parametros"])
            self.assertTrue(len(serialized) > 0)
            json_completo = json.dumps(esc)
            self.assertTrue(len(json_completo) > 0)
