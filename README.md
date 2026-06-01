# reservoir-pressure-web

Interfaz web + API para estimar la presión de un yacimiento de petróleo. El ingeniero
sube la historia de producción y la tabla PVT de un campo y obtiene la trayectoria de
presión estimada por el modelo de ML, con una explicación de cómo se procesaron sus datos.

> **Estado:** esqueleto / MVP. El backend corre con un predictor stub (físicamente
> plausible pero NO es el LSTM entrenado), para poder desarrollar el front contra una API
> viva. Ver `api/model.py` para enchufar el modelo real.

## Estructura

```
reservoir-pressure-web/
├── web/   → front React + Vite + TypeScript (gráficos con Recharts)
└── api/   → backend FastAPI (validación + feature engineering + inferencia)
```

`api/features.py` es la única fuente de verdad del feature engineering: el back lo usa para
inferencia y cualquier script externo debería importar de ahí en vez de duplicarlo.

## Arquitectura

```
Front (React/Vite)  ──HTTP/JSON──►  API (FastAPI)  ──►  Modelo ML (PyTorch)
                                       │
                                       └─ validación + feature engineering
```

Flujo stateless: subís datos → la API valida, construye features y predice → ves el
resultado. Sin base de datos ni autenticación en esta etapa (ver *Pendiente*).

## Datos de entrada

El usuario aporta tres cosas:

**1. Historia de producción** (CSV, una fila por timestep):

| Columna | Unidad | Descripción |
|---|---|---|
| `tiempo_dias` | días | tiempo desde inicio de producción |
| `Caudal_Prod_Petroleo_bbl` | bbl/día | caudal de producción de petróleo |
| `Caudal_Iny_Agua_bbl` | bbl/día | caudal de inyección de agua |
| `Prod_Acumulada_Petroleo` | bbl | producción acumulada de petróleo |
| `Prod_Acumulada_Gas` | scf | producción acumulada de gas |
| `Prod_Acumulada_Agua` | bbl | producción acumulada de agua |
| `Iny_Acumulada_Agua` | bbl | inyección acumulada de agua |

**2. Propiedades estáticas del reservorio**: porosidad (0–1), permeabilidad (mD),
espesor neto (m), área (m²) y presión inicial (psi). Se cargan en el formulario o
subiendo un **archivo de config TOML** (tabla `[reservorio]`, ver ejemplo en `sample-data/`).

**3. Tabla PVT** (CSV): curvas de laboratorio del fluido, columnas `p_grid_psi`,
`bo_rb_stb`, `bg_rb_scf`, `rs_scf_stb`.

La API valida columnas, tipos y rangos; registra cualquier limpieza/reemplazo y lo
devuelve junto con la predicción para que el usuario entienda qué se hizo con sus datos.

## Datos de ejemplo

En `sample-data/` hay un caso de prueba real y coherente, extraído de la simulación 1 del
campo **Volve** (dataset del notebook 5):

- `produccion_ejemplo.csv` — historia de producción (425 timesteps).
- `reservorio_ejemplo.toml` — propiedades estáticas del reservorio.
- `pvt_ejemplo.csv` — tabla PVT de Volve.

Sirven para recorrer el wizard de punta a punta (subir producción → cargar el TOML en el
paso 2 → subir el PVT → estimar).

## API

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/predict` | recibe los datos y devuelve trayectoria + baseline + explicabilidad |
| `POST` | `/api/validate` | valida la historia de producción sin predecir |
| `GET`  | `/api/model-info` | versión y métricas de validación del modelo |
| `GET`  | `/api/health` | healthcheck |

Docs interactivas en `http://localhost:8000/docs`.

## Desarrollo

Requisitos: Python 3.11+ y Node 20.19+ (lo pide Vite 8). Desde la raíz del repo:

```bash
make init      # instala dependencias de backend y frontend (una vez)
make up        # levanta backend (:8000) y frontend (:5173) en segundo plano
make down      # baja ambos
make restart   # reinicia ambos
make logs      # sigue los logs de ambos procesos
make help      # lista los targets
```

`make init` crea el virtualenv del backend e instala sus dependencias, y corre
`npm install` en el frontend. Después, `make up` corre los dos procesos en background y
guarda sus PIDs y logs en `.run/`.

`make up` corre los dos procesos en background y guarda sus PIDs y logs en `.run/`.

### Manual (sin Makefile)

```bash
cd api && .venv/bin/uvicorn main:app --reload --port 8000     # backend
cd web && npm run dev                                          # frontend (proxea /api → :8000)
# tests del backend: cd api && pytest -q
```

## Cómo cambiar el modelo

El modelo está aislado detrás de una sola clase: `api/model.py` → `Predictor`. Para
reemplazar el stub por un modelo entrenado (o cambiar un modelo por otro) **solo se toca
ese archivo**; los endpoints, la validación y el front no se modifican.

El contrato es:

- **`Predictor.load(self)`** — se llama una vez al levantar la API. Acá se carga el artefacto
  entrenado (pesos, scalers, lo que haga falta) y se deja en `self`.
- **`Predictor.predict(self, history, static, pvt) -> np.ndarray`** — recibe la historia de
  producción (DataFrame), las propiedades estáticas (dict) y la tabla PVT (DataFrame), y
  devuelve un array de presiones en psi, una por timestep.

### Pasos

1. **Entrenar y guardar el artefacto.** Guardar los pesos del modelo y los `StandardScaler`
   (ajustados solo con datos de entrenamiento) en `api/artifacts/`. Ese directorio ya está
   en `.gitignore`: los artefactos pesados se versionan aparte (git-lfs o release), no en el repo.
2. **Mantener la paridad de features.** El modelo debe consumir exactamente las features que
   produce `api/features.py` (`build_features`) — mismos nombres, fórmulas y orden con que
   fue entrenado. Para cambiar las features, modificarlas en `features.py` y reentrenar; es la
   única fuente de verdad del feature engineering.
3. **Implementar `load` y `predict`** en `Predictor`, usando `build_features(...)` para armar
   la entrada, aplicando los scalers cargados y devolviendo las presiones desnormalizadas.
4. **Actualizar el baseline** (`mean_curve_baseline`) con la curva promedio real del
   entrenamiento, en lugar de la recta placeholder actual.
5. **Sumar las dependencias del modelo.** Descomentar `torch` en `requirements.txt` (o agregar
   lo que use el modelo) y fijar la versión.
6. **Actualizar los metadatos.** En `model.py`, `MODEL_VERSION`, `VALIDATION_METRICS` y
   `MODEL_NOTE` se exponen en `GET /api/model-info`: dejarlos reflejando el modelo real
   (idealmente métricas multi-seed, no de una sola corrida).

> El predictor stub actual deja en claro la forma esperada de `predict`: tomar features,
> producir una presión por timestep. Mientras `build_features` y el contrato de entrada no
> cambien, se puede intercambiar el modelo por detrás sin tocar nada más.

## Pendiente

- Enchufar el LSTM entrenado en `api/model.py` (hoy es un stub).
- Validar/avisar mejor cuando el rango de la tabla PVT no cubre las presiones de operación
  (la interpolación al grid del modelo ya está en `build_pvt_vector`).
- Autenticación (JWT), persistencia (PostgreSQL), historial de consultas, comparación
  contra métodos físicos (PTA/EBM) y escenarios pre-cargados.
