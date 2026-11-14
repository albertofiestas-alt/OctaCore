"""Pruebas de regla1 y regla2 (dueño: Rafael). Valores esperados calculados a mano."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from contratos import HORIZONTES, Pronostico, cargar_config
from reglas import DIAS_MINIMOS_REGLA2, regla1, regla1_lote, regla2, regla2_lote

FECHA = date(2025, 6, 1)
CFG = cargar_config()


def _mov(dias_antes: int, monto: float, tipo: str = "ingreso", **extra) -> dict:
    fila = {
        "customer_id": "P0001",
        "transaction_id": f"T{abs(hash((dias_antes, monto, tipo))) % 10**6:06d}",
        "fecha_hora": pd.Timestamp(FECHA - timedelta(days=dias_antes)) + pd.Timedelta(hours=12),
        "monto": monto if tipo == "ingreso" else -abs(monto),
        "moneda": "PEN",
        "tipo": tipo,
        "categoria": "otros",
        "comercio": "ComercioFicticio",
        "saldo": None,
    }
    fila.update(extra)
    return fila


def _historia(filas: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(filas)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    return df.sort_values("fecha_hora").reset_index(drop=True)


def _tabla(p: Pronostico) -> dict[int, tuple[float, float, float, float]]:
    return {h: (c.p5, c.p20, c.p50, c.p80) for h, c in p.por_horizonte.items()}


# --------------------------------------------------------------------------- #
# regla1: valores a mano
# --------------------------------------------------------------------------- #


def test_regla1_valores_a_mano():
    # 900 en los últimos 90 días -> base = 900 / 3 / 30 = 10 soles por día.
    h = _historia([_mov(120, 50, "gasto"), _mov(10, 900)])
    assert _tabla(regla1(h, FECHA, CFG)) == {
        3: (15.0, 22.5, 30.0, 30.0),
        7: (35.0, 52.5, 70.0, 70.0),
        14: (70.0, 105.0, 140.0, 140.0),
    }


def test_regla1_ventana_de_90_dias_exacta():
    # fecha-90 entra; fecha-91 no; el día de la fecha tampoco (sin mirar el futuro).
    dentro = regla1(_historia([_mov(90, 900)]), FECHA, CFG)
    fuera = regla1(_historia([_mov(91, 900), _mov(0, 5000)]), FECHA, CFG)
    assert dentro.por_horizonte[3].p50 == 30.0
    assert _tabla(fuera)[14] == (0.0, 0.0, 0.0, 0.0)


def test_regla1_excluye_atipicos_detectados_y_gastos():
    h = _historia([
        _mov(10, 900, atipico_detectado=False),
        _mov(5, 9000, atipico_detectado=True),
        _mov(3, 400, "gasto", atipico_detectado=False),
    ])
    assert regla1(h, FECHA, CFG).por_horizonte[3].p50 == 30.0


# --------------------------------------------------------------------------- #
# regla2: valores a mano
# --------------------------------------------------------------------------- #


def test_regla2_valores_a_mano_ingreso_semanal():
    # 70 soles cada 7 días (offsets 1, 8, ..., 113 antes de la fecha); primer movimiento hace 120 días.
    # En los últimos 56 días hay 8 cobros. Ventanas de 7 y 14 días: siempre 70 y 140.
    # Ventanas de 3 días (54): 22 contienen un cobro (70) y 32 no (0).
    # Cuantil lineal sobre 54 valores ordenados: posición q*53 -> p5, p20, p50 en ceros; p80 (42.4) en 70.
    filas = [_mov(120, 10, "gasto")] + [_mov(d, 70) for d in range(1, 120, 7)]
    t = _tabla(regla2(_historia(filas), FECHA, CFG))
    assert t[7] == (70.0, 70.0, 70.0, 70.0)
    assert t[14] == (140.0, 140.0, 140.0, 140.0)
    assert t[3] == (0.0, 0.0, 0.0, 70.0)


def test_regla2_historia_corta_cae_en_regla1(caplog):
    h = _historia([_mov(DIAS_MINIMOS_REGLA2 - 1, 10, "gasto"), _mov(10, 900), _mov(3, 50)])
    with caplog.at_level(logging.INFO, logger="reglas"):
        r2 = regla2(h, FECHA, CFG)
    assert r2 == regla1(h, FECHA, CFG)
    assert "respaldo" in caplog.text


def test_regla2_con_historia_justa_no_cae():
    h = _historia([_mov(DIAS_MINIMOS_REGLA2, 10, "gasto")] + [_mov(d, 70) for d in range(1, 60, 7)])
    assert regla2(h, FECHA, CFG) != regla1(h, FECHA, CFG)


# --------------------------------------------------------------------------- #
# Casos borde y propiedades
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("regla", [regla1, regla2])
def test_ingreso_cero(regla):
    h = _historia([_mov(d, 20, "gasto") for d in range(1, 150, 3)])
    p = regla(h, FECHA, CFG)
    assert all(v == 0.0 for fila in _tabla(p).values() for v in fila)


@pytest.mark.parametrize("regla", [regla1, regla2])
def test_historia_vacia(regla):
    vacia = _historia([_mov(1, 10)]).iloc[0:0]
    assert set(regla(vacia, FECHA, CFG).por_horizonte) == set(HORIZONTES)


@settings(max_examples=40, deadline=None)
@given(
    montos=st.lists(st.floats(min_value=0, max_value=5000, allow_nan=False), min_size=1, max_size=60),
    dias=st.lists(st.integers(min_value=1, max_value=200), min_size=1, max_size=60),
)
def test_siempre_tres_claves_ordenado_y_no_negativo(montos, dias):
    filas = [_mov(200, 1, "gasto")] + [_mov(d, m) for d, m in zip(dias, montos)]
    h = _historia(filas)
    for regla in (regla1, regla2):
        p = regla(h, FECHA, CFG)
        assert set(p.por_horizonte) == {3, 7, 14}
        for c in p.por_horizonte.values():
            assert 0 <= c.p5 <= c.p20 <= c.p50 <= c.p80


# --------------------------------------------------------------------------- #
# Versión por lotes = versión individual
# --------------------------------------------------------------------------- #


def test_lote_coincide_con_individual():
    rng = np.random.default_rng(20261114)
    p, d = 4, 160
    inicio = date(2025, 1, 1)
    primer = np.array([0, 10, 40, 100])
    ingresos = np.where(rng.random((p, d)) < 0.4, rng.uniform(20, 300, (p, d)), 0.0).round(2)
    for i in range(p):
        ingresos[i, : primer[i]] = 0.0
    l1 = regla1_lote(ingresos, CFG)
    l2 = regla2_lote(ingresos, primer, CFG)
    assert l1.shape == l2.shape == (p, d, 3, 4)

    for i in range(p):
        filas = [{
            **_mov(0, 1, "gasto"),
            "fecha_hora": pd.Timestamp(inicio + timedelta(days=int(primer[i]))) + pd.Timedelta(hours=8),
        }]
        for dia in np.flatnonzero(ingresos[i]):
            filas.append({**_mov(0, float(ingresos[i, dia])),
                          "fecha_hora": pd.Timestamp(inicio + timedelta(days=int(dia))) + pd.Timedelta(hours=12)})
        h = _historia(filas)
        for t in (5, 50, 70, 103, 140, 159):
            if t <= primer[i]:
                continue
            fecha = inicio + timedelta(days=t)
            for lote, regla in ((l1, regla1), (l2, regla2)):
                indiv = np.array([[c.p5, c.p20, c.p50, c.p80] for c in
                                  (regla(h, fecha, CFG).por_horizonte[hz] for hz in (3, 7, 14))])
                np.testing.assert_allclose(lote[i, t], indiv, atol=0.006,
                                           err_msg=f"persona {i} corte {t} {regla.__name__}")


def test_lote_no_mira_el_futuro():
    rng = np.random.default_rng(1)
    ingresos = rng.uniform(0, 100, (2, 120))
    base = regla2_lote(ingresos, np.zeros(2, dtype=int), CFG)
    alterado = ingresos.copy()
    alterado[:, 90:] = 1e6
    nuevo = regla2_lote(alterado, np.zeros(2, dtype=int), CFG)
    np.testing.assert_array_equal(base[:, :91], nuevo[:, :91])
