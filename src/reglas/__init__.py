"""Escalones 1 y 2: regla ingenua y regla robusta (misma forma que el modelo).

Dueño: Rafael. Esqueleto V0 (Anexo E): reemplaza el cuerpo, NO la firma.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from contratos import Config, Pronostico


def regla1(historia: pd.DataFrame, fecha: date, cfg: Config) -> Pronostico:
    """Ingreso promedio mensual / 30 * h."""
    raise NotImplementedError("reglas.regla1 (Rafael)")


def regla2(historia: pd.DataFrame, fecha: date, cfg: Config) -> Pronostico:
    """Percentiles empíricos del ingreso acumulado en ventanas de h días de las últimas 8 semanas."""
    raise NotImplementedError("reglas.regla2: 12:30 (Rafael), la usa el control 1")


__all__ = ["regla1", "regla2"]
