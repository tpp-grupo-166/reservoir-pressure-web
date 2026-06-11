"""Modelo PINN del notebook 7: balance de materiales con corrección neuronal (UDE).

La física como esqueleto: la presión se integra desde la ODE de balance de materiales

    dP/dt = -(dF/dt - q_e) / (Vp · c_t(P)),
    c_t(P) = c_u + (c_s - c_u) · sigmoid((Pb - P) / tau)

donde F es el voidage en volúmenes de reservorio (Np·Bo0 + gas_libre·Bg(Pb) + Wp − Winj)
y q_e es un influjo efectivo aprendido por una MLP 5→16→16→1 acotada, adimensional y
regularizada (la física manda). Euler explícito diferenciable de punta a punta, con
P[0] = P_init como condición de borde.

A diferencia de los demás modelos entrena MULTI-CAMPO (Volve + SPE9 + Norne train):
su gracia es transferir a regímenes no vistos vía la física compartida. Las métricas
usan el mismo test (Norne sims 25-30) que el resto para ser comparables, pero OJO:
el zero-shot a un campo realmente nuevo es real pero no robusto (notebook 7: SPE9
+0.39±0.15 con mediana por sim variable según seed). La banda es el min/max del
ensemble de 3 seeds, como en el LSTM.

Entrenar (~minutos en CPU): cd api && python train.py --model pinn
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from features import M3_TO_BBL, bubble_point
from models.base import Model, baseline_from_curve
from models.datasets import (NORNE_URL, SPE9_URL, TARGET, TEST_SIMS, TRAIN_SIMS,
                             VOLVE_URL, mean_delta_curve, read_url)

ARTIFACT = Path(__file__).parent.parent / "artifacts" / "pinn.pt"

# Constantes del notebook 7.
C_U_LO, C_U_HI = 1e-6, 1e-4   # compresibilidad sub-saturada (1/psi)
C_S_MAX = 2e-3                # extra de compresibilidad con gas libre
A_MAX = 2.0     # el influjo aprendido nunca supera A_MAX x mediana(|dF|) de la sim
LAMBDA = 0.05   # peso de la regularización L2 de la corrección (la física manda)
SEEDS = (0, 1, 2)
EPOCHS, LR_PHYS, LR_NET = 300, 0.05, 0.01


class PINNModel(Model):
    """Híbrido UDE del notebook 7, servido zero-shot (sin calibración few-shot)."""

    name = "pinn"

    def __init__(self) -> None:
        self._members = []   # (raw_params, mlp, raw_alpha) por seed
        self._mean_delta = None

    def load(self) -> bool:
        if not ARTIFACT.exists():
            return False
        import torch

        art = torch.load(ARTIFACT, map_location="cpu", weights_only=False)
        members = []
        for m in art["members"]:
            mlp = _make_mlp(0)
            mlp.load_state_dict(m["mlp"])
            mlp.eval()
            members.append((tuple(torch.tensor(v) for v in m["raw"]), mlp,
                            torch.tensor(m["raw_alpha"])))
        self._members = members
        self._mean_delta = np.asarray(art["mean_delta_curve"], dtype=np.float64)
        self.version = art["version"]
        self.metrics = art["metrics"]
        self.note = art["note"]
        return True

    def predict_band(self, history: pd.DataFrame, static: dict, pvt: pd.DataFrame):
        import torch

        pad = _pad_from_user(history, static, pvt)
        with torch.no_grad():
            preds = np.stack([
                _integrate(pad, raw, mlp=mlp, raw_alpha=ra)[0].numpy()[0]
                for raw, mlp, ra in self._members
            ])  # (n_seeds, T)
        return preds.mean(axis=0), preds.min(axis=0), preds.max(axis=0)

    def baseline(self, history: pd.DataFrame, static: dict) -> np.ndarray:
        return baseline_from_curve(static["presion_inicial_psi"], self._mean_delta,
                                   len(history))

    def train(self) -> None:
        import torch

        fields = {"Volve": read_url(VOLVE_URL), "SPE9": read_url(SPE9_URL),
                  "Norne": read_url(NORNE_URL)}
        norne = fields["Norne"]
        frames = {n: _prep_field(raw, n) for n, raw in fields.items()}
        norne_train = frames["Norne"][frames["Norne"].sim_id.isin(TRAIN_SIMS)]
        norne_test = frames["Norne"][frames["Norne"].sim_id.isin(TEST_SIMS)]
        train_pads = [_pad_field(frames["Volve"]), _pad_field(frames["SPE9"]),
                      _pad_field(norne_train)]
        test_pad = _pad_field(norne_test)
        print(f"train: Volve {frames['Volve'].gid.nunique()} sims + "
              f"SPE9 {frames['SPE9'].gid.nunique()} + Norne {norne_train.gid.nunique()} | "
              f"test: Norne {norne_test.gid.nunique()}")

        members, r2s, maes = [], [], []
        for seed in SEEDS:
            raw, mlp, ra = _train_hybrid(train_pads, seed)
            members.append(dict(raw=[float(v) for v in raw],
                                mlp=mlp.state_dict(), raw_alpha=float(ra)))
            with torch.no_grad():
                P, _ = _integrate(test_pad, raw, mlp=mlp, raw_alpha=ra)
            m = _eval(test_pad, P.numpy())
            r2s.append(m["r2"]); maes.append(m["mae"])
            print(f"  seed {seed}: test R2={m['r2']:+.3f}  MAE={m['mae']:.0f} psi  "
                  f"med/sim={m['med']:+.3f}")

        metrics = dict(R2_medio=round(float(np.mean(r2s)), 4),
                       R2_std=round(float(np.std(r2s)), 4),
                       MAE_psi=round(float(np.mean(maes)), 1))
        print(f"ensemble ({len(SEEDS)} seeds): R2={metrics['R2_medio']}±{metrics['R2_std']}  "
              f"MAE={metrics['MAE_psi']} psi")

        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "members": members,
            "mean_delta_curve": mean_delta_curve(norne, TRAIN_SIMS).astype(np.float32),
            "metrics": metrics,
            "version": "pinn-notebook7-v1",
            "note": (f"PINN híbrido (balance de materiales + corrección neuronal acotada) "
                     f"del notebook 7, entrenado multi-campo (Volve + SPE9 + Norne 1-24), "
                     f"{len(SEEDS)} seeds. Métricas = test Norne (sims 25-30). Servido "
                     "zero-shot: en un campo de régimen no cubierto la transferencia es "
                     "real pero no robusta (ver notebook 7); la calibración few-shot con "
                     "1-3 sims del campo queda fuera de la web por ahora."),
        }, ARTIFACT)
        print(f"artefacto guardado en {ARTIFACT}")


# ---- preparación de datos (voidage en volúmenes de reservorio) ----

def _bg_at_pb(sub: pd.DataFrame) -> float:
    # Interpola la curva PVT Bg(P) de la sim y la evalúa en el punto de burbuja.
    x = sub[TARGET].to_numpy(); y = sub["Bg_rb_scf"].to_numpy()
    o = np.argsort(x)
    return float(np.interp(sub["Presion_Burbuja_psi"].iloc[0], x[o], y[o]))


def _prep_field(raw: pd.DataFrame, field: str) -> pd.DataFrame:
    """Voidage F, fracción vaciada vf y metadatos por sim (prep del notebook 7)."""
    keys = ["reservoir_id", "sim_id"]
    r = raw.sort_values(keys + ["tiempo_dias"]).reset_index(drop=True)
    g = r.groupby(keys, sort=False)
    Vp = (r["Area"] * r["Espesor_Neto_m"] * r["Porosidad"] * M3_TO_BBL).clip(lower=1.0)
    Bo0 = g["Bo_rb_stb"].transform("first")          # PVT a P_init (a-priori)
    Rs0 = g["Rs_scf_stb"].transform("first")
    Bg_pb = g.apply(_bg_at_pb, include_groups=False).reindex(
        pd.MultiIndex.from_frame(r[keys])).to_numpy()
    Np, Gp, Wp, Winj = (r["Prod_Acumulada_Petroleo"], r["Prod_Acumulada_Gas"],
                        r["Prod_Acumulada_Agua"], r["Iny_Acumulada_Agua"])
    free_gas = (Gp - Np * Rs0).clip(lower=0.0)
    Fvoid = Np * Bo0 + free_gas * Bg_pb + Wp - Winj   # voidage en vol. de reservorio
    out = pd.DataFrame({
        "sim_id": r["sim_id"],
        "gid": field + "_" + r["sim_id"].astype(str),
        "Vp": Vp.to_numpy(),
        "P_init": g[TARGET].transform("first").to_numpy(),
        "Pb": r["Presion_Burbuja_psi"].to_numpy(),
        "F": Fvoid.to_numpy(),
        "Winj": Winj.to_numpy(),
        TARGET: r[TARGET].to_numpy(),
    })
    out["dF"] = out.groupby("gid")["F"].diff().fillna(out["F"])
    out["vf"] = out["F"] / out["Vp"]
    out["winj_f"] = out["Winj"] / out["Vp"]
    return out


def _pad_field(frame: pd.DataFrame) -> dict:
    """Empaqueta las sims de un campo en tensores [n_sims, T] con máscara."""
    import torch

    sims = list(frame.groupby("gid", sort=False))
    T = max(len(d) for _, d in sims); n = len(sims)
    Z = lambda: np.zeros((n, T), np.float32)
    dF, Pobs, mask, vfp, winjp = Z(), Z(), Z(), Z(), Z()
    Vp = np.zeros(n, np.float32); Pini = np.zeros(n, np.float32)
    Pb = np.zeros(n, np.float32); dFs = np.zeros(n, np.float32)
    for i, (gid, d) in enumerate(sims):
        L = len(d)
        dF[i, :L] = d["dF"].to_numpy(); Pobs[i, :L] = d[TARGET].to_numpy(); mask[i, :L] = 1.0
        vfp[i, 1:L] = d["vf"].to_numpy()[:-1]          # acumulados al paso ANTERIOR
        winjp[i, 1:L] = d["winj_f"].to_numpy()[:-1]
        Vp[i] = d["Vp"].iloc[0]; Pini[i] = d["P_init"].iloc[0]; Pb[i] = d["Pb"].iloc[0]
        dFs[i] = max(float(np.median(np.abs(d["dF"].to_numpy()))), 1e-6)
    t = lambda a: torch.tensor(a)
    pad = dict(dF=t(dF), Pobs=t(Pobs), mask=t(mask), vfp=t(vfp), winjp=t(winjp),
               Vp=t(Vp), Pini=t(Pini), Pb=t(Pb), dFs=t(dFs))
    pbar = (pad["Pobs"] * pad["mask"]).sum(1) / pad["mask"].sum(1)
    pad["sstot"] = (((pad["Pobs"] - pbar[:, None]) ** 2) * pad["mask"]).sum(1).clamp(min=1.0)
    return pad


def _pad_from_user(history: pd.DataFrame, static: dict, pvt: pd.DataFrame) -> dict:
    """El mismo empaquetado, para la única "sim" del usuario (sin presión observada).

    El voidage usa la tabla PVT del usuario evaluada a-priori: Bo y Rs a P_init,
    Bg en el punto de burbuja. Nada se evalúa a la presión actual (sin leakage).
    """
    import torch

    Vp = max(float(static["area_m2"] * static["espesor_neto_m"] * static["porosidad"])
             * M3_TO_BBL, 1.0)
    p_init = float(static["presion_inicial_psi"])
    pb = bubble_point(pvt)
    grid = pvt["p_grid_psi"].to_numpy()
    o = np.argsort(grid)
    bo0 = float(np.interp(p_init, grid[o], pvt["bo_rb_stb"].to_numpy()[o]))
    rs0 = float(np.interp(p_init, grid[o], pvt["rs_scf_stb"].to_numpy()[o]))
    bg_pb = float(np.interp(pb, grid[o], pvt["bg_rb_scf"].to_numpy()[o]))

    h = history.sort_values("tiempo_dias")
    Np = h["Prod_Acumulada_Petroleo"].to_numpy(dtype=np.float64)
    Gp = h["Prod_Acumulada_Gas"].to_numpy(dtype=np.float64)
    Wp = h["Prod_Acumulada_Agua"].to_numpy(dtype=np.float64)
    Winj = h["Iny_Acumulada_Agua"].to_numpy(dtype=np.float64)
    free_gas = np.clip(Gp - Np * rs0, 0.0, None)
    F = Np * bo0 + free_gas * bg_pb + Wp - Winj
    dF = np.diff(F, prepend=0.0); dF[0] = F[0]
    vf, winj_f = F / Vp, Winj / Vp

    T = len(F)
    t = lambda a: torch.tensor(np.asarray(a, np.float32))
    vfp = np.zeros(T, np.float32); vfp[1:] = vf[:-1]
    winjp = np.zeros(T, np.float32); winjp[1:] = winj_f[:-1]
    return dict(dF=t(dF)[None, :], mask=t(np.ones(T))[None, :],
                vfp=t(vfp)[None, :], winjp=t(winjp)[None, :],
                Vp=t([Vp]), Pini=t([p_init]), Pb=t([pb]),
                dFs=t([max(float(np.median(np.abs(dF))), 1e-6)]))


# ---- el modelo en sí: parámetros físicos acotados + MLP + integrador ----

def _unpack(raw):
    """Parámetros sin restricción → (c_u, c_s, tau) en rango físico."""
    import torch

    a, b, d = raw
    c_u = C_U_LO + (C_U_HI - C_U_LO) * torch.sigmoid(a)
    c_s = c_u + C_S_MAX * torch.sigmoid(b)
    tau = 50.0 + 400.0 * torch.sigmoid(d)
    return c_u, c_s, tau


def _make_mlp(seed: int):
    import torch

    torch.manual_seed(seed)
    mlp = torch.nn.Sequential(
        torch.nn.Linear(5, 16), torch.nn.Tanh(),
        torch.nn.Linear(16, 16), torch.nn.Tanh(),
        torch.nn.Linear(16, 1))
    with torch.no_grad():                  # la corrección arranca ~0
        mlp[-1].weight.mul_(0.1); mlp[-1].bias.zero_()
    return mlp


def _integrate(pad, raw, mlp=None, raw_alpha=None):
    """Euler explícito de dP = -(dF - q_e)/(Vp·ct(P)). Diferenciable de punta a punta."""
    import torch

    c_u, c_s, tau = _unpack(raw)
    dF, Vp, Pb, Pini, dFs = pad["dF"], pad["Vp"], pad["Pb"], pad["Pini"], pad["dFs"]
    vfp, winjp = pad["vfp"], pad["winjp"]
    n, T = dF.shape
    cur = Pini.clone(); cols = [cur]
    corr_sq = torch.zeros(())
    alpha = A_MAX * torch.sigmoid(raw_alpha) if raw_alpha is not None else None
    for tt in range(1, T):
        ct = c_u + (c_s - c_u) * torch.sigmoid((Pb - cur) / tau)
        dFe = dF[:, tt]
        if mlp is not None:
            x = torch.stack([vfp[:, tt] * 10.0,
                             dF[:, tt] / dFs,
                             winjp[:, tt] * 10.0,
                             (cur - Pb) / 500.0,
                             (cur - Pini) / 1000.0], dim=1)
            c = torch.tanh(mlp(x).squeeze(1))
            dFe = dFe - alpha * c * dFs        # influjo aprendido (acotado)
            corr_sq = corr_sq + ((c * pad["mask"][:, tt]) ** 2).sum()
        cur = cur - dFe / (Vp * ct)
        cols.append(cur)
    P = torch.stack(cols, dim=1)
    reg = corr_sq / pad["mask"].sum()
    return P, reg


def _norm_mse(pad, raw, **kw):
    """Loss scale-free: media de (1 - R2) por sim + reg de la corrección."""
    P, reg = _integrate(pad, raw, **kw)
    ssres = (((P - pad["Pobs"]) ** 2) * pad["mask"]).sum(1)
    return (ssres / pad["sstot"]).mean(), reg


def _train_hybrid(train_pads: list[dict], seed: int):
    import torch

    torch.manual_seed(seed); np.random.seed(seed)
    mlp = _make_mlp(seed)
    a = torch.zeros((), requires_grad=True); b = torch.zeros((), requires_grad=True)
    d = torch.zeros((), requires_grad=True)
    ra = torch.zeros((), requires_grad=True)
    opt = torch.optim.Adam([
        dict(params=[a, b, d], lr=LR_PHYS),                        # física: lr alto
        dict(params=list(mlp.parameters()) + [ra], lr=LR_NET)])    # red: lr bajo
    for _ in range(EPOCHS):
        opt.zero_grad()
        terms = [_norm_mse(p, (a, b, d), mlp=mlp, raw_alpha=ra) for p in train_pads]
        loss = (torch.stack([t[0] for t in terms]).mean()
                + LAMBDA * torch.stack([t[1] for t in terms]).mean())
        loss.backward(); opt.step()
    mlp.eval()
    return (a.detach(), b.detach(), d.detach()), mlp, ra.detach()


def _eval(pad, P: np.ndarray) -> dict:
    """R2 global, MAE y mediana del R2 por sim sobre un pad con presión observada."""
    Pobs = pad["Pobs"].numpy(); m = pad["mask"].numpy().astype(bool)
    fp = np.concatenate([P[i][m[i]] for i in range(P.shape[0])])
    fy = np.concatenate([Pobs[i][m[i]] for i in range(P.shape[0])])
    ss_tot = float(((fy - fy.mean()) ** 2).sum())
    r2 = 1.0 - float(((fy - fp) ** 2).sum()) / ss_tot
    r2s = []
    for i in range(P.shape[0]):
        y, p = Pobs[i][m[i]], P[i][m[i]]
        if len(y) > 1 and np.ptp(y) > 0:
            r2s.append(1.0 - float(((y - p) ** 2).sum()) / float(((y - y.mean()) ** 2).sum()))
    return dict(r2=r2, mae=float(np.abs(fy - fp).mean()), med=float(np.median(r2s)))
