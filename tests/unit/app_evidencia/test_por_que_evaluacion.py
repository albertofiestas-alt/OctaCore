from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app import servicio_falso
from app.componentes import AVISO

PAGINAS = Path(__file__).resolve().parents[3] / "src" / "app" / "pages"
PQ, EV = str(PAGINAS / "3_Por_que.py"), str(PAGINAS / "5_Evaluacion.py")
PERSONAS = list(servicio_falso.PERSONAS)


@pytest.fixture(autouse=True)
def falso(monkeypatch):
    monkeypatch.setenv("APP_FAKE", "1")


def textos(at):
    return " ".join([m.value for m in at.markdown] + [e.value for e in at.error]
                    + [i.value for i in at.info] + [w.value for w in at.warning]
                    + [c.value for c in at.caption] + [s.value for s in at.subheader])


@pytest.mark.parametrize("persona", PERSONAS)
def test_por_que_carga_con_aviso_y_confianza(persona):
    at = AppTest.from_file(PQ, default_timeout=30).run()
    at.selectbox[0].select(persona).run()
    assert not at.exception
    t = textos(at)
    assert AVISO in t and "Confianza:" in t and "Supuestos y evidencia" in t and "Límites" in t
    assert len(at.dataframe) >= 2  # rango + puntos de control


def test_por_que_confianza_baja_con_razon():
    at = AppTest.from_file(PQ, default_timeout=30).run()
    at.selectbox[0].select("P0003").run()
    t = textos(at)
    assert "Confianza: baja" in t and "2 semanas de historia" in t


def test_evaluacion_sin_archivos_da_mensaje_con_comando(monkeypatch):
    at = AppTest.from_file(EV, default_timeout=30).run()
    assert not at.exception
    t = textos(at)
    assert "python tareas.py eval" in t and AVISO in t and "datos son sintéticos" in t


def test_evaluacion_auditoria_encontrada_y_no_encontrada():
    at = AppTest.from_file(EV, default_timeout=30).run()
    at.text_input[0].input("R-000000000001").run()
    assert not at.exception and "Se reproduce" in textos(at)
    at.text_input[0].input("R-inventado").run()
    assert "No existe ese identificador" in textos(at)


def test_evaluacion_salud_muestra_valores_del_servicio():
    at = AppTest.from_file(EV, default_timeout=30).run()
    vals = {m.label: m.value for m in at.metric}
    assert vals["p50 (ms)"] == "120" and vals["p95 (ms)"] == "300"
