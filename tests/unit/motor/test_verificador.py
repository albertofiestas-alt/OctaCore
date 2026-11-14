"""Pruebas de src/motor/verificador.py (sección 4 tarea 5: toda cifra de los textos tiene origen)."""

from __future__ import annotations

from datetime import date

import pytest

from contratos import EstadoPersona, PagoConFecha, Pronostico
from motor import decidir
from motor.verificador import cifras_en_texto, cifras_permitidas, textos_sin_origen

# --------------------------------------------------------------------------- #
# cifras_en_texto
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("S/1,234.50", [1234.5]),
        ("faltan S/200.", [200.0]),
        ("faltan S/200", [200.0]),
        ("vence el día 14", [14.0]),
        ("del día 14.", [14.0]),
        ("S/45.56 en 3 días", [45.56, 3.0]),
        ("Puedes gastar hasta S/20 hoy.", [20.0]),
        ("S/1,234,567.89 y S/7", [1234567.89, 7.0]),
        ("los días 3,7,14", [3.0, 7.0, 14.0]),
        ("S/12,34", [12.0, 34.0]),  # coma que no es de miles: dos números
        ("Confianza: media.", []),
        ("", []),
        ("(S/300)", [300.0]),
        ("hoy: 0", [0.0]),
    ],
)
def test_cifras_en_texto(texto, esperado):
    assert cifras_en_texto(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "El escenario P20 es una semana mala y el P5 una semana muy mala.",
        "P50 y P80 son escenarios.",
        "p5, p20.",
    ],
)
def test_cifras_en_texto_ignora_etiquetas_de_cuantil(texto):
    assert cifras_en_texto(texto) == []


def test_cifras_en_texto_solo_ignora_las_etiquetas_no_los_montos():
    # P5 se ignora, pero el monto que le sigue no.
    assert cifras_en_texto("En P5 gastarías S/5.") == [5.0]
    # P7 no es etiqueta de cuantil: tampoco es una cifra suelta (va pegado a una letra).
    assert cifras_en_texto("el código P7") == []


# --------------------------------------------------------------------------- #
# cifras_permitidas y textos_sin_origen
# --------------------------------------------------------------------------- #


def test_cifras_permitidas_incluye_estado_desglose_y_redondeos(estado_tipico, pronostico_tipico, cfg):
    d = decidir(estado_tipico, pronostico_tipico, cfg)
    ok = cifras_permitidas(estado_tipico, d)
    # estado: saldo, colchón, semanas, número de pagos, días y montos
    for x in (400.0, 50.0, float(estado_tipico.semanas_historia), 3.0, 5.0, 80.0, 9.0, 60.0, 14.0, 350.0):
        assert x in ok
    # decisión: número de hoy, permitidos redondeados (45.56) y sus floor/ceil
    assert 20.0 in ok
    assert 45.56 in ok and 45.0 in ok and 46.0 in ok
    # propuesta: apartar 13 y g5 = 7
    assert 13.0 in ok and 7.0 in ok


def test_decisiones_reales_no_tienen_cifras_sin_origen(
    estado_tipico, pronostico_tipico, estado_caso_orden_pagos, pronostico_caso_orden_pagos, cfg
):
    for estado, pron in ((estado_tipico, pronostico_tipico), (estado_caso_orden_pagos, pronostico_caso_orden_pagos)):
        d = decidir(estado, pron, cfg)
        assert textos_sin_origen(estado, d) == []


def test_cifra_inventada_en_la_explicacion_se_detecta(estado_tipico, pronostico_tipico, cfg):
    """Caso que DEBE fallar: una cifra que no sale de ningún lado."""
    d = decidir(estado_tipico, pronostico_tipico, cfg)
    falsa = d.model_copy(update={"explicacion": d.explicacion + " Te sobran S/987.65 al mes."})
    problemas = textos_sin_origen(estado_tipico, falsa)
    assert problemas
    assert any("987.65" in p for p in problemas)


def test_cifra_inventada_en_propuesta_supuesto_y_mensaje_se_detecta(estado_tipico, pronostico_tipico, cfg):
    d = decidir(estado_tipico, pronostico_tipico, cfg)
    prop = d.propuestas[0].model_copy(update={"texto": "Aparta S/4321 por día."})
    falsa = d.model_copy(
        update={
            "propuestas": [prop],
            "supuestos": [*d.supuestos, "Ganas 1,111 al mes."],
            "mensaje_falta": "no alcanza para el pago del dia 99: faltan S/5",
        }
    )
    problemas = textos_sin_origen(estado_tipico, falsa)
    for cifra in ("4321", "1111", "99"):
        assert any(p.startswith(cifra + " ") for p in problemas), (cifra, problemas)


def test_porcentaje_inventado_se_detecta(estado_tipico, pronostico_tipico, cfg):
    d = decidir(estado_tipico, pronostico_tipico, cfg)
    falsa = d.model_copy(update={"limites": [*d.limites, "Acierta el 83 de cada 100 veces."]})
    assert len(textos_sin_origen(estado_tipico, falsa)) == 2


def test_saldo_negativo_se_acepta_sin_signo(cfg):
    estado = EstadoPersona(
        customer_id="NEG", fecha_corte=date(2026, 3, 1), saldo=-125.5, pagos=[], colchon=0, semanas_historia=8
    )
    pron = Pronostico(por_horizonte={h: {"p5": 0, "p20": 0, "p50": 0, "p80": 0} for h in (3, 7, 14)})
    d = decidir(estado, pron, cfg)
    assert 125.5 in cifras_permitidas(estado, d)
    assert textos_sin_origen(estado, d) == []


def test_textos_sin_origen_no_muta_entradas(estado_tipico, pronostico_tipico, cfg):
    d = decidir(estado_tipico, pronostico_tipico, cfg)
    antes = (estado_tipico.model_dump(), d.model_dump())
    textos_sin_origen(estado_tipico, d)
    assert (estado_tipico.model_dump(), d.model_dump()) == antes


def test_montos_con_decimales_redondeados_a_dos(cfg):
    estado = EstadoPersona(
        customer_id="DEC",
        fecha_corte=date(2026, 3, 1),
        saldo=1000.0,
        pagos=[PagoConFecha(pago_id="a", dia=5, monto=123.456, categoria="servicios")],
        colchon=0,
        semanas_historia=8,
    )
    pron = Pronostico(por_horizonte={h: {"p5": 10, "p20": 20, "p50": 30, "p80": 40} for h in (3, 7, 14)})
    d = decidir(estado, pron, cfg)
    assert textos_sin_origen(estado, d) == []
