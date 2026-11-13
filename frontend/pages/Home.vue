<script setup>
import { computed, ref } from 'vue'
import { router, usePage } from '@inertiajs/vue3'

const props = defineProps({
  appName: { type: String, default: 'SIMTELE Risk' },
  serverTime: { type: String, default: '' },
  serverInfo: { type: Object, default: () => ({}) },
  stats: { type: Object, default: () => ({}) },
  slowFact: { type: Object, default: null },
})

const page = usePage()
const count = ref(0)
const name = ref('')
const busy = ref('')

const flashMessages = computed(() => page.flash?.messages ?? [])

const statCards = computed(() => [
  { label: 'Módulos', value: props.stats.modules ?? '—' },
  { label: 'Escenarios', value: props.stats.scenarios ?? '—' },
  { label: 'Métodos', value: props.stats.methods ?? '—' },
])

const stack = [
  { name: 'Django', version: '6.1.3', tone: 'bg-emerald-400' },
  { name: 'inertia-django', version: '2.0.0', tone: 'bg-emerald-400' },
  { name: 'Inertia client', version: 'v3.11', tone: 'bg-cyan-400' },
  { name: 'Vue', version: '3.5', tone: 'bg-emerald-400' },
  { name: 'Tailwind CSS', version: '4.3', tone: 'bg-cyan-400' },
  { name: 'Vite', version: '7.3', tone: 'bg-emerald-400' },
]

function reloadProps(only, key) {
  busy.value = key
  router.reload({
    only,
    preserveScroll: true,
    onFinish: () => {
      busy.value = ''
    },
  })
}

function submitGreeting() {
  const value = name.value.trim()
  if (!value) return
  router.post(
    '/greet/',
    { name: value },
    {
      preserveScroll: true,
      // Inertia sends visit data as JSON by default. Django's `request.POST`
      // only parses form-encoded/multipart bodies, so force FormData here.
      forceFormData: true,
      onSuccess: () => {
        name.value = ''
      },
    },
  )
}

function flashTone(level) {
  return level === 'error' || level === 'warning'
    ? 'border-amber-300/20 bg-amber-400/10 text-amber-100'
    : 'border-emerald-300/20 bg-emerald-400/10 text-emerald-100'
}
</script>

