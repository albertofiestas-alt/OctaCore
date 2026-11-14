"""Pruebas de la página 4_Asistente con AppTest (modo de ejemplo y con flujo real simulado)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.componentes import AVISO
from contratos import Respuesta

PAGINA = str(Path(__file__).resolve().parents[3] / "src" / "app" / "pages" / "4_Asistente.py")


@pytest.fixture(autouse=True)
def falso(monkeypatch):
    monkeypatch.setenv("APP_FAKE", "1")


def textos(at):
    return " ".join([m.value for m in at.markdown] + [e.value for e in at.error] + [w.value for w in at.warning]
                    + [i.value for i in at.info] + [c.value for c in at.caption] + [s.value for s in at.subheader]
                    + [t.value for t in at.title])


def abrir():
    return AppTest.from_file(PAGINA, default_timeout=30).run()


def preguntar(at, texto):
    at.chat_input[0].set_value(texto).run()
    return at


def test_carga_con_avisos():
    at = abrir()
    assert not at.exception
    t = textos(at)
    assert AVISO in t and "no es asesoría" in t.lower()
    assert len(at.button) >= 3  # tres ejemplos


def test_ejemplo_responde_con_modo_de_ejemplo_y_citas():
    at = preguntar(abrir(), "¿Por qué hoy puedo gastar S/20?")
    assert not at.exception
    t = textos(at)
    assert "MODO DE EJEMPLO" in t and "Hoy puedes gastar hasta S/20" in t
    assert "Fuentes" in t and "decision#" in t


def test_concepto_muestra_cita_de_la_kb():
    t = textos(preguntar(abrir(), "¿Qué significa confianza media?"))
    assert "Fuentes" in t and "kb:confianza#" in t


def test_historial_se_acumula():
    at = preguntar(abrir(), "¿Qué significa ámbar?")
    at = preguntar(at, "¿Qué es el semáforo?")
    assert len(at.chat_message) >= 4


def test_fuera_de_alcance_es_rechazo_visible():
    at = preguntar(abrir(), "Dame una receta de lasaña")
    assert not at.exception
    assert any("asesoría" in w.value.lower() for w in at.warning)


def test_boton_de_ejemplo_envia_la_pregunta():
    at = abrir()
    at.button[0].click().run()
    assert not at.exception
    assert len(at.chat_message) >= 2


def test_pregunta_larga_se_rechaza_sin_romper():
    at = preguntar(abrir(), "x" * 500)
    assert not at.exception
    assert any("200" in w.value for w in at.warning)


def test_usa_el_flujo_real_si_existe(monkeypatch):
    llamadas = []

    def falso_preguntar(servicio, customer_id, fecha, texto, contexto=None):
        llamadas.append((customer_id, texto))
        return Respuesta(texto="Respuesta del flujo real", intencion="concepto", fuente="kb", citas=["kb:confianza#1"])

    monkeypatch.setenv("APP_FAKE", "0")
    monkeypatch.setattr("asistente.flujo.preguntar", falso_preguntar)
    at = preguntar(abrir(), "¿Qué significa confianza?")
    assert llamadas and "Respuesta del flujo real" in textos(at)
    assert "MODO DE EJEMPLO" not in textos(at)
