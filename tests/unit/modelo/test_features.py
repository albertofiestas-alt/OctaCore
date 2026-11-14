from __future__ import annotations

import math
from datetime import date

import pandas as pd
import pytest

from modelo import FEATURES, HistoriaInsuficiente, construir_features

FECHA = date(2025, 9, 15)


def _fila(cid, tid, ts, monto, tipo):
    return {"customer_id": cid, "transaction_id": tid, "fecha_hora": ts, "monto": monto, "moneda": "PEN",
            "tipo": tipo, "categoria": "c", "comercio": "m", "saldo": None}


def test_anti_futuro_variables_no_cambian_si_se_altera_lo_posterior(historia, cfg_modelo):
    antes = construir_features(historia, FECHA, cfg_modelo)

    corte = pd.Timestamp(FECHA)
    alterada = historia.copy()
    posterior = alterada["fecha_hora"] >= corte
    assert posterior.any(), "la prueba necesita datos en o después de la fecha"
    alterada.loc[posterior, "monto"] = alterada.loc[posterior, "monto"] * 1000 + 777
    extra = alterada[posterior].head(5).copy()
    extra["tipo"] = "ingreso"
    extra["monto"] = 99999.0
    alterada = pd.concat([alterada, extra], ignore_index=True)

    despues = construir_features(alterada, FECHA, cfg_modelo)
    assert antes == despues


def test_anti_futuro_historia_truncada_da_lo_mismo(historia, cfg_modelo):
    completa = construir_features(historia, FECHA, cfg_modelo)
    truncada = historia[historia["fecha_hora"] < pd.Timestamp(FECHA)]
    assert construir_features(truncada, FECHA, cfg_modelo) == completa


def test_variables_son_exactamente_features_y_numericas(historia, cfg_modelo):
    f = construir_features(historia, FECHA, cfg_modelo)
    assert list(f) == FEATURES
    assert len(FEATURES) == 9
    assert all(isinstance(v, (int, float)) and math.isfinite(v) for v in f.values())


def test_valores_calculados_a_mano(cfg_modelo):
    # 40 días de historia: ingreso de 100 el día 30 y de 50 el día 39 (el último).
    base = pd.Timestamp("2025-01-01")
    filas = [_fila("X", f"g{i}", base + pd.Timedelta(days=i, hours=9), -5.0, "gasto") for i in range(40)]
    for i, m in ((30, 100.0), (39, 50.0)):
        filas.append(_fila("X", f"i{i}", base + pd.Timedelta(days=i, hours=12), m, "ingreso"))
    h = pd.DataFrame(filas)
    f = construir_features(h, date(2025, 2, 10), cfg_modelo)  # día 40 = 2025-02-10
    assert f["ingreso_28d"] == 150.0
    assert f["ingreso_56d"] == 150.0
    assert f["n_ingresos_28d"] == 2
    assert f["dias_desde_ultimo_ingreso"] == 0
    assert f["mediana_ingreso_dia_28d"] == 0.0
    assert f["dia_semana"] == date(2025, 2, 10).weekday()
    assert f["dia_mes"] == 10
    assert f["mes_sin"] == pytest.approx(math.sin(2 * math.pi * 2 / 12))
    assert f["mes_cos"] == pytest.approx(math.cos(2 * math.pi * 2 / 12))


def test_historia_corta_lanza_historia_insuficiente(historia, cfg_modelo):
    inicio = historia["fecha_hora"].min().normalize()
    dos_semanas = inicio + pd.Timedelta(days=14)
    corta = historia[historia["fecha_hora"] < dos_semanas]
    with pytest.raises(HistoriaInsuficiente):
        construir_features(corta, dos_semanas.date(), cfg_modelo)


def test_historia_vacia_antes_de_la_fecha_lanza_historia_insuficiente(historia, cfg_modelo):
    with pytest.raises(HistoriaInsuficiente):
        construir_features(historia, date(2000, 1, 1), cfg_modelo)
