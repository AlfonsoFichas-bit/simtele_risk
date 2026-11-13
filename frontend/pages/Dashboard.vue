<script setup>
import { ref, computed } from 'vue'
import { router } from '@inertiajs/vue3'

const props = defineProps({
  titulo: { type: String, default: 'SIMTELE-RISK | Sistema de Simulación Numérica por Cable' },
  modulos: { type: Array, default: () => [] },
  escenarios_disponibles: { type: Array, default: () => [] },
  corrida: { type: Object, default: () => ({}) },
  ultimas_simulaciones: { type: Array, default: () => [] },
})

// Estado reactivo
const escenarioActual = ref(props.corrida?.tipo_escenario || 'NORMAL')
const tolerancia = ref(props.corrida?.tolerancia || 1e-6)
const maxIter = ref(props.corrida?.max_iter || 100)
const cargando = ref(false)
const pestanaIteraciones = ref('Jacobi')

// Métodos disponibles para las pestañas de iteración paso a paso
const metodosDisponibles = computed(() => {
  return props.corrida?.metodos || []
})

const metodoSeleccionadoData = computed(() => {
  return metodosDisponibles.value.find((m) => m.metodo === pestanaIteraciones.value) || metodosDisponibles.value[0] || null
})

// Ejecutar simulación con nuevo escenario o parámetros
function ejecutarSimulacion(tipo = null) {
  if (tipo) {
    escenarioActual.value = tipo
  }
  cargando.value = true
  router.post(
    '/modulo-2/ejecutar',
    {
      escenario: escenarioActual.value,
      tolerancia: Number(tolerancia.value),
      max_iter: Number(maxIter.value),
    },
    {
      preserveScroll: true,
      onFinish: () => {
        cargando.value = false
        // Si la pestaña actual no tiene iteraciones o cambió, sincronizar
        if (pestanaIteraciones.value === 'Factorización LU') {
          pestanaIteraciones.value = 'Jacobi'
        }
      },
    }
  )
}

// Recargar simulación desde la base de datos
function recargarSimulacion(id) {
  cargando.value = true
  router.get(
    `/modulo-2/recargar/${id}/`,
    {},
    {
      preserveScroll: true,
      onFinish: () => {
        cargando.value = false
        if (props.corrida?.tipo_escenario) {
          escenarioActual.value = props.corrida.tipo_escenario
          tolerancia.value = props.corrida.tolerancia
          maxIter.value = props.corrida.max_iter
        }
      },
    }
  )
}

// Funciones de formateo numérico
function formatNum(num, dec = 6) {
  if (num === null || num === undefined) return '—'
  const val = Number(num)
  if (isNaN(val)) return 'NaN'
  if (val !== 0 && (Math.abs(val) < 1e-4 || Math.abs(val) >= 1e6)) {
    return val.toExponential(4)
  }
  return val.toFixed(dec)
}

