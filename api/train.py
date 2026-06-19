"""Entrena un modelo del registry y guarda su artefacto en `artifacts/`.

Uso:
    cd api && python train.py --model lstm

Qué genera y con qué datos entrena depende de cada modelo: ver el docstring de
`models/<nombre>.py`. La API sirve el modelo elegido con la env var MODEL.
"""
from __future__ import annotations

import argparse

from models.registry import available, get_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena un modelo del registry.")
    parser.add_argument("--model", default="lstm", choices=available(),
                        help="nombre del modelo a entrenar (default: lstm)")
    args = parser.parse_args()
    try:
        get_model(args.model).train()
    except NotImplementedError as exc:
        raise SystemExit(str(exc))


if __name__ == "__main__":
    main()
