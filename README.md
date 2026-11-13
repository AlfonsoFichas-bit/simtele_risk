# SIMTELE-RISK | Sistema de Simulación Numérica para Teleféricos Urbanos

Plataforma computacional para la evaluación de riesgos operacionales y análisis numérico en sistemas de transporte por cable aéreo (teleféricos). Proyecto desarrollado para la asignatura de **Métodos Numéricos** en la carrera de **Ingeniería Informática**.

---

## 🚀 Arquitectura Tecnológica

El sistema implementa un stack moderno full-stack reactivo sin dependencias de APIs REST desconectadas:

- **Backend:** Python 3.12+ con **Django 6.1**
- **Capa SPA / Adaptador:** **Inertia.js v3** (`inertia-django` 2.0)
- **Frontend:** **Vue 3** (Composition API, `<script setup>`) + Vite 7
- **Diseño & UI:** **Tailwind CSS 4** con paleta de monitoreo industrial oscuro
- **Motor Matemático:** Módulo desacoplado en `numerico/sistemas_lineales.py` con NumPy para estructuras tensoriales y algoritmos numéricos implementados paso a paso
- **Base de Datos:**
  - **Local (Desarrollo):** SQLite 3 nativo
  - **Producción (Cloud):** PostgreSQL en **Neon Tech** serverless mediante variable de entorno `DATABASE_URL` y `dj-database-url`

---

## 📊 Diagrama Entidad-Relación (DER)

El modelo de datos almacena la trazabilidad completa de cada experimento numérico (parámetros de entrada, escenarios de perturbación, tiempo de CPU, convergencia y desglose de iteraciones paso a paso).

```mermaid
erDiagram
    CASO_ESTUDIO ||--o{ ESCENARIO : "tiene"
    ESCENARIO ||--o{ SIMULACION : "ejecuta"
    SIMULACION ||--o{ EJECUCION_METODO : "contiene"
    EJECUCION_METODO ||--o{ ITERACION_RESULTADO : "registra pasos"
    EJECUCION_METODO ||--|| RESULTADO_RESUMEN : "consolida"

    CASO_ESTUDIO {
        int id PK
        string nombre
        string modelo_version
        text descripcion
    }

    ESCENARIO {
        int id PK
        int caso_id FK
        string tipo "NORMAL | ESTRES | MAL_CONDICIONADO"
        json parametros_json "Matriz A, vector b, x_ref, kappa(A)"
        string fuente_datos
    }

    SIMULACION {
        int id PK
        int escenario_id FK
        datetime fecha
        string usuario
        string estado "COMPLETADO"
    }

    EJECUCION_METODO {
        int id PK
        int simulacion_id FK
        string metodo "LU | Jacobi | Gauss-Seidel | Gradiente Conjugado"
        float tolerancia
        float paso
        int max_iter
        boolean convergio
        float tiempo_ms
    }

    ITERACION_RESULTADO {
        int id PK
        int ejecucion_id FK
        int numero
        json aproximacion_json "Vector x^(k)"
        float residual "Norma ||Ax - b||_inf"
        float error_abs "Norma ||x - x*||_inf"
        float error_rel
    }

    RESULTADO_RESUMEN {
        int id PK
        int ejecucion_id FK
        json referencia "Vector x*"
        json valor_json "Vector final x"
        json metrica_error_json
        text interpretacion
    }
```

---

## 🎯 Alcance Implementado (Semana 1)

