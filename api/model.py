"""Carga e inferencia del modelo.

`Predictor` carga el artefacto entrenado (`artifacts/model.pt`) si existe; si no, cae a un
**stub** físicamente plausible para que el front se pueda desarrollar sin modelo. Generar el
artefacto: `python train.py` (ver README, "Entrenar y activar el modelo real").
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from features import (DYNAMIC_COLUMNS, PRESSURE_SCALE, STATIC_COLUMNS,
                      build_features, build_pvt_vector)

ARTIFACT = Path(__file__).parent / "artifacts" / "model.pt"

# Defaults del stub (cuando no hay artefacto entrenado).
STUB_VERSION = "stub-v0"
STUB_METRICS = dict(R2_medio=0.0, R2_std=0.0, MAE_psi=0.0)
STUB_NOTE = ("STUB de desarrollo: no es el modelo entrenado. Devuelve una trayectoria "
             "derivada de un voidage de superficie crudo. Correr `python train.py` para "
             "activar el LSTM real.")


class Predictor:
    """Singleton de inferencia. `load()` se llama una vez al levantar la API."""

    _instance: "Predictor | None" = None

    def __init__(self) -> None:
        self.ready = False
        self.mode = "stub"
        self.version = STUB_VERSION
        self.metrics = STUB_METRICS
        self.note = STUB_NOTE
        self._nets = []
        self._scaler_dynamic = None
        self._scaler_static = None
        self._mean_delta = None

    @classmethod
    def instance(cls) -> "Predictor":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load()
        return cls._instance

    def load(self) -> None:
        """Carga el artefacto si existe y torch está disponible; si no, queda en modo stub."""
        if ARTIFACT.exists():
            try:
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
                self.mode = "model"
            except Exception as exc:
                self.note = f"{STUB_NOTE} (fallo al cargar el artefacto: {exc})"
                self.mode = "stub"
        self.ready = True

    def predict_band(self, history: pd.DataFrame, static: dict, pvt: pd.DataFrame):
        """Devuelve (estimada, banda_inferior, banda_superior) en psi, por timestep.

        En modo modelo, la banda es el min/max del ensemble de seeds (incertidumbre real).
        En modo stub, una banda nominal de ±3% alrededor del proxy.
        """
        feats = build_features(history, static, pvt)
        p_init = static["presion_inicial_psi"]

        if self.mode == "model":
            import torch

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

        # stub: voidage de superficie crudo como proxy de la caída
        net_surface = (feats["Np_over_PV"] + feats["Wp_over_PV"] - feats["Winj_over_PV"]).to_numpy()
        mean = p_init + (-0.6 * net_surface * PRESSURE_SCALE)
        return mean, mean * 0.97, mean * 1.03

    def baseline(self, history: pd.DataFrame, static: dict) -> np.ndarray:
        """Curva de caída promedio del entrenamiento, anclada al P_init del input."""
        p_init = static["presion_inicial_psi"]
        n = len(history)
        if self.mode == "model" and self._mean_delta is not None:
            # interpola/recorta la curva promedio al largo de la serie del usuario
            src = self._mean_delta
            idx = np.linspace(0, len(src) - 1, n)
            return p_init + np.interp(idx, np.arange(len(src)), src)
        return p_init + np.linspace(0.0, -150.0, n)  # stub
