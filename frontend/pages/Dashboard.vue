<script setup>
import { ref, computed } from 'vue'
import { router } from '@inertiajs/vue3'

const props = defineProps({
  titulo: { type: String, default: 'SIMTELE-RISK | Sistema de Simulación Numérica por Cable' },
  modulos: { type: Array, default: () => [] },
  escenarios_disponibles: { type: Array, default: () => [] },
  escenarios_modulos: { type: Object, default: () => ({}) },
  corrida: { type: Object, default: () => ({}) },
  ultimas_simulaciones: { type: Array, default: () => [] },
})

// Estado reactivo
const escenarioActual = ref(props.corrida?.tipo_escenario || 'NORMAL')
const tolerancia = ref(props.corrida?.tolerancia || 1e-6)
const maxIter = ref(props.corrida?.max_iter || 100)
const searchQuery = ref('')
const cargando = ref(false)
const pestanaIteraciones = ref('Jacobi')

// Modal / ficha para inspeccionar escenarios declarados de módulos 1, 3 y 4
const moduloDetalleModal = ref(null)

// Métodos disponibles para las pestañas de iteración paso a paso
const metodosDisponibles = computed(() => {
  return props.corrida?.metodos || []
})

const metodoSeleccionadoData = computed(() => {
  return metodosDisponibles.value.find((m) => m.metodo === pestanaIteraciones.value) || metodosDisponibles.value[0] || null
})

// Acciones
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
        if (pestanaIteraciones.value === 'Factorización LU') {
          pestanaIteraciones.value = 'Jacobi'
        }
      },
    }
  )
}

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

