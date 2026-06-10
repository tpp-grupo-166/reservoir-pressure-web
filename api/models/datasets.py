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

import pandas as pd

BASE = "https://raw.githubusercontent.com/tpp-grupo-166/opm-datasets/main/datasets"
NORNE_URL = f"{BASE}/consistentes/dataset_norne.csv"
PVT_NORNE_URL = f"{BASE}/pvt_norne.csv"
TARGET = "Presion_Reservorio_psi"

TRAIN_SIMS, TEST_SIMS = list(range(1, 25)), list(range(25, 31))


def read_url(url: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(urllib.request.urlopen(url).read()))


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
