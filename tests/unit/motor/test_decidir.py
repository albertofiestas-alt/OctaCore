"""Motor de respaldo (src/motor/__init__.py): decidir(estado, pronostico, cfg).

Casos del Plan 04 (sección 10) y fixtures de tests/fixtures. Función pura: sin archivos ni hora.
"""

from __future__ import annotations

import copy
import random
import re
from datetime import date

import pytest

from contratos import Decision, EstadoPersona, Pronostico
from motor import decidir


def estado(saldo, pagos=(), colchon=0.0, semanas=12, cliente="P0001"):
    return EstadoPersona(
        customer_id=cliente, fecha_corte=date(2025, 3, 1), saldo=saldo, colchon=colchon, semanas_historia=semanas,
        pagos=[{"pago_id": f"pago-{i}", "dia": d, "monto": m, "categoria": c}
               for i, (d, m, c) in enumerate(pagos)])


def pron(h3=(0, 0, 0, 0), h7=(0, 0, 0, 0), h14=(0, 0, 0, 0)):
    def q(t):
        return dict(zip(("p5", "p20", "p50", "p80"), t))
    return Pronostico(por_horizonte={3: q(h3), 7: q(h7), 14: q(h14)})


# --- casos del plan -----------------------------------------------------------

def test_orden_de_pagos_es_sin_alcance(cfg, estado_caso_orden_pagos, pronostico_caso_orden_pagos, decision_sin_alcance):
    d = decidir(estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg)
    assert isinstance(d, Decision)
    assert d.numero_hoy == 0
    assert d.mensaje_falta == "no alcanza para el pago del dia 3: faltan S/200"
    esperado = decision_sin_alcance
    assert [p.model_dump() for p in d.por_pago] == [p.model_dump() for p in esperado.por_pago]
    assert d.confianza == esperado.confianza
    assert d.desglose == esperado.desglose
    assert d.supuestos == esperado.supuestos
    assert d.limites == esperado.limites
    assert d.propuestas == []


def test_caso_tipico_es_verde_con_propuesta(cfg, estado_tipico, pronostico_tipico, decision_verde):
    d = decidir(estado_tipico, pronostico_tipico, cfg)
    esperado = decision_verde
    assert d.numero_hoy == 20
    assert [p.model_dump() for p in d.por_pago] == [p.model_dump() for p in esperado.por_pago]
    assert d.confianza == "media"
    assert d.desglose == esperado.desglose
    assert d.supuestos == esperado.supuestos
    assert d.limites == esperado.limites
    assert d.mensaje_falta is None
    (prop,) = d.propuestas
    assert prop.monto == 13.0 and prop.pago_id == esperado.propuestas[0].pago_id
    assert prop.texto.startswith("Gasta hasta S/7 por día y aparta S/13 por día")
    assert prop.antes == {"numero_hoy": 20, "cubierto_en_p5": False}
    assert prop.despues == {"numero_hoy": 7, "cubierto_en_p5": True}
    assert prop.propuesta_id == "P0002-2025-11-14-1"


def test_pago_justo_cubierto(cfg):
    d = decidir(estado(100, [(5, 100, "alquiler")]), pron(), cfg)
    assert d.numero_hoy == 0 and d.mensaje_falta is None
    assert d.por_pago[0].semaforo == "verde"  # cobertura exacta 0 con P5


def test_sin_pagos_solo_punto_de_control_14(cfg):
    d = decidir(estado(0), pron(h14=(0, 280, 300, 400)), cfg)
    assert d.numero_hoy == 20  # 280 / 14
    assert d.desglose["puntos_de_control"] == [
        {"dia": 14, "ingreso_conservador": 280.0, "pagos_acumulados": 0.0, "permitido": 20.0}]


def test_pago_el_dia_cero_y_dos_el_mismo_dia(cfg):
    d = decidir(estado(500, [(0, 100, "servicios"), (0, 50, "servicios"), (4, 30, "otros")]), pron(), cfg)
    assert d.numero_hoy >= 0
    assert [p["dia"] for p in d.desglose["puntos_de_control"]] == [0, 4, 14]  # dia 0 agrupado, divisor max(d, 1)
    assert d.desglose["puntos_de_control"][0]["permitido"] == 350.0


