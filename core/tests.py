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
