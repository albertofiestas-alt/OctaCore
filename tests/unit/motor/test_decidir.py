"""Pruebas del motor de decisión (plan de Sebastián, sección 10).

Las funciones puras (ingreso_conservador, permitido, semaforo, confianza, ...) se
prueban directo; las de decidir completo necesitan motor.plantillas.
"""

from __future__ import annotations

import pytest

from contratos import Decision, EstadoPersona, Pronostico
from motor import con_registro_id, decidir
from motor.decidir import (
    confianza,
    construir_desglose,
    construir_evidencia,
    ingreso_conservador,
    numerador,
    permitido,
    proponer,
    puntos_de_control,
    semaforo,
    semaforo_con_gasto,
)

CLAVES_DESGLOSE = {
    "saldo",
    "colchon",
    "cuantil",
    "numero_hoy",
    "puntos_de_control",
    "dia_limitante",
    "faltante",
    "registro_id",
}
CLAVES_PUNTO = {"dia", "ingreso_conservador", "pagos_acumulados", "numerador", "permitido"}
CLAVES_EVIDENCIA = {
    "semanas_historia",
    "pagos_detectados",
    "rango_14d",
    "cuantil_usado",
    "ancho_relativo",
    "punto_limite",
}


# --------------------------------------------------------------------------- #
# Ayudas para construir casos
# --------------------------------------------------------------------------- #


def _estado(saldo, pagos=(), colchon=0.0, semanas=12, customer_id="T0001"):
    return EstadoPersona.model_validate(
        {
            "customer_id": customer_id,
            "fecha_corte": "2025-11-14",
            "saldo": saldo,
            "colchon": colchon,
            "semanas_historia": semanas,
            "pagos": [
                {"pago_id": f"p{i}-d{dia}", "dia": dia, "monto": monto, "categoria": cat}
                for i, (dia, monto, cat) in enumerate(
                    (p if len(p) == 3 else (*p, "servicios")) for p in pagos
                )
            ],
        }
    )


def _cuantil(p5, p20, p50, p80):
    return {"p5": p5, "p20": p20, "p50": p50, "p80": p80}


def _pron(h3, h7, h14):
    return Pronostico.model_validate({"por_horizonte": {3: _cuantil(*h3), 7: _cuantil(*h7), 14: _cuantil(*h14)}})


# --------------------------------------------------------------------------- #
# Funciones puras
# --------------------------------------------------------------------------- #


def test_ingreso_conservador_usa_el_mayor_horizonte_menor_o_igual(pronostico_tipico):
    assert ingreso_conservador(pronostico_tipico, 0, 0.2) == 0.0
    assert ingreso_conservador(pronostico_tipico, 2, 0.2) == 0.0
    assert ingreso_conservador(pronostico_tipico, 3, 0.2) == 60.0
    assert ingreso_conservador(pronostico_tipico, 6, 0.2) == 60.0
    assert ingreso_conservador(pronostico_tipico, 8, 0.2) == 200.0
    assert ingreso_conservador(pronostico_tipico, 14, 0.05) == 250.0
    assert ingreso_conservador(pronostico_tipico, 30, 0.2) == 420.0  # d > 14 usa h = 14
    # El cuantil se compara con tolerancia (0.2 y 0.20000000001 son el mismo).
    assert ingreso_conservador(pronostico_tipico, 14, 0.2 + 1e-12) == 420.0


def test_puntos_de_control_agrupa_dias_y_agrega_el_14(estado_tipico):
    assert puntos_de_control(estado_tipico) == [5, 9, 14]
    assert puntos_de_control(_estado(100)) == [14]
    assert puntos_de_control(_estado(100, [(0, 10), (0, 20), (5, 1)])) == [0, 5, 14]


