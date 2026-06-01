"""Contrato de entrada/salida de la API (Pydantic v2).

Es la fuente de verdad del contrato: el cliente tipado del front (`web/src/types`)
debe reflejar estos modelos.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ----------------------------- entrada -----------------------------

class StaticProps(BaseModel):
    """Propiedades estáticas del reservorio (constantes por campo)."""
    porosidad: float = Field(..., gt=0, lt=1, description="fracción (0–1)")
    permeabilidad_mD: float = Field(..., gt=0)
    espesor_neto_m: float = Field(..., gt=0)
    area_m2: float = Field(..., gt=0)
    presion_inicial_psi: float = Field(..., gt=0)


# La historia de producción y la tabla PVT entran como CSV (multipart),
# no como JSON: se parsean y validan en validation.py.


# ----------------------------- salida ------------------------------

class Prediction(BaseModel):
    tiempo_dias: list[float]
    presion_estimada_psi: list[float]
    presion_inicial_psi: float


class Baseline(BaseModel):
    nombre: str
    presion_psi: list[float]


class FeatureDoc(BaseModel):
    nombre: str
    descripcion: str
    fisica: str


class CleaningStep(BaseModel):
    accion: str
    columna: str
    filas: int
    motivo: str


class Explainability(BaseModel):
    features_construidos: list[FeatureDoc]
    data_cleaning: list[CleaningStep]
    transformaciones: list[str]
    advertencias: list[str]


class ValidationMetrics(BaseModel):
    R2_medio: float
    R2_std: float
    MAE_psi: float


class ModelInfo(BaseModel):
    version: str
    metricas_validacion: ValidationMetrics
    nota: str


class PredictResponse(BaseModel):
    prediction: Prediction
    baseline: Baseline
    explainability: Explainability
    model_info: ModelInfo


class ValidateResponse(BaseModel):
    ok: bool
    n_filas: int
    columnas_detectadas: list[str]
    advertencias: list[str]
    errores: list[str]
