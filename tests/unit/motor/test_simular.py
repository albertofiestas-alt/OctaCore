"""motor.simular (opción C): "¿y si cobro S/250 el día 2?" o "¿y si gasto S/50 hoy?".

Prueba clave del plan (sección 8): con el caso de 100 y 300, un ingreso extra de 250 el día 2 cambia
el número de hoy de 0 a un valor positivo y el semáforo del pago del día 3 mejora; sin ingreso extra
el resultado es idéntico a decidir.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from contratos import Escenario, EstadoPersona, IngresoExtra, Pronostico
from motor import decidir
from motor.simular import simular
from motor.verificador import textos_sin_origen


def _esc(*ingresos, gasto_hoy=0.0):
    return Escenario(ingresos_extra=tuple(IngresoExtra(dia=d, monto=m) for d, m in ingresos), gasto_hoy=gasto_hoy)


def test_ingreso_extra_cambia_el_numero_y_mejora_el_semaforo(
    estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg
):
    base = decidir(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg)
    sim = simular(estado_caso_orden_pagos, pronostico_caso_orden_pagos, _esc((2, 250)), cfg)

    assert base.numero_hoy == 0
    assert base.por_pago[0].semaforo == "rojo"
    # día 3: 100 + 0 + 250 - 300 = 50 -> 16.67/día; día 14: 100 + 400 + 250 - 300 = 450 -> 32.14/día
    assert sim.numero_hoy == 16
    assert sim.mensaje_falta is None
    assert sim.por_pago[0].semaforo == "verde"


def test_escenario_vacio_es_identico_a_decidir(estado_tipico, pronostico_tipico, cfg):
    assert simular(estado_tipico, pronostico_tipico, Escenario(), cfg) == decidir(estado_tipico, pronostico_tipico, cfg)


def test_gasto_hoy_baja_el_numero(estado_tipico, pronostico_tipico, cfg):
    # gastar 70 hoy: día 14 pasa de 280 a 210 -> 15/día
    sim = simular(estado_tipico, pronostico_tipico, _esc(gasto_hoy=70), cfg)
    assert sim.numero_hoy == 15
    assert sim.desglose["saldo"] == 330.0


def test_ingreso_extra_solo_cuenta_desde_su_dia(estado_tipico, pronostico_tipico, cfg):
    # 140 el día 10: no ayuda a los días 5 y 9, sí al 14 (280 + 140 = 420 -> 30/día); el 14 sigue limitando (30 < 45.56)
    sim = simular(estado_tipico, pronostico_tipico, _esc((10, 140)), cfg)
    puntos = {p["dia"]: p for p in sim.desglose["puntos_de_control"]}
    assert puntos[5]["ingreso_extra"] == 0
    assert puntos[9]["ingreso_extra"] == 0
    assert puntos[14]["ingreso_extra"] == 140
    assert puntos[14]["numerador"] == 420
    assert sim.numero_hoy == 30


def test_simulacion_es_transparente(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg):
    sim = simular(estado_caso_orden_pagos, pronostico_caso_orden_pagos, _esc((2, 250), gasto_hoy=20), cfg)
    assert sim.evidencia["escenario"] == {"gasto_hoy": 20.0, "ingresos_extra": [{"dia": 2, "monto": 250.0}]}
    assert sim.desglose["ingresos_extra"] == [{"dia": 2, "monto": 250.0}]
    assert any("simulación" in s.lower() for s in sim.supuestos)
    assert textos_sin_origen(estado_caso_orden_pagos, sim) == []


def test_propuesta_simulada_no_choca_con_la_real(estado_tipico, pronostico_tipico, cfg):
    real = decidir(estado_tipico, pronostico_tipico, cfg)
    sim = simular(estado_tipico, pronostico_tipico, _esc(gasto_hoy=1), cfg)
    assert real.propuestas and sim.propuestas
    assert sim.propuestas[0].propuesta_id != real.propuestas[0].propuesta_id
    assert sim.propuestas[0].propuesta_id.endswith(":simulada")


def test_es_pura(estado_tipico, pronostico_tipico, cfg):
    antes = (estado_tipico.model_dump(), pronostico_tipico.model_dump())
    esc = _esc((2, 100), gasto_hoy=10)
    a = simular(estado_tipico, pronostico_tipico, esc, cfg)
    b = simular(estado_tipico, pronostico_tipico, esc, cfg)
    assert a == b
    assert (estado_tipico.model_dump(), pronostico_tipico.model_dump()) == antes


def test_gasto_mayor_que_el_saldo_no_rompe(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg):
    sim = simular(estado_caso_orden_pagos, pronostico_caso_orden_pagos, _esc(gasto_hoy=5000), cfg)
    assert sim.numero_hoy == 0
    assert "faltan S/5200" in sim.mensaje_falta


@pytest.mark.parametrize(
    "datos",
    [
        {"ingresos_extra": [{"dia": 15, "monto": 10}]},
        {"ingresos_extra": [{"dia": 2, "monto": 10001}]},
        {"ingresos_extra": [{"dia": 1, "monto": 1}] * 4},
        {"gasto_hoy": -1},
    ],
)
def test_escenario_fuera_de_rango_se_rechaza_antes_del_motor(datos):
    # Validación del plan: día 0..14, monto 0..10000, máximo 3 ingresos extra (lo hace el contrato Escenario).
    with pytest.raises(ValidationError):
        Escenario.model_validate(datos)


def test_pago_con_estado_sin_pagos(cfg):
    estado = EstadoPersona.model_validate(
        {"customer_id": "P9", "fecha_corte": "2025-01-01", "saldo": 0, "pagos": [], "semanas_historia": 10}
    )
    pron = Pronostico.model_validate(
        {"por_horizonte": {h: {"p5": 0, "p20": 0, "p50": 0, "p80": 0} for h in (3, 7, 14)}}
    )
    sim = simular(estado, pron, _esc((0, 140)), cfg)
    assert sim.numero_hoy == 10  # 140 / 14