def test_numerador_y_permitido_caso_tipico(estado_tipico, pronostico_tipico, cfg):
    assert numerador(estado_tipico, pronostico_tipico, 5, 0.2, cfg) == pytest.approx(330.0)
    assert numerador(estado_tipico, pronostico_tipico, 5, 0.2, cfg, con_colchon=False) == pytest.approx(380.0)
    assert permitido(estado_tipico, pronostico_tipico, 5, 0.2, cfg) == pytest.approx(66.0)
    assert permitido(estado_tipico, pronostico_tipico, 9, 0.2, cfg) == pytest.approx(410 / 9)
    assert permitido(estado_tipico, pronostico_tipico, 14, 0.2, cfg) == pytest.approx(20.0)
    assert permitido(estado_tipico, pronostico_tipico, 14, 0.05, cfg) == pytest.approx(110 / 14)


def test_semaforo_verde_ambar_rojo(cfg):
    estado = _estado(100, [(1, 50), (7, 80), (10, 200)])
    pron = _pron((0, 0, 0, 0), (0, 50, 100, 150), (0, 50, 100, 150))
    assert semaforo(estado, pron, 1, cfg) == "verde"  # 100 - 50 >= 0 con P5
    assert semaforo(estado, pron, 7, cfg) == "ambar"  # P5: -30; P50: +70
    assert semaforo(estado, pron, 10, cfg) == "rojo"  # P50: 100 + 100 - 330 < 0


def test_semaforo_no_descuenta_colchon(cfg):
    estado = _estado(300, [(5, 300)], colchon=100)
    pron = _pron((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))
    assert semaforo(estado, pron, 5, cfg) == "verde"


def test_semaforo_con_gasto_caso_tipico(estado_tipico, pronostico_tipico, cfg):
    assert semaforo_con_gasto(estado_tipico, pronostico_tipico, 14, 20, cfg) == "ambar"
    assert semaforo_con_gasto(estado_tipico, pronostico_tipico, 14, 7, cfg) == "verde"
    assert semaforo_con_gasto(estado_tipico, pronostico_tipico, 14, 0, cfg) == semaforo(
        estado_tipico, pronostico_tipico, 14, cfg
    )


def test_confianza_alta_media_baja(estado_tipico, pronostico_tipico, cfg):
    pron_alta = _pron((0, 0, 0, 0), (0, 0, 0, 0), (500, 550, 600, 700))  # ancho 0.33
    pron_baja = _pron((0, 0, 0, 0), (0, 0, 0, 0), (0, 50, 100, 200))  # ancho 2.0
    assert confianza(estado_tipico, pron_alta, cfg) == "alta"
    assert confianza(estado_tipico, pronostico_tipico, cfg) == "media"  # ancho 0.95
    assert confianza(estado_tipico, pron_baja, cfg) == "baja"


def test_confianza_baja_con_poca_historia(estado_tipico, cfg):
    pron_alta = _pron((0, 0, 0, 0), (0, 0, 0, 0), (500, 550, 600, 700))
    poca = estado_tipico.model_copy(update={"semanas_historia": 2})
    assert confianza(poca, pron_alta, cfg) == "baja"


def test_proponer_caso_tipico(estado_tipico, pronostico_tipico, cfg):
    props = proponer(estado_tipico, pronostico_tipico, cfg, 20, "media", texto=lambda datos: "x")
    assert len(props) == 1
    p = props[0]
    assert p.monto == 13
    assert p.pago_id == "P0002:Financiera Ficticia:2025-11-28"
    assert p.propuesta_id == "P0002:2025-11-14:apartar_p5:P0002:Financiera Ficticia:2025-11-28"
    assert p.antes == {"numero_hoy": 20, "semaforo_pago_limite": "ambar"}
    assert p.despues == {"numero_hoy": 7, "semaforo_pago_limite": "verde"}
    assert p.confianza == "media"


def test_proponer_pasa_los_datos_a_la_plantilla(estado_tipico, pronostico_tipico, cfg):
    vistos = []
    proponer(estado_tipico, pronostico_tipico, cfg, 20, "media", texto=lambda datos: vistos.append(datos) or "x")
    assert vistos == [
        {
            "g5": 7,
            "numero_hoy": 20,
            "apartar": 13,
            "pago_id": "P0002:Financiera Ficticia:2025-11-28",
            "dia": 14,
            "monto": 350.0,
            "categoria": "deuda",
        }
    ]


