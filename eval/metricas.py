"""Métricas del pronóstico. Dueño: Rafael. Sin MAPE (se rompe con semanas de ingreso cero)."""

from __future__ import annotations

import numpy as np


def _par(y, otro) -> tuple[np.ndarray, np.ndarray]:
    """Convierte a arreglos float y exige datos y mismo largo (falla claro en vez de dar nan)."""
    a, b = np.asarray(y, dtype=float), np.asarray(otro, dtype=float)
    if a.size == 0:
        raise ValueError("no hay datos para calcular la métrica")
    if a.shape != b.shape:
        raise ValueError(f"largos distintos: {a.shape} contra {b.shape}")
    return a, b


def pinball(y, q, tau: float) -> float:
    """Pérdida pinball media: mean(max(tau*(y-q), (tau-1)*(y-q)))."""
    y, q = _par(y, q)
    e = y - q
    return float(np.mean(np.maximum(tau * e, (tau - 1) * e)))


def mae(y, pred) -> float:
    y, pred = _par(y, pred)
    return float(np.mean(np.abs(y - pred)))


def calibracion(y, q20) -> float:
    """Fracción de casos en que el ingreso real supera el P20 pronosticado; debe rondar 0.80.

    Cuenta y >= q20 (como el plan): con ingreso cero los empates y == q20 == 0 cuentan a favor.
    Para separar empates de descalibración real ver src/modelo/calibracion.py (cobertura).
    """
    y, q20 = _par(y, q20)
    return float(np.mean(y >= q20))
