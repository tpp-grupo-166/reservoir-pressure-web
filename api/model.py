"""Carga e inferencia del modelo.

⚠️  STUB: hoy NO carga el LSTM real. Devuelve una trayectoria físicamente plausible
derivada de un voidage de superficie crudo, para que el front se pueda desarrollar contra
una API viva.
Cuando esté el artefacto entrenado, reemplazar `Predictor.predict` por la inferencia
PyTorch real (cargar pesos + scaler + el FE de features.py) y descomentar torch en
requirements.txt.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from features import PRESSURE_SCALE, build_features, build_pvt_vector

# Métricas de validación del modelo (transfer cross-reservoir multi-seed, ver auditoría).
MODEL_VERSION = "stub-v0"
VALIDATION_METRICS = dict(R2_medio=0.70, R2_std=0.08, MAE_psi=113.0)
MODEL_NOTE = (
    "STUB de desarrollo. Métricas mostradas = transfer cross-reservoir multi-seed del "
    "modelo de referencia, NO de ajuste in-sample. Reemplazar por el LSTM entrenado."
)


class Predictor:
    """Singleton de inferencia. `load()` se llama una vez al levantar la API."""

    _instance: "Predictor | None" = None

    def __init__(self) -> None:
        self.ready = False
        # TODO: self.net = torch.load(...); self.scaler = ...

    @classmethod
    def instance(cls) -> "Predictor":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load()
        return cls._instance

    def load(self) -> None:
        # TODO: cargar pesos del LSTM + scaler entrenados.
        self.ready = True

    def predict(self, history: pd.DataFrame, static: dict, pvt: pd.DataFrame) -> np.ndarray:
        """Devuelve la trayectoria de presión estimada (psi), un valor por timestep.

        STUB: usa un voidage de superficie crudo (retiro − inyección) como proxy de la
        caída de presión. Físicamente coherente (más retiro neto → más caída) pero NO es
        el modelo entrenado.
        """
        feats = build_features(history, static, pvt)
        _pvt_vector = build_pvt_vector(pvt)  # el modelo real lo consume; el stub lo ignora
        p_init = static["presion_inicial_psi"]
        net_surface = (feats["Np_over_PV"] + feats["Wp_over_PV"] - feats["Winj_over_PV"]).to_numpy()
        # respuesta lineal placeholder; el LSTM real captura la dinámica temporal.
        delta = -0.6 * net_surface * PRESSURE_SCALE
        return p_init + delta


def mean_curve_baseline(history: pd.DataFrame, static: dict) -> np.ndarray:
    """Baseline honesto: trayectoria de caída 'promedio' anclada a P_init (ver auditoría).

    STUB: caída lineal suave hasta -150 psi sobre el horizonte. Reemplazar por la curva
    promedio real del set de entrenamiento.
    """
    p_init = static["presion_inicial_psi"]
    n = len(history)
    return p_init + np.linspace(0.0, -150.0, n)
