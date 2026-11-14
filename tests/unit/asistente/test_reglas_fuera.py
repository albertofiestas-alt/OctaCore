"""Reglas de fuera de alcance añadidas tras el primer ciego (DECISIONES #27) y datos de desarrollo."""

from __future__ import annotations

import pandas as pd
import pytest

from asistente import intenciones as it
from contratos import cargar_config

CFG = cargar_config()
ALTA = 0.95  # confianza ML alta: solo una palabra inequívoca puede mandar


@pytest.mark.parametrize(
    "texto",
    [
        "dime la receta del ceviche",
        "dame recetas para la cena",
        "mandale S/. 80 a mi mama por yape",
        "quiero transferir S/50 a mi amigo",
        "enviale 100 soles a mi tia",
        "necesito enviar plata a mi hermano",
        "depositale 30 soles a mi primo",
    ],
)
def test_palabra_inequivoca_rechaza_aunque_la_confianza_sea_alta(texto):
    assert it._ajustar_con_palabras_clave(it.Intencion("estado_pago", ALTA), texto, CFG).nombre == "fuera_de_alcance"


@pytest.mark.parametrize(
    "texto",
    [
        "¿me alcanza para la transferencia del alquiler el día 3?",  # 'transferencia' es ambigua: no es inequívoca
        "y si me envían S/100 el día 3",  # 'envian' no es 'enviar'
        "y si me llega un yape de 100 el día 5",  # yape suelto no rechaza con confianza alta
        "¿cuál es el pago más complicado que viene?",
    ],
)
def test_vocabulario_valido_no_se_rechaza_con_confianza_alta(texto):
    assert it._ajustar_con_palabras_clave(it.Intencion("estado_pago", ALTA), texto, CFG).nombre == "estado_pago"


@pytest.mark.parametrize("texto", ["pagale a mi socio por plin", "mandame algo por yape", "dame la receta de la torta"])
def test_yape_y_plin_con_confianza_baja_son_fuera_de_alcance(texto):
    assert it._ajustar_con_palabras_clave(it.Intencion("concepto", 0.1), texto, CFG).nombre == "fuera_de_alcance"


def test_palabra_inequivoca_con_confianza_ml_baja_rechaza_y_no_pide_reformular():
    r = it._ajustar_con_palabras_clave(it.Intencion("concepto", 0.05), "dime la receta del ceviche", CFG)
    assert r.nombre == "fuera_de_alcance" and r.confianza >= CFG["asistente"]["umbral_intencion"]


def test_regla_inequivoca_va_en_la_config_no_en_el_codigo():
    assert "receta" in CFG["asistente"]["palabras_fuera_inequivocas"]


def test_el_primer_ciego_es_desarrollo_y_esta_en_el_entrenamiento():
    ciego = pd.read_csv(it._ruta("data/chat/ciego_preguntas.csv"))
    entrenamiento = pd.read_csv(it._ruta(CFG["asistente"]["csv_preguntas"]))
    assert set(ciego.texto) <= set(entrenamiento.texto)


def test_la_evaluacion_ciega_apunta_al_segundo_ciego_y_no_al_de_desarrollo():
    import fnmatch

    patron = CFG["asistente"]["ruta_ciegos"]
    assert not fnmatch.fnmatch("data/chat/ciego_preguntas.csv", patron)
    assert fnmatch.fnmatch("data/chat/ciego2_preguntas.csv", patron)