def test_redondeo_siempre_hacia_abajo(cfg):
    assert decidir(estado(0), pron(h14=(0, 642.6, 700, 800)), cfg).numero_hoy == 45  # 45.9


def test_faltante_se_redondea_hacia_arriba(cfg):
    d = decidir(estado(100, [(3, 300.5, "alquiler")]), pron(), cfg)
    assert d.mensaje_falta == "no alcanza para el pago del dia 3: faltan S/201"


def test_cuantiles_iguales_y_saldo_negativo_sin_excepcion(cfg):
    d = decidir(estado(-50, [(2, 10, "otros")]), pron(h14=(100, 100, 100, 100)), cfg)
    assert d.numero_hoy == 0
    assert d.mensaje_falta.startswith("no alcanza para el pago del dia 2")
    assert d.confianza in ("alta", "media", "baja")


def test_colchon_resta_del_numerador(cfg):
    sin = decidir(estado(0), pron(h14=(0, 280, 300, 400)), cfg).numero_hoy
    con = decidir(estado(0, colchon=70), pron(h14=(0, 280, 300, 400)), cfg).numero_hoy
    assert (sin, con) == (20, 15)


def test_cuantil_conservador_sale_del_cfg(cfg):
    p = pron(h14=(70, 280, 300, 400))
    assert decidir(estado(0), p, cfg).numero_hoy == 20
    assert decidir(estado(0), p, cfg.con(cuantil_conservador=0.05)).numero_hoy == 5


# --- semáforo ------------------------------------------------------------------

@pytest.mark.parametrize("p5,p50,esperado", [(200, 300, "verde"), (50, 200, "ambar"), (0, 100, "rojo")])
def test_semaforo(cfg, p5, p50, esperado):
    # saldo 100, pago 250 el día 7; cobertura = 100 + ingreso(7) - 250
    p = pron(h7=(p5, p5, p50, p50 + 100), h14=(p5, p5, p50, p50 + 100))
    d = decidir(estado(100, [(7, 250, "alquiler")]), p, cfg)
    assert d.por_pago[0].semaforo == esperado


# --- confianza -------------------------------------------------------------------

@pytest.mark.parametrize("h14,semanas,esperado", [
    ((400, 450, 500, 600), 12, "alta"),     # ancho 0.4 < 0.5
    ((250, 420, 600, 820), 12, "media"),    # ancho 0.95
    ((150, 700, 900, 1400), 12, "baja"),    # ancho 1.39 > 1.2
    ((400, 450, 500, 600), 3, "baja"),      # poca historia, aunque el ancho sea bueno
])
def test_confianza(cfg, h14, semanas, esperado):
    assert decidir(estado(0, semanas=semanas), pron(h14=h14), cfg).confianza == esperado


def test_poca_historia_no_propone_y_lo_dice(cfg):
    e = estado(300, [(6, 250, "alquiler")], semanas=2)
    d = decidir(e, pron(h14=(0, 120, 300, 700)), cfg)
    assert d.confianza == "baja" and d.propuestas == []
    assert d.limites[-1] == "Hay menos de 4 semanas de historia: solo se muestra el número de hoy, sin propuestas."
    assert "2 semanas" in d.explicacion


def test_umbrales_sin_fijar_es_error_claro(cfg):
    sin = cfg.con(umbrales_confianza=None, preregistro={})
    with pytest.raises(ValueError, match="umbrales_confianza"):
        decidir(estado(0), pron(), sin)


# --- propuesta -------------------------------------------------------------------

def test_no_propone_si_g5_es_negativo(cfg):
    d = decidir(estado(100, [(3, 300, "alquiler")]), pron(h14=(0, 400, 500, 600)), cfg)
    assert d.propuestas == []


def test_no_propone_si_g5_alcanza_el_numero(cfg):
    d = decidir(estado(1000, [(5, 100, "servicios")]), pron(h3=(50, 50, 50, 50), h7=(900, 900, 900, 900),
                                                           h14=(900, 900, 900, 900)), cfg)
    assert d.propuestas == []