def test_proponer_limite_en_dia_14_sin_pago_usa_el_ultimo_pago(cfg):
    estado = _estado(200, [(5, 50)], semanas=10)
    pron = _pron((0, 50, 60, 70), (0, 50, 60, 70), (0, 300, 400, 450))
    # P20: d5 40, d14 32.14 -> 32. P5: d5 30, d14 10.71 -> 10 (mínimo en el día 14 sin pago).
    props = proponer(estado, pron, cfg, 32, "media", texto=lambda datos: "x")
    assert len(props) == 1
    assert props[0].pago_id == "p0-d5"
    assert props[0].monto == 22


def test_proponer_sin_pagos_no_propone(cfg):
    estado = _estado(100)
    pron = _pron((0, 0, 0, 0), (0, 0, 0, 0), (0, 180, 200, 210))
    assert proponer(estado, pron, cfg, 20, "media", texto=lambda datos: "x") == []


def test_proponer_g5_negativo_o_suficiente_no_propone(estado_tipico, cfg):
    pron_iguales = _pron((60, 60, 60, 60), (200, 200, 200, 200), (420, 420, 420, 420))
    assert proponer(estado_tipico, pron_iguales, cfg, 20, "alta", texto=lambda datos: "x") == []
    pron_p5_cero = _pron((0, 60, 120, 210), (0, 200, 320, 450), (0, 420, 600, 820))
    # P5 a 14 días: 400 - 490 - 50 < 0 -> g5 negativo, sin propuesta.
    assert proponer(estado_tipico, pron_p5_cero, cfg, 20, "baja", texto=lambda datos: "x") == []


def test_construir_desglose_claves_exactas(estado_tipico, pronostico_tipico, cfg):
    des = construir_desglose(estado_tipico, pronostico_tipico, cfg)
    assert set(des) == CLAVES_DESGLOSE
    assert des["numero_hoy"] == 20
    assert des["dia_limitante"] == 14
    assert des["faltante"] is None
    assert des["registro_id"] == ""
    assert des["cuantil"] == "p20"
    assert [set(p) for p in des["puntos_de_control"]] == [CLAVES_PUNTO] * 3
    assert [p["permitido"] for p in des["puntos_de_control"]] == [66.0, 45.56, 20.0]
    assert [p["pagos_acumulados"] for p in des["puntos_de_control"]] == [80.0, 140.0, 490.0]
    assert [p["ingreso_conservador"] for p in des["puntos_de_control"]] == [60.0, 200.0, 420.0]
    assert [p["numerador"] for p in des["puntos_de_control"]] == [330.0, 410.0, 280.0]


def test_construir_evidencia_claves(estado_tipico, pronostico_tipico, cfg):
    ev = construir_evidencia(estado_tipico, pronostico_tipico, cfg)
    assert set(ev) == CLAVES_EVIDENCIA
    assert ev["semanas_historia"] == 20
    assert ev["pagos_detectados"] == 3
    assert ev["rango_14d"] == {"p5": 250.0, "p20": 420.0, "p50": 600.0, "p80": 820.0}
    assert ev["cuantil_usado"] == "p20"
    assert ev["ancho_relativo"] == 0.95
    assert ev["punto_limite"] == {"dia": 14, "pago_id": "P0002:Financiera Ficticia:2025-11-28", "permitido": 20.0}


# --------------------------------------------------------------------------- #
# decidir completo (usa motor.plantillas)
# --------------------------------------------------------------------------- #


def test_caso_tipico(estado_tipico, pronostico_tipico, cfg):
    d = decidir(estado_tipico, pronostico_tipico, cfg)
    assert isinstance(d, Decision)
    assert d.numero_hoy == 20
    assert d.mensaje_falta is None
    assert d.desglose["dia_limitante"] == 14
    assert [p.permitido for p in d.por_pago] == [66.0, 45.56, 20.0]
    assert [p.semaforo for p in d.por_pago] == ["verde", "verde", "verde"]
    assert d.confianza == "media"
    assert len(d.propuestas) == 1
    prop = d.propuestas[0]
    assert prop.monto == 13
    assert prop.despues["numero_hoy"] == 7
    assert prop.texto  # lo escribe plantillas.texto_propuesta
    assert d.explicacion_fuente == "plantilla"
    assert d.respaldo is False
    assert d.registro_id == ""


