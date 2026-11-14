"""Casos de estrés del motor (Anexo C de la propuesta v9): sin excepción y con salida coherente.

Fila "Escenarios de estrés" de la v9: 20 o más casos extremos, sin errores; los casos inviables se
declaran, no se ocultan. Cada caso lleva en un comentario el cálculo HECHO A MANO (número de hoy,
faltante, semáforo) y pasa por _coherente (invariantes + textos_sin_origen vacío).

Configuración usada en las cuentas: cuantil conservador P20, propuesta con P5, umbral de historia
4 semanas, confianza alta si ancho < 0.5 y baja si ancho > 1.2 (ancho = (p80 - p5) / max(p50, 1) a 14 días).

Tabla Anexo C -> prueba (las filas de "Archivos" y el calendario real son de la ingesta, de Mathias):

| Anexo C                                  | Prueba en este archivo                                             |
|------------------------------------------|--------------------------------------------------------------------|
| Ingresos: ocho semanas sin ingreso       | test_ocho_semanas_sin_ingreso, test_pronostico_todo_cero           |
| Ingresos: un ingreso grande al final     | test_un_solo_ingreso_grande_al_final_de_la_ventana                 |
| Ingresos: ingreso enorme el día del pago | test_ingreso_enorme_el_mismo_dia_del_pago                          |
| Pagos: pago 10 veces el saldo            | test_pago_diez_veces_mayor_que_el_saldo, test_montos_enormes_pago_impagable |
| Pagos: dos pagos el mismo día            | test_cincuenta_pagos_el_mismo_dia, test_todos_los_pagos_el_dia_cero*|
| Pagos: pago el día 0 y el día 14         | test_pago_el_dia_cero_y_el_dia_catorce                             |
| Pagos: sin ningún pago con fecha         | test_pronostico_todo_cero_sin_saldo, test_colchon_mayor_que_el_saldo_sin_pagos |
| Pagos: pagos con monto cero              | test_pagos_con_monto_cero, test_mezcla_de_todo                     |
| Pagos: pago fuera de la ventana (día 30) | test_pago_en_el_dia_30                                             |
| Saldo: saldo negativo inicial            | test_pronostico_todo_cero_sin_saldo[-500], test_mezcla_de_todo     |
| Saldo: saldo cero                        | test_saldo_cero, test_pronostico_todo_cero_sin_saldo[0]            |
| Saldo: saldo enorme                      | test_saldo_enorme, test_montos_enormes_saldo_alcanza               |
| Saldo: colchón mayor que el saldo        | test_colchon_mayor_que_el_saldo*                                   |
| Historia: un día / menos de 4 semanas    | test_historia_corta_confianza_baja_sin_propuesta[0, 3, 4]          |
| Calendario: mes de 28, 31, bisiesto      | test_calendario_no_cambia_la_decision[...] (el motor usa días relativos) |
| Modelo: cuantiles iguales                | test_cuantiles_iguales                                             |
| Modelo: pronóstico todo cero             | test_pronostico_todo_cero                                          |
| Modelo: cuantiles cruzados               | INVIABLE declarado: test_inviable_rechazado_por_el_contrato        |
| Modelo: pronóstico con negativos         | INVIABLE declarado: test_inviable_rechazado_por_el_contrato        |
| Montos NaN, infinito, negativos          | INVIABLE declarado: test_inviable_rechazado_por_el_contrato        |
| Simular: gasto hoy enorme                | test_simular_gasto_hoy_enorme                                      |
| Simular: 3 ingresos extra el mismo día   | test_simular_tres_ingresos_extra_el_mismo_dia                      |
| Simular: ingreso extra el día 0 y el 14  | test_simular_ingreso_extra_dia_cero_y_catorce                      |
| Simular: escenario fuera de rango        | INVIABLE declarado: test_inviable_rechazado_por_el_contrato        |

Casos INVIABLES: el contrato (src/contratos/modelos.py) los rechaza con ValidationError ANTES de llegar
al motor, así que el motor nunca los ve. Se declaran aquí, no se ocultan.

Observación de diseño (no es fallo, lo pide el plan de Sebastián, sección 5): el faltante descuenta el
colchón y el semáforo no. Por eso, con colchón mayor que el saldo, el mensaje puede decir "no alcanza
para el pago del dia 7" mientras ese pago está en verde (ver test_colchon_mayor_que_el_saldo).
"""

