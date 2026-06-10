"""Tests del registry de modelos enchufables y del dispatch del Predictor."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import model
import models.pinn
import models.ridge
import models.xgboost
from models.registry import available, get_model
from models.stub import StubModel

STATIC = dict(porosidad=0.24, permeabilidad_mD=400.0, espesor_neto_m=170.0,
              area_m2=1.6e7, presion_inicial_psi=4100.0)


def _history(n: int = 50) -> pd.DataFrame:
    return pd.DataFrame({
        "tiempo_dias": np.arange(1, n + 1, dtype=float),
        "Caudal_Prod_Petroleo_bbl": np.full(n, 1000.0),
        "Caudal_Iny_Agua_bbl": np.full(n, 800.0),
        "Prod_Acumulada_Petroleo": np.cumsum(np.full(n, 1000.0)),
        "Prod_Acumulada_Gas": np.cumsum(np.full(n, 1.5e6)),
        "Prod_Acumulada_Agua": np.cumsum(np.full(n, 200.0)),
        "Iny_Acumulada_Agua": np.cumsum(np.full(n, 800.0)),
    })


def _pvt() -> pd.DataFrame:
    p = np.arange(1500, 5501, 250, dtype=float)
    return pd.DataFrame({
        "p_grid_psi": p,
        "bo_rb_stb": np.full(len(p), 1.12),
        "bg_rb_scf": np.full(len(p), 0.0006),
        "rs_scf_stb": np.full(len(p), 1500.0),
    })


@pytest.fixture
def fresh_predictor():
    """Resetea el singleton para que cada test arme su propio Predictor."""
    model.Predictor._instance = None
    yield
    model.Predictor._instance = None


def test_registry_resolves_by_name():
    assert isinstance(get_model("stub"), StubModel)
    assert get_model("inexistente") is None
    assert {"stub", "lstm", "ridge", "xgboost", "pinn"} <= set(available())


def _artifact(name):
    return {"ridge": models.ridge.ARTIFACT, "xgboost": models.xgboost.ARTIFACT,
            "pinn": models.pinn.ARTIFACT}[name]


@pytest.mark.parametrize("name", ["ridge", "xgboost", "pinn"])
def test_trained_model_contract(name):
    if not _artifact(name).exists():
        pytest.skip(f"sin artefacto {name} (correr train.py --model {name})")
    m = get_model(name)
    assert m.load() is True
    n = 50
    pred, lower, upper = m.predict_band(_history(n), STATIC, _pvt())
    base = m.baseline(_history(n), STATIC)
    assert len(pred) == len(lower) == len(upper) == len(base) == n
    assert (lower <= pred + 1e-6).all() and (pred <= upper + 1e-6).all()
    assert m.version.startswith(name)


def test_stub_contract():
    stub = StubModel()
    assert stub.load() is True
    n = 50
    pred, lower, upper = stub.predict_band(_history(n), STATIC, _pvt())
    base = stub.baseline(_history(n), STATIC)
    assert len(pred) == len(lower) == len(upper) == len(base) == n
    assert (lower <= upper).all()
    assert base[0] == pytest.approx(STATIC["presion_inicial_psi"])


def test_predictor_serves_model_from_env(fresh_predictor, monkeypatch):
    monkeypatch.setenv("MODEL", "stub")
    p = model.Predictor.instance()
    assert p.ready and p.mode == "stub"
    assert p.version == "stub-v0"


def test_predictor_falls_back_on_unknown_model(fresh_predictor, monkeypatch):
    monkeypatch.setenv("MODEL", "inexistente")
    p = model.Predictor.instance()
    assert p.ready and p.mode == "stub"
    assert "no registrado" in p.note
