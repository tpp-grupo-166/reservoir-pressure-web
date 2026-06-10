"""Arquitectura del modelo (LSTM + encoder de PVT, del notebook 5).

Definición pura de la red, única fuente de la arquitectura. Vive separada de
`models/lstm.py` porque definir un `nn.Module` requiere torch en el import: el adapter
la importa lazy (recién al cargar/entrenar) para que la API bootee sin torch instalado.
El feature engineering vive en `features.py`; el escalado y el loop de entrenamiento
viven afuera de esta clase.
"""
from __future__ import annotations

import torch
from torch import nn


class LSTMPVT(nn.Module):
    """LSTM seq-to-seq con dos MLP encoders (PVT y estáticos).

    Entrada por timestep: `n_dynamic` features dinámicos + el contexto (PVT + estáticos)
    broadcasteado. Salida: el delta de presión normalizado, un valor por timestep.
    """

    def __init__(self, pvt_dim: int, n_dynamic: int = 9, n_static: int = 3,
                 context_dim: int = 16, hidden_size: int = 64) -> None:
        super().__init__()
        self.pvt_encoder = nn.Sequential(
            nn.Linear(pvt_dim, 32), nn.GELU(), nn.Linear(32, context_dim))
        self.static_encoder = nn.Sequential(
            nn.Linear(n_static, 16), nn.GELU(), nn.Linear(16, context_dim))
        self.lstm = nn.LSTM(n_dynamic + 2 * context_dim, hidden_size,
                            num_layers=2, batch_first=True)
        self.head = nn.Linear(hidden_size, 1)

    def forward(self, dynamic: torch.Tensor, static: torch.Tensor,
                pvt: torch.Tensor) -> torch.Tensor:
        """dynamic (B,T,n_dynamic), static (B,n_static), pvt (B,pvt_dim) → (B,T) delta norm."""
        context = torch.cat([self.pvt_encoder(pvt), self.static_encoder(static)], dim=-1)
        context = context.unsqueeze(1).expand(-1, dynamic.shape[1], -1)
        lstm_out, _ = self.lstm(torch.cat([dynamic, context], dim=-1))
        return self.head(lstm_out).squeeze(-1)
