"""Pruebas de src/asistente/plantillas.py: toda cifra del texto sale de la Decision, el Escenario o los pasajes."""

import json
import re

import pytest

from asistente.plantillas import plantilla, resultados_de
from contratos import Escenario

NUM = re.compile(r"\d+(?:\.\d+)?")
PASAJE = {"id": "kb:confianza#1", "texto": "La confianza puede ser alta, media o baja.", "score": 0.5}
DECISIONES = ["decision_verde", "decision_rojo", "decision_confianza_baja", "decision_sin_alcance"]


def cifras(texto):
    return {float(x) for x in NUM.findall(texto)}


def permitidas(resultados):
    return cifras(json.dumps(resultados, default=str, ensure_ascii=False))


@pytest.mark.parametrize("intencion", ["explicar_numero", "estado_pago", "que_pasa_si", "propuesta", "concepto"])
@pytest.mark.parametrize("nombre", DECISIONES)
def test_toda_cifra_viene_de_los_resultados(request, intencion, nombre):
    d = request.getfixturevalue(nombre)
    esc = Escenario(ingresos_extra=[{"dia": 5, "monto": 150}], gasto_hoy=0)
    res = resultados_de(d, escenario=esc, simulada=d, pasajes=[PASAJE])
    texto, acciones = plantilla(intencion, res)
    assert cifras(texto) <= permitidas(res), (texto, cifras(texto) - permitidas(res))
    assert len(texto.split()) <= 120
    assert isinstance(acciones, list) and all(isinstance(a, str) for a in acciones)


@pytest.mark.parametrize("intencion", ["explicar_numero", "estado_pago", "que_pasa_si", "propuesta"])
def test_tres_bloques(decision_verde, intencion):
    texto, _ = plantilla(intencion, resultados_de(decision_verde, escenario=Escenario(), simulada=decision_verde))
    i, j, k = (texto.find(s) for s in ("Datos:", "Qué significa:", "Qué puedes hacer:"))
    assert 0 <= i < j < k


def test_explicar_numero_cifras_clave(decision_verde):
    texto, _ = plantilla("explicar_numero", resultados_de(decision_verde))
    assert "S/20" in texto and "media" in texto and "día 14" in texto


def test_estado_pago_por_dia(decision_verde):
    res = resultados_de(decision_verde, parametros={"dia": 9, "monto": None})
    texto, _ = plantilla("estado_pago", res)
    assert "día 9" in texto and "S/60" in texto and "Cubierto" in texto and "día 5" not in texto


def test_estado_pago_dia_sin_pago(decision_verde):
    texto, _ = plantilla("estado_pago", resultados_de(decision_verde, parametros={"dia": 2, "monto": None}))
    assert "No hay un pago" in texto and "día 2" in texto


def test_estado_pago_sin_alcance_dice_faltante(decision_sin_alcance):
    res = resultados_de(decision_sin_alcance)
    assert res["faltante"] == 200.0
    texto, _ = plantilla("estado_pago", res)
    assert "faltan S/200" in texto and "No cubierto" in texto


def test_que_pasa_si_antes_y_despues(decision_verde, decision_rojo):
    esc = Escenario(ingresos_extra=[{"dia": 5, "monto": 150}])
    texto, acciones = plantilla("que_pasa_si", resultados_de(decision_rojo, escenario=esc, simulada=decision_verde))
    assert "S/0" in texto and "S/20" in texto and "S/150" in texto and "día 5" in texto
    assert "simulación" in texto.lower() and acciones


def test_que_pasa_si_sin_simulacion_no_inventa(decision_verde):
    res = resultados_de(decision_verde, escenario=Escenario(gasto_hoy=80))
    texto, _ = plantilla("que_pasa_si", res)
    assert cifras(texto) <= permitidas(res) and "no pude" in texto.lower()


def test_propuesta_con_y_sin(decision_verde, decision_rojo):
    texto, _ = plantilla("propuesta", resultados_de(decision_verde))
    assert "Gasta hasta S/7 por día" in texto and "S/20" in texto
    texto, _ = plantilla("propuesta", resultados_de(decision_rojo))
    assert "no hay una propuesta" in texto.lower()


def test_concepto_cita_el_pasaje():
    texto, _ = plantilla("concepto", {"pasajes": [PASAJE]})
    assert "[kb:confianza#1]" in texto and "alta, media o baja" in texto


def test_concepto_sin_pasajes_dice_que_no_sabe():
    texto, acciones = plantilla("concepto", {"pasajes": []})
    assert "no encontré" in texto.lower() and "[kb:" not in texto and acciones


@pytest.mark.parametrize("intencion", ["fuera_de_alcance", "reformular", "desconocida"])
def test_rechazo_y_reformular_son_fijos(intencion):
    texto, acciones = plantilla(intencion, {})
    assert texto and not NUM.search(texto)
    if intencion != "fuera_de_alcance":
        assert len(acciones) >= 3


def test_fuera_de_alcance_aclara_limites():
    texto, _ = plantilla("fuera_de_alcance", {})
    assert "asesoría" in texto.lower()


def test_resultados_de_no_muta_y_es_serializable(decision_verde):
    antes = decision_verde.model_dump()
    res = resultados_de(decision_verde, escenario=Escenario(), simulada=decision_verde, pasajes=[PASAJE])
    json.dumps(res)
    assert decision_verde.model_dump() == antes
