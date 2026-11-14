"""Métricas del pronóstico. Dueño: Rafael. Sin MAPE (se rompe con semanas de ingreso cero)."""

from __future__ import annotations


def pinball(y, q, tau: float) -> float:
    """Pérdida pinball media: mean(max(tau*(y-q), (tau-1)*(y-q)))."""
    raise NotImplementedError("eval.metricas.pinball (Rafael)")


def mae(y, pred) -> float:
    raise NotImplementedError("eval.metricas.mae (Rafael)")


def calibracion(y, q20) -> float:
    """Fracción de casos en que el ingreso real supera el P20 pronosticado; debe rondar 0.80."""
    raise NotImplementedError("eval.metricas.calibracion (Rafael)")