from __future__ import annotations

import math
from datetime import date

import pytest
from pydantic import ValidationError

from contratos import Cuantiles, Decision, Escenario, EstadoPersona, IngresoExtra, PagoConFecha, Pronostico
from motor import decidir
from motor.plantillas import LIMITES_FIJOS
from motor.simular import simular
from motor.verificador import textos_sin_origen


def _estado(saldo, pagos, colchon=0.0, semanas=8, fecha=date(2026, 3, 1)) -> EstadoPersona:
    return EstadoPersona(
        customer_id="ESTRES",
        fecha_corte=fecha,
        saldo=saldo,
        pagos=[PagoConFecha(pago_id=f"E{i}", dia=d, monto=m, categoria="otros") for i, (d, m) in enumerate(pagos)],
        colchon=colchon,
        semanas_historia=semanas,
    )


def _pron(p5, p20, p50, p80) -> Pronostico:
    return Pronostico(por_horizonte={h: {"p5": p5, "p20": p20, "p50": p50, "p80": p80} for h in (3, 7, 14)})


def _pron_h(c3, c7, c14) -> Pronostico:
    """Pronóstico distinto por horizonte: cada cN es (p5, p20, p50, p80)."""
    return Pronostico(
        por_horizonte={h: dict(zip(("p5", "p20", "p50", "p80"), c)) for h, c in ((3, c3), (7, c7), (14, c14))}
    )


def _esc(*ingresos, gasto_hoy=0.0) -> Escenario:
    return Escenario(ingresos_extra=tuple(IngresoExtra(dia=d, monto=m) for d, m in ingresos), gasto_hoy=gasto_hoy)


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


# --------------------------------------------------------------------------- #
# Ingresos
# --------------------------------------------------------------------------- #


def test_ocho_semanas_sin_ingreso(cfg):
    # Ocho semanas sin ingreso -> el modelo pronostica cero en todos los horizontes.
    estado = _estado(500.0, [(7, 200.0)], semanas=8)
    d = decidir(estado, _pron(0, 0, 0, 0), cfg)
    _coherente(estado, d)
    # día 7: (500 - 200) / 7 = 42.86 ; día 14: 300 / 14 = 21.43 -> 21. Sin faltante.
    # semáforo día 7 (P5): 500 - 200 = 300 >= 0 -> verde. ancho 0 -> alta. g5 == g20 -> sin propuesta.
    assert d.numero_hoy == 21
    assert d.desglose["faltante"] is None
    assert d.por_pago[0].semaforo == "verde"
    assert d.confianza == "alta"
    assert d.propuestas == []


def test_un_solo_ingreso_grande_al_final_de_la_ventana(cfg):
    # Solo el horizonte 14 trae ingreso: no rescata el pago del día 10 (que usa h=7, con ingreso 0).
    estado = _estado(100.0, [(10, 500.0)])
    pron = _pron_h((0, 0, 0, 0), (0, 0, 0, 0), (1000, 2000, 3000, 4000))
    d = decidir(estado, pron, cfg)
    _coherente(estado, d)
    # día 10: (100 + 0 - 500) / 10 = -40 ; día 14: (100 + 2000 - 500) / 14 = 114.29
    # mínimo -40 en el día 10 -> número 0, faltante ceil(400) = 400.
    # semáforo día 10: P5 100 - 500 < 0 y P50 100 - 500 < 0 -> rojo.
    # ancho (4000 - 1000) / 3000 = 1.0 -> media. g5 < 0 -> sin propuesta.
    assert d.numero_hoy == 0
    assert d.desglose["dia_limitante"] == 10
    assert d.desglose["faltante"] == 400
    assert d.por_pago[0].semaforo == "rojo"
    assert d.confianza == "media"
    assert d.propuestas == []


