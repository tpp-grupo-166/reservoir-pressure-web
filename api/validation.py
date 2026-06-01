"""Validación de los datos de entrada y registro de la explicabilidad.

Toda corrección/filtrado se registra en `cleaning` para devolverse al usuario.
"""
from __future__ import annotations

import io

import pandas as pd

REQUIRED_HISTORY_COLUMNS = [
    "tiempo_dias",
    "Caudal_Prod_Petroleo_bbl",
    "Caudal_Iny_Agua_bbl",
    "Prod_Acumulada_Petroleo",
    "Prod_Acumulada_Gas",
    "Prod_Acumulada_Agua",
    "Iny_Acumulada_Agua",
]
REQUIRED_PVT_COLUMNS = ["p_grid_psi", "bo_rb_stb", "bg_rb_scf", "rs_scf_stb"]


class ValidationError(ValueError):
    """Error de datos de entrada (→ HTTP 422)."""


def read_csv(content: bytes) -> pd.DataFrame:
    try:
        return pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise ValidationError(f"No se pudo leer el CSV: {exc}") from exc


def validate_history(df: pd.DataFrame) -> tuple[list[str], list[dict]]:
    """Valida la historia de producción. Devuelve (advertencias, pasos_de_limpieza)."""
    missing = [c for c in REQUIRED_HISTORY_COLUMNS if c not in df.columns]
    if missing:
        raise ValidationError(f"Faltan columnas en la historia de producción: {missing}")

    warnings: list[str] = []
    cleaning: list[dict] = []

    if not df["tiempo_dias"].is_monotonic_increasing:
        warnings.append("`tiempo_dias` no es estrictamente creciente; se ordenó por tiempo.")

    # Los chequeos de acumuladas se hacen sobre los datos YA ORDENADOS por tiempo:
    # si se evaluaran sobre el orden crudo, un input desordenado dispararía falsos
    # "tramos decrecientes" que en realidad son saltos hacia atrás en el tiempo.
    ordered = df.sort_values("tiempo_dias")
    for col in ["Prod_Acumulada_Petroleo", "Prod_Acumulada_Agua", "Iny_Acumulada_Agua"]:
        if (ordered[col].diff().dropna() < 0).any():
            warnings.append(f"`{col}` tiene tramos decrecientes (¿acumulada mal calculada?).")

    for col in REQUIRED_HISTORY_COLUMNS:
        n_nan = int(df[col].isna().sum())
        if n_nan:
            cleaning.append(dict(accion="reemplazo NaN→0", columna=col, filas=n_nan,
                                 motivo="valor faltante en columna requerida"))
    return warnings, cleaning


def validate_pvt(df: pd.DataFrame, p_init: float) -> list[str]:
    missing = [c for c in REQUIRED_PVT_COLUMNS if c not in df.columns]
    if missing:
        raise ValidationError(f"Faltan columnas en la tabla PVT: {missing}")

    warnings: list[str] = []
    lo, hi = df["p_grid_psi"].min(), df["p_grid_psi"].max()
    if not (lo <= p_init <= hi):
        warnings.append(
            f"La tabla PVT cubre {lo:.0f}–{hi:.0f} psi pero la presión inicial es "
            f"{p_init:.0f} psi: se extrapoló (revisar el rango de la tabla)."
        )
    return warnings
