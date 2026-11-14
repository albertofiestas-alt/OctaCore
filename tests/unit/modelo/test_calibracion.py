"""Calibración por cuantil (nivel P1). Tolerancia declarada: TOLERANCIA = 0.03 (3 puntos, plan de Gino).

Criterio con empates: con ingreso cero hay muchas ventanas con y == q == 0. Un cuantil tau está calibrado si
tau cae en el intervalo [P(y < q), P(y <= q)] (ensanchado por la tolerancia). Un desajuste explicado solo por
empates NO es descalibración y el desplazamiento no lo corrige.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from modelo.calibracion import calibrar, cobertura, desplazamiento, diagnostico
from modelo.modelo import _armar_muestras

TOLERANCIA = 0.03
VAL_DESDE = pd.Timestamp("2026-05-01")  # mes 17 (el año 1 empieza el 2025-01-01)
VAL_HASTA = pd.Timestamp("2026-09-01")  # fin del mes 20 (exclusivo)


def test_cobertura_separa_empates():
    y = np.array([0, 0, 0, 0, 5, 6, 7, 8, 9, 10], dtype=float)
    q = np.zeros(10)
    menor, menor_igual = cobertura(y, q)
    assert (menor, menor_igual) == (0.0, 0.4)  # el 40 % son empates en cero


def test_casi_empates_cuentan_como_empate():
    y = np.full(100, 1500.00)
    q = np.full(100, 1500.004)  # sueldo fijo y cuantil con ruido de centavos
    assert cobertura(y, q) == (1.0, 1.0)  # sin tolerancia parece descalibrado
    assert cobertura(y, q, eps=1.0) == (0.0, 1.0)  # con tolerancia es un empate: tau cabe en [0, 1]
    assert desplazamiento(y - q, 0.20, eps=1.0) == 0.0


def test_desplazamiento_corrige_un_sesgo_real():
    rng = np.random.default_rng(0)
    y = rng.gamma(4.0, 25.0, 5000)
    q = np.full_like(y, 40.0)  # cuantil 20 demasiado bajo a propósito
    s = desplazamiento(y - q, 0.20)
    assert s > 0
    menor, menor_igual = cobertura(y, q + s)
    assert menor - TOLERANCIA <= 0.20 <= menor_igual + TOLERANCIA


def test_desplazamiento_es_cero_si_el_desajuste_es_solo_empates():
    y = np.concatenate([np.zeros(600), np.random.default_rng(1).gamma(4.0, 25.0, 400)])
    q = np.zeros_like(y)  # P20 = 0 con 60 % de ceros: está bien calibrado
    assert desplazamiento(y - q, 0.20) == 0.0


def test_calibrar_no_muta_el_modelo_original_y_deja_cuantiles_ordenados(modelo_entrenado, movimientos):
    val = movimientos[movimientos["fecha_hora"] < VAL_HASTA]
    antes = dict(getattr(modelo_entrenado, "offsets", {}))
    nuevo = calibrar(modelo_entrenado, val, VAL_DESDE)
    assert nuevo is not modelo_entrenado
    assert dict(getattr(modelo_entrenado, "offsets", {})) == antes
    assert set(nuevo.offsets) == set(modelo_entrenado.modelos)


def test_calibracion_en_validacion_cumple_la_tolerancia(modelo_entrenado, movimientos, cfg_modelo):
    val = movimientos[movimientos["fecha_hora"] < VAL_HASTA]
    nuevo = calibrar(modelo_entrenado, val, VAL_DESDE)
    X, Y = _armar_muestras(val, cfg_modelo, desde=VAL_DESDE)
    filas = diagnostico(nuevo, X, Y)
    assert len(filas) == 12
    for f in filas:
        assert f["cob_menor"] - TOLERANCIA <= f["tau"] <= f["cob_menor_igual"] + TOLERANCIA, f