def test_ingreso_enorme_el_mismo_dia_del_pago(cfg):
    # El ingreso del horizonte 7 cuenta para el pago del día 7 (acumulado hasta d inclusive).
    estado = _estado(50.0, [(7, 1000.0)])
    pron = _pron_h((0, 0, 0, 0), (1e6, 1e6, 1e6, 1e6), (1e6, 1e6, 1e6, 1e6))
    d = decidir(estado, pron, cfg)
    _coherente(estado, d)
    # día 7: (50 + 1e6 - 1000) / 7 = 142721.43 ; día 14: 999050 / 14 = 71360.71 -> 71360.
    # semáforo día 7: 50 + 1e6 - 1000 >= 0 -> verde. ancho 0 -> alta.
    assert d.numero_hoy == 71360
    assert d.desglose["dia_limitante"] == 14
    assert d.por_pago[0].semaforo == "verde"
    assert d.confianza == "alta"


# --------------------------------------------------------------------------- #
# Pagos
# --------------------------------------------------------------------------- #


def test_pago_diez_veces_mayor_que_el_saldo(cfg):
    estado = _estado(200.0, [(5, 2000.0)])
    d = decidir(estado, _pron(100, 300, 600, 900), cfg)
    _coherente(estado, d)
    # día 5 (h=3): (200 + 300 - 2000) / 5 = -300 ; día 14: -1500 / 14 = -107.14
    # mínimo -300 en el día 5 -> número 0, faltante 1500.
    # semáforo: P5 200 + 100 - 2000 < 0, P50 200 + 600 - 2000 < 0 -> rojo.
    # ancho (900 - 100) / 600 = 1.33 > 1.2 -> baja.
    assert d.numero_hoy == 0
    assert d.desglose["dia_limitante"] == 5
    assert d.desglose["faltante"] == 1500
    assert d.mensaje_falta == "no alcanza para el pago del dia 5: faltan S/1500"
    assert d.por_pago[0].semaforo == "rojo"
    assert d.confianza == "baja"


def test_pago_el_dia_cero_y_el_dia_catorce(cfg):
    estado = _estado(1000.0, [(0, 300.0), (14, 400.0)])
    d = decidir(estado, _pron(0, 140, 280, 420), cfg)
    _coherente(estado, d)
    # día 0 (divisor 1, h=0): 1000 - 300 = 700 ; día 14: (1000 + 140 - 700) / 14 = 31.43 -> 31.
    # semáforos: día 0 P5 700 >= 0 verde ; día 14 P5 1000 + 0 - 700 = 300 >= 0 verde.
    # g5 = 300 / 14 = 21.43 < 31 -> propuesta: después 21, apartar 10, pago del día 14.
    assert [p["dia"] for p in d.desglose["puntos_de_control"]] == [0, 14]
    assert d.numero_hoy == 31
    assert d.desglose["dia_limitante"] == 14
    assert [p.semaforo for p in d.por_pago] == ["verde", "verde"]
    assert len(d.propuestas) == 1
    assert d.propuestas[0].monto == 10
    assert d.propuestas[0].despues["numero_hoy"] == 21
    assert d.propuestas[0].pago_id == "E1"


def test_pagos_con_monto_cero(cfg):
    estado = _estado(300.0, [(3, 0.0), (9, 0.0)])
    d = decidir(estado, _pron(0, 0, 0, 0), cfg)
    _coherente(estado, d)
    # día 3: 300 / 3 = 100 ; día 9: 300 / 9 = 33.33 ; día 14: 300 / 14 = 21.43 -> 21.
    # semáforos: 300 >= 0 -> verde los dos.
    assert [p["dia"] for p in d.desglose["puntos_de_control"]] == [3, 9, 14]
    assert d.numero_hoy == 21
    assert d.desglose["dia_limitante"] == 14
    assert [p.permitido for p in d.por_pago] == [100.0, 33.33]
    assert all(p.semaforo == "verde" for p in d.por_pago)


