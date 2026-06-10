# reservoir-pressure-web

[![CI](https://github.com/maximopalopoli/reservoir-pressure-web/actions/workflows/ci.yml/badge.svg)](https://github.com/maximopalopoli/reservoir-pressure-web/actions/workflows/ci.yml)
![coverage](https://img.shields.io/badge/coverage-84%25-brightgreen)

Interfaz web + API para estimar la presión de un yacimiento de petróleo. El ingeniero
sube la historia de producción y la tabla PVT de un campo y obtiene la trayectoria de
presión estimada por el modelo de ML, con una explicación de cómo se procesaron sus datos.

> **Estado:** MVP. Sirve el modelo elegido por la env var `MODEL` (default: el LSTM del
> notebook 5); sin artefacto entrenado cae a un stub de desarrollo físicamente plausible
> (ver *Los modelos*).

## Estructura

```
reservoir-pressure-web/
├── web/   → front React + Vite + TypeScript (gráficos con Recharts)
└── api/   → backend FastAPI (validación + feature engineering + inferencia)
    └── models/   → modelos enchufables, uno por archivo (ver "Los modelos")
```

Flujo stateless: el front manda los datos a la API, que valida, construye features
(en `api/features.py`, única fuente de verdad) y predice con el modelo. Sin base de datos
ni autenticación en esta etapa.

## Datos

El usuario aporta tres archivos; en `sample-data/` hay un caso real completo (simulación 1
del campo Volve). Para probarlo sin datos propios, el primer paso del wizard tiene un botón
**"Cargar caso de ejemplo"** que carga ese caso en los tres pasos, listo para estimar.

- **Historia de producción** (CSV, una fila por timestep): `tiempo_dias`,
  `Caudal_Prod_Petroleo_bbl`, `Caudal_Iny_Agua_bbl`, `Prod_Acumulada_Petroleo`,
  `Prod_Acumulada_Gas`, `Prod_Acumulada_Agua`, `Iny_Acumulada_Agua`.
- **Propiedades estáticas** (formulario o archivo TOML con tabla `[reservorio]`): porosidad,
  permeabilidad, espesor neto, área y presión inicial.
- **Tabla PVT** (CSV): `p_grid_psi`, `bo_rb_stb`, `bg_rb_scf`, `rs_scf_stb`.

La API valida columnas, tipos y rangos, y devuelve cualquier limpieza junto con la predicción.

## Desarrollo

Requisitos: Python 3.11+ y Node 20.19+. Desde la raíz del repo:

```bash
make init      # instala dependencias de backend y frontend (una vez)
make up        # levanta backend (:8000) y frontend (:5173) en background
make down      # baja ambos
make restart   # reinicia ambos
make logs      # sigue los logs
make test      # ejecuta tests del backend
make train     # entrena un modelo (MODEL=ridge|xgboost|lstm|pinn; default lstm)
```

`make up` deja PIDs y logs en `.run/`. Tests del backend: `cd api && pytest -q`.

## Base de datos

La aplicación usa PostgreSQL para persistencia de usuarios. Las migraciones se gestionan con Alembic.

```bash
make up-docker  # levanta la base de datos PostgreSQL en Docker
```

### Migraciones

Desde el directorio `api/`:

```bash
# Crear una nueva migración (detecta cambios en los modelos)
.venv/bin/alembic revision --autogenerate -m "descripcion_del_cambio"

# Aplicar todas las migraciones pendientes
.venv/bin/alembic upgrade head

# Ver el estado de las migraciones
.venv/bin/alembic current
.venv/bin/alembic history
```

Las migraciones se aplican automáticamente al ejecutar `make up`.

### Acceso directo a PostgreSQL

```bash
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d reservoir_db
```

Comandos útiles en psql:
```sql
\d                    # listar todas las tablas
\d users              # describir la tabla users
SELECT * FROM users;  # ver todos los usuarios
```

## Los modelos

Los modelos son enchufables: cada uno vive en `api/models/<nombre>.py`, se registra por
nombre en `api/models/registry.py`, y la API sirve el que diga la variable de entorno
`MODEL` (default: `lstm`). Si el elegido no puede cargar su artefacto (p. ej. un clone
limpio, porque `artifacts/` está gitignored), cae al stub.

| `MODEL` | origen | qué es | banda de incertidumbre |
|---|---|---|---|
| `lstm` (default) | notebook 5 | ensemble de 5 LSTM + encoder de PVT, secuencial | min/max del ensemble |
| `ridge` | notebook 6 | lineal pointwise sobre features de superficie, sin PVT | ±1.96σ de residuos de CV |
| `xgboost` | notebook 6 | árboles pointwise, mismas features que ridge | ±1.96σ de residuos de CV |
| `pinn` | notebook 7 | balance de materiales + corrección neuronal (UDE), multi-campo | min/max de 3 seeds |
| `stub` | — | proxy físico sin entrenamiento (fallback universal) | nominal ±3% |

El contrato (`api/models/base.py`) es sobre los datos crudos del usuario (historia +
estáticos + PVT): cada modelo hace su propio feature engineering adentro, porque los FE
son deliberadamente distintos (el LSTM usa el vector PVT de 51D que ridge/xgboost
descartan por leakage, y el pinn trabaja en volúmenes de reservorio).

Todos entrenan y reportan métricas con el mismo split de Norne (24 train / 6 test) para
que `/api/model-info` sea comparable entre modelos. La excepción parcial es el `pinn`,
que suma Volve y SPE9 al train: su gracia es transferir entre regímenes termodinámicos
vía la física compartida, aunque el test es el mismo. Los datos salen del repo del
equipo (`tpp-grupo-166/opm-datasets`), de la variante `datasets/consistentes/`: la PVT
de `datasets/` fue editada después de simular y rompe cualquier modelo de balance de
materiales (ver el README de esa carpeta).

### Entrenar y activar

Desde la raíz del repo (o `python train.py --model <nombre>` desde `api/`):

```bash
cd api && .venv/bin/pip install -r requirements-model.txt   # torch + sklearn + xgboost (una vez)
make train MODEL=lstm    # descarga los datos, entrena y guarda artifacts/lstm.pt
MODEL=lstm make up       # sirve ese modelo (MODEL es la misma env var que lee la API)
```

`ridge` y `xgboost` entrenan en segundos; `lstm` y `pinn` en minutos (CPU). Cada
artefacto va a `artifacts/<nombre>.pt|.joblib` (el viejo `artifacts/model.pt` del LSTM
se sigue leyendo). Verificá con `curl -s localhost:8000/api/model-info` que `version`
sea la esperada (p. ej. `lstm-pvt-notebook5-v1`).

> **Nota:** las métricas que exponen todos son del test in-distribution de Norne, que es
> poco exigente (las 30 sims son parecidas entre sí). El transfer a un campo nuevo es
> otra historia (ver la auditoría y los notebooks 6-7): tratá la estimación como
> preliminar, y la nota de cada artefacto como parte del resultado.

### Agregar un modelo

1. Crear `api/models/<nombre>.py` con una subclase de `models.base.Model`: `load()`
   (artefacto → listo para servir), `predict_band(history, static, pvt)` → `(estimada,
   inf, sup)` en psi por timestep, `baseline(history, static)`, y opcionalmente `train()`.
2. Registrarla en `api/models/registry.py`.
3. `make train MODEL=<nombre>` y servir con `MODEL=<nombre> make up`.

El FE va adentro del modelo (importá de `api/features.py` lo que sirva); helpers
compartidos de datos en `api/models/datasets.py` y el baseline estándar en
`models.base.baseline_from_curve`.

## Pendiente

- API y endpoint de predicción
  - Migrar todo el endpoint de predicción y todas sus dependencias a la nueva estructura de la API.
- Versionar/distribuir los artefactos entrenados (`artifacts/<modelo>.pt|.joblib`): hoy
  cada quien los regenera con `make train`. Falta el canal de release (git-lfs o adjunto)
  para no depender del entrenamiento local.
- Persistencia de predicciones (PostgreSQL)
  - Crear modelo de SQLAlchemy para `Prediction`.
  - Guardar cada predicción (inputs, outputs, versión del modelo, timestamp) al
    resolver `/api/predict`.
  - Asociar el historial al usuario (FK en `predictions`) y filtrar por dueño.
- Historial de consultas
  - `GET /api/history` paginado.
  - Vista de historial en el front: lista de consultas previas + reabrir un resultado.
- Validar/avisar mejor cuando el rango de la tabla PVT no cubre las presiones de operación
  (la interpolación al grid del modelo ya está en `build_pvt_vector`).
- Curva de presión por física (no-ML) como segunda curva de contraste. El modelo `pinn`
  ya sirve una trayectoria de balance de materiales como modelo elegible; lo que queda de
  esta idea es mostrarla JUNTO a la del ML en `TrajectoryChart` (no crear `api/physics.py`
  desde cero). Sirve de chequeo de cordura (si se separan mucho, desconfiar del modelo) y
  le da credibilidad a la herramienta frente a un ingeniero, que confía en el balance de
  materiales.
