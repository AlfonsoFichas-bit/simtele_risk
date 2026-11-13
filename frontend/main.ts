import './tailwind.css'
import './app.css'

import { createInertiaApp } from '@inertiajs/vue3'
import { createApp, h } from 'vue'
import type { DefineComponent } from 'vue'

createInertiaApp({
  title: (title) => (title ? `${title} · SIMTELE Risk` : 'SIMTELE Risk'),
  resolve: (name) => {
    const pages = import.meta.glob('./pages/**/*.vue', { eager: true }) as Record<
      string,
      { default: DefineComponent }
    >
    const page = pages[`./pages/${name}.vue`]
    if (!page) {
      throw new Error(`Inertia page not found: ${name}`)
    }
    return page.default
  },
  setup({ el, App, props, plugin }) {
    createApp({ render: () => h(App, props) })
      .use(plugin)
      .mount(el)
  },
  progress: {
    color: '#22d3ee',
  },
  // Inertia v3 has its own HTTP client. Point it at Django's CSRF names
  // instead of Laravel's defaults (XSRF-TOKEN / X-XSRF-TOKEN).
  http: {
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken',
  },
})
