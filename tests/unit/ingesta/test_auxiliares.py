"""Pruebas de proximos_pagos, semanas_historia y cargar_etiquetas."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest

from contratos import PagoInferido
from ingesta import ErrorIngesta
from ingesta.auxiliares import cargar_etiquetas, proximos_pagos, semanas_historia

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "movimientos_minimo.csv"


def _p(dia, comercio="Casero", cid="P1", monto=-300.0, cat="alquiler"):
    return {"customer_id": cid, "comercio": comercio, "categoria": cat, "monto": monto, "dia_mes": dia}


def test_ventana_y_orden():
    pagos = [_p(20, "B"), _p(17, "A"), _p(30, "Lejos"), _p(5, "Pasado"), _p(1, "Otro", cid="P2")]
    r = proximos_pagos(pagos, "P1", date(2025, 3, 15))
    assert [x.pago_id for x in r] == ["P1:A:2025-03-17", "P1:B:2025-03-20"]
    assert [x.dia for x in r] == [2, 5]
    assert all(x.monto == 300.0 for x in r)


def test_ventana_inclusiva_y_personalizada():
    assert len(proximos_pagos([_p(29)], "P1", date(2025, 3, 15))) == 1  # día 14
    assert proximos_pagos([_p(30)], "P1", date(2025, 3, 15)) == []  # día 15
    assert len(proximos_pagos([_p(30)], "P1", date(2025, 3, 15), ventana=15)) == 1


def test_cambio_de_mes_y_anio():
    r = proximos_pagos([_p(3)], "P1", date(2025, 3, 25))
    assert r[0].pago_id == "P1:Casero:2025-04-03" and r[0].dia == 9
    r = proximos_pagos([_p(5)], "P1", date(2025, 12, 28))
    assert r[0].pago_id == "P1:Casero:2026-01-05" and r[0].dia == 8


def test_dia_31_en_febrero():
    assert proximos_pagos([_p(31)], "P1", date(2025, 2, 20))[0].pago_id == "P1:Casero:2025-02-28"
    assert proximos_pagos([_p(31)], "P1", date(2024, 2, 20))[0].pago_id == "P1:Casero:2024-02-29"
    # 28 de febrero con pago el 31: es hoy (día 0)
    assert proximos_pagos([_p(31)], "P1", date(2025, 2, 28))[0].dia == 0
    # 1 de marzo: el 31 de marzo está a 30 días, fuera de ventana
    assert proximos_pagos([_p(31)], "P1", date(2025, 3, 1)) == []


def test_pago_de_hoy_es_dia_cero():
    r = proximos_pagos([_p(15)], "P1", date(2025, 3, 15))
    assert r[0].dia == 0 and r[0].pago_id.endswith("2025-03-15")


def test_fecha_corte_datetime_y_pago_inferido():
    pi = PagoInferido(customer_id="P1", comercio="Luz", categoria="servicios", monto=80, dia_mes=18)
    r = proximos_pagos([pi], "P1", datetime(2025, 3, 15, 23, 59))
    assert r[0].dia == 3 and r[0].categoria == "servicios" and r[0].monto == 80


def test_persona_sin_pagos():
    assert proximos_pagos([_p(16)], "P9", date(2025, 3, 15)) == []
    assert proximos_pagos([], "P1", date(2025, 3, 15)) == []


def _mov(*filas):
    return pd.DataFrame(filas, columns=["customer_id", "fecha_hora"]).assign(
        fecha_hora=lambda d: pd.to_datetime(d["fecha_hora"], format="ISO8601")
    )


def test_semanas_historia():
    m = _mov(("P1", "2025-01-01 10:00"), ("P1", "2025-02-01"), ("P2", "2025-03-01"))
    assert semanas_historia(m, "P1", date(2025, 1, 29)) == 4
    assert semanas_historia(m, "P1", date(2025, 1, 28)) == 3
    assert semanas_historia(m, "P1", datetime(2025, 3, 1, 8)) == 8


def test_semanas_historia_sin_datos_o_futuros():
    m = _mov(("P1", "2025-02-01"))
    assert semanas_historia(m, "P9", date(2025, 3, 1)) == 0
    assert semanas_historia(m.iloc[0:0], "P1", date(2025, 3, 1)) == 0
    assert semanas_historia(m, "P1", date(2025, 1, 1)) == 0  # solo movimientos posteriores


def test_cargar_etiquetas_fixture():
    e = cargar_etiquetas(FIXTURE)
    assert e.index.name == "transaction_id" and e.index.is_unique
    assert list(e.columns) == ["es_duplicado", "es_atipico", "pago_con_fecha", "arquetipo"]
    for c in ("es_duplicado", "es_atipico", "pago_con_fecha"):
        assert e[c].dtype == bool
    assert bool(e.loc["T000003", "pago_con_fecha"]) is True
    assert e.loc["T000001", "arquetipo"] == "conductor"


def test_cargar_etiquetas_primer_registro_por_id(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text(
        "customer_id,transaction_id,fecha_hora,monto,moneda,tipo,categoria,comercio,es_atipico\n"
        "P1,T1,2025-01-01,10,PEN,ingreso,otros,X,True\n"
        "P1,T1,2025-01-01,10,PEN,ingreso,otros,X,False\n",
        encoding="utf-8",
    )
    e = cargar_etiquetas(f)
    assert list(e.columns) == ["es_atipico"] and len(e) == 1 and bool(e.loc["T1", "es_atipico"]) is True


def test_cargar_etiquetas_sin_etiquetas(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text(
        "customer_id,transaction_id,fecha_hora,monto,moneda,tipo,categoria,comercio\nP1,T1,2025-01-01,10,PEN,ingreso,otros,X\n",
        encoding="utf-8",
    )
    with pytest.raises(ErrorIngesta):
        cargar_etiquetas(f)
