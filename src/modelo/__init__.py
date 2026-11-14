"""Capa 2: modelo por cuantiles (LightGBM; plan B GradientBoostingRegressor).

Dueño: Gino. Esqueleto V0 (Anexo E): reemplaza el cuerpo, NO la firma.
El servicio usa: Modelo.cargar(cfg["ruta_modelo"]).predecir(historia, fecha).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from contratos import Config, Pronostico

FEATURES: list[str] = []  # nombres de las variables, en orden (Gino)


class HistoriaInsuficiente(Exception):
    """Menos de cfg["umbral_historia_semanas"] semanas de historia: el servicio usa la regla 2."""


def construir_features(historia: pd.DataFrame, fecha: date, cfg: Config) -> dict[str, float]:
    raise NotImplementedError("modelo.construir_features (Gino)")


def entrenar(movimientos_train: pd.DataFrame, cfg: Config, semilla: int) -> Modelo:
    raise NotImplementedError("modelo.entrenar: modelo v1 a las 15:30 (Gino)")


class Modelo:
    def predecir(self, historia: pd.DataFrame, fecha: date) -> Pronostico:
        """Cuantiles ordenados y no negativos. Puede lanzar HistoriaInsuficiente."""
        raise NotImplementedError("Modelo.predecir: 15:30 (Gino)")

    def guardar(self, ruta: str | Path) -> None:
        raise NotImplementedError("Modelo.guardar (Gino)")

    @classmethod
    def cargar(cls, ruta: str | Path) -> Modelo:
        raise NotImplementedError("Modelo.cargar (Gino)")


__all__ = ["FEATURES", "HistoriaInsuficiente", "Modelo", "construir_features", "entrenar"]