def test_pago_justo_cubierto_verde(cfg):
    estado = _estado(300, [(5, 300)])
    pron = _pron((0, 0, 10, 20), (0, 0, 10, 20), (0, 100, 200, 300))
    d = decidir(estado, pron, cfg)
    assert d.numero_hoy == 0
    assert d.mensaje_falta is None  # el mínimo es 0, no negativo: está cubierto
    assert d.por_pago[0].semaforo == "verde"


def test_pago_justo_cubierto_ambar(cfg):
    estado = _estado(250, [(5, 300)])
    pron = _pron((0, 20, 60, 80), (0, 20, 60, 80), (0, 100, 200, 300))
    d = decidir(estado, pron, cfg)
    assert d.por_pago[0].semaforo == "ambar"
    assert d.numero_hoy == 0
    assert d.mensaje_falta == "no alcanza para el pago del dia 5: faltan S/30"


def test_sin_pagos_solo_dia_14(cfg):
    estado = _estado(100)
    pron = _pron((0, 0, 0, 0), (0, 0, 0, 0), (0, 180, 200, 210))
    d = decidir(estado, pron, cfg)
    assert d.numero_hoy == 20  # (100 + 180) / 14
    assert d.por_pago == []
    assert [p["dia"] for p in d.desglose["puntos_de_control"]] == [14]
    assert d.desglose["dia_limitante"] == 14
    assert d.desglose["puntos_de_control"][0]["ingreso_conservador"] == 180.0
    assert d.propuestas == []


def test_pago_dia_cero_y_dos_pagos_mismo_dia(cfg):
    estado = _estado(200, [(0, 20), (0, 30), (5, 10), (5, 15)])
    pron = _pron((10, 20, 30, 40), (10, 20, 30, 40), (100, 200, 300, 400))
    d = decidir(estado, pron, cfg)
    assert [p["dia"] for p in d.desglose["puntos_de_control"]] == [0, 5, 14]
    assert d.desglose["puntos_de_control"][0]["permitido"] == 150.0  # divisor max(0, 1)
    assert d.desglose["puntos_de_control"][1]["pagos_acumulados"] == 75.0
    assert len(d.por_pago) == 4
    assert d.numero_hoy == int(min(150.0, (200 + 20 - 75) / 5, (200 + 200 - 75) / 14))


def test_semaforo_en_decision(cfg):
    estado = _estado(100, [(1, 50), (7, 80), (10, 200)])
    pron = _pron((0, 0, 0, 0), (0, 50, 100, 150), (0, 50, 100, 150))
    d = decidir(estado, pron, cfg)
    assert [p.semaforo for p in d.por_pago] == ["verde", "ambar", "rojo"]


def test_redondeo_hacia_abajo_45_9(cfg):
    estado = _estado(145.9, [(1, 100)])
    pron = _pron((0, 0, 0, 0), (0, 0, 0, 0), (1000, 1000, 1000, 1000))
    d = decidir(estado, pron, cfg)
    assert d.desglose["puntos_de_control"][0]["numerador"] == pytest.approx(45.9)
    assert d.numero_hoy == 45
    assert isinstance(d.desglose["numero_hoy"], int)


def test_faltante_hacia_arriba(cfg):
    estado = _estado(100.4, [(3, 300)])
    pron = _pron((0, 0, 0, 0), (0, 0, 0, 0), (300, 400, 500, 600))
    d = decidir(estado, pron, cfg)
    assert d.mensaje_falta == "no alcanza para el pago del dia 3: faltan S/200"  # ceil(199.6)
    assert d.desglose["faltante"] == 200


def test_cuantiles_iguales_sin_excepcion(cfg):
    estado = _estado(100, [(4, 50)])
    pron = _pron((100, 100, 100, 100), (100, 100, 100, 100), (100, 100, 100, 100))
    d = decidir(estado, pron, cfg)
    assert d.numero_hoy >= 0
    assert d.propuestas == []  # g5 == g20: no hace falta proponer
    assert d.confianza == "alta"  # ancho 0


