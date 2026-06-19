"""Modelos enchufables: un módulo por modelo + registry por nombre.

Para agregar un modelo nuevo: crear `models/<nombre>.py` con una subclase de
`models.base.Model` y registrarla con `models.registry.register`.
"""