# --------------------------------------------------------------------------- #
# Saldo y colchón
# --------------------------------------------------------------------------- #


def test_saldo_cero(cfg):
    estado = _estado(0.0, [(7, 100.0)])
    d = decidir(estado, _pron(50, 150, 200, 250), cfg)
    _coherente(estado, d)
    # día 7: (0 + 150 - 100) / 7 = 7.14 ; día 14: 50 / 14 = 3.57 -> 3.
    # semáforo día 7: P5 0 + 50 - 100 = -50 < 0 ; P50 200 - 100 = 100 >= 0 -> ambar.
    # ancho (250 - 50) / 200 = 1.0 -> media. g5 día 7 = -50 / 7 < 0 -> sin propuesta.
    assert d.numero_hoy == 3
    assert d.desglose["faltante"] is None
    assert d.por_pago[0].semaforo == "ambar"
    assert d.confianza == "media"
    assert d.propuestas == []


def test_saldo_enorme(cfg):
    estado = _estado(1e9, [(7, 500.0)])
    d = decidir(estado, _pron(0, 0, 0, 0), cfg)
    _coherente(estado, d)
    # día 7: 999999500 / 7 = 142857071.43 ; día 14: 999999500 / 14 = 71428535.71 -> 71428535.
    assert d.numero_hoy == 71_428_535
    assert d.desglose["dia_limitante"] == 14
    assert d.por_pago[0].semaforo == "verde"


def test_colchon_mayor_que_el_saldo(cfg):
    estado = _estado(100.0, [(7, 50.0)], colchon=500.0)
    d = decidir(estado, _pron(0, 0, 0, 0), cfg)
    _coherente(estado, d)
    # día 7: (100 - 50 - 500) / 7 = -64.29 ; día 14: -450 / 14 = -32.14
    # mínimo en el día 7 -> número 0, faltante ceil(450) = 450.
    # semáforo SIN colchón (plan, sección 5): 100 - 50 = 50 >= 0 -> verde. Es el diseño, no un fallo.
    assert d.numero_hoy == 0
    assert d.desglose["faltante"] == 450
    assert d.mensaje_falta == "no alcanza para el pago del dia 7: faltan S/450"
    assert d.por_pago[0].semaforo == "verde"


def test_colchon_mayor_que_el_saldo_sin_pagos(cfg):
    estado = _estado(100.0, [], colchon=500.0)
    d = decidir(estado, _pron(0, 0, 0, 0), cfg)
    _coherente(estado, d)
    # Solo el día 14: (100 - 500) / 14 = -28.57 -> número 0, faltante 400.
    assert d.numero_hoy == 0
    assert d.desglose["faltante"] == 400
    assert d.mensaje_falta == "no alcanza para el pago del dia 14: faltan S/400"


# --------------------------------------------------------------------------- #
# Historia y calendario
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("semanas", "confianza", "n_propuestas"),
    [(0, "baja", 0), (3, "baja", 0), (4, "alta", 1)],
)
def test_historia_corta_confianza_baja_sin_propuesta(cfg, semanas, confianza, n_propuestas):
    # 0 semanas (un solo día de historia) y 3 (< 4) -> baja y sin propuesta; 4 llega al umbral.
    estado = _estado(500.0, [(7, 100.0)], semanas=semanas)
    d = decidir(estado, _pron(40, 50, 60, 65), cfg)
    _coherente(estado, d)
    # día 7: (500 + 50 - 100) / 7 = 64.29 ; día 14: 450 / 14 = 32.14 -> 32 (no depende de la historia).
    # ancho (65 - 40) / 60 = 0.42 < 0.5 -> alta solo si hay historia suficiente.
    # g5 = (500 + 40 - 100) / 14 = 31.43 < 32 -> propuesta (después 31, apartar 1) si hay historia.
    assert d.numero_hoy == 32
    assert d.confianza == confianza
    assert len(d.propuestas) == n_propuestas
    if n_propuestas:
        assert d.propuestas[0].monto == 1
        assert d.propuestas[0].pago_id == "E0"  # el 14 no tiene pago: se nombra el último <= 14


