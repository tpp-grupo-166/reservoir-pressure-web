"""Datos de entrenamiento compartidos por los modelos (repo del equipo).

Los datasets salen de `consistentes/`: la PVT de `datasets/` (y del upstream
ricomateo/opm-proof-of-concept) fue editada después de simular y quedó inconsistente
con las presiones (ver datasets/consistentes/README.md en tpp-grupo-166/opm-datasets).

El split por simulación de Norne es el MISMO para todos los modelos, para que las
métricas que expone `/api/model-info` sean comparables entre ellos.
"""
from __future__ import annotations

import io
import urllib.request

import numpy as np
import pandas as pd

BASE = "https://raw.githubusercontent.com/tpp-grupo-166/opm-datasets/main/datasets"
NORNE_URL = f"{BASE}/consistentes/dataset_norne.csv"
VOLVE_URL = f"{BASE}/consistentes/dataset_volve.csv"
SPE9_URL = f"{BASE}/consistentes/dataset_spe9.csv"
PVT_NORNE_URL = f"{BASE}/pvt_norne.csv"
TARGET = "Presion_Reservorio_psi"

TRAIN_SIMS, TEST_SIMS = list(range(1, 25)), list(range(25, 31))


def read_url(url: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(urllib.request.urlopen(url).read()))


def pointwise_rows(raw: pd.DataFrame, pvt: pd.DataFrame, sim_ids: list[int],
                   columns: list[str]):
    """Apila filas (X, delta, grupo=sim) de las sims pedidas; delta = P − P_init.

    Prep común de los modelos pointwise (Ridge, XGBoost): cada timestep es una fila
    independiente con las `columns` que el modelo declara.
    """
    from features import build_features

    xs, ys, gs = [], [], []
    for sid in sim_ids:
        sim = raw[raw.sim_id == sid].sort_values("tiempo_dias")
        static = static_from_raw(sim)
        feats = build_features(sim, static, pvt)
        xs.append(feats[columns].to_numpy())
        ys.append(sim[TARGET].to_numpy() - static["presion_inicial_psi"])
        gs.append(np.full(len(sim), sid))
    return np.vstack(xs), np.concatenate(ys), np.concatenate(gs)


def mean_delta_curve(raw: pd.DataFrame, sim_ids: list[int]):
    """Curva de caída promedio (P − P_init) de las sims pedidas, para el baseline.

    Truncada al largo de la sim más corta; cada artefacto la guarda y la sirve
    `baseline_from_curve`.
    """
    min_len = int(raw[raw.sim_id.isin(sim_ids)].groupby("sim_id").size().min())
    deltas = []
    for sid in sim_ids:
        sim = raw[raw.sim_id == sid].sort_values("tiempo_dias").head(min_len)
        p = sim[TARGET].to_numpy()
        deltas.append(p - p[0])
    return np.stack(deltas).mean(axis=0)


def static_from_raw(sim_df: pd.DataFrame) -> dict:
    """Propiedades estáticas de una sim en el formato que espera `build_features`.

    P_init = primera presión de la sim (los CSV consistentes no traen la columna
    `Presion_Inicial_Reservorio_psi`; en los editados era exactamente este valor).
    """
    r = sim_df.iloc[0]
    return dict(porosidad=float(r["Porosidad"]),
                permeabilidad_mD=float(r["Permeabilidad_mD"]),
                espesor_neto_m=float(r["Espesor_Neto_m"]),
                area_m2=float(r["Area"]),
                presion_inicial_psi=float(r["Presion_Reservorio_psi"]))
