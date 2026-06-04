"""Test del caso de ejemplo (`sample-data/`) que carga el botón del wizard.

si cambian los CSV de ejemplo o el feature engineering, este test
avisa que el botón "Cargar caso de ejemplo" dejó de producir
una predicción válida. Correr con: cd api && pytest -q
"""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "sample-data"
HISTORY = SAMPLE_DIR / "produccion_ejemplo.csv"
PVT = SAMPLE_DIR / "pvt_ejemplo.csv"
TOML = SAMPLE_DIR / "reservorio_ejemplo.toml"


def _static_from_toml() -> dict:
    """Propiedades estáticas del ejemplo, leídas del TOML para no duplicar valores."""
    return tomllib.loads(TOML.read_text())["reservorio"]


def test_sample_files_exist():
    assert HISTORY.exists(), HISTORY
    assert PVT.exists(), PVT
    assert TOML.exists(), TOML


def test_predict_with_example_files():
    """El caso de ejemplo produce una trayectoria válida vía `static_props` (lo que manda el botón)."""
    static = _static_from_toml()
    n_rows = len(pd.read_csv(HISTORY))
    resp = client.post(
        "/api/predict",
        files={"history_csv": ("produccion_ejemplo.csv", HISTORY.read_bytes(), "text/csv"),
               "pvt_csv": ("pvt_ejemplo.csv", PVT.read_bytes(), "text/csv")},
        data={"static_props": json.dumps(static)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    pred = body["prediction"]
    # La trayectoria (y su baseline) cubren toda la historia de producción.
    assert len(pred["presion_estimada_psi"]) == n_rows
    assert len(body["baseline"]["presion_psi"]) == n_rows
    # La presión inicial se respeta y la explicabilidad trae features.
    assert pred["presion_inicial_psi"] == static["presion_inicial_psi"]
    assert body["explainability"]["features_construidos"]


def test_predict_with_example_toml():
    """El TOML de ejemplo también se acepta como propiedades del reservorio."""
    resp = client.post(
        "/api/predict",
        files={"history_csv": ("produccion_ejemplo.csv", HISTORY.read_bytes(), "text/csv"),
               "pvt_csv": ("pvt_ejemplo.csv", PVT.read_bytes(), "text/csv"),
               "static_toml": ("reservorio_ejemplo.toml", TOML.read_bytes(), "application/toml")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["prediction"]["presion_inicial_psi"] == _static_from_toml()["presion_inicial_psi"]
