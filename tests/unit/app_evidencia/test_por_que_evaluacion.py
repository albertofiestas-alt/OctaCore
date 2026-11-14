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


def test_evaluacion_con_resultados_de_main():
    at = AppTest.from_file(EV, default_timeout=30).run()
    assert not at.exception
    t = textos(at)
    assert "No se adopta: se usa la regla 2" in t and AVISO in t and "datos son sintéticos" in t
    assert "[respaldo]" in t and "Generador 1.0" in t and "Generador 1.1" in t
    assert "31/42" in t and "34/42" in t and "ya pasó a desarrollo" in t
    assert "Pendiente" in t  # sesgos, calidad_datos, ablaciones aún no existen
    filas = [r for df in at.dataframe for r in df.value.to_dict("records")]
    assert any(f.get("Métrica") == "Pagos descubiertos (pp)" and abs(f["Media"] - 0.433) < 0.001 for f in filas)
    assert any(f.get("Métrica") == "Gasto permitido (S/ por día)" and abs(f["Media"] - 0.309) < 0.001 for f in filas)
    assert [e.label for e in at.expander if "Elegibilidad" in e.label]
    assert "Señal indicativa, no es puntaje de crédito" in " ".join(c.value for c in at.caption)


def test_evaluacion_sin_ningun_archivo_no_falla(monkeypatch, tmp_path):
    monkeypatch.setenv("UKKU_RESULTADOS", str(tmp_path / "no_existe"))
    at = AppTest.from_file(EV, default_timeout=30).run()
    assert not at.exception
    t = textos(at)
    assert "Pendiente" in t and "sesgos.csv" in t and "calidad_datos.json" in t and "ablaciones.csv" in t
    assert AVISO in t


def test_evaluacion_archivo_ilegible_no_falla(monkeypatch, tmp_path):
    (tmp_path / "pares.csv").write_text("a,b" + chr(10) + "solo,uno,dos,tres", encoding="utf-8")
    (tmp_path / "calidad_datos.json").write_text("{no es json", encoding="utf-8")
    monkeypatch.setenv("UKKU_RESULTADOS", str(tmp_path))
    assert not AppTest.from_file(EV, default_timeout=30).run().exception


def test_evaluacion_calidad_presente(monkeypatch, tmp_path):
    (tmp_path / "calidad_datos.json").write_text(
        '{"filas_entrada": 10, "filas_salida": 8, "duplicados_eliminados": 2}', encoding="utf-8")
    monkeypatch.setenv("UKKU_RESULTADOS", str(tmp_path))
    at = AppTest.from_file(EV, default_timeout=30).run()
    assert {m.label: m.value for m in at.metric}["Filas limpias"] == "8"


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
