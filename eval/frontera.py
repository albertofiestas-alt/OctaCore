"""Frontera de seguridad: (% de pagos descubiertos, gasto permitido) por método y cuantil. Dueño: Rafael."""

from __future__ import annotations


def frontera(df, cfg, metodos=("regla1", "regla2", "modelo")):
    """Cuatro puntos por método (cuantil conservador P5, P20, P50 y P80), más las referencias de gasto cero y gasto fijo.
    Guarda eval/resultados/frontera.csv."""
    raise NotImplementedError("eval.frontera.frontera (Rafael)")