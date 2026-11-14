"""Casos de estrés del motor (Anexo C): sin excepción y con salida coherente."""

from __future__ import annotations

import math
from datetime import date

import pytest

from contratos import Decision, EstadoPersona, PagoConFecha, Pronostico
from motor import decidir
from motor.plantillas import LIMITES_FIJOS
from motor.verificador import textos_sin_origen


def _estado(saldo, pagos, colchon=0.0, semanas=8) -> EstadoPersona:
    return EstadoPersona(
        customer_id="ESTRES",
        fecha_corte=date(2026, 3, 1),
        saldo=saldo,
        pagos=[PagoConFecha(pago_id=f"E{i}", dia=d, monto=m, categoria="otros") for i, (d, m) in enumerate(pagos)],
        colchon=colchon,
        semanas_historia=semanas,
    )


def _pron(p5, p20, p50, p80) -> Pronostico:
    return Pronostico(por_horizonte={h: {"p5": p5, "p20": p20, "p50": p50, "p80": p80} for h in (3, 7, 14)})


def _coherente(estado: EstadoPersona, d: Decision) -> None:
    """Invariantes que debe cumplir cualquier Decision."""
    assert d.numero_hoy >= 0 and float(d.numero_hoy).is_integer()
    assert d.numero_hoy == d.desglose["numero_hoy"]
    assert len(d.por_pago) == len(estado.pagos)
    assert d.supuestos and d.evidencia and d.explicacion
    assert all(f in d.limites for f in LIMITES_FIJOS)
    assert textos_sin_origen(estado, d) == []
    faltante = d.desglose["faltante"]
    if faltante is None:
        assert d.mensaje_falta is None
    else:
        assert d.numero_hoy == 0
        assert isinstance(faltante, int) and faltante > 0
        assert d.mensaje_falta == f"no alcanza para el pago del dia {d.desglose['dia_limitante']}: faltan S/{faltante}"
    for prop in d.propuestas:
        assert 0 <= prop.despues["numero_hoy"] < d.numero_hoy


def test_montos_enormes_saldo_alcanza(cfg):
    estado = _estado(1e7, [(5, 1e7 / 2), (14, 1e6)])
    d = decidir(estado, _pron(1e7, 1e7, 1e7, 1e7), cfg)
    _coherente(estado, d)
    # permitido día 5: (1e7 + 1e7 - 5e6) / 5 = 3e6 ; día 14: (2e7 - 6e6) / 14 = 1e6
    assert d.numero_hoy == 1_000_000


def test_montos_enormes_pago_impagable(cfg):
    estado = _estado(100.0, [(3, 1e7)])
    d = decidir(estado, _pron(0, 0, 0, 0), cfg)
    _coherente(estado, d)
    assert d.numero_hoy == 0
    assert d.desglose["faltante"] == math.ceil(1e7 - 100)
    assert all(p.semaforo == "rojo" for p in d.por_pago)


def test_cincuenta_pagos_el_mismo_dia(cfg):
    estado = _estado(5000.0, [(7, 50.0)] * 50, colchon=10)
    d = decidir(estado, _pron(100, 200, 300, 400), cfg)
    _coherente(estado, d)
    # Se agrupan en un solo punto de control (7) más el 14.
    assert [p["dia"] for p in d.desglose["puntos_de_control"]] == [7, 14]
    assert d.desglose["puntos_de_control"][0]["pagos_acumulados"] == 2500.0
    assert d.evidencia["pagos_detectados"] == 50
    # día 7: (5000 + 200 - 2500 - 10) / 7 = 384.28 ; día 14: 2690/14 = 192.14
    assert d.numero_hoy == 192


def test_todos_los_pagos_el_dia_cero(cfg):
    estado = _estado(300.0, [(0, 100.0), (0, 150.0), (0, 80.0)])
    d = decidir(estado, _pron(0, 50, 100, 150), cfg)
    _coherente(estado, d)
    # día 0 (divisor 1): 300 - 330 = -30 -> no alcanza, faltan 30.
    assert d.numero_hoy == 0
    assert d.desglose["dia_limitante"] == 0
    assert d.desglose["faltante"] == 30
    assert all(p.semaforo == "rojo" for p in d.por_pago)


def test_todos_los_pagos_el_dia_cero_cubiertos(cfg):
    estado = _estado(1000.0, [(0, 100.0), (0, 150.0)])
    d = decidir(estado, _pron(0, 0, 0, 0), cfg)
    _coherente(estado, d)
    # día 0: 750/1 ; día 14: 750/14 = 53.57
    assert d.numero_hoy == 53
    assert all(p.semaforo == "verde" for p in d.por_pago)


def test_pronostico_todo_cero(cfg):
    estado = _estado(280.0, [(5, 100.0), (10, 40.0)], colchon=0)
    d = decidir(estado, _pron(0, 0, 0, 0), cfg)
    _coherente(estado, d)
    # día 5: 180/5 = 36 ; día 10: 140/10 = 14 ; día 14: 140/14 = 10
    assert d.numero_hoy == 10
    assert d.propuestas == []  # g5 == g20: no hay nada que apartar
    assert d.evidencia["ancho_relativo"] == 0.0


@pytest.mark.parametrize("saldo", [-500.0, 0.0])
def test_pronostico_todo_cero_sin_saldo(cfg, saldo):
    estado = _estado(saldo, [])
    d = decidir(estado, _pron(0, 0, 0, 0), cfg)
    _coherente(estado, d)
    assert d.numero_hoy == 0
    if saldo < 0:
        assert d.mensaje_falta == "no alcanza para el pago del dia 14: faltan S/500"
    else:
        assert d.mensaje_falta is None


def test_pago_en_el_dia_30(cfg):
    estado = _estado(600.0, [(30, 300.0)])
    d = decidir(estado, _pron(100, 150, 200, 250), cfg)
    _coherente(estado, d)
    # día 14: (600 + 150) / 14 = 53.57 ; día 30: usa h=14 -> (750 - 300) / 30 = 15
    assert [p["dia"] for p in d.desglose["puntos_de_control"]] == [14, 30]
    assert d.desglose["dia_limitante"] == 30
    assert d.numero_hoy == 15


def test_mezcla_de_todo(cfg):
    pagos = [(0, 1e7)] + [(3, 2000.0)] * 50 + [(30, 0.0)]
    estado = _estado(-1e7, pagos, colchon=200, semanas=0)
    d = decidir(estado, _pron(0, 0, 0, 0), cfg)
    _coherente(estado, d)
    assert d.numero_hoy == 0
    assert d.confianza == "baja"
    assert d.propuestas == []