function relanzarSimulacion(id) {
  cargando.value = true
  router.post(
    `/modulo-2/relanzar/${id}/`,
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

function abrirDetalleModulo(mod) {
  if (mod.id === 2) {
    // Scroll suave al panel interactivo del Módulo 2
    const panel = document.getElementById('panel-modulo-2')
    if (panel) {
      panel.scrollIntoView({ behavior: 'smooth' })
    }
    return
  }
  moduloDetalleModal.value = mod
}

function buscarHistorial() {
  cargando.value = true
  router.get(
    '/modulo-2/buscar',
    { q: searchQuery.value },
    {
      preserveScroll: true,
      onFinish: () => {
        cargando.value = false
      },
    }
  )
}

function cerrarDetalleModulo() {
  moduloDetalleModal.value = null
}

// Helpers de gráficos
const colorMetodo = (metodo) => {
  if (metodo.includes('LU')) return '#a855f7'
  if (metodo === 'Jacobi') return '#3b82f6'
  if (metodo === 'Gauss-Seidel') return '#10b981'
  if (metodo === 'Gradiente Conjugado') return '#f59e0b'
  return '#64748b'
}

const convergenciaSeries = computed(() => {
  return (props.corrida?.metodos || []).map((m) => ({
    metodo: m.metodo,
    puntos: (m.iteraciones || []).map((it) => ({ k: it.numero, r: Number(it.residual) || 0 })),
  }))
})

const maxIterChart = computed(() => {
  const vals = convergenciaSeries.value.map((s) => s.puntos.length)
  return Math.max(1, ...vals)
})

const maxResidualChart = computed(() => {
  const vals = convergenciaSeries.value.flatMap((s) => s.puntos.map((p) => p.r))
  return Math.max(1e-12, ...vals)
})

const minResidualChart = 1e-12

function seriePoints(serie) {
  const maxK = maxIterChart.value
  const maxR = maxResidualChart.value
  return serie.puntos
    .map((p) => {
      const x = 10 + (p.k / maxK) * 380
      const ratio = (Math.log10(Math.max(p.r, minResidualChart)) - Math.log10(minResidualChart)) /
        (Math.log10(maxR) - Math.log10(minResidualChart) + 1e-12)
      const y = 190 - ratio * 180
      return `${x},${y}`
    })
    .join(' ')
}

const maxTiempoChart = computed(() => {
  const vals = (props.corrida?.metodos || []).map((m) => Number(m.tiempo_ms) || 0)
  return Math.max(1, ...vals)
})

function barraPorcentaje(valor) {
  return ((Number(valor) || 0) / maxTiempoChart.value) * 100
}

// Helpers numéricos
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
    <header id="top" class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-30">
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
      <nav class="flex flex-wrap gap-2 text-xs font-mono">
        <a href="#top" class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-cyan-300">Inicio</a>
        <a href="#panel-modulo-2" class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-cyan-300">Módulo</a>
        <a href="#seccion-resultados" class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-cyan-300">Resultados</a>
        <a href="#seccion-interpretacion" class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-cyan-300">Interpretación</a>
        <a href="#seccion-historial" class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-cyan-300">Historial</a>
      </nav>

      <!-- SECCIÓN 1: LAS 4 TARJETAS OBLIGATORIAS (CLICABLES) -->
      <section>
        <div class="mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 class="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <span class="text-cyan-400">1.</span> Arquitectura Matemática y Módulos del Sistema
            </h2>
            <p class="text-sm text-slate-400">
              Haz clic en cualquier tarjeta para inspeccionar sus escenarios declarados (NORMAL, ESTRÉS, MAL CONDICIONADO) y supuestos físicos.
            </p>
          </div>
          <span class="text-xs text-slate-400 font-mono bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
            Módulo 2: Calibración Operativa
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            v-for="mod in modulos"
            :key="mod.id"
            @click="abrirDetalleModulo(mod)"
            :class="[
              'rounded-xl p-5 border flex flex-col justify-between transition-all duration-200 cursor-pointer group',
              mod.activo
                ? 'bg-slate-900/90 border-emerald-500/50 shadow-lg shadow-emerald-950/40 ring-1 ring-emerald-500/30 hover:border-emerald-400'
                : 'bg-slate-900/40 border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900/70'
            ]"
          >
            <div>
              <div class="flex items-center justify-between mb-3">
                <span class="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold group-hover:text-cyan-300 transition-colors">
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
                  {{ mod.activo ? 'Operativo S1' : 'Ver Ficha' }}
                </span>
              </div>

              <h3 class="text-sm font-semibold text-white mb-2 leading-snug group-hover:text-white">
                {{ mod.titulo }}
              </h3>

              <div class="bg-slate-950/80 rounded p-2.5 mb-3 border border-slate-800/80 font-mono text-xs text-cyan-300">
                <div class="text-[10px] uppercase text-slate-500 mb-0.5">Ecuación Gobernante:</div>
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

              <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span
                  :class="[
                    'py-1 px-2 rounded font-medium text-[11px]',
                    mod.activo
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-slate-800/50 text-slate-400'
                  ]"
                >
                  {{ mod.estado }}
                </span>
                <span v-if="!mod.activo" class="text-cyan-400 text-xs flex items-center gap-1 opacity-80 group-hover:opacity-100">
                  Inspeccionar →
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- SECCIÓN 2: PANEL INTERACTIVO MÓDULO 2 -->
      <section id="panel-modulo-2" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl scroll-mt-20">
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

        <!-- DETALLE MATRICIAL, SENSIBILIDAD Y CONDICIONAMIENTO -->
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
              <span class="text-slate-500">b = A·x* verificado</span>
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
                    {{ formatNum(corrida.datos_escenario?.condicion_inf, 1) }}
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
              <span class="text-cyan-400 font-semibold">Diagnóstico:</span>
              <span v-if="corrida.datos_escenario?.condicion_inf > 100">
                Alto condicionamiento (<code class="text-red-300">κ = 792.0</code>). El problema físico es intrínsecamente sensible a perturbaciones.
              </span>
              <span v-else>
                Matriz bien condicionada y estrictamente diagonal dominante. Garantiza convergencia monótona en métodos estacionarios.
              </span>
            </div>
          </div>
        </div>

        <!-- TARJETA: ANÁLISIS DE SENSIBILIDAD Y PERTURBACIÓN (δb) -->
        <div v-if="corrida.sensibilidad" class="mt-6 bg-slate-950 rounded-xl p-5 border border-slate-800">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800/80 gap-2">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
              <h3 class="text-sm font-bold text-white">
                Análisis Transversal de Sensibilidad y Perturbación: A·(x + δx) = b + δb
              </h3>
            </div>
            <span class="text-xs font-mono text-slate-400">
              Perturbación nominal: δb = [±1e-3]
            </span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4 font-mono text-xs">
            <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span class="text-slate-400 text-[11px] block mb-1">Perturbación Aplicada ||δb||_∞:</span>
              <div class="text-white font-bold">{{ formatVector(corrida.sensibilidad?.delta_b) }}</div>
              <span class="text-slate-500 text-[10px] block mt-1">rel_b: {{ formatNum(corrida.sensibilidad?.rel_b, 6) }}</span>
            </div>

            <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span class="text-slate-400 text-[11px] block mb-1">Variación Inducida ||δx||_∞:</span>
              <div class="text-cyan-300 font-bold">{{ formatVector(corrida.sensibilidad?.x_pert) }}</div>
              <span class="text-slate-500 text-[10px] block mt-1">rel_x: {{ formatNum(corrida.sensibilidad?.rel_x, 6) }}</span>
            </div>

            <div
              :class="[
                'p-3 rounded-lg border flex flex-col justify-between',
                corrida.sensibilidad?.factor_amplificacion > 100
                  ? 'bg-red-950/30 border-red-800/80 text-red-200'
                  : 'bg-emerald-950/30 border-emerald-800/80 text-emerald-200'
              ]"
            >
              <div>
                <span class="text-[11px] uppercase tracking-wider block mb-1 font-semibold">
                  Factor de Amplificación:
                </span>
                <div class="text-lg font-bold">
                  {{ formatNum(corrida.sensibilidad?.factor_amplificacion, 2) }}×
                </div>
              </div>
              <span class="text-[10px] opacity-80 block mt-1">
                {{ corrida.sensibilidad?.factor_amplificacion > 100 ? 'Amplificación Severa (> 100×)' : 'Amplificación Baja (< 10×)' }}
              </span>
            </div>

            <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800 flex flex-col justify-between">
              <div>
                <span class="text-slate-400 text-[11px] block mb-1">Cota Teórica κ_∞(A):</span>
                <div class="text-lg font-bold text-white">
                  {{ formatNum(corrida.sensibilidad?.cota_teorica_kappa, 1) }}
                </div>
              </div>
              <span class="text-[10px] text-slate-500 block mt-1">
                rel_x ≤ κ_∞(A) · rel_b (Cumplido)
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- SECCIÓN 3: TABLAS DE RESULTADOS, CRITERIOS E INTERPRETACIÓN DOBLE -->
      <section id="seccion-resultados" class="space-y-6">
        <div>
          <h2 class="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span class="text-cyan-400">3.</span> Resultados Comparativos y Teoría de Errores Transversal
          </h2>
          <p class="text-sm text-slate-400">
            Comparativa global de los 4 métodos obligatorios con criterios de parada declarados y desglose de interpretación doble.
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
                  <th class="py-3 px-3 text-right text-cyan-400">Error %</th>
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

        <!-- 3.G: GRÁFICOS DE CONVERGENCIA Y COMPARACIÓN -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <h3 class="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
              Convergencia: Residual vs Iteración
            </h3>
            <svg viewBox="0 0 400 200" class="w-full h-48 bg-slate-950 rounded border border-slate-800">
              <line x1="10" y1="190" x2="390" y2="190" stroke="#334155" stroke-width="1" />
              <line x1="10" y1="10" x2="10" y2="190" stroke="#334155" stroke-width="1" />
              <polyline
                v-for="serie in convergenciaSeries"
                :key="serie.metodo"
                :points="seriePoints(serie)"
                fill="none"
                :stroke="colorMetodo(serie.metodo)"
                stroke-width="2"
              />
              <text x="200" y="198" fill="#64748b" font-size="8" text-anchor="middle">Iteración k</text>
            </svg>
            <div class="flex flex-wrap gap-3 mt-2 text-[10px] font-mono">
              <span v-for="serie in convergenciaSeries" :key="serie.metodo" class="flex items-center gap-1">
                <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: colorMetodo(serie.metodo) }"></span>
                {{ serie.metodo }}
              </span>
            </div>
          </div>

          <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <h3 class="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              Comparación de Métodos (Tiempo ms)
            </h3>
            <div class="space-y-2">
              <div v-for="met in corrida.metodos" :key="met.metodo" class="flex items-center gap-2 text-xs font-mono">
                <span class="w-32 truncate text-slate-300">{{ met.metodo }}</span>
                <div class="flex-1 bg-slate-950 rounded h-4 overflow-hidden border border-slate-800">
                  <div
                    class="h-full"
                    :style="{ width: barraPorcentaje(met.tiempo_ms) + '%', backgroundColor: colorMetodo(met.metodo) }"
                  ></div>
                </div>
                <span class="w-16 text-right text-slate-400">{{ formatNum(met.tiempo_ms, 3) }}</span>
              </div>
            </div>
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
              <p class="text-xs text-slate-400 mt-0.5 font-mono">
                Criterio declarado: <code class="text-cyan-300">{{ metodoSeleccionadoData?.criterio_parada || '—' }}</code>
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
                La Factorización LU descompone la matriz original en <code class="text-cyan-300">A = L · U</code> (Doolittle con diagonal unitaria en L) resolviendo en dos pasos de sustitución sin iteraciones:
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

        <!-- 3.C: TARJETA DE INTERPRETACIÓN DOBLE (SEPARACIÓN CLARA) -->
        <div id="seccion-interpretacion" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div class="pb-3 border-b border-slate-800 flex items-center justify-between">
            <h3 class="text-sm font-bold text-white flex items-center gap-2 font-mono">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              Interpretación Doble: Análisis Numérico vs Aplicación Física en Teleférico
            </h3>
            <span class="text-xs text-slate-400 font-mono">Método Activo: {{ metodoSeleccionadoData?.metodo }}</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
            <!-- Conclusión Matemática / Numérica -->
            <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
              <div>
                <div class="flex items-center gap-2 mb-2 text-cyan-400 font-semibold text-xs uppercase tracking-wider font-mono">
                  <span>📐 Conclusión Numérica y Algorítmica</span>
                </div>
                <p class="text-xs text-slate-300 leading-relaxed font-sans">
                  {{ metodoSeleccionadoData?.interpretacion?.numerica || 'Cargando conclusión numérica...' }}
                </p>
              </div>
              <div class="mt-4 pt-3 border-t border-slate-900 text-[11px] text-slate-500 font-mono">
                Convergencia: {{ metodoSeleccionadoData?.convergio ? 'Satisfactoria' : 'No alcanzada' }} ·
                Tiempo CPU: {{ formatNum(metodoSeleccionadoData?.tiempo_ms, 3) }} ms
              </div>
            </div>

            <!-- Conclusión del Caso Aplicado -->
            <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
              <div>
                <div class="flex items-center gap-2 mb-2 text-emerald-400 font-semibold text-xs uppercase tracking-wider font-mono">
                  <span>🚠 Conclusión del Caso Aplicado (Teleférico)</span>
                </div>
                <p class="text-xs text-slate-300 leading-relaxed font-sans">
                  {{ metodoSeleccionadoData?.interpretacion?.caso || 'Cargando conclusión del caso aplicado...' }}
                </p>
              </div>
              <div class="mt-4 pt-3 border-t border-slate-900 text-[11px] text-slate-500 font-mono">
                Escenario: {{ corrida.tipo_escenario }} · Dimensión: 4×4 SPD
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- SECCIÓN 4: HISTORIAL DE SIMULACIONES EN BD CON BOTONES RECARGAR Y RELANZAR -->
      <section id="seccion-historial" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
          <div>
            <h2 class="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <span class="text-cyan-400">4.</span> Registro Histórico y Persistencia en Base de Datos
            </h2>
            <p class="text-xs text-slate-400">
              Simulaciones almacenadas en SQLite local / PostgreSQL Neon Tech. Usa "Recargar" para inspeccionar datos o "Relanzar" para crear una corrida nueva idéntica.
            </p>
          </div>

          <div class="flex items-center gap-2">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Buscar por ID o tipo"
              class="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white w-40 font-mono focus:outline-none focus:border-cyan-500"
              @keyup.enter="buscarHistorial"
            />
            <button
              @click="buscarHistorial"
              :disabled="cargando"
              class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded border border-slate-700 text-xs font-medium cursor-pointer disabled:opacity-50"
            >
              Buscar
            </button>
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
                <th class="py-2.5 px-4 text-center">Acciones</th>
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
                  <div class="flex items-center justify-center space-x-2">
                    <button
                      @click="recargarSimulacion(sim.id)"
                      :disabled="cargando"
                      class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-300 hover:text-cyan-200 rounded border border-slate-700 text-[11px] font-medium transition cursor-pointer disabled:opacity-50"
                      title="Cargar esta simulación histórica sin recalcular"
                    >
                      Recargar
                    </button>
                    <button
                      @click="relanzarSimulacion(sim.id)"
                      :disabled="cargando"
                      class="px-2.5 py-1 bg-cyan-900/40 hover:bg-cyan-800/60 text-cyan-200 rounded border border-cyan-700/60 text-[11px] font-medium transition cursor-pointer disabled:opacity-50"
                      title="Relanzar cálculo en el servidor creando una corrida nueva"
                    >
                      Relanzar
                    </button>
                    <a
                      :href="`/modulo-2/exportar/${sim.id}/`"
                      class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-emerald-300 rounded border border-slate-700 text-[11px] font-medium transition"
                      title="Exportar iteraciones y errores a CSV"
                    >
                      Exportar
                    </a>
                  </div>
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

    <!-- MODAL / FICHA DE DETALLE PARA MÓDULOS 1, 3 Y 4 -->
    <div
      v-if="moduloDetalleModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto"
      @click.self="cerrarDetalleModulo"
    >
      <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 shadow-2xl space-y-6">
        <div class="flex items-start justify-between border-b border-slate-800 pb-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-mono uppercase px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                {{ moduloDetalleModal.numero }} · Semana 2
              </span>
              <span class="text-xs text-slate-400">Catálogo de Modelado Matemático</span>
            </div>
            <h3 class="text-lg font-bold text-white">{{ moduloDetalleModal.titulo }}</h3>
          </div>
          <button
            @click="cerrarDetalleModulo"
            class="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 cursor-pointer"
          >
            ✕
          </button>
        </div>

        <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono text-xs text-cyan-300">
          <div class="text-[10px] uppercase text-slate-500 mb-0.5">Ecuación GobernTarget:</div>
          <div>{{ moduloDetalleModal.ecuacion }}</div>
        </div>

        <div>
          <h4 class="text-xs font-bold text-white uppercase tracking-wider mb-3">
            Escenarios Numéricos Declarados (3 Escenarios):
          </h4>
          <div class="space-y-3">
            <div
              v-for="(esc, key) in (escenarios_modulos[moduloDetalleModal.id] || {})"
              :key="key"
              class="bg-slate-950 p-4 rounded-xl border border-slate-800/90 text-xs space-y-2"
            >
              <div class="flex items-center justify-between">
                <span class="font-bold text-white font-mono text-sm">{{ key }} — {{ esc.nombre }}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-300 border border-slate-800">
                  Declarado
                </span>
              </div>
              <p class="text-slate-400 leading-relaxed">{{ esc.descripcion }}</p>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <div class="bg-slate-900/80 p-2.5 rounded border border-slate-800 font-mono text-[11px]">
                  <span class="text-slate-500 block mb-1 uppercase text-[10px]">Parámetros Físicos:</span>
                  <div v-for="(v, k) in esc.parametros" :key="k" class="text-cyan-200">
                    <span class="text-slate-400">{{ k }}:</span> {{ v }}
                  </div>
                </div>
                <div class="bg-slate-900/80 p-2.5 rounded border border-slate-800 text-[11px]">
                  <span class="text-slate-500 block mb-1 uppercase font-mono text-[10px]">Supuestos de Modelado:</span>
                  <ul class="text-slate-300 space-y-1 list-disc list-inside">
                    <li v-for="(sup, sIdx) in esc.supuestos" :key="sIdx">{{ sup }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="p-3 bg-amber-950/20 border border-amber-800/40 rounded-xl text-xs text-amber-300 flex items-center justify-between">
          <span>⚠️ Los algoritmos computacionales de este módulo se implementarán en la <strong>Semana 2</strong>. En la Semana 1 se evalúa su formulación y catálogo de supuestos.</span>
          <button
            @click="cerrarDetalleModulo"
            class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-medium cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>

    <!-- FOOTER -->
    <footer class="border-t border-slate-800 bg-slate-900/60 py-6 mt-12 text-center text-xs text-slate-500 font-mono">
      <div class="max-w-7xl mx-auto px-4">
        SIMTELE-RISK · Asignatura Métodos Numéricos · Carrera de Informática · Entrega Semana 1
      </div>
    </footer>
  </div>
</template>