<template>
  <div class="relative min-h-screen overflow-hidden">
    <!-- Ambient background: gradient blobs + a faded grid, all Tailwind. -->
    <div class="pointer-events-none absolute inset-0 -z-10">
      <div class="absolute -top-48 left-1/2 h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-cyan-500/10 blur-3xl"></div>
      <div class="absolute -bottom-24 -right-24 h-96 w-96 rounded-full bg-emerald-500/10 blur-3xl"></div>
      <div class="absolute inset-0 bg-[linear-gradient(to_right,rgba(148,163,184,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.06)_1px,transparent_1px)] bg-[size:56px_56px] [mask-image:radial-gradient(ellipse_at_center,black,transparent_78%)]"></div>
    </div>

    <div class="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-8 sm:px-8 lg:py-10">
      <header class="flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="grid size-10 place-items-center rounded-xl bg-cyan-400/10 ring-1 ring-cyan-300/30">
            <span class="font-mono text-sm font-bold tracking-tight text-cyan-300">SR</span>
          </div>
          <div>
            <p class="text-sm font-semibold tracking-wide text-white">
              SIMTELE <span class="text-cyan-300">RISK</span>
            </p>
            <p class="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">starter kit</p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <span class="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.16em] text-slate-400">
            Django 6.1
          </span>
          <span class="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.16em] text-cyan-200">
            Inertia v3
          </span>
          <span class="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.16em] text-slate-400">
            Tailwind 4
          </span>
        </div>
      </header>

      <main class="mt-12 flex-1">
        <section class="max-w-3xl">
          <p class="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-400/5 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-200">
            <span class="size-1.5 rounded-full bg-emerald-400"></span>
            entorno listo
          </p>

          <h1 class="mt-5 text-4xl font-semibold tracking-tight text-white sm:text-5xl">
            Django + Inertia + Vue,
            <span class="block text-cyan-300 sm:inline">sin construir una API.</span>
          </h1>

          <p class="mt-4 max-w-2xl text-base leading-7 text-slate-400">
            Base mínima para SIMTELE Risk: rutas, sesiones y CSRF siguen en Django;
            la interfaz vive en componentes Vue y se estiliza al 100% con Tailwind.
            El formulario, la recarga parcial y el contador ya están conectados.
          </p>
        </section>

        <section class="mt-10 grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
          <!-- Interactive demo -->
          <article class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 shadow-2xl shadow-black/30 backdrop-blur sm:p-6">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 class="text-sm font-semibold text-white">Panel de pruebas</h2>
                <p class="mt-1 text-xs text-slate-500">Todo lo que ves aquí viene de props de Django.</p>
              </div>
              <span class="rounded-full border border-white/10 bg-slate-950/60 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.16em] text-slate-500">
                Home.vue
              </span>
            </div>

            <!-- Server time + partial reload -->
            <div class="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/5 bg-slate-950/50 px-4 py-3">
              <div>
                <p class="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">serverTime</p>
                <p class="mt-1 font-mono text-sm text-slate-200">{{ serverTime }}</p>
              </div>
              <button
                type="button"
                :disabled="busy === 'stats'"
                class="inline-flex items-center justify-center rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-cyan-300/30 hover:bg-cyan-400/10 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60 disabled:cursor-not-allowed disabled:opacity-50"
                @click="reloadProps(['stats'], 'stats')"
              >
                {{ busy === 'stats' ? 'Recargando…' : 'Recargar stats' }}
              </button>
            </div>

            <!-- Stats -->
            <div class="mt-3 grid grid-cols-3 gap-3">
              <div
                v-for="stat in statCards"
                :key="stat.label"
                class="rounded-xl border border-white/5 bg-white/[0.02] p-4"
              >
                <p class="font-mono text-2xl font-semibold text-white">{{ stat.value }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ stat.label }}</p>
              </div>
            </div>

            <!-- v3 once prop -->
            <div class="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3">
              <div>
                <p class="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">once · serverInfo</p>
                <p class="mt-1 font-mono text-[11px] text-slate-400">
                  Python {{ serverInfo.python }} · Django {{ serverInfo.django }}
                </p>
              </div>
              <span class="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-2 py-1 font-mono text-[9px] uppercase tracking-[0.14em] text-cyan-200">
                once
              </span>
            </div>

            <!-- Client state + optional prop -->
            <div class="mt-3 grid gap-3 sm:grid-cols-2">
              <div class="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <p class="text-xs text-slate-500">Estado local (Vue)</p>
                <div class="mt-3 flex items-center gap-3">
                  <button
                    type="button"
                    aria-label="Restar uno"
                    class="grid size-8 place-items-center rounded-lg border border-white/10 bg-white/5 font-mono text-base text-slate-300 transition hover:border-cyan-300/30 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60"
                    @click="count--"
                  >
                    −
                  </button>
                  <span class="min-w-10 text-center font-mono text-2xl font-semibold text-white">{{ count }}</span>
                  <button
                    type="button"
                    aria-label="Sumar uno"
                    class="grid size-8 place-items-center rounded-lg border border-white/10 bg-white/5 font-mono text-base text-slate-300 transition hover:border-cyan-300/30 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60"
                    @click="count++"
                  >
                    +
                  </button>
                </div>
              </div>

              <div class="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <p class="text-xs text-slate-500">Prop opcional</p>
                <button
                  type="button"
                  :disabled="busy === 'slowFact'"
                  class="mt-2 inline-flex items-center justify-center rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-cyan-300/30 hover:bg-cyan-400/10 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60 disabled:cursor-not-allowed disabled:opacity-50"
                  @click="reloadProps(['slowFact'], 'slowFact')"
                >
                  {{ busy === 'slowFact' ? 'Cargando…' : 'Cargar slowFact' }}
                </button>
                <p v-if="slowFact" class="mt-2 text-xs leading-5 text-cyan-200/80">{{ slowFact.body }}</p>
                <p v-else class="mt-2 text-xs leading-5 text-slate-600">No viaja en la primera carga.</p>
              </div>
            </div>

            <!-- Form: POST + CSRF + redirect -->
            <form class="mt-3 rounded-xl border border-white/5 bg-white/[0.02] p-4" @submit.prevent="submitGreeting">
              <label for="name" class="text-xs text-slate-500">POST + CSRF + redirect</label>
              <div class="mt-2 flex flex-col gap-2 sm:flex-row">
                <input
                  id="name"
                  v-model="name"
                  type="text"
                  name="name"
                  autocomplete="name"
                  placeholder="Tu nombre"
                  class="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2.5 text-sm text-white placeholder:text-slate-600 focus:border-cyan-300/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/20"
                />
                <button
                  type="submit"
                  class="inline-flex items-center justify-center rounded-lg bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
                >
                  Enviar saludo
                </button>
              </div>

              <ul v-if="flashMessages.length" class="mt-3 space-y-2">
                <li
                  v-for="(message, index) in flashMessages"
                  :key="index"
                  class="rounded-lg border px-3 py-2 text-xs"
                  :class="flashTone(message.level)"
                >
                  {{ message.message }}
                </li>
              </ul>
            </form>
          </article>

          <!-- Side column -->
          <div class="space-y-5">
            <article class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur sm:p-6">
              <div class="flex items-center justify-between">
                <h2 class="text-sm font-semibold text-white">Stack</h2>
                <span class="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">fijado</span>
              </div>

              <ul class="mt-4 space-y-3">
                <li v-for="item in stack" :key="item.name" class="flex items-center justify-between gap-3">
                  <div class="flex items-center gap-2.5">
                    <span class="size-1.5 rounded-full" :class="item.tone"></span>
                    <span class="text-sm text-slate-300">{{ item.name }}</span>
                  </div>
                  <span class="font-mono text-[11px] text-slate-500">{{ item.version }}</span>
                </li>
              </ul>
            </article>

            <article class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur sm:p-6">
              <h2 class="text-sm font-semibold text-white">Qué demuestra</h2>
              <ul class="mt-4 space-y-3 text-sm leading-6 text-slate-400">
                <li class="flex gap-2.5">
                  <span class="mt-0.5 text-cyan-300">✓</span>
                  Componente Vue montado por Inertia.
                </li>
                <li class="flex gap-2.5">
                  <span class="mt-0.5 text-cyan-300">✓</span>
                  CSRF y sesiones gestionados por Django.
                </li>
                <li class="flex gap-2.5">
                  <span class="mt-0.5 text-cyan-300">✓</span>
                  Recarga parcial con <code class="font-mono text-cyan-200">only</code>.
                </li>
                <li class="flex gap-2.5">
                  <span class="mt-0.5 text-cyan-300">✓</span>
                  Flash messages de Django en <code class="font-mono text-cyan-200">flash.messages</code>.
                </li>
                <li class="flex gap-2.5">
                  <span class="mt-0.5 text-cyan-300">✓</span>
                  Props <code class="font-mono text-cyan-200">always</code> y
                  <code class="font-mono text-cyan-200">once</code> de v3.
                </li>
                <li class="flex gap-2.5">
                  <span class="mt-0.5 text-cyan-300">✓</span>
                  Estilos 100% Tailwind, sin CSS propio.
                </li>
                <li class="flex gap-2.5">
                  <span class="mt-0.5 text-cyan-300">✓</span>
                  Build de producción con Vite.
                </li>
              </ul>
            </article>

            <article class="rounded-2xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur sm:p-6">
              <h2 class="text-sm font-semibold text-white">Siguiente paso</h2>
              <p class="mt-2 text-xs leading-5 text-slate-500">
                Añade una vista nueva y su componente en
                <code class="font-mono text-slate-300">frontend/pages</code>.
              </p>
              <pre class="mt-3 overflow-x-auto rounded-xl border border-white/5 bg-slate-950/70 p-4 font-mono text-[11px] leading-6 text-slate-400"><code>@inertia("Module/Index")
def index(request):
    return {"title": "Módulo 1"}</code></pre>
            </article>
          </div>
        </section>
      </main>

      <footer class="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-white/5 pt-5 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
        <span>{{ appName }} · starter</span>
        <span>Tailwind 4 · Vite 7 · Inertia v3</span>
      </footer>
    </div>
  </div>
</template>
