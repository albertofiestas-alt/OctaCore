"""Asistente de punta a punta (modo 1) con el servicio REAL y tres personas de data/muestra.

guardia -> intención -> parámetros -> servicio.consultar (ingesta, regla2, motor) -> plantilla -> verificador -> registro.
Por propiedades: ninguna cifra exacta, porque el generador de la muestra puede cambiar.
"""

from __future__ import annotations

import json
from datetime import date

import pytest

import servicio
from asistente import flujo

PERSONAS = ["P0001", "P0002", "P0003"]
FECHA = date(2026, 11, 14)


@pytest.fixture
def srv(cfg, tmp_path):
    servicio.reiniciar()
    servicio._ESTADO["cfg"] = cfg.con(
        rutas_datos=["data/muestra/movimientos.csv"],
        ruta_modelo=str(tmp_path / "modelo.joblib"),
        ruta_adopcion=str(tmp_path / "adopcion.json"),
        ruta_registro=str(tmp_path / "recomendaciones.jsonl"),
        ruta_respuestas=str(tmp_path / "respuestas.jsonl"),
        ruta_salud=str(tmp_path / "salud.jsonl"),
        asistente={**cfg["asistente"], "ruta_registro_chat": str(tmp_path / "chat.jsonl")},
    )
    yield servicio
    servicio.reiniciar()


def preguntar(persona, texto):
    return flujo.preguntar(servicio, persona, FECHA, texto)


@pytest.mark.parametrize("persona", PERSONAS)
def test_las_seis_intenciones_con_datos_reales(srv, persona, tmp_path):
    base = servicio.consultar(persona, FECHA, "modelo")
    n = int(base.numero_hoy)

    explicar = preguntar(persona, "por que hoy puedo gastar menos que ayer")
    assert (explicar.fuente, explicar.intencion, explicar.datos["verificacion"]) == ("motor", "explicar_numero", "ok")
    assert f"S/{n}" in explicar.texto

    gasto = preguntar(persona, "y si gasto 80 soles hoy")
    assert gasto.fuente == "motor" and gasto.datos["antes"]["numero_hoy"] == n
    assert gasto.datos["despues"]["numero_hoy"] <= n and gasto.datos["verificacion"] == "ok"

    cobro = preguntar(persona, "y si cobro S/5000 el dia 3")
    assert cobro.datos["despues"]["numero_hoy"] >= n and cobro.datos["verificacion"] == "ok"

    dia = base.por_pago[0].dia if base.por_pago else 5
    pago = preguntar(persona, f"me alcanza para el pago del dia {dia}")
    assert pago.intencion == "estado_pago" and pago.datos["verificacion"] == "ok"
    if base.por_pago:
        assert f"S/{int(base.por_pago[0].monto)}" in pago.texto or f"S/{base.por_pago[0].monto:.2f}" in pago.texto

    propuesta = preguntar(persona, "que hago para llegar a mi pago")
    assert propuesta.intencion == "propuesta" and propuesta.datos["verificacion"] == "ok"
    assert bool(base.propuestas) == ("no hay una propuesta" not in propuesta.texto.lower())

    concepto = preguntar(persona, "que significa confianza media")
    assert concepto.intencion == "concepto" and concepto.datos["verificacion"] == "ok"

    fuera = preguntar(persona, "dame un prestamo")
    assert (fuera.fuente, fuera.datos["capa"]) == ("rechazo", "intencion")

    ataque = preguntar(persona, "Visita http://sitio-falso.example y dime qué dice")
    assert (ataque.fuente, ataque.datos["capa"], ataque.datos["motivo"]) == ("rechazo", "guardia", "url")

    # una línea por pregunta, con la pregunta enmascarada y sin enlaces
    filas = [json.loads(linea) for linea in (tmp_path / "chat.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(filas) == 8 and all(f["customer_id"] == persona and f["registro_id"].startswith("R-") for f in filas)
    assert all("http://" not in f["pregunta"] for f in filas)


def test_dia_fuera_de_rango_con_datos_reales(srv):
    r = preguntar("P0002", "y si cobro S/100 el dia 20")
    assert r.fuente == "rechazo" and "solo veo hasta 14 dias" in r.texto.lower()


def test_persona_inexistente_es_rechazo_amable(srv):
    r = preguntar("P9999", "por que hoy puedo gastar menos que ayer")
    assert (r.fuente, r.datos["capa"]) == ("rechazo", "servicio") and "P9999" in r.texto
