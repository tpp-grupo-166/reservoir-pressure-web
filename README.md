# reservoir-pressure-web

Interfaz web + API para estimar la presión de un yacimiento de petróleo. El ingeniero
sube la historia de producción y la tabla PVT de un campo y obtiene la trayectoria de
presión estimada por el modelo de ML, con una explicación de cómo se procesaron sus datos.

> **Estado:** MVP. Sirve el LSTM entrenado si el artefacto existe; si no, un stub de
> desarrollo físicamente plausible (ver *El modelo*).

## Estructura

```
reservoir-pressure-web/
├── web/   → front React + Vite + TypeScript (gráficos con Recharts)
└── api/   → backend FastAPI (validación + feature engineering + inferencia)
```

Flujo stateless: el front manda los datos a la API, que valida, construye features
(en `api/features.py`, única fuente de verdad) y predice con el modelo. Sin base de datos
ni autenticación en esta etapa.

## Datos

El usuario aporta tres archivos; en `sample-data/` hay un caso real completo (simulación 1
del campo Volve) para recorrer el wizard de punta a punta.

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
```

`make up` deja PIDs y logs en `.run/`. Tests del backend: `cd api && pytest -q`.

## El modelo

El modelo del notebook 5 (LSTM + encoder de PVT) ya está implementado: arquitectura en
`api/net.py`, entrenamiento en `api/train.py`, inferencia en `api/model.py`. La API sirve
el modelo real si existe el artefacto entrenado; si no (p. ej. un clone limpio, porque
`artifacts/*.pt` está gitignored), cae a un stub físicamente plausible pero no entrenado.

### Entrenar y activar

Desde `api/` con el venv activado:

```bash
pip install -r requirements-model.txt   # torch (no hace falta para el stub)
python train.py                          # descarga Norne, entrena y guarda artifacts/model.pt
make restart                             # (desde la raíz) recarga la API con el artefacto
```

Verificá con `curl -s localhost:8000/api/model-info`: `version` pasa de `stub-v0` a
`lstm-pvt-notebook5-v1`.

> **Nota:** es el modelo más frágil según la auditoría (el transfer cross-reservoir depende
> de la seed); las métricas que expone son del test in-distribution de Norne. Tratá la
> estimación como preliminar.

### Cambiar el modelo

El modelo está aislado en `api/model.py` → `Predictor`; reemplazarlo no toca endpoints,
validación ni front. El contrato:

- **`load()`** — carga el artefacto (pesos + scalers) al levantar la API; si no existe, stub.
- **`predict_band(history, static, pvt)`** — devuelve `(estimada, inf, sup)` en psi, una por
  timestep.
- **`baseline(history, static)`** — la curva de referencia (caída promedio del entrenamiento).

El modelo debe consumir las features de `api/features.py` (`build_features`) con los mismos
nombres y orden con que fue entrenado; para cambiarlas, editar ahí y reentrenar.

## Pendiente

- Versionar/distribuir el artefacto entrenado (`artifacts/model.pt`): hoy cada quien lo
  regenera con `python train.py`. Falta el canal de release (git-lfs o adjunto) para no
  depender del entrenamiento local.
- Validar/avisar mejor cuando el rango de la tabla PVT no cubre las presiones de operación
  (la interpolación al grid del modelo ya está en `build_pvt_vector`).
- Persistencia (PostgreSQL)
  - Sumar Postgres al `docker-compose.yml` + capa de acceso (SQLAlchemy + tabla
    `predictions` + tabla `users`).
  - Crear los modelos de SQLAlchemy para `Prediction` y `User`.
  - Crear los servicios de SQLAlchemy para `PredictionService` y `UserService`.
  - Guardar cada predicción (inputs, outputs, versión del modelo, timestamp) al
    resolver `/api/predict`.
  - Asociar el historial al usuario (FK en `predictions`) y filtrar por dueño.
- Historial de consultas
  - `GET /api/history` paginado.
  - Vista de historial en el front: lista de consultas previas + reabrir un resultado.
- Dashboard de predicciones
  - Migrar la página del dashboard para que siga el diseño de las páginas de login y register.
- Curva de presión por física (no-ML), para contrastar con el modelo
  - Backend (`api/physics.py`): calcular una segunda trayectoria con balance de materiales
    —el principio de que la presión cae cuando se produce más fluido del que se repone— y
    sumarla a la respuesta de `/api/predict`.
  - Front: dibujarla en `TrajectoryChart` junto a la curva del ML. Sirve de chequeo de
    cordura (si se separan mucho, desconfiar del modelo) y le da credibilidad a la
    herramienta frente a un ingeniero, que confía en el balance de materiales.
