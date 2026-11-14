"""Capa 2: modelo por cuantiles (LightGBM; plan B GradientBoostingRegressor).

Dueño: Gino. Mismos nombres y firmas del esqueleto V0 (Anexo E); el cuerpo vive en features.py y modelo.py.
El servicio usa: Modelo.cargar(cfg["ruta_modelo"]).predecir(historia, fecha).
"""

from __future__ import annotations

from .features import FEATURES, HistoriaInsuficiente, construir_features
from .modelo import Modelo, entrenar

__all__ = ["FEATURES", "HistoriaInsuficiente", "Modelo", "construir_features", "entrenar"]
