"""Smoke tests del backend. Correr con: cd api && pytest -q"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _history_csv() -> bytes:
    n = 50
    t = np.arange(1, n + 1, dtype=float)
    df = pd.DataFrame({
        "tiempo_dias": t,
        "Caudal_Prod_Petroleo_bbl": np.full(n, 1000.0),
        "Caudal_Iny_Agua_bbl": np.full(n, 800.0),
        "Prod_Acumulada_Petroleo": np.cumsum(np.full(n, 1000.0)),
        "Prod_Acumulada_Gas": np.cumsum(np.full(n, 1.5e6)),
        "Prod_Acumulada_Agua": np.cumsum(np.full(n, 200.0)),
        "Iny_Acumulada_Agua": np.cumsum(np.full(n, 800.0)),
    })
    return df.to_csv(index=False).encode()


def _pvt_csv() -> bytes:
    p = np.arange(1500, 5501, 250, dtype=float)
    df = pd.DataFrame({
        "p_grid_psi": p,
        "bo_rb_stb": np.full(len(p), 1.12),
        "bg_rb_scf": np.full(len(p), 0.0006),
        "rs_scf_stb": np.full(len(p), 1500.0),
    })
    return df.to_csv(index=False).encode()


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_predict_shape():
    static = dict(porosidad=0.24, permeabilidad_mD=400.0, espesor_neto_m=170.0,
                  area_m2=1.6e7, presion_inicial_psi=4100.0)
    resp = client.post(
        "/api/predict",
        files={"history_csv": ("h.csv", _history_csv(), "text/csv"),
               "pvt_csv": ("pvt.csv", _pvt_csv(), "text/csv")},
        data={"static_props": json.dumps(static)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["prediction"]["presion_estimada_psi"]) == 50
    assert len(body["baseline"]["presion_psi"]) == 50
    assert body["prediction"]["presion_inicial_psi"] == 4100.0
    assert body["explainability"]["features_construidos"]


def test_unsorted_input_no_false_cumulative_warning():
    """Input desordenado en el tiempo pero con acumuladas correctas:
    debe avisar solo del orden, NO disparar falsos 'tramos decrecientes'."""
    df = pd.read_csv(__import__("io").BytesIO(_history_csv())).sample(
        frac=1.0, random_state=1)  # baraja las filas
    resp = client.post(
        "/api/validate",
        files={"history_csv": ("h.csv", df.to_csv(index=False).encode(), "text/csv")},
    )
    assert resp.status_code == 200, resp.text
    warns = resp.json()["advertencias"]
    assert any("tiempo_dias" in w for w in warns)
    assert not any("decrecientes" in w for w in warns)


def test_predict_with_toml():
    """Las propiedades del reservorio se pueden pasar como archivo TOML."""
    toml = b"""
[reservorio]
porosidad = 0.239
permeabilidad_mD = 2353.78
espesor_neto_m = 77.75
area_m2 = 6796200.0
presion_inicial_psi = 4773.49
"""
    resp = client.post(
        "/api/predict",
        files={"history_csv": ("h.csv", _history_csv(), "text/csv"),
               "pvt_csv": ("pvt.csv", _pvt_csv(), "text/csv"),
               "static_toml": ("r.toml", toml, "application/toml")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["prediction"]["presion_inicial_psi"] == 4773.49


def test_predict_no_static_props():
    """Sin static_props ni static_toml → 422 con mensaje claro."""
    resp = client.post(
        "/api/predict",
        files={"history_csv": ("h.csv", _history_csv(), "text/csv"),
               "pvt_csv": ("pvt.csv", _pvt_csv(), "text/csv")},
    )
    assert resp.status_code == 422


def test_predict_missing_column():
    bad = pd.read_csv(__import__("io").BytesIO(_history_csv())).drop(columns=["Iny_Acumulada_Agua"])
    static = dict(porosidad=0.24, permeabilidad_mD=400.0, espesor_neto_m=170.0,
                  area_m2=1.6e7, presion_inicial_psi=4100.0)
    resp = client.post(
        "/api/predict",
        files={"history_csv": ("h.csv", bad.to_csv(index=False).encode(), "text/csv"),
               "pvt_csv": ("pvt.csv", _pvt_csv(), "text/csv")},
        data={"static_props": json.dumps(static)},
    )
    assert resp.status_code == 422
