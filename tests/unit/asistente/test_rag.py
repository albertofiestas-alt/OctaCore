"""Pruebas de src/asistente/rag.py y de la base de conocimiento kb/ (TF-IDF local, sin red)."""

import re
from pathlib import Path

import pytest

from asistente.rag import BaseConocimiento, kb_dinamica

RAIZ = Path(__file__).resolve().parents[3]
ID = re.compile(r"^kb:[a-z0-9_]+#\d+$")


@pytest.fixture(scope="module")
def kb():
    return BaseConocimiento(str(RAIZ / "kb"))


def test_documentos_cortos_con_titulo_e_id_estable():
    docs = sorted((RAIZ / "kb").glob("*.md"))
    assert 10 <= len(docs) <= 14
    for d in docs:
        lineas = d.read_text(encoding="utf-8").splitlines()
        assert lineas[0].startswith("# ") and len(lineas[0]) > 3, d.name
        assert len(" ".join(lineas[1:]).split()) <= 120, d.name
        assert re.fullmatch(r"[a-z0-9_]+", d.stem), d.name  # el nombre del archivo es el id


def test_no_describe_productos_ni_politicas_de_bbva():
    todo = " ".join(p.read_text(encoding="utf-8") for p in (RAIZ / "kb").glob("*.md")).lower()
    for prohibida in ("bbva", "tasa de interés", "tarjeta de crédito", "préstamo"):
        assert prohibida not in todo


@pytest.mark.parametrize(
    "consulta,doc",
    [
        ("¿Qué significa confianza media?", "confianza"),
        ("qué es P5 y P20", "ingreso_conservador"),
        ("¿qué es el número de hoy?", "numero_hoy"),
        ("qué significa ámbar en el semáforo", "semaforo"),
        ("de dónde salen los pagos que detecta", "pagos_inferidos"),
        ("qué significa respaldo", "respaldo"),
        ("¿esto es asesoría financiera o puntaje de crédito?", "no_es_asesoria"),
        ("los datos son reales o sintéticos", "datos_sinteticos"),
    ],
)
def test_recupera_el_documento_correcto(kb, consulta, doc):
    r = kb.buscar(consulta)
    assert r and r[0]["id"].startswith(f"kb:{doc}#"), r


def test_forma_del_resultado(kb):
    r = kb.buscar("qué significa confianza media", k=3)
    assert 1 <= len(r) <= 3
    for p in r:
        assert ID.match(p["id"]) and p["texto"].strip() and p["score"] >= 0.15
    assert [p["score"] for p in r] == sorted((p["score"] for p in r), reverse=True)
    assert len({p["id"] for p in r}) == len(r)


def test_k_limita_y_minimo_alto_deja_vacio(kb):
    assert len(kb.buscar("pagos con fecha", k=1)) == 1
    assert kb.buscar("qué significa confianza media", minimo=0.99) == []


@pytest.mark.parametrize("consulta", ["receta de lasaña con queso", "quién ganó el partido", "", "   ", "¿?"])
def test_sin_evidencia_devuelve_vacio(kb, consulta):
    assert kb.buscar(consulta) == []


def test_cada_documento_se_encuentra_por_su_titulo(kb):
    for d in (RAIZ / "kb").glob("*.md"):
        titulo = d.read_text(encoding="utf-8").splitlines()[0][2:]
        assert any(p["id"].startswith(f"kb:{d.stem}#") for p in kb.buscar(titulo)), titulo


def test_es_determinista():
    a = BaseConocimiento(str(RAIZ / "kb")).buscar("qué es el semáforo")
    b = BaseConocimiento(str(RAIZ / "kb")).buscar("qué es el semáforo")
    assert a == b


def test_carpeta_vacia_o_inexistente_no_lanza(tmp_path):
    assert BaseConocimiento(str(tmp_path)).buscar("confianza") == []
    assert BaseConocimiento(str(tmp_path / "no_existe")).buscar("confianza") == []


def test_kb_dinamica_cita_la_decision(decision_verde):
    ps = kb_dinamica(decision_verde)
    assert [p["id"] for p in ps] == [f"decision#{i}" for i in range(1, len(ps) + 1)]
    texto = " ".join(p["texto"] for p in ps)
    assert "S/20" in texto and "media" in texto
    assert all(p["texto"].strip() for p in ps)


def test_kb_dinamica_sin_pagos(decision_sin_alcance):
    assert kb_dinamica(decision_sin_alcance)[0]["id"] == "decision#1"
