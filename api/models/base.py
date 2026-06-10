"""Contrato común de los modelos enchufables.

Cada modelo recibe los datos CRUDOS del usuario (historia de producción, propiedades
estáticas y tabla PVT) y hace su propio feature engineering adentro: los FE de los
distintos modelos son deliberadamente distintos (p. ej. el LSTM usa el vector PVT de
51D que Ridge/XGBoost descartan por leakage), así que no se comparte a nivel interfaz.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class Model(ABC):
    """Un modelo servible por la API.

    `version`, `metrics` y `note` son los metadatos que expone `/api/model-info`;
    quedan definidos recién después de `load()`.
    """

    name: str  # nombre con el que se registra (y valor de la env var MODEL)
    version: str
    metrics: dict
    note: str

    @abstractmethod
    def load(self) -> bool:
        """Deja el modelo listo para servir (p. ej. carga su artefacto).

        Devuelve False si no puede servir (falta el artefacto); levanta excepción si
        el intento de carga falla. En ambos casos `Predictor` cae al stub.
        """

    @abstractmethod
    def predict_band(
        self, history: pd.DataFrame, static: dict, pvt: pd.DataFrame
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Devuelve (estimada, banda_inferior, banda_superior) en psi, por timestep."""

    @abstractmethod
    def baseline(self, history: pd.DataFrame, static: dict) -> np.ndarray:
        """Curva de referencia anclada al P_init del input."""

    def train(self) -> None:
        """Entrena el modelo y guarda su artefacto en `artifacts/` (CLI: train.py).

        Default: no entrenable. Los modelos con artefacto lo sobreescriben.
        """
        raise NotImplementedError(f"el modelo '{self.name}' no se entrena")
