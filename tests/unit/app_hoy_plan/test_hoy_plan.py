from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app import servicio_falso
from app.componentes import AVISO

PAGINAS = Path(__file__).resolve().parents[3] / "src" / "app" / "pages"
HOY, PLAN = str(PAGINAS / "1_Hoy.py"), str(PAGINAS / "2_Plan.py")
PERSONAS = list(servicio_falso.PERSONAS)


@pytest.fixture(autouse=True)
def falso(monkeypatch):
    monkeypatch.setenv("APP_FAKE", "1")


def textos(at):
    return " ".join([m.value for m in at.markdown] + [e.value for e in at.error]
                    + [w.value for w in at.warning] + [i.value for i in at.info]
                    + [c.value for c in at.caption] + [s.value for s in at.subheader])


def abrir(ruta, persona):
    at = AppTest.from_file(ruta, default_timeout=30).run()
    return at.selectbox[0].select(persona).run() if persona != PERSONAS[0] else at


@pytest.mark.parametrize("ruta", [HOY, PLAN])
@pytest.mark.parametrize("persona", PERSONAS)
def test_carga_sin_excepcion_con_aviso(ruta, persona):
    at = abrir(ruta, persona)
    assert not at.exception
    t = textos(at)
    assert AVISO in t and "DATOS DE EJEMPLO" in t


def test_hoy_verde_numero_y_cubierto_con_texto():
    t = textos(abrir(HOY, "P0001"))
    assert "Hoy puedes gastar hasta" in t and "S/20" in t
    assert t.count("✔ Cubierto") == 3
    for frase in ("Gastas cada día lo que indica el número de hoy.", "No promete resultados."):
        assert frase in t


def test_hoy_sin_alcance_mensaje_de_falta():
    t = textos(abrir(HOY, "P0005"))
    assert "No alcanza para el pago del dia 3: faltan S/200" in t
    assert "✖ No cubierto" in t


def test_hoy_banner_respaldo_solo_si_respaldo():
    assert "regla sencilla" in textos(abrir(HOY, "P0003"))
    assert "regla sencilla" not in textos(abrir(HOY, "P0001"))


def test_error_del_servicio_sin_traceback(monkeypatch):
    def falla(*a, **k):
        raise RuntimeError("boom interno")
    monkeypatch.setattr(servicio_falso, "consultar", falla)
    at = AppTest.from_file(HOY, default_timeout=30).run()
    assert not at.exception
    assert "No pudimos calcular" in textos(at) and "boom" not in textos(at)


def test_plan_muestra_propuesta_evidencia_y_responde_una_vez(monkeypatch):
    llamadas = []
    monkeypatch.setattr(servicio_falso, "responder",
                        lambda pid, acc: llamadas.append((pid, acc)) or
                        {"ok": True, "mensaje": servicio_falso.MENSAJE_SIMULACION})
    at = AppTest.from_file(PLAN, default_timeout=30).run()
    t = textos(at)
    assert "Gasta hasta S/7 por día" in t and "Semanas de historia: 20" in t
    assert len(at.table) == 1
    at.button[0].click().run()
    assert llamadas == [("P0002-2025-11-14-1", "aprobar")]
    assert all(b.disabled for b in at.button)
    assert "Simulación: no se movió ningún dinero." in " ".join(s.value for s in at.success)
    at.run()
    assert len(llamadas) == 1


def test_plan_sin_propuesta_explica_por_que():
    assert "No hay propuesta" in textos(abrir(PLAN, "P0003"))
    assert "ni gastando S/0" in textos(abrir(PLAN, "P0005"))
