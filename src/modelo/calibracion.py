"""Calibración por cuantil con la ventana de validación (dueño: Gino, nivel P1).

Regla: el desplazamiento se mide SOLO con datos de la ventana de validación (meses 17-20) y personas de
entrenamiento; quien llama pasa `movimientos_val` ya recortado (sin meses 21-24) y `desde` (inicio de la ventana).

Empates: con ingreso cero hay muchas ventanas con y == q == 0. Un cuantil tau está calibrado si tau cae en
[P(y < q), P(y <= q)]. El desplazamiento es el cuantil tau de los residuos (y - q): si el desajuste es solo por
empates, ese cuantil es 0 y no corrige nada.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .modelo import Modelo, _armar_muestras, _nombres


def cobertura(y: np.ndarray, q: np.ndarray, eps: float = 0.0) -> tuple[float, float]:
    """(P(y < q - eps), P(y <= q + eps)). Un cuantil tau bien calibrado cumple P(y<q) <= tau <= P(y<=q).

    `eps` (soles) agrupa los casi-empates: un sueldo fijo de 1500.00 y un cuantil de 1500.004 son un empate.
    """
    y, q = np.asarray(y, dtype=float), np.asarray(q, dtype=float)
    return float(np.mean(y < q - eps)), float(np.mean(y <= q + eps))


def desplazamiento(residuos: np.ndarray, tau: float, eps: float = 0.0) -> float:
    """Cuantil tau de los residuos (y - q): lo que hay que sumar al cuantil para llegar a la cobertura tau.

    Si |desplazamiento| <= eps es un empate, no una descalibración: no se corrige (devuelve 0).
    """
    s = float(np.quantile(np.asarray(residuos, dtype=float), tau, method="inverted_cdf"))
    return 0.0 if abs(s) <= eps else s


def _predicciones(modelo: Modelo, X: pd.DataFrame, con_offset: bool) -> dict[tuple[int, str], np.ndarray]:
    return {
        k: np.maximum(0.0, m.predict(X) + (modelo.offsets[k] if con_offset else 0.0))
        for k, m in modelo.modelos.items()
    }


def diagnostico(modelo: Modelo, X: pd.DataFrame, Y: dict[int, np.ndarray]) -> list[dict]:
    """Una fila por (horizonte, cuantil), con los desplazamientos del modelo ya aplicados."""
    tau_de = _nombres(modelo.cfg)
    eps = float(modelo.cfg["modelo"]["tolerancia_empate_soles"])
    filas = []
    for (h, nombre), q in _predicciones(modelo, X, con_offset=True).items():
        y = Y[h]
        menor, menor_igual = cobertura(y, q, eps)
        filas.append(
            {
                "horizonte": h,
                "cuantil": nombre,
                "tau": tau_de[nombre],
                "n": int(len(y)),
                "n_ingreso_cero": int(np.sum(y == 0)),
                "pct_q_cero": float(np.mean(q == 0)),
                "cob_menor": menor,  # P(y < q)
                "cob_menor_igual": menor_igual,  # P(y <= q)
                "y_mayor_q": 1.0 - menor_igual,  # fracción con y > q (criterio del plan, estricto)
                "y_mayor_igual_q": 1.0 - menor,  # fracción con y >= q
            }
        )
    return filas


def calibrar(modelo: Modelo, movimientos_val: pd.DataFrame, desde: pd.Timestamp) -> Modelo:
    """Modelo nuevo con el desplazamiento por (horizonte, cuantil) medido en la ventana de validación.

    No muta `modelo`. Parte de los desplazamientos que ya tenga (los reemplaza: se mide sobre predicciones crudas).
    """
    X, Y = _armar_muestras(movimientos_val, modelo.cfg, desde=desde)
    tau_de = _nombres(modelo.cfg)
    eps = float(modelo.cfg["modelo"]["tolerancia_empate_soles"])
    offsets = {
        (h, nombre): desplazamiento(Y[h] - q, tau_de[nombre], eps)
        for (h, nombre), q in _predicciones(modelo, X, con_offset=False).items()
    }
    return Modelo(modelo.modelos, modelo.cfg, offsets)
