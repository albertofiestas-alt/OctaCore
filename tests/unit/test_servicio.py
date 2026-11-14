"""Servicio (dueño: Anderson)."""

from __future__ import annotations

import json
from datetime import date

import pytest

from contratos import Decision, Registro, hash_config
from servicio import consultar
from servicio.registro import construir_registro, leer_registros, linea, registrar

ENTRADAS = {"customer_id": "C0002", "fecha": "2025-11-14", "metodo": "regla2"}


def test_registro_lleva_versiones_semilla_y_hash(cfg):
    r = construir_registro(ENTRADAS, cfg)
    assert r.hash_config == hash_config(cfg)
    assert r.semilla == cfg.semilla_generador
    assert r.version_generador == cfg.version_generador
    assert r.version_modelo == cfg.version_modelo


def test_una_linea_json_por_recomendacion(cfg, tmp_path):
    ruta = tmp_path / "sub" / "recomendaciones.jsonl"
    registrar(construir_registro(ENTRADAS, cfg), ruta)
    registrar(construir_registro({**ENTRADAS, "metodo": "modelo"}, cfg), ruta)

    lineas = ruta.read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 2
    for l in lineas:
        Registro.model_validate(json.loads(l))
    assert [r.entradas["metodo"] for r in leer_registros(ruta)] == ["regla2", "modelo"]


def test_linea_determinista(cfg):
    a = linea(construir_registro(dict(ENTRADAS), cfg))
    b = linea(construir_registro(dict(reversed(list(ENTRADAS.items()))), cfg))
    assert a == b


def test_registro_conserva_unicode(cfg, tmp_path):
    ruta = tmp_path / "r.jsonl"
    registrar(construir_registro({"nota": "Señal ámbar"}, cfg), ruta)
    assert "Señal ámbar" in ruta.read_text(encoding="utf-8")


def test_leer_registro_inexistente_devuelve_vacio(tmp_path):
    assert leer_registros(tmp_path / "no-existe.jsonl") == []


@pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="consultar con regla 2 a las 13:00")
def test_consultar_devuelve_decision():
    assert isinstance(consultar("C0001", date(2025, 11, 14), "regla2"), Decision)