### 1. Cuatro Módulos Físicos Obligatorios
1. **Detención de Emergencia de Cabinas:** Modelado cinemático y dinámico de desaceleración ante frenado de emergencia ($dx/dt = v$, $dv/dt = -a(v, t)$). Métodos: EDO (RK2, RK4), Integración (Trapecio, Simpson 1/3, Romberg), Raíces ($v(t)=0$).
2. **Deterioro Mecánico y Mantenimiento (Operativo en Semana 1):** Calibración multivariable de desgaste en 4 poleas acopladas ($A x = b$) mediante matrices Simétricas Definidas Positivas (SPD) y análisis de vida útil residual ($D(t) - D_{\text{umbral}} = 0$).
3. **Oscilaciones por Viento:** Dinámica vibratoria bajo ráfagas laterales ($m x'' + c x' + k x = F(t)$). Métodos: EDO e Integración.
4. **Reconstrucción de Señales de Sensores:** Recuperación de telemetría perdida en torres intermedias ($P_n(x) = \sum y_i L_i(x)$ o Splines Cúbicos).

### 2. Algoritmos de Sistemas Lineales ($A x = b$, tamaño 4×4)
- **Factorización LU:** Método directo exacto con descomposición de Doolittle ($A = L \cdot U$) con $L$ triangular inferior unitaria y sustitución sucesiva hacia adelante y hacia atrás.
- **Método de Jacobi:** Algoritmo iterativo simultáneo con descomposición diagonal.
- **Método de Gauss-Seidel:** Algoritmo iterativo sucesivo con actualización inmediata de componentes de la solución.
- **Gradiente Conjugado:** Algoritmo sobre subespacios de Krylov optimizado para matrices SPD.
- **Solución Directa de Referencia:** Cálculo de alta precisión para comparación formal.
- **Número de Condición:** $\kappa_\infty(A) = \Vert A\Vert_\infty \cdot \Vert A^{-1}\Vert_\infty$ e identificación de simetría y autovalores positivos (SPD).

### 3. Teoría de Errores Transversal
Evaluación transversal en todos los métodos bajo norma infinito:
- **Error Absoluto:** $E_{\text{abs}} = \Vert x_{\text{aprox}} - x_{\text{ref}}\Vert_\infty$
- **Error Relativo:** $E_{\text{rel}} = \frac{\Vert x_{\text{aprox}} - x_{\text{ref}}\Vert_\infty}{\Vert x_{\text{ref}}\Vert_\infty}$
- **Error Porcentual:** $E_{\%} = E_{\text{rel}} \times 100\%$
- **Residuo Numérico:** $R = \Vert A x_{\text{aprox}} - b\Vert_\infty$

### 4. Tres Escenarios Numéricos del Módulo 2
- **NORMAL:** Matriz 4×4 SPD estrictamente diagonal dominante ($\kappa_\infty(A) \approx 3.14$). Convergencia rápida y monótona en todos los métodos.
- **ESTRÉS:** Matriz 4×4 SPD con mayor acoplamiento inter-poleas y dominancia diagonal débil ($\kappa_\infty(A) = 7.0$). Ralentiza la tasa de contracción espectral de Jacobi y Gauss-Seidel, triplicando el número de iteraciones requeridas (52 vs 17 en normal) para alcanzar la tolerancia de parada.
- **MAL CONDICIONADO:** Matriz 4×4 SPD cuasi-singular con número de condición $\kappa_\infty(A) = 792.0$ y vector consistente $b = A \cdot x^* = [4.935, 4.965, 4.955, 4.915]$. Evidencia la distinción clave entre la sensibilidad intrínseca del problema ante perturbaciones (amplificación de $\delta b$ superior a $490\times$) y la convergencia algorítmica: Jacobi y Gauss-Seidel no convergen por pérdida de dominancia diagonal, mientras que Gradiente Conjugado converge con exactitud al preservar la estructura Simétrica Definida Positiva (SPD).

> **Nota sobre el Entregable:** El documento PDF con los ejemplos resueltos a mano, deducciones analíticas de los cuatro modelos y tablas impresas de error se compila por separado como complemento de este aplicativo web.

### 5. Persistencia, Recarga y Relanzamiento
Todas las ejecuciones se registran íntegramente en las 6 tablas relacionales. El panel incluye una tabla inferior interactiva con las últimas 5 simulaciones y dos acciones:
- **Recargar:** Recupera fielmente los parámetros, iteraciones y resultados de un experimento histórico desde la base de datos sin recalcular.
- **Relanzar:** Re-ejecuta el algoritmo en el servidor con los mismos parámetros del registro histórico, creando una nueva simulación independiente en la BD.

---

## 🛠️ Instalación y Puesta en Marcha

### Prerrequisitos
- Python 3.12 o superior
- Node.js 20+ o Bun
- Git

### 1. Clonar el repositorio y configurar el entorno virtual
```bash
# Crear entorno virtual
python -m venv .venv

# Activar en Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# O en Git Bash / Linux / macOS:
# source .venv/bin/activate

# Instalar dependencias backend
pip install -r requirements.txt
```

### 2. Configurar Base de Datos y Migraciones
Por defecto el sistema utiliza SQLite local (`db.sqlite3`). Para usar PostgreSQL (Neon Tech), defina la variable `DATABASE_URL`:
```bash
# Opcional para Neon Postgres:
# $env:DATABASE_URL="postgres://usuario:password@ep-xyz.neon.tech/neondb?sslmode=require"

python manage.py makemigrations
python manage.py migrate
```

### 3. Instalar dependencias del Frontend
```bash
npm install
```

### 4. Compilar y Ejecutar en Desarrollo
Ejecuta dos terminales en la raíz del proyecto:

**Terminal 1 (Vite HMR):**
```bash
npm run dev
```

**Terminal 2 (Django Server):**
```bash
python manage.py runserver 127.0.0.1:8000
```

Accede desde tu navegador a: **`http://127.0.0.1:8000`**

### 5. Compilación para Producción
```bash
npm run build
python manage.py collectstatic --noinput
```

---

## 🧪 Pruebas Automatizadas

El proyecto cuenta con suite de pruebas unitarias cubriendo la lógica matemática y las vistas Inertia:
```bash
python manage.py test
```
Resultados verificados:
- Renderizado de componentes Inertia (`Dashboard.vue`)
- Integridad de persistencia en las 6 tablas relacionales
- Convergencia de métodos numéricos (LU, Jacobi, Gauss-Seidel, Gradiente Conjugado)
- Recarga de simulaciones históricas
