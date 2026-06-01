"""Feature engineering — ÚNICA fuente de verdad (ver README "Cómo cambiar el modelo").

El back lo usa para inferencia y cualquier script (raíz, /audit) debería importar de acá
en vez de duplicarlo.

Reproduce el feature engineering del modelo del notebook 5 (LSTM + encoder de PVT):
  - 9 features dinámicos adimensionales (normalizados por el volumen poral),
  - 3 estáticos (porosidad, log-permeabilidad, presión inicial normalizada),
  - la tabla PVT completa como vector de contexto de 51 dimensiones.

La tabla PVT entra como vector fijo por simulación (no se evalúa a la presión actual del
reservorio), que es lo que evita el leakage del target.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

M3_TO_BBL = 6.28981
PRESSURE_SCALE = 5000.0

# Grid de presión canónico sobre el que el modelo espera la tabla PVT (1500–5500 psi, 17 pts).
# La tabla del usuario se interpola a este grid antes de armar el vector.
CANONICAL_PVT_GRID = np.arange(1500.0, 5501.0, 250.0)
PVT_VECTOR_DIM = 3 * len(CANONICAL_PVT_GRID)  # [Bo·17, Bg·17, Rs·17] = 51

# Features que ve el modelo (deben coincidir con el artefacto entrenado del notebook 5).
DYNAMIC_COLUMNS = [
    "Np_over_PV", "Wp_over_PV", "Winj_over_PV", "GOR_cum",
    "qo_over_PV", "qwinj_over_PV", "WOR_inst", "water_cut_cum", "VRR_simple",
]
STATIC_COLUMNS = ["Porosidad", "log10_Permeabilidad_mD", "P_initial_norm"]


def build_features(history: pd.DataFrame, static: dict, pvt: pd.DataFrame) -> pd.DataFrame:
    """Construye los features por timestep (9 dinámicos + 3 estáticos) del modelo.

    `history`: una fila por timestep (historia de producción).
    `static`:  dict con las propiedades estáticas del reservorio.
    `pvt`:     tabla PVT del campo (se usa en `build_pvt_vector`, no acá).

    Los estáticos se repiten en cada fila; `model.predict` toma la primera para el contexto.
    """
    f = pd.DataFrame({"tiempo_dias": history["tiempo_dias"]})

    pore_volume = (
        static["area_m2"] * static["espesor_neto_m"] * static["porosidad"] * M3_TO_BBL
    )

    Np = history["Prod_Acumulada_Petroleo"]
    Gp = history["Prod_Acumulada_Gas"]
    Wp = history["Prod_Acumulada_Agua"]
    Winj = history["Iny_Acumulada_Agua"]
    qo = history["Caudal_Prod_Petroleo_bbl"]
    qwinj = history["Caudal_Iny_Agua_bbl"]

    # estáticos
    f["Porosidad"] = static["porosidad"]
    f["log10_Permeabilidad_mD"] = np.log10(max(static["permeabilidad_mD"], 1e-3))
    f["P_initial_norm"] = static["presion_inicial_psi"] / PRESSURE_SCALE

    # dinámicos de superficie, normalizados por volumen poral (adimensionales)
    f["Np_over_PV"] = Np / pore_volume
    f["Wp_over_PV"] = Wp / pore_volume
    f["Winj_over_PV"] = Winj / pore_volume
    f["qo_over_PV"] = qo / pore_volume
    f["qwinj_over_PV"] = qwinj / pore_volume
    with np.errstate(divide="ignore", invalid="ignore"):
        f["GOR_cum"] = np.where(Np > 0, Gp / Np, 0.0)
        dt = history["tiempo_dias"].diff().replace(0, np.nan)
        water_rate = Wp.diff() / dt
        f["WOR_inst"] = np.where(qo > 0, water_rate / qo, 0.0)
        total_liquid = Np + Wp
        f["water_cut_cum"] = np.where(total_liquid > 0, Wp / total_liquid, 0.0)
        f["VRR_simple"] = np.where(total_liquid > 0, Winj / total_liquid, 0.0)

    return f.fillna(0.0)


def build_pvt_vector(pvt: pd.DataFrame) -> np.ndarray:
    """Vector PVT de 51D que ve el encoder: [Bo·17, Bg·17·1000, Rs·17/1000].

    Interpola las curvas Bo/Bg/Rs de la tabla del usuario al grid canónico (la tabla puede
    venir con otro grid). El re-escalado ×1000 / ÷1000 deja las tres curvas en órdenes de
    magnitud comparables, como en el entrenamiento.
    """
    p = pvt["p_grid_psi"].to_numpy()
    bo = np.interp(CANONICAL_PVT_GRID, p, pvt["bo_rb_stb"].to_numpy())
    bg = np.interp(CANONICAL_PVT_GRID, p, pvt["bg_rb_scf"].to_numpy()) * 1000.0
    rs = np.interp(CANONICAL_PVT_GRID, p, pvt["rs_scf_stb"].to_numpy()) / 1000.0
    return np.concatenate([bo, bg, rs]).astype(np.float32)


# Documentación de features para la explicabilidad del front.
FEATURE_DOCS = [
    dict(nombre="Np_over_PV",
         descripcion="Petróleo producido acumulado sobre el volumen poral.",
         fisica="Fracción del volumen del reservorio ya extraída como petróleo."),
    dict(nombre="Wp_over_PV",
         descripcion="Agua producida acumulada sobre el volumen poral.",
         fisica="Cuánta agua salió, relativa al tamaño del reservorio."),
    dict(nombre="Winj_over_PV",
         descripcion="Agua inyectada acumulada sobre el volumen poral.",
         fisica="La inyección repone volumen y sostiene la presión (recuperación secundaria)."),
    dict(nombre="GOR_cum",
         descripcion="Relación gas-petróleo acumulada.",
         fisica="Indica liberación de gas; sube cuando la presión cae bajo el punto de burbuja."),
    dict(nombre="qo_over_PV",
         descripcion="Caudal instantáneo de petróleo sobre el volumen poral.",
         fisica="Ritmo de extracción relativo al tamaño del reservorio."),
    dict(nombre="qwinj_over_PV",
         descripcion="Caudal instantáneo de inyección de agua sobre el volumen poral.",
         fisica="Ritmo de reposición relativo al tamaño del reservorio."),
    dict(nombre="WOR_inst",
         descripcion="Relación agua-petróleo instantánea.",
         fisica="Crece con la irrupción de agua del acuífero o la inyección."),
    dict(nombre="water_cut_cum",
         descripcion="Fracción de agua en el líquido producido acumulado.",
         fisica="Refleja el avance del frente de agua en el reservorio."),
    dict(nombre="VRR_simple",
         descripcion="Voidage Replacement Ratio: inyección sobre líquido producido (volúmenes de superficie).",
         fisica="VRR≈1 mantiene la presión; <1 la deja caer."),
    dict(nombre="tabla PVT (Bo/Bg/Rs)",
         descripcion="Las tres curvas de laboratorio del fluido, como vector de contexto de 51 dimensiones.",
         fisica="Le dicen al modelo qué fluido tiene en frente, sin revelar la presión actual."),
]