# --- pureza, propiedades y textos -------------------------------------------------

def test_pureza_no_cambia_entradas_y_es_determinista(cfg, estado_tipico, pronostico_tipico):
    e0, p0 = copy.deepcopy(estado_tipico), copy.deepcopy(pronostico_tipico)
    a = decidir(estado_tipico, pronostico_tipico, cfg)
    b = decidir(estado_tipico, pronostico_tipico, cfg)
    assert estado_tipico == e0 and pronostico_tipico == p0
    assert a == b
    assert a.respaldo is False and a.registro_id == ""  # los pone el servicio


def _caso_aleatorio(rng):
    h = [sorted(rng.uniform(0, 600) for _ in range(4)) for _ in range(3)]
    pagos = [(rng.randint(0, 14), round(rng.uniform(10, 400), 2), "otros") for _ in range(rng.randint(0, 4))]
    return (round(rng.uniform(-100, 800), 2), pagos, rng.choice([0, 0, 25, 60]),
            pron(tuple(h[0]), tuple(h[1]), tuple(h[2])))


def test_propiedades_en_600_casos_aleatorios(cfg):
    rng = random.Random(7)
    for _ in range(600):
        saldo, pagos, colchon, p = _caso_aleatorio(rng)
        d = decidir(estado(saldo, pagos, colchon), p, cfg)
        assert d.numero_hoy >= 0 and d.numero_hoy == int(d.numero_hoy)
        # monotonía: más saldo nunca baja el número
        assert decidir(estado(saldo + 50, pagos, colchon), p, cfg).numero_hoy >= d.numero_hoy
        # más pagos nunca lo suben
        mas = pagos + [(rng.randint(0, 14), 40.0, "otros")]
        assert decidir(estado(saldo, mas, colchon), p, cfg).numero_hoy <= d.numero_hoy
        # propuesta: gastando g por día, ningún punto queda descubierto en P5 (con colchón)
        for prop in d.propuestas:
            g = prop.despues["numero_hoy"]
            assert 0 <= g < d.numero_hoy and prop.monto == d.numero_hoy - g
            for dia in {x[0] for x in pagos} | {14}:
                ing5 = max([p.por_horizonte[h].p5 for h in (3, 7, 14) if h <= dia] or [0.0])
                acumulado = sum(m for dd, m, _ in pagos if dd <= dia)
                assert saldo + ing5 - acumulado - colchon - g * dia >= -1e-6


def test_toda_cifra_de_los_textos_tiene_origen(cfg, estado_tipico, pronostico_tipico):
    d = decidir(estado_tipico, pronostico_tipico, cfg)
    permitidas = {str(int(x)) for x in (
        d.numero_hoy, estado_tipico.semanas_historia, len(estado_tipico.pagos), 14, 4, 5, 20,
        *[p.monto for p in estado_tipico.pagos], *[p.dia for p in estado_tipico.pagos],
        *[pp.monto for pp in d.propuestas], *[pp.despues["numero_hoy"] for pp in d.propuestas])}
    textos = [d.explicacion, *d.supuestos, *d.limites, *[p.texto for p in d.propuestas]]
    for t in textos:
        for cifra in re.findall(r"\d+", t):
            assert cifra in permitidas, f"cifra {cifra} sin origen en: {t}"


def test_decision_rojo_construida(cfg):
    e = estado(200, [(2, 60, "servicios"), (9, 600, "alquiler")], semanas=10)
    p = pron(h3=(0, 0, 0, 0), h7=(100, 320, 400, 500), h14=(150, 700, 900, 1400))
    d = decidir(e, p, cfg)
    assert d.numero_hoy == 0
    assert d.mensaje_falta == "no alcanza para el pago del dia 9: faltan S/140"
    assert [x.semaforo for x in d.por_pago] == ["verde", "rojo"]
    assert d.confianza == "baja" and d.propuestas == []
    assert "faltan S/140" in d.explicacion
