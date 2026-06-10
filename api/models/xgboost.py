"""Modelo XGBoost del notebook 6: boosting de árboles sobre features de superficie.

Mismo planteo pointwise que el Ridge (delta = P − P_init por timestep, features de
superficie sin el vector PVT) pero con árboles: captura no linealidades dentro del
dominio de entrenamiento. Hiperparámetros tal cual el notebook 6; los árboles no
necesitan escalado, así que no hay pipeline con scaler.

Entrenar (rápido, segundos): cd api && python train.py --model xgboost

Como en el Ridge, la banda es ±1.96·std de los residuos de la cross-validation por
sim en train (global, nominal): un solo modelo, sin ensemble del cual derivar
incertidumbre.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from features import DYNAMIC_COLUMNS, STATIC_COLUMNS, build_features
from models.base import Model, baseline_from_curve
from models.datasets import (NORNE_URL, PVT_NORNE_URL, TEST_SIMS, TRAIN_SIMS,
                             mean_delta_curve, pointwise_rows, read_url)

ARTIFACT = Path(__file__).parent.parent / "artifacts" / "xgboost.joblib"

FEATURE_COLUMNS = DYNAMIC_COLUMNS + STATIC_COLUMNS
# hiperparámetros del notebook 6
XGB_PARAMS = dict(n_estimators=400, max_depth=6, learning_rate=0.05,
                  subsample=0.8, colsample_bytree=0.8, random_state=0)


class XGBoostModel(Model):
    """XGBRegressor pointwise sobre features de superficie (notebook 6)."""

    name = "xgboost"

    def __init__(self) -> None:
        self._regressor = None
        self._band_halfwidth = 0.0
        self._mean_delta = None

    def load(self) -> bool:
        if not ARTIFACT.exists():
            return False
        import joblib

        art = joblib.load(ARTIFACT)
        self._regressor = art["regressor"]
        self._band_halfwidth = float(art["band_halfwidth_psi"])
        self._mean_delta = np.asarray(art["mean_delta_curve"], dtype=np.float64)
        self.version = art["version"]
        self.metrics = art["metrics"]
        self.note = art["note"]
        return True

    def predict_band(self, history: pd.DataFrame, static: dict, pvt: pd.DataFrame):
        feats = build_features(history, static, pvt)
        delta = self._regressor.predict(feats[FEATURE_COLUMNS].to_numpy())
        pred = static["presion_inicial_psi"] + delta
        return pred, pred - self._band_halfwidth, pred + self._band_halfwidth

    def baseline(self, history: pd.DataFrame, static: dict) -> np.ndarray:
        return baseline_from_curve(static["presion_inicial_psi"], self._mean_delta,
                                   len(history))

    def train(self) -> None:
        import joblib
        from sklearn.model_selection import GroupKFold, cross_val_predict
        from xgboost import XGBRegressor

        norne = read_url(NORNE_URL)
        pvt = read_url(PVT_NORNE_URL)
        print(f"Norne: {norne.sim_id.nunique()} sims")

        Xtr, ytr, gtr = pointwise_rows(norne, pvt, TRAIN_SIMS, FEATURE_COLUMNS)
        Xte, yte, _ = pointwise_rows(norne, pvt, TEST_SIMS, FEATURE_COLUMNS)

        regressor = XGBRegressor(**XGB_PARAMS)
        regressor.fit(Xtr, ytr)

        # banda: residuos out-of-fold en train (la CV agrupa por sim, no mezcla series)
        gkf = GroupKFold(n_splits=min(5, len(set(gtr))))
        cv_pred = cross_val_predict(XGBRegressor(**XGB_PARAMS), Xtr, ytr,
                                    cv=gkf, groups=gtr)
        band = 1.96 * float(np.std(ytr - cv_pred))

        pred_te = regressor.predict(Xte)
        ss_res = float(((yte - pred_te) ** 2).sum())
        ss_tot = float(((yte - yte.mean()) ** 2).sum())
        metrics = dict(R2_medio=round(1.0 - ss_res / ss_tot, 4), R2_std=0.0,
                       MAE_psi=round(float(np.abs(yte - pred_te).mean()), 1))
        print(f"test R2={metrics['R2_medio']}  MAE={metrics['MAE_psi']} psi")

        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "regressor": regressor,
            "band_halfwidth_psi": band,
            "mean_delta_curve": mean_delta_curve(norne, TRAIN_SIMS).astype(np.float32),
            "metrics": metrics,
            "version": "xgboost-notebook6-v1",
            "note": ("XGBoost pointwise sobre features de superficie, sin PVT, entrenado "
                     "en Norne (sims 1-24). Métricas = test Norne (sims 25-30). Como el "
                     "Ridge, el transfer cross-reservoir es malo (ver notebook 6/LOFO). "
                     "Banda = ±1.96·std de residuos de CV."),
        }, ARTIFACT)
        print(f"artefacto guardado en {ARTIFACT}")
