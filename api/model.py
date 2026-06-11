"""Dispatcher de inferencia.

`Predictor` resuelve qué modelo servir por nombre (variable de entorno `MODEL`,
default `lstm`) contra el registry de `models/`. Si el elegido no puede cargar su
artefacto (clone limpio: `artifacts/` está gitignored) cae al **stub**, que no
necesita artefacto. Generar un artefacto: `python train.py --model <nombre>`
(ver README, "Entrenar y activar el modelo real").
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from models.base import Model
from models.registry import get_model
from models.stub import StubModel

DEFAULT_MODEL = "lstm"


class Predictor:
    """Singleton de inferencia. `load()` se llama una vez al levantar la API."""

    _instance: "Predictor | None" = None

    def __init__(self) -> None:
        self.ready = False
        self._active: Model = StubModel()

    @classmethod
    def instance(cls) -> "Predictor":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load()
        return cls._instance

    def load(self) -> None:
        """Carga el modelo pedido por la env var MODEL; si no puede, cae al stub."""
        name = os.environ.get("MODEL", DEFAULT_MODEL)
        candidate = get_model(name)
        failure = f"modelo '{name}' no registrado" if candidate is None else None
        if candidate is not None:
            try:
                if not candidate.load():
                    candidate = None  # falta el artefacto: stub sin ruido
            except Exception as exc:
                candidate = None
                failure = f"fallo al cargar el artefacto: {exc}"
        if candidate is None:
            candidate = StubModel()
            candidate.load()
            if failure:
                candidate.note = f"{candidate.note} ({failure})"
        self._active = candidate
        self.mode = "stub" if isinstance(candidate, StubModel) else "model"
        self.ready = True

    @property
    def version(self) -> str:
        return self._active.version

    @property
    def metrics(self) -> dict:
        return self._active.metrics

    @property
    def note(self) -> str:
        return self._active.note

    def predict_band(self, history: pd.DataFrame, static: dict, pvt: pd.DataFrame):
        """Devuelve (estimada, banda_inferior, banda_superior) en psi, por timestep."""
        return self._active.predict_band(history, static, pvt)

    def baseline(self, history: pd.DataFrame, static: dict) -> np.ndarray:
        """Curva de referencia anclada al P_init del input."""
        return self._active.baseline(history, static)
