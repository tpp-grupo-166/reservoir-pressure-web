"""Modelo LSTM del notebook 5: ensemble de 5 seeds + encoder de PVT.

Inferencia y entrenamiento del modelo que sirve la API por default. La arquitectura
está en `models/lstm_net.py` (separada para que torch se importe recién acá adentro).

Entrenar (ver README, "Entrenar y activar el modelo real"):
    cd api && python train.py --model lstm

Genera `artifacts/lstm.pt` con: pesos del ensemble, dimensiones de la arquitectura,
parámetros de los z-score scalers (ajustados solo con train), la curva de delta promedio
del baseline, y las métricas de evaluación. Reentrenar es idempotente (seed fija).

Entrena con Norne (split por simulación: 24 train / 6 test). El feature engineering se
toma de `features.py` (la misma fuente que usa la API → paridad train/serving garantizada).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from features import (DYNAMIC_COLUMNS, PRESSURE_SCALE, STATIC_COLUMNS,
                      build_features, build_pvt_vector)
from models.base import Model, baseline_from_curve
from models.datasets import (NORNE_URL, PVT_NORNE_URL, TARGET, TEST_SIMS,
                             TRAIN_SIMS, read_url, static_from_raw)

ARTIFACT = Path(__file__).parent.parent / "artifacts" / "lstm.pt"
# nombre que usaba el artefacto antes del registry; se sigue leyendo para no
# degradar al stub un checkout que ya tenía el modelo entrenado
LEGACY_ARTIFACT = ARTIFACT.with_name("model.pt")

N_EPOCHS, LR, WEIGHT_DECAY = 30, 1e-3, 1e-3
SEEDS = [0, 1, 2, 7, 42]   # ensemble: la dispersión entre seeds da la banda de incertidumbre


class LSTMModel(Model):
    """Ensemble de 5 LSTM + encoder de PVT del notebook 5."""

    name = "lstm"

    def __init__(self) -> None:
        self._nets = []
        self._scaler_dynamic = None
        self._scaler_static = None
        self._mean_delta = None

    def load(self) -> bool:
        path = ARTIFACT if ARTIFACT.exists() else LEGACY_ARTIFACT
        if not path.exists():
            return False
        import torch

        from models.lstm_net import LSTMPVT

        art = torch.load(path, map_location="cpu", weights_only=False)
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
        return baseline_from_curve(static["presion_inicial_psi"], self._mean_delta,
                                   len(history))

    def train(self) -> None:
        import torch

        norne = read_url(NORNE_URL)
        pvt = read_url(PVT_NORNE_URL)
        min_len = int(norne.groupby("sim_id").size().min())
        print(f"Norne: {norne.sim_id.nunique()} sims, truncado a {min_len} timesteps")

        Xtr, ytr = _prepare(norne, pvt, TRAIN_SIMS, min_len)
        Xte, yte = _prepare(norne, pvt, TEST_SIMS, min_len)

        # scalers (solo train), aplicados como (x - mean) / scale
        dyn_mean, dyn_scale = _fit_scaler(Xtr["dynamic"].reshape(-1, Xtr["dynamic"].shape[-1]))
        stat_mean, stat_scale = _fit_scaler(Xtr["static"])

        def scaled_tensors(X):
            d = (X["dynamic"] - dyn_mean) / dyn_scale
            s = (X["static"] - stat_mean) / stat_scale
            return (torch.tensor(d, dtype=torch.float32),
                    torch.tensor(s, dtype=torch.float32),
                    torch.tensor(X["pvt"], dtype=torch.float32))

        d_tr, s_tr, p_tr = scaled_tensors(Xtr)
        pinit_tr = Xtr["initial_pressure"][:, None]
        delta_tr = torch.tensor((ytr - pinit_tr) / PRESSURE_SCALE, dtype=torch.float32)
        d_te, s_te, p_te = scaled_tensors(Xte)
        pinit_te = Xte["initial_pressure"][:, None]

        # ensemble: un modelo por seed; la dispersión entre ellos es la banda de incertidumbre
        state_dicts, r2s, maes = [], [], []
        for seed in SEEDS:
            sd, model = _train_one(seed, d_tr, s_tr, p_tr, delta_tr, Xtr["pvt"].shape[1])
            state_dicts.append(sd)
            with torch.no_grad():
                pred_te = pinit_te + model(d_te, s_te, p_te).numpy() * PRESSURE_SCALE
            m = _metrics(yte, pred_te)
            r2s.append(m["R2_medio"]); maes.append(m["MAE_psi"])
            print(f"  seed {seed:2d}: test R2={m['R2_medio']}  MAE={m['MAE_psi']} psi")

        metrics = dict(R2_medio=round(float(np.mean(r2s)), 4),
                       R2_std=round(float(np.std(r2s)), 4),
                       MAE_psi=round(float(np.mean(maes)), 1))
        print(f"ensemble ({len(SEEDS)} seeds): R2={metrics['R2_medio']}±{metrics['R2_std']}  "
              f"MAE={metrics['MAE_psi']} psi")

        mean_delta = (ytr - Xtr["initial_pressure"][:, None]).mean(axis=0)  # baseline

        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "state_dicts": state_dicts,
            "arch": dict(pvt_dim=Xtr["pvt"].shape[1], n_dynamic=len(DYNAMIC_COLUMNS),
                         n_static=len(STATIC_COLUMNS), context_dim=16, hidden_size=64),
            "scaler_dynamic": dict(mean=dyn_mean, scale=dyn_scale),
            "scaler_static": dict(mean=stat_mean, scale=stat_scale),
            "mean_delta_curve": mean_delta.astype(np.float32),
            "metrics": metrics,
            "version": "lstm-pvt-notebook5-v1",
            "note": (f"Ensemble de {len(SEEDS)} LSTM + encoder de PVT entrenados en Norne "
                     "(sims 1-24). Métricas = test Norne (sims 25-30), media±std entre seeds. "
                     "El transfer cross-reservoir es más variable (ver auditoría): preliminar."),
        }, ARTIFACT)
        print(f"artefacto guardado en {ARTIFACT}")


def _prepare(raw: pd.DataFrame, pvt: pd.DataFrame, sim_ids: list[int], min_len: int):
    """Apila las sims en tensores RAW (dynamic, static, pvt, P_init) + el target y."""
    dyn, stat, pinit, ys = [], [], [], []
    pvt_vec = build_pvt_vector(pvt)
    for sid in sim_ids:
        sim = raw[raw.sim_id == sid].sort_values("tiempo_dias").head(min_len)
        static = static_from_raw(sim)
        feats = build_features(sim, static, pvt)
        dyn.append(feats[DYNAMIC_COLUMNS].to_numpy())
        stat.append(feats[STATIC_COLUMNS].iloc[0].to_numpy())
        pinit.append(static["presion_inicial_psi"])
        ys.append(sim[TARGET].to_numpy()[:min_len])
    X = dict(
        dynamic=np.stack(dyn).astype(np.float32),
        static=np.stack(stat).astype(np.float32),
        pvt=np.tile(pvt_vec, (len(sim_ids), 1)),
        initial_pressure=np.array(pinit, dtype=np.float32),
    )
    return X, np.stack(ys).astype(np.float32)


def _fit_scaler(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve (mean, scale) por columna; scale=1 donde el desvío es 0."""
    mean = arr.mean(axis=0)
    scale = arr.std(axis=0)
    scale[scale == 0] = 1.0
    return mean, scale


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    yt, yp = y_true.ravel(), y_pred.ravel()
    ss_res = float(((yt - yp) ** 2).sum())
    ss_tot = float(((yt - yt.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    mae = float(np.abs(yt - yp).mean())
    return dict(R2_medio=round(r2, 4), R2_std=0.0, MAE_psi=round(mae, 1))


def _train_one(seed: int, d_tr, s_tr, p_tr, delta_tr, pvt_dim: int):
    """Entrena un modelo con una seed y devuelve (state_dict, modelo)."""
    import torch
    from torch import nn

    from models.lstm_net import LSTMPVT

    torch.manual_seed(seed)
    np.random.seed(seed)
    model = LSTMPVT(pvt_dim=pvt_dim)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=N_EPOCHS)
    for _ in range(N_EPOCHS):
        loss = nn.functional.mse_loss(model(d_tr, s_tr, p_tr), delta_tr)
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    model.eval()
    return model.state_dict(), model
