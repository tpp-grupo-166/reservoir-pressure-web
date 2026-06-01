"""API FastAPI del estimador de presión de reservorio.

Levantar en desarrollo:
    cd api && uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import json
import tomllib

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import model
from features import FEATURE_DOCS
from schemas import (
    Baseline, Explainability, ModelInfo, Prediction, PredictResponse,
    StaticProps, ValidateResponse, ValidationMetrics,
)
from validation import ValidationError, read_csv, validate_history, validate_pvt

app = FastAPI(title="Reservoir Pressure Estimator API", version="0.1.0")

# En desarrollo el front corre en :5173 (Vite). Ajustar en producción.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/model-info", response_model=ModelInfo)
def model_info() -> ModelInfo:
    return ModelInfo(
        version=model.MODEL_VERSION,
        metricas_validacion=ValidationMetrics(**model.VALIDATION_METRICS),
        nota=model.MODEL_NOTE,
    )


@app.post("/api/validate", response_model=ValidateResponse)
async def validate(history_csv: UploadFile = File(...)) -> ValidateResponse:
    """Valida la historia de producción sin predecir (feedback temprano del wizard)."""
    df = read_csv(await history_csv.read())
    try:
        warnings, _ = validate_history(df)
    except ValidationError as exc:
        return ValidateResponse(ok=False, n_filas=len(df),
                                columnas_detectadas=list(df.columns),
                                advertencias=[], errores=[str(exc)])
    return ValidateResponse(ok=True, n_filas=len(df),
                            columnas_detectadas=list(df.columns),
                            advertencias=warnings, errores=[])


async def _parse_static(static_props: str | None, static_toml: UploadFile | None) -> StaticProps:
    """Construye StaticProps desde un archivo TOML (tiene prioridad) o desde el JSON del form."""
    if static_toml is not None:
        try:
            data = tomllib.loads((await static_toml.read()).decode("utf-8"))
            data = data.get("reservorio", data)  # admite [reservorio] o claves al tope
            return StaticProps.model_validate(data)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"TOML de reservorio inválido: {exc}")
    if static_props is not None:
        try:
            return StaticProps.model_validate(json.loads(static_props))
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"static_props inválido: {exc}")
    raise HTTPException(
        status_code=422,
        detail="Faltan las propiedades del reservorio: enviá static_props (JSON) o static_toml (archivo).",
    )


@app.post("/api/predict", response_model=PredictResponse)
async def predict(
    history_csv: UploadFile = File(...),
    pvt_csv: UploadFile = File(...),
    static_props: str | None = Form(None, description="JSON con las propiedades estáticas (StaticProps)"),
    static_toml: UploadFile | None = File(None, description="Config TOML con [reservorio] (alternativa a static_props)"),
) -> PredictResponse:
    static = await _parse_static(static_props, static_toml)

    history = read_csv(await history_csv.read())
    pvt = read_csv(await pvt_csv.read())

    try:
        warnings, cleaning = validate_history(history)
        warnings += validate_pvt(pvt, static.presion_inicial_psi)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    history = history.sort_values("tiempo_dias").reset_index(drop=True).fillna(0.0)
    static_dict = static.model_dump()

    predictor = model.Predictor.instance()
    pred = predictor.predict(history, static_dict, pvt)
    base = model.mean_curve_baseline(history, static_dict)

    return PredictResponse(
        prediction=Prediction(
            tiempo_dias=history["tiempo_dias"].tolist(),
            presion_estimada_psi=[round(float(v), 1) for v in pred],
            presion_inicial_psi=static.presion_inicial_psi,
        ),
        baseline=Baseline(
            nombre="curva de caída promedio (entrenamiento)",
            presion_psi=[round(float(v), 1) for v in base],
        ),
        explainability=Explainability(
            features_construidos=FEATURE_DOCS,
            data_cleaning=cleaning,
            transformaciones=[
                "normalización por volumen poral (features adimensionales)",
                "tabla PVT como vector de contexto, sin evaluar a la presión actual (sin leakage)",
                "z-score con estadísticas del entrenamiento",
            ],
            advertencias=warnings,
        ),
        model_info=ModelInfo(
            version=model.MODEL_VERSION,
            metricas_validacion=ValidationMetrics(**model.VALIDATION_METRICS),
            nota=model.MODEL_NOTE,
        ),
    )