function formatVector(vec) {
  if (!Array.isArray(vec)) return '—'
  return '[' + vec.map((v) => formatNum(v, 4)).join(', ') + ']'
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
    <!-- BARRA SUPERIOR -->
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-30">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-900/30">
            SR
          </div>
          <div>
            <h1 class="text-base sm:text-lg font-bold tracking-tight text-white flex items-center gap-2">
              SIMTELE-RISK
              <span class="text-xs px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono">
                Semana 1
              </span>
            </h1>
            <p class="text-xs text-slate-400">Sistema de Simulación Numérica para Teleféricos Urbanos</p>
          </div>
        </div>

        <div class="flex items-center space-x-4 text-xs">
          <div class="hidden sm:flex items-center space-x-2 text-slate-400 bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-700/60 font-mono">
            <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Django 6 + Inertia + Vue 3</span>
          </div>
          <span class="text-xs px-2.5 py-1 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800 font-medium">
            Persistencia BD Activa
          </span>
        </div>
      </div>
    </header>

    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">

      <!-- SECCIÓN 1: LAS 4 TARJETAS OBLIGATORIAS -->
      <section>
        <div class="mb-4">
          <h2 class="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span class="text-cyan-400">1.</span> Arquitectura Matemática y Módulos del Sistema
          </h2>
          <p class="text-sm text-slate-400">
            Los 4 casos de estudio físicos obligatorios de SIMTELE-RISK con sus modelos gobernantes y cobertura transversal de métodos numéricos.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            v-for="mod in modulos"
            :key="mod.id"
            :class="[
              'rounded-xl p-5 border flex flex-col justify-between transition-all duration-200',
              mod.activo
                ? 'bg-slate-900/90 border-emerald-500/50 shadow-lg shadow-emerald-950/40 ring-1 ring-emerald-500/30'
                : 'bg-slate-900/40 border-slate-800 hover:border-slate-700'
            ]"
          >
            <div>
              <div class="flex items-center justify-between mb-3">
                <span class="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
                  {{ mod.numero }}
                </span>
                <span
                  :class="[
                    'text-[10px] font-medium px-2 py-0.5 rounded-full border',
                    mod.activo
                      ? 'bg-emerald-950 text-emerald-300 border-emerald-700/80'
                      : 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                  ]"
                >
                  {{ mod.activo ? 'Operativo S1' : 'Semana 2' }}
                </span>
              </div>

              <h3 class="text-sm font-semibold text-white mb-2 leading-snug">
                {{ mod.titulo }}
              </h3>

              <div class="bg-slate-950/80 rounded p-2.5 mb-3 border border-slate-800/80 font-mono text-xs text-cyan-300">
                <div class="text-[10px] uppercase text-slate-500 mb-0.5">Ecuación GobernTarget:</div>
                <div class="overflow-x-auto">{{ mod.ecuacion }}</div>
              </div>

              <p class="text-xs text-slate-400 mb-3 line-clamp-3">
                {{ mod.descripcion }}
              </p>
            </div>

            <div>
              <div class="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1.5">
                Métodos Asociados:
              </div>
              <ul class="text-[11px] text-slate-300 space-y-1 font-mono">
                <li v-for="(met, idx) in mod.metodos" :key="idx" class="flex items-center gap-1.5">
                  <span class="text-cyan-400">•</span>
                  <span>{{ met }}</span>
                </li>
              </ul>

              <div class="mt-4 pt-3 border-t border-slate-800/80">
                <span
                  :class="[
                    'block text-center text-xs py-1 px-2 rounded font-medium',
                    mod.activo
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-slate-800/50 text-slate-400'
                  ]"
                >
                  {{ mod.estado }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- SECCIÓN 2: PANEL INTERACTIVO MÓDULO 2 -->
      <section class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div class="flex flex-col lg:flex-row lg:items-center justify-between pb-6 border-b border-slate-800 gap-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="px-2 py-0.5 text-xs rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono font-semibold">
                MÓDULO 2 OPERATIVO
              </span>
              <span class="text-xs text-slate-400">Sistemas Lineales y Calibración de Desgaste</span>
            </div>
            <h2 class="text-2xl font-bold text-white tracking-tight">
              Calibración de Desgaste de Poleas en Teleférico
            </h2>
            <p class="text-sm text-slate-400 mt-1 max-w-3xl">
              Resolución del sistema acoplado <code class="text-cyan-300 font-mono">A·x = b</code> de dimensión 4×4 donde <code class="text-cyan-300 font-mono">x</code> representa la tasa calibrada de desgaste (mm/ciclo) en 4 poleas críticas.
            </p>
          </div>

          <!-- Controles de Simulación -->
          <div class="flex flex-wrap items-center gap-3">
            <div>
              <label class="block text-[11px] uppercase tracking-wider text-slate-400 mb-1 font-semibold">Tolerancia</label>
              <input
                v-model="tolerancia"
                type="number"
                step="1e-7"
                min="1e-12"
                max="1e-1"
                class="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white w-28 font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label class="block text-[11px] uppercase tracking-wider text-slate-400 mb-1 font-semibold">Max Iter</label>
              <input
                v-model="maxIter"
                type="number"
                min="10"
                max="1000"
                class="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white w-20 font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div class="pt-5">
              <button
                @click="ejecutarSimulacion()"
                :disabled="cargando"
                class="px-4 py-2 bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white font-medium text-xs rounded-lg shadow-md transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                <svg v-if="cargando" class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>{{ cargando ? 'Calculando...' : 'Ejecutar Simulación' }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- SELECTOR DE ESCENARIOS (3 ESCENARIOS OBLIGATORIOS) -->
        <div class="mt-6">
          <label class="block text-xs uppercase tracking-wider text-slate-400 mb-2 font-semibold">
            Seleccionar Escenario de Ensayo Numérico:
          </label>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            <button
              v-for="esc in escenarios_disponibles"
              :key="esc.clave"
              @click="ejecutarSimulacion(esc.clave)"
              :class="[
                'p-4 rounded-xl text-left border transition-all cursor-pointer',
                corrida.tipo_escenario === esc.clave
                  ? 'bg-slate-800/90 border-cyan-500 shadow-md ring-1 ring-cyan-500/50'
                  : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/50'
              ]"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="font-bold text-sm text-white font-mono">{{ esc.clave }}</span>
                <span
                  v-if="corrida.tipo_escenario === esc.clave"
                  class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"
                ></span>
              </div>
              <div class="text-xs font-medium text-cyan-300 mb-1">{{ esc.nombre }}</div>
              <div class="text-[11px] text-slate-400 leading-relaxed">{{ esc.descripcion }}</div>
            </button>
          </div>
        </div>

        <!-- DETALLE MATRICIAL Y CONDICIONAMIENTO -->
        <div class="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Matriz A -->
          <div class="bg-slate-950 rounded-xl p-4 border border-slate-800 font-mono">
            <div class="flex items-center justify-between text-xs text-slate-400 mb-3 border-b border-slate-800 pb-2">
              <span class="font-bold text-white">Matriz de Rigidez / Desgaste A (4×4)</span>
              <span class="text-slate-500">Coeficientes acoplados</span>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-center text-xs">
                <tbody>
                  <tr v-for="(fila, i) in corrida.datos_escenario?.A" :key="i" class="border-b border-slate-900 last:border-0">
                    <td v-for="(val, j) in fila" :key="j" class="py-1 px-2 text-cyan-200">
                      {{ formatNum(val, 2) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Vector b y Solución de Referencia -->
          <div class="bg-slate-950 rounded-xl p-4 border border-slate-800 font-mono text-xs">
            <div class="flex items-center justify-between text-slate-400 mb-3 border-b border-slate-800 pb-2">
              <span class="font-bold text-white">Vector b & Solución x* Exacta</span>
              <span class="text-slate-500">Lecturas de sensores</span>
            </div>
            <div class="space-y-3">
              <div>
                <span class="text-slate-500 text-[11px] block">Vector de Cargas / Lecturas b:</span>
                <div class="text-emerald-300 font-semibold bg-slate-900 p-2 rounded border border-slate-800 mt-1">
                  {{ formatVector(corrida.datos_escenario?.b) }}
                </div>
              </div>
              <div>
                <span class="text-slate-500 text-[11px] block">Solución Teórica Referencia x* (Exacta):</span>
                <div class="text-cyan-300 font-semibold bg-slate-900 p-2 rounded border border-slate-800 mt-1">
                  {{ formatVector(corrida.datos_escenario?.x_exacta) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Diagnóstico de Condicionamiento y Simetría -->
          <div class="bg-slate-950 rounded-xl p-4 border border-slate-800 text-xs flex flex-col justify-between">
            <div>
              <div class="flex items-center justify-between text-slate-400 mb-3 border-b border-slate-800 pb-2">
                <span class="font-bold text-white">Análisis de Sensibilidad Numérica</span>
                <span class="font-mono text-cyan-400">Teoría κ(A)</span>
              </div>

              <div class="space-y-2.5">
                <div class="flex items-center justify-between">
                  <span class="text-slate-400">Número de Condición κ_∞(A):</span>
                  <span
                    :class="[
                      'font-mono font-bold px-2 py-0.5 rounded',
                      corrida.datos_escenario?.condicion_inf > 100
                        ? 'bg-red-950 text-red-400 border border-red-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    ]"
                  >
                    {{ formatNum(corrida.datos_escenario?.condicion_inf, 2) }}
                  </span>
                </div>

                <div class="flex items-center justify-between">
                  <span class="text-slate-400">Matriz Simétrica:</span>
                  <span class="font-mono text-emerald-400 font-semibold">
                    {{ corrida.datos_escenario?.es_simetrica ? 'SÍ (A = Aᵀ)' : 'NO' }}
                  </span>
                </div>

                <div class="flex items-center justify-between">
                  <span class="text-slate-400">Definida Positiva (SPD):</span>
                  <span
                    :class="[
                      'font-mono font-semibold px-2 py-0.5 rounded',
                      corrida.datos_escenario?.es_spd
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : 'bg-amber-950 text-amber-400 border border-amber-800'
                    ]"
                  >
                    {{ corrida.datos_escenario?.es_spd ? 'SÍ (Autovalores > 0)' : 'NO' }}
                  </span>
                </div>
              </div>
            </div>

            <div class="mt-3 p-2 bg-slate-900/90 rounded border border-slate-800 text-[11px] text-slate-400">
              <span class="text-cyan-400 font-semibold">Nota Teórica:</span>
              <span v-if="corrida.datos_escenario?.condicion_inf > 100">
                Alto condicionamiento (<code class="text-red-300">κ > 1000</code>). Perturbaciones mínimas en datos provocan grandes variaciones en la solución.
              </span>
              <span v-else>
                Matriz bien condicionada y estrictamente diagonal dominante. Se garantiza convergencia monótona en métodos iterativos.
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- SECCIÓN 3: TABLAS DE RESULTADOS Y ERRORES -->
      <section class="space-y-6">
        <div>
          <h2 class="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span class="text-cyan-400">3.</span> Resultados Comparativos y Teoría de Errores Transversal
          </h2>
          <p class="text-sm text-slate-400">
            Comparativa global de los 4 métodos obligatorios con evaluación rigurosa de errores y desglose paso a paso de cada iteración.
          </p>
        </div>

        <!-- 3.A: TABLA COMPARATIVA RESUMEN (LOS 4 MÉTODOS) -->
        <div class="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div class="px-6 py-4 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
            <h3 class="text-sm font-bold text-white flex items-center gap-2 font-mono">
              <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
              Tabla Comparativa Global: LU vs Jacobi vs Gauss-Seidel vs Gradiente Conjugado
            </h3>
            <span class="text-xs text-slate-400 font-mono">Norma infinito ||·||_∞</span>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs font-mono">
              <thead class="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th class="py-3 px-4">Método</th>
                  <th class="py-3 px-3 text-center">Estado</th>
                  <th class="py-3 px-3 text-center">Iteraciones</th>
                  <th class="py-3 px-3 text-right">Tiempo (ms)</th>
                  <th class="py-3 px-4">Solución Obtenida x</th>
                  <th class="py-3 px-3 text-right text-emerald-400">Residuo ||Ax-b||</th>
                  <th class="py-3 px-3 text-right">Error Absoluto</th>
                  <th class="py-3 px-3 text-right">Error Relativo</th>
                  <th class="py-3 px-3 text-right text-cyan-400">Error Porcentual</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800/80">
                <tr
                  v-for="met in corrida.metodos"
                  :key="met.metodo"
                  class="hover:bg-slate-800/40 transition-colors"
                >
                  <td class="py-3.5 px-4 font-bold text-white flex items-center gap-2">
                    <span
                      class="w-2 h-2 rounded-full"
                      :class="{
                        'bg-purple-400': met.metodo.includes('LU'),
                        'bg-blue-400': met.metodo === 'Jacobi',
                        'bg-emerald-400': met.metodo === 'Gauss-Seidel',
                        'bg-amber-400': met.metodo === 'Gradiente Conjugado'
                      }"
                    ></span>
                    {{ met.metodo }}
                  </td>
                  <td class="py-3.5 px-3 text-center">
                    <span
                      :class="[
                        'px-2 py-0.5 rounded text-[10px] font-semibold',
                        met.convergio
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : 'bg-red-950 text-red-300 border border-red-800'
                      ]"
                    >
                      {{ met.convergio ? 'Convergió' : 'No conv.' }}
                    </span>
                  </td>
                  <td class="py-3.5 px-3 text-center font-bold text-slate-200">
                    {{ met.iteraciones?.length || 1 }}
                  </td>
                  <td class="py-3.5 px-3 text-right text-slate-300">
                    {{ formatNum(met.tiempo_ms, 3) }}
                  </td>
                  <td class="py-3.5 px-4 text-cyan-200">
                    {{ formatVector(met.solucion) }}
                  </td>
                  <td class="py-3.5 px-3 text-right text-emerald-300 font-semibold">
                    {{ formatNum(met.resumen_error?.residual) }}
                  </td>
                  <td class="py-3.5 px-3 text-right text-slate-300">
                    {{ formatNum(met.resumen_error?.error_abs) }}
                  </td>
                  <td class="py-3.5 px-3 text-right text-slate-300">
                    {{ formatNum(met.resumen_error?.error_rel) }}
                  </td>
                  <td class="py-3.5 px-3 text-right text-cyan-400 font-semibold">
                    {{ formatNum(met.resumen_error?.error_porc, 4) }}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 3.B: SELECTOR DE PESTAÑAS Y TABLA DE ITERACIONES PASO A PASO -->
        <div class="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div class="px-6 py-4 bg-slate-900/90 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 class="text-sm font-bold text-white flex items-center gap-2">
                <span class="text-cyan-400 font-mono">Paso a Paso:</span>
                Tabla de Convergencia Iterativa Detallada
              </h3>
              <p class="text-xs text-slate-400 mt-0.5">
                Seguimiento de aproximación, residual y decrecimiento del error en cada ciclo k.
              </p>
            </div>

            <!-- Selector de Pestañas -->
            <div class="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
              <button
                v-for="met in corrida.metodos"
                :key="met.metodo"
                @click="pestanaIteraciones = met.metodo"
                :class="[
                  'px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer',
                  pestanaIteraciones === met.metodo
                    ? 'bg-cyan-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900'
                ]"
              >
                {{ met.metodo }}
              </button>
            </div>
          </div>

          <!-- Si el método es Factorización LU, mostramos L y U -->
          <div v-if="metodoSeleccionadoData?.metodo === 'Factorización LU'" class="p-6 space-y-4">
            <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs">
              <p class="text-slate-300 mb-2">
                <span class="text-cyan-400 font-semibold">Método Directo Exacto:</span>
                La Factorización LU descompone la matriz original en <code class="text-cyan-300">A = L · U</code> (Doolittle con diagonal unitaria en L) resolviendo en dos pasos de sustitución sin proceso iterativo:
                <code class="text-emerald-300">L · y = b</code> seguido de <code class="text-emerald-300">U · x = y</code>.
              </p>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 font-mono">
                <div class="bg-slate-900 p-3 rounded border border-slate-800">
                  <span class="text-slate-400 block mb-1 font-semibold">Matriz L (Triangular Inferior Unitaria):</span>
                  <div v-for="(f, idx) in metodoSeleccionadoData.L" :key="idx" class="text-cyan-300">
                    {{ formatVector(f) }}
                  </div>
                </div>
                <div class="bg-slate-900 p-3 rounded border border-slate-800">
                  <span class="text-slate-400 block mb-1 font-semibold">Matriz U (Triangular Superior):</span>
                  <div v-for="(f, idx) in metodoSeleccionadoData.U" :key="idx" class="text-emerald-300">
                    {{ formatVector(f) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tabla de iteraciones para Jacobi, GS y Gradiente Conjugado -->
          <div v-else class="overflow-x-auto max-h-96">
            <table class="w-full text-left text-xs font-mono">
              <thead class="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800 sticky top-0 backdrop-blur z-10">
                <tr>
                  <th class="py-2.5 px-4 text-center">k</th>
                  <th class="py-2.5 px-4">Vector Aproximado x^(k)</th>
                  <th class="py-2.5 px-3 text-right text-emerald-400">Residuo ||Ax-b||</th>
                  <th class="py-2.5 px-3 text-right">Error Absoluto</th>
                  <th class="py-2.5 px-3 text-right">Error Relativo</th>
                  <th class="py-2.5 px-3 text-right text-cyan-400">Error %</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800/80">
                <tr
                  v-for="it in metodoSeleccionadoData?.iteraciones"
                  :key="it.numero"
                  :class="[
                    'hover:bg-slate-800/30 transition-colors',
                    it.numero === metodoSeleccionadoData?.iteraciones.length ? 'bg-cyan-950/20 font-semibold' : ''
                  ]"
                >
                  <td class="py-2 px-4 text-center text-slate-400">
                    {{ it.numero }}
                  </td>
                  <td class="py-2 px-4 text-cyan-200">
                    {{ formatVector(it.aproximacion) }}
                  </td>
                  <td class="py-2 px-3 text-right text-emerald-300">
                    {{ formatNum(it.residual) }}
                  </td>
                  <td class="py-2 px-3 text-right text-slate-300">
                    {{ formatNum(it.error_abs) }}
                  </td>
                  <td class="py-2 px-3 text-right text-slate-300">
                    {{ formatNum(it.error_rel) }}
                  </td>
                  <td class="py-2 px-3 text-right text-cyan-400">
                    {{ formatNum(it.error_porc, 4) }}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- SECCIÓN 4: HISTORIAL DE SIMULACIONES EN BD (PERSISTENCIA COMPROBADA) -->
      <section class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
          <div>
            <h2 class="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <span class="text-cyan-400">4.</span> Registro Histórico y Persistencia en Base de Datos
            </h2>
            <p class="text-xs text-slate-400">
              Simulaciones almacenadas en SQLite local / PostgreSQL Neon Tech con modelos relacionales normalizados.
            </p>
          </div>

          <div class="flex items-center gap-2">
            <span class="text-xs text-slate-400">Simulación Activa:</span>
            <span class="font-mono text-xs px-2.5 py-1 rounded bg-slate-800 text-cyan-400 font-bold border border-slate-700">
              #{{ corrida.simulacion_id }}
            </span>
          </div>
        </div>

        <div class="mt-4 overflow-x-auto">
          <table class="w-full text-left text-xs font-mono">
            <thead class="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th class="py-2.5 px-4">ID</th>
                <th class="py-2.5 px-4">Fecha y Hora</th>
                <th class="py-2.5 px-4">Escenario</th>
                <th class="py-2.5 px-4">Usuario</th>
                <th class="py-2.5 px-3 text-center">Estado</th>
                <th class="py-2.5 px-3 text-center">Métodos</th>
                <th class="py-2.5 px-4 text-center">Acción</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/80">
              <tr
                v-for="sim in ultimas_simulaciones"
                :key="sim.id"
                :class="[
                  'hover:bg-slate-800/30 transition-colors',
                  sim.id === corrida.simulacion_id ? 'bg-cyan-950/30 font-semibold' : ''
                ]"
              >
                <td class="py-2.5 px-4 text-cyan-400 font-bold">
                  #{{ sim.id }}
                </td>
                <td class="py-2.5 px-4 text-slate-300">
                  {{ sim.fecha }}
                </td>
                <td class="py-2.5 px-4">
                  <span
                    :class="[
                      'px-2 py-0.5 rounded text-[10px] font-semibold font-mono',
                      sim.escenario_tipo === 'NORMAL' ? 'bg-blue-950 text-blue-300 border border-blue-800' :
                      sim.escenario_tipo === 'ESTRES' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                      'bg-red-950 text-red-300 border border-red-800'
                    ]"
                  >
                    {{ sim.escenario_tipo }}
                  </span>
                </td>
                <td class="py-2.5 px-4 text-slate-400">
                  {{ sim.usuario }}
                </td>
                <td class="py-2.5 px-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 font-medium">
                    {{ sim.estado }}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-center text-slate-300">
                  {{ sim.metodos_count }} algoritmos
                </td>
                <td class="py-2.5 px-4 text-center">
                  <button
                    @click="recargarSimulacion(sim.id)"
                    class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 hover:text-cyan-200 rounded border border-slate-700 text-[11px] font-medium transition cursor-pointer"
                  >
                    Recargar Datos
                  </button>
                </td>
              </tr>
              <tr v-if="!ultimas_simulaciones || ultimas_simulaciones.length === 0">
                <td colspan="7" class="py-6 text-center text-slate-500">
                  No hay simulaciones registradas aún en la base de datos.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <!-- FOOTER -->
    <footer class="border-t border-slate-800 bg-slate-900/60 py-6 mt-12 text-center text-xs text-slate-500 font-mono">
      <div class="max-w-7xl mx-auto px-4">
        SIMTELE-RISK · Asignatura Métodos Numéricos · Carrera de Informática · Entrega Semana 1
      </div>
    </footer>
  </div>
</template>