def test_saldo_negativo_sin_excepcion(cfg):
    estado = _estado(-50, [(2, 10)])
    pron = _pron((0, 0, 0, 0), (0, 0, 0, 0), (100, 100, 100, 100))
    d = decidir(estado, pron, cfg)
    assert d.numero_hoy == 0
    assert d.mensaje_falta == "no alcanza para el pago del dia 2: faltan S/60"
    assert d.propuestas == []


def test_saldo_negativo_sin_pagos_nombra_el_dia_14(cfg):
    estado = _estado(-50)
    pron = _pron((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))
    d = decidir(estado, pron, cfg)
    assert d.numero_hoy == 0
    assert d.mensaje_falta == "no alcanza para el pago del dia 14: faltan S/50"


def test_empate_elige_el_dia_menor(cfg):
    # d5: (100 - 50) / 5 = 10; d14: (100 + 90 - 50) / 14 = 10.
    estado = _estado(100, [(5, 50)])
    pron = _pron((0, 0, 0, 0), (0, 0, 0, 0), (90, 90, 90, 90))
    d = decidir(estado, pron, cfg)
    assert d.desglose["dia_limitante"] == 5
    assert d.numero_hoy == 10


def test_pureza(estado_tipico, pronostico_tipico, cfg):
    antes_estado = estado_tipico.model_dump()
    antes_pron = pronostico_tipico.model_dump()
    antes_cfg = repr(cfg)
    d1 = decidir(estado_tipico, pronostico_tipico, cfg)
    d2 = decidir(estado_tipico, pronostico_tipico, cfg)
    assert estado_tipico.model_dump() == antes_estado
    assert pronostico_tipico.model_dump() == antes_pron
    assert repr(cfg) == antes_cfg
    assert d1 == d2


def test_poca_historia_confianza_baja_sin_propuestas(estado_tipico, pronostico_tipico, cfg):
    poca = estado_tipico.model_copy(update={"semanas_historia": 2})
    d = decidir(poca, pronostico_tipico, cfg)
    assert d.confianza == "baja"
    assert d.propuestas == []
    assert d.numero_hoy == 20


@pytest.mark.parametrize(
    "caso",
    [
        "tipico",
        "orden_pagos",
        "sin_pagos",
        "saldo_negativo",
        "poca_historia",
    ],
)
def test_supuestos_evidencia_limites_no_vacios(
    caso, estado_tipico, pronostico_tipico, estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg
):
    pron_cero = _pron((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))
    estado, pron = {
        "tipico": (estado_tipico, pronostico_tipico),
        "orden_pagos": (estado_caso_orden_pagos, pronostico_caso_orden_pagos),
        "sin_pagos": (_estado(100), pronostico_tipico),
        "saldo_negativo": (_estado(-50, [(2, 10)]), pron_cero),
        "poca_historia": (estado_tipico.model_copy(update={"semanas_historia": 1}), pronostico_tipico),
    }[caso]
    d = decidir(estado, pron, cfg)
    assert d.supuestos and all(d.supuestos)
    assert d.limites and all(d.limites)
    assert d.evidencia and set(d.evidencia) == CLAVES_EVIDENCIA
    assert d.confianza in {"alta", "media", "baja"}
    assert d.explicacion
    assert set(d.desglose) == CLAVES_DESGLOSE


def test_desglose_orden_pagos(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg):
    d = decidir(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg)
    assert d.desglose["dia_limitante"] == 3
    assert d.desglose["faltante"] == 200
    assert d.por_pago[0].semaforo == "rojo"
    assert d.evidencia["punto_limite"]["pago_id"] == "alquiler-03"


def test_con_registro_id(estado_tipico, pronostico_tipico, cfg):
    d = decidir(estado_tipico, pronostico_tipico, cfg)
    d2 = con_registro_id(d, "reg-123")
    assert d2.registro_id == "reg-123"
    assert d2.desglose["registro_id"] == "reg-123"
    # El original no cambia (copia, no mutación).
    assert d.registro_id == ""
    assert d.desglose["registro_id"] == ""
    # El resto queda igual.
    assert d2.model_dump(exclude={"registro_id", "desglose"}) == d.model_dump(exclude={"registro_id", "desglose"})
