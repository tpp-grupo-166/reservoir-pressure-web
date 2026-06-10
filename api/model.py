"""Carga e inferencia del modelo.

`Predictor` resuelve qué modelo servir por nombre (variable de entorno `MODEL`,
default `lstm`) contra el registry de `models/`. Si el elegido no puede cargar su
artefacto (clone limpio: `artifacts/` está gitignored) cae al **stub**, que no
necesita artefacto. Generar el artefacto del LSTM: `python train.py` (ver README,
"Entrenar y activar el modelo real").
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from features import (DYNAMIC_COLUMNS, PRESSURE_SCALE, STATIC_COLUMNS,
                      build_features, build_pvt_vector)
from models.base import Model
from models.registry import get_model, register
from models.stub import StubModel

ARTIFACT = Path(__file__).parent / "artifacts" / "model.pt"

DEFAULT_MODEL = "lstm"


@register
class _LSTMModel(Model):
    """Ensemble de 5 LSTM + encoder de PVT del notebook 5 (`net.py`/`train.py`).

    Vive acá de forma transitoria: se muda a `models/lstm.py` junto con el
    entrenamiento en el siguiente paso del refactor.
    """

    name = "lstm"

    def __init__(self) -> None:
        self._nets = []
        self._scaler_dynamic = None
        self._scaler_static = None
        self._mean_delta = None

    def load(self) -> bool:
        if not ARTIFACT.exists():
            return False
        import torch
        from net import LSTMPVT

        art = torch.load(ARTIFACT, map_location="cpu", weights_only=False)
        nets = []
        for sd in art["state_dicts"]:
            net = LSTMPVT(**art["arch"])
            net.load_state_dict(sd)
            net.eval()
            nets.append(net)
        self._nets = nets
        self._scaler_dynamic = art["scaler_dynamic"]
        self._scaler_static = art["scaler_static"]
        self._mean_delta = np.asarray(art["mean_delta_curve"], dtype=np.float64)
        self.version = art["version"]
        self.metrics = art["metrics"]
        self.note = art["note"]
        return True

    def predict_band(self, history: pd.DataFrame, static: dict, pvt: pd.DataFrame):
        # la banda es el min/max del ensemble de seeds (incertidumbre real)
        import torch

        feats = build_features(history, static, pvt)
        p_init = static["presion_inicial_psi"]
        dyn = feats[DYNAMIC_COLUMNS].to_numpy()[None, :, :]
        stat = feats[STATIC_COLUMNS].iloc[0].to_numpy()[None, :]
        dyn = (dyn - self._scaler_dynamic["mean"]) / self._scaler_dynamic["scale"]
        stat = (stat - self._scaler_static["mean"]) / self._scaler_static["scale"]
        pvt_vec = build_pvt_vector(pvt)[None, :]
        t_dyn = torch.tensor(dyn, dtype=torch.float32)
        t_stat = torch.tensor(stat, dtype=torch.float32)
        t_pvt = torch.tensor(pvt_vec, dtype=torch.float32)
        with torch.no_grad():
            preds = np.stack([
                p_init + net(t_dyn, t_stat, t_pvt).numpy()[0] * PRESSURE_SCALE
                for net in self._nets
            ])  # (n_models, T)
        return preds.mean(axis=0), preds.min(axis=0), preds.max(axis=0)

    def baseline(self, history: pd.DataFrame, static: dict) -> np.ndarray:
        # interpola/recorta la curva de caída promedio del train al largo del input
        p_init = static["presion_inicial_psi"]
        src = self._mean_delta
        idx = np.linspace(0, len(src) - 1, len(history))
        return p_init + np.interp(idx, np.arange(len(src)), src)


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
