# SIMTELE Risk

Starter de **Django + Inertia.js v3 + Vue 3 + Tailwind CSS 4** con Vite.

Todo se ejecuta **desde la raíz del repositorio**: no hace falta entrar a
`frontend/` ni a ninguna otra carpeta.

```
.
├── config/            # configuración de Django
├── core/              # vistas, rutas y {% vite_assets %}
├── frontend/          # código Vue + Tailwind (sin package.json propio)
│   ├── main.ts        # entrypoint de Inertia
│   ├── tailwind.css   # entrada de Tailwind v4
│   ├── app.css        # tema y capa base
│   ├── env.d.ts
│   └── pages/         # páginas de Inertia
├── static/build/      # salida de `npm run build` (ignorada por git)
├── templates/
│   ├── layout.html    # layout HTML que carga los assets
│   └── inertia.html   # formato de primera carga de Inertia v3
├── manage.py
├── package.json       # scripts y dependencias del frontend
├── tsconfig.json
└── vite.config.ts
```

## Requisitos

- Python 3.12+ y Django 6.1
- Node.js 20+ (o Bun)
- Un entorno virtual de Python

## Puesta en marcha

Desde la raíz del repositorio:

```bash
# 1. Dependencias de Python
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

# 2. Base de datos
python manage.py migrate

# 3. Dependencias del frontend
npm install                     # o: bun install

# 4. Desarrollo: dos terminales, ambas en la raíz
npm run dev                     # Vite en http://127.0.0.1:5173
python manage.py runserver 127.0.0.1:8000
```

Abre <http://127.0.0.1:8000>.

> Con `DEBUG=1`, `{% vite_assets %}` apunta al servidor de Vite y añade el
> cliente de HMR. Con `DEBUG=0`, lee `static/build/manifest.json`.

> El aviso `WARNING: This is a development server...` de `runserver` se
> oculta automáticamente en desarrollo mediante la variable oficial
> `DJANGO_RUNSERVER_HIDE_WARNING` (ver `config/settings.py`). Con `DEBUG=0`
> el aviso vuelve a mostrarse, para que nadie confunda `runserver` con un
> servidor de producción.

## Producción

```bash
npm run build                   # genera static/build/
python manage.py collectstatic --noinput
```

O simplemente `./build.sh` (usa Bun si está disponible y, si no, npm).

Variables de entorno útiles:

| Variable             | Por defecto              | Uso                                   |
| -------------------- | ------------------------ | ------------------------------------- |
| `DJANGO_SECRET_KEY`  | clave de desarrollo      | clave real en producción              |
| `DJANGO_DEBUG`       | `1`                      | `0` para servir el build de Vite      |
| `VITE_DEV_SERVER`    | `http://127.0.0.1:5173`  | URL del servidor de Vite en desarrollo |

## Scripts

| Comando             | Qué hace                                      |
| ------------------- | --------------------------------------------- |
| `npm run dev`       | Servidor de Vite con HMR                      |
| `npm run build`     | Build de producción en `static/build/`        |
| `npm run preview`   | Sirve el build localmente                     |
| `npm run typecheck` | `tsc --noEmit`                                |

## Cómo funciona

- Django renderiza `templates/inertia.html`, que extiende `layout.html`.
- `layout.html` carga `{% vite_assets %}`, una etiqueta propia en
  `core/templatetags/vite.py`. En desarrollo devuelve el `<script>` del entry
  de Vite; en producción lee el manifest y emite el CSS y el JS con hash.
- `frontend/main.ts` monta Inertia y resuelve las páginas desde
  `frontend/pages/**/*.vue`.
- Las vistas usan `@inertia("Home")`; el diccionario que devuelven son los
  props de la página. El ejemplo incluye `always()`, `once()` y `optional()`,
  recarga parcial, CSRF y mensajes flash.

### Añadir una página

1. Crea la vista:

   ```python
   @inertia("Module/Index")
   def index(request):
       return {"title": "Módulo 1"}
   ```

2. Crea `frontend/pages/Module/Index.vue`.

No hay que tocar `vite.config.ts`: el glob de `main.ts` descubre la página.

## Pruebas

```bash
python manage.py test -v 2
```

## Notas de estilo

- El CSS es **100% Tailwind**. `frontend/app.css` solo declara tokens con
  `@theme` y una capa `base`; las utilidades viven en los componentes.
- `tailwind.css` usa `source(none)` y declara explícitamente qué escanear
  (`frontend/` y `templates/`), así no se cuelan clases de `docs/` ni de
  `static/build/`.