@pytest.mark.parametrize("fecha", [date(2028, 2, 29), date(2027, 2, 28), date(2026, 1, 31)], ids=str)
def test_calendario_no_cambia_la_decision(cfg, fecha):
    # Bisiesto, mes de 28 y de 31 días: el motor trabaja con días relativos a la fecha de corte,
    # así que la decisión es la misma (pasar de fechas a días es tarea de la ingesta).
    pagos = [(1, 80.0), (13, 120.0)]
    pron = _pron(20, 60, 90, 120)
    base = decidir(_estado(400.0, pagos), pron, cfg)
    estado = _estado(400.0, pagos, fecha=fecha)
    d = decidir(estado, pron, cfg)
    _coherente(estado, d)
    # día 1: (400 - 80) / 1 = 320 ; día 13 (h=7): (400 + 60 - 200) / 13 = 20 ; día 14: 260 / 14 = 18.57 -> 18.
    assert d.numero_hoy == base.numero_hoy == 18
    assert d.desglose == base.desglose
    assert d.por_pago == base.por_pago


# --------------------------------------------------------------------------- #
# Modelo
# --------------------------------------------------------------------------- #


def test_cuantiles_iguales(cfg):
    estado = _estado(100.0, [(5, 250.0)])
    d = decidir(estado, _pron(200, 200, 200, 200), cfg)
    _coherente(estado, d)
    # día 5 (h=3): (100 + 200 - 250) / 5 = 10 ; día 14: 50 / 14 = 3.57 -> 3.
    # semáforo P5: 50 >= 0 -> verde. ancho 0 -> alta. g5 == g20 -> sin propuesta.
    assert d.numero_hoy == 3
    assert d.por_pago[0].semaforo == "verde"
    assert d.confianza == "alta"
    assert d.evidencia["ancho_relativo"] == 0.0
    assert d.propuestas == []


# --------------------------------------------------------------------------- #
# Simular (opción C)
# --------------------------------------------------------------------------- #


def test_simular_gasto_hoy_enorme(cfg):
    estado = _estado(500.0, [(7, 100.0)])
    d = simular(estado, _pron(0, 0, 0, 0), _esc(gasto_hoy=10000.0), cfg)  # 10000: máximo del contrato
    _coherente(estado, d)
    # saldo simulado 500 - 10000 = -9500. día 7: (-9500 - 100) / 7 = -1371.43 ; día 14: -9600 / 14 = -685.71
    # mínimo en el día 7 -> número 0, faltante 9600. semáforo: -9600 con P5 y P50 -> rojo.
    assert d.numero_hoy == 0
    assert d.desglose["saldo"] == -9500.0
    assert d.desglose["faltante"] == 9600
    assert d.mensaje_falta == "no alcanza para el pago del dia 7: faltan S/9600"
    assert d.por_pago[0].semaforo == "rojo"
    assert d.evidencia["escenario"]["gasto_hoy"] == 10000.0


def test_simular_tres_ingresos_extra_el_mismo_dia(cfg):
    estado = _estado(100.0, [(5, 400.0)])
    pron = _pron(0, 0, 0, 0)
    base = decidir(estado, pron, cfg)
    d = simular(estado, pron, _esc((5, 100.0), (5, 100.0), (5, 100.0)), cfg)
    _coherente(estado, d)
    # Sin escenario: día 5: (100 - 400) / 5 = -60 -> faltan 300.
    # Con 3 x 100 el día 5: día 5: (100 + 300 - 400) / 5 = 0 ; día 14: 0 / 14 = 0. Empate -> día 5.
    # Mínimo exactamente 0 (no negativo) -> número 0 y SIN faltante. semáforo P5: 0 >= 0 -> verde.
    assert base.desglose["faltante"] == 300
    assert d.numero_hoy == 0
    assert d.desglose["faltante"] is None
    assert d.desglose["dia_limitante"] == 5
    assert d.desglose["puntos_de_control"][0]["ingreso_extra"] == 300.0
    assert len(d.desglose["ingresos_extra"]) == 3
    assert d.por_pago[0].semaforo == "verde"


