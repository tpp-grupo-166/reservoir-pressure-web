"""Modelo Ridge del notebook 6: regresión lineal sobre features de superficie.

El control data-driven más simple del proyecto. Predice el delta de presión
(P − P_init) por timestep, cada fila por separado, desde las features de superficie
de `features.py` pero SIN el vector PVT (el notebook 6 lo descarta: es casi constante
entre sims y los modelos pointwise no lo aprovechan). Pipeline del notebook 6:
StandardScaler + Ridge con alpha elegido por GroupKFold sobre las sims de train.

Entrenar (rápido, segundos): cd api && python train.py --model ridge

A diferencia del LSTM no hay ensemble del cual derivar incertidumbre: la banda es
±1.96·std de los residuos de la cross-validation por sim en train (global, nominal).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from features import DYNAMIC_COLUMNS, STATIC_COLUMNS, build_features
from models.base import Model, baseline_from_curve
from models.datasets import (NORNE_URL, PVT_NORNE_URL, TEST_SIMS, TRAIN_SIMS,
                             mean_delta_curve, pointwise_rows, read_url)

ARTIFACT = Path(__file__).parent.parent / "artifacts" / "ridge.joblib"

FEATURE_COLUMNS = DYNAMIC_COLUMNS + STATIC_COLUMNS
ALPHAS = [1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0]


class RidgeModel(Model):
    """StandardScaler + Ridge pointwise sobre features de superficie (notebook 6)."""

    name = "ridge"

    def __init__(self) -> None:
        self._pipeline = None
        self._band_halfwidth = 0.0
        self._mean_delta = None

    def load(self) -> bool:
        if not ARTIFACT.exists():
            return False
        import joblib

        art = joblib.load(ARTIFACT)
        self._pipeline = art["pipeline"]
        self._band_halfwidth = float(art["band_halfwidth_psi"])
        self._mean_delta = np.asarray(art["mean_delta_curve"], dtype=np.float64)
        self.version = art["version"]
        self.metrics = art["metrics"]
        self.note = art["note"]
        return True

    def predict_band(self, history: pd.DataFrame, static: dict, pvt: pd.DataFrame):
        feats = build_features(history, static, pvt)
        delta = self._pipeline.predict(feats[FEATURE_COLUMNS].to_numpy())
        pred = static["presion_inicial_psi"] + delta
        return pred, pred - self._band_halfwidth, pred + self._band_halfwidth

    def baseline(self, history: pd.DataFrame, static: dict) -> np.ndarray:
        return baseline_from_curve(static["presion_inicial_psi"], self._mean_delta,
                                   len(history))

    def train(self) -> None:
        import joblib
        from sklearn.linear_model import Ridge
        from sklearn.model_selection import (GridSearchCV, GroupKFold,
                                             cross_val_predict)
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        norne = read_url(NORNE_URL)
        pvt = read_url(PVT_NORNE_URL)
        print(f"Norne: {norne.sim_id.nunique()} sims")

        Xtr, ytr, gtr = pointwise_rows(norne, pvt, TRAIN_SIMS, FEATURE_COLUMNS)
        Xte, yte, _ = pointwise_rows(norne, pvt, TEST_SIMS, FEATURE_COLUMNS)

        # alpha por GroupKFold sobre las sims de train (mismo protocolo que el notebook 6)
        gkf = GroupKFold(n_splits=min(5, len(set(gtr))))
        gs = GridSearchCV(make_pipeline(StandardScaler(), Ridge()),
                          {"ridge__alpha": ALPHAS}, cv=gkf, scoring="r2")
        gs.fit(Xtr, ytr, groups=gtr)
        pipeline = gs.best_estimator_
        alpha = gs.best_params_["ridge__alpha"]

        # banda: residuos out-of-fold en train (la CV agrupa por sim, no mezcla series)
        cv_pred = cross_val_predict(gs.best_estimator_, Xtr, ytr, cv=gkf, groups=gtr)
        band = 1.96 * float(np.std(ytr - cv_pred))

        pred_te = pipeline.predict(Xte)
        ss_res = float(((yte - pred_te) ** 2).sum())
        ss_tot = float(((yte - yte.mean()) ** 2).sum())
        metrics = dict(R2_medio=round(1.0 - ss_res / ss_tot, 4), R2_std=0.0,
                       MAE_psi=round(float(np.abs(yte - pred_te).mean()), 1))
        print(f"alpha={alpha:g}  test R2={metrics['R2_medio']}  MAE={metrics['MAE_psi']} psi")

        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "pipeline": pipeline,
            "band_halfwidth_psi": band,
            "mean_delta_curve": mean_delta_curve(norne, TRAIN_SIMS).astype(np.float32),
            "metrics": metrics,
            "version": "ridge-notebook6-v1",
            "note": (f"Ridge pointwise (alpha={alpha:g}) sobre features de superficie, "
                     "sin PVT, entrenado en Norne (sims 1-24). Métricas = test Norne "
                     "(sims 25-30). Control simple: el transfer cross-reservoir es malo "
                     "(ver notebook 6/LOFO). Banda = ±1.96·std de residuos de CV."),
        }, ARTIFACT)
        print(f"artefacto guardado en {ARTIFACT}")
