"""Métricas del pronóstico (eval/metricas.py), con valores calculados a mano y semanas de ingreso cero.

eval/ no es un paquete: el módulo se carga por ruta.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[3]


def _cargar():
    spec = importlib.util.spec_from_file_location("eval_metricas", RAIZ / "eval" / "metricas.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


m = _cargar()


def test_pinball_a_mano():
    # y=[10, 0], q=[8, 2], tau=0.2: residuos +2 y -2 -> 0.2*2 = 0.4 y (0.2-1)*(-2) = 1.6 -> media 1.0
    assert m.pinball(np.array([10.0, 0.0]), np.array([8.0, 2.0]), 0.2) == pytest.approx(1.0)


def test_pinball_con_mediana_es_la_mitad_del_mae():
    y, q = np.array([10.0, 0.0, 7.0]), np.array([8.0, 2.0, 7.5])
    assert m.pinball(y, q, 0.5) == pytest.approx(0.5 * m.mae(y, q))


def test_pinball_con_semanas_de_ingreso_cero_no_se_rompe():
    y = np.zeros(4)
    assert m.pinball(y, np.zeros(4), 0.2) == 0.0  # el MAPE aquí dividiría entre cero
    assert m.pinball(y, np.full(4, 10.0), 0.2) == pytest.approx((0.2 - 1) * (0 - 10) * 1.0)


def test_mae_a_mano():
    assert m.mae(np.array([10.0, 0.0]), np.array([8.0, 2.0])) == pytest.approx(2.0)


def test_mae_con_ingreso_cero_es_finito():
    assert m.mae(np.zeros(3), np.array([0.0, 5.0, 0.0])) == pytest.approx(5.0 / 3)


def test_calibracion_a_mano():
    # y >= q20 en 3 de 4 casos (los empates en cero cuentan a favor, como dice el plan)
    y, q20 = np.array([0.0, 5.0, 10.0, 0.0]), np.array([0.0, 4.0, 12.0, 0.0])
    assert m.calibracion(y, q20) == pytest.approx(0.75)


def test_acepta_listas_y_series():
    import pandas as pd

    assert m.mae([10, 0], [8, 2]) == pytest.approx(2.0)
    assert m.pinball(pd.Series([10.0, 0.0]), pd.Series([8.0, 2.0]), 0.2) == pytest.approx(1.0)
    assert m.calibracion([1, 2], [1, 3]) == pytest.approx(0.5)


@pytest.mark.parametrize("funcion", ["mae", "pinball", "calibracion"])
def test_entradas_vacias_o_de_distinto_largo_fallan_claro(funcion):
    f = getattr(m, funcion)
    args = (0.2,) if funcion == "pinball" else ()
    with pytest.raises(ValueError):
        f(np.array([]), np.array([]), *args)
    with pytest.raises(ValueError):
        f(np.array([1.0, 2.0]), np.array([1.0]), *args)