def test_simular_ingreso_extra_dia_cero_y_catorce(cfg):
    estado = _estado(100.0, [(3, 150.0), (14, 200.0)])
    pron = _pron(0, 0, 0, 0)
    d = simular(estado, pron, _esc((0, 100.0), (14, 500.0)), cfg)
    _coherente(estado, d)
    # día 3: (100 + 100 - 150) / 3 = 16.67 ; día 14: (100 + 600 - 350) / 14 = 25 -> número 16, día 3.
    # El extra del día 14 no ayuda al pago del día 3. Semáforos: 50 >= 0 y 350 >= 0 -> verde, verde.
    # Sin escenario: día 3: -50 / 3 = -16.67 ; día 14: (100 - 350) / 14 = -17.86 -> limita el 14, faltan 250.
    base = decidir(estado, pron, cfg)
    assert (base.desglose["dia_limitante"], base.desglose["faltante"]) == (14, 250)
    assert d.numero_hoy == 16
    assert d.desglose["dia_limitante"] == 3
    assert [p["ingreso_extra"] for p in d.desglose["puntos_de_control"]] == [100.0, 600.0]
    assert [p.semaforo for p in d.por_pago] == ["verde", "verde"]
    assert d.propuestas == []  # pronóstico cero: g5 == g20


# --------------------------------------------------------------------------- #
# Casos INVIABLES: inviable declarado, no oculto
# --------------------------------------------------------------------------- #
# El contrato los rechaza con ValidationError antes de que el motor los vea. Si algún día el
# contrato dejara de rechazarlos, esta prueba falla y obliga a decidir qué debe hacer el motor.

_C = {"p5": 10, "p20": 20, "p50": 30, "p80": 40}
_INVIABLES = {
    "cuantiles_cruzados": lambda: Cuantiles(p5=50, p20=20, p50=30, p80=40),
    "cuantiles_cruzados_en_pronostico": lambda: Pronostico(
        por_horizonte={3: _C, 7: _C, 14: {"p5": 10, "p20": 20, "p50": 30, "p80": 25}}
    ),
    "pronostico_negativo": lambda: _pron(-10, 0, 10, 20),
    "horizonte_faltante": lambda: Pronostico(por_horizonte={3: _C, 7: _C}),
    "horizonte_no_soportado": lambda: Pronostico(por_horizonte={3: _C, 7: _C, 14: _C, 30: _C}),
    "cuantil_nan": lambda: _pron(float("nan"), 0, 10, 20),
    "cuantil_infinito": lambda: _pron(0, 0, 10, float("inf")),
    "pago_monto_negativo": lambda: _estado(100.0, [(3, -50.0)]),
    "pago_dia_negativo": lambda: _estado(100.0, [(-1, 50.0)]),
    "pago_monto_infinito": lambda: _estado(100.0, [(3, float("inf"))]),
    "saldo_nan": lambda: _estado(float("nan"), []),
    "saldo_infinito": lambda: _estado(float("-inf"), []),
    "colchon_negativo": lambda: _estado(100.0, [], colchon=-1.0),
    "semanas_negativas": lambda: _estado(100.0, [], semanas=-1),
    "escenario_cuatro_ingresos": lambda: _esc((1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0)),
    "escenario_ingreso_dia_15": lambda: _esc((15, 100.0)),
    "escenario_gasto_negativo": lambda: _esc(gasto_hoy=-1.0),
}


@pytest.mark.parametrize("construir", list(_INVIABLES.values()), ids=list(_INVIABLES))
def test_inviable_rechazado_por_el_contrato(construir):
    # Inviable declarado, no oculto: nunca llega al motor.
    with pytest.raises(ValidationError):
        construir()
