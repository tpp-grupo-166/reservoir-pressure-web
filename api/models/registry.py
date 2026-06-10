"""Registry de modelos enchufables: nombre → clase."""
from __future__ import annotations

from models.base import Model
from models.lstm import LSTMModel
from models.stub import StubModel

_MODELS: dict[str, type[Model]] = {}


def register(cls: type[Model]) -> type[Model]:
    """Registra una subclase de Model por su `name`. Usable como decorador."""
    _MODELS[cls.name] = cls
    return cls


def get_model(name: str) -> Model | None:
    """Instancia el modelo registrado con ese nombre (None si no existe)."""
    cls = _MODELS.get(name)
    return cls() if cls is not None else None


def available() -> list[str]:
    return sorted(_MODELS)


register(StubModel)
register(LSTMModel)
