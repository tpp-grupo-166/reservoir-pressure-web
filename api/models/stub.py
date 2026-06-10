"""Stub de desarrollo: trayectoria físicamente plausible sin modelo entrenado.

Es el fallback universal del `Predictor` (clone limpio sin artefactos, torch ausente,
o nombre de modelo desconocido): el front siempre tiene algo coherente que graficar.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from features import PRESSURE_SCALE, build_features
from models.base import Model


class StubModel(Model):
    name = "stub"

    def __init__(self) -> None:
        self.version = "stub-v0"
        self.metrics = dict(R2_medio=0.0, R2_std=0.0, MAE_psi=0.0)
        self.note = ("STUB de desarrollo: no es el modelo entrenado. Devuelve una trayectoria "
                     "derivada de un voidage de superficie crudo. Correr `python train.py` para "
                     "activar el LSTM real.")

    def load(self) -> bool:
        return True  # no necesita artefacto

    def predict_band(self, history: pd.DataFrame, static: dict, pvt: pd.DataFrame):
        # voidage de superficie crudo como proxy de la caída, banda nominal de ±3%
        feats = build_features(history, static, pvt)
        p_init = static["presion_inicial_psi"]
        net_surface = (feats["Np_over_PV"] + feats["Wp_over_PV"] - feats["Winj_over_PV"]).to_numpy()
        mean = p_init + (-0.6 * net_surface * PRESSURE_SCALE)
        return mean, mean * 0.97, mean * 1.03

    def baseline(self, history: pd.DataFrame, static: dict) -> np.ndarray:
        return static["presion_inicial_psi"] + np.linspace(0.0, -150.0, len(history))
