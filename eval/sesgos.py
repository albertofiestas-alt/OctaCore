"""Sesgos por grupo: arquetipo, tercil de ingreso, tercil de volatilidad y cambio de patrón. Dueño: Rafael."""

from __future__ import annotations


def sesgos(df, resultados_por_persona, cfg):
    """Por grupo y método: % descubiertos, gasto permitido y calibración del P20. Brecha = máximo menos mínimo;
    alerta si supera cfg["preregistro"]["umbral_alerta_sesgo"]. Guarda eval/resultados/sesgos.csv."""
    raise NotImplementedError("eval.sesgos.sesgos (Rafael)")