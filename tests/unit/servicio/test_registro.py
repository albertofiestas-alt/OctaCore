"""Registro JSONL y observabilidad del servicio (dueño: Anderson)."""

from __future__ import annotations

import json

from contratos import Registro, hash_config
from servicio.observabilidad import _percentil, anotar, resumen
from servicio.registro import buscar, construir_registro, leer_registros, linea, registrar

ENTRADAS = {"customer_id": "P0002", "fecha": "2025-11-14", "metodo_pedido": "regla2"}


def test_registro_lleva_id_versiones_semilla_y_hash(cfg):
    r = construir_registro(ENTRADAS, cfg)
    assert r.registro_id.startswith("R-")
    assert r.hash_config == hash_config(cfg)
    assert r.semilla == cfg["semilla_generador"]
    assert r.version_generador == cfg["version_generador"]
    assert r.version_modelo == cfg["version_modelo"]


def test_ids_distintos_por_recomendacion(cfg):
    assert construir_registro(ENTRADAS, cfg).registro_id != construir_registro(ENTRADAS, cfg).registro_id


def test_una_linea_json_por_recomendacion(cfg, tmp_path):
    ruta = tmp_path / "sub" / "recomendaciones.jsonl"
    registrar(construir_registro(ENTRADAS, cfg), ruta)
    registrar(construir_registro({**ENTRADAS, "metodo_pedido": "modelo"}, cfg), ruta)

    lineas = ruta.read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 2
    for l in lineas:
        Registro.model_validate(json.loads(l))
    assert [r.entradas["metodo_pedido"] for r in leer_registros(ruta)] == ["regla2", "modelo"]


def test_linea_determinista(cfg):
    a = linea(construir_registro(dict(ENTRADAS), cfg, registro_id="R-1"))
    b = linea(construir_registro(dict(reversed(list(ENTRADAS.items()))), cfg, registro_id="R-1"))
    assert a == b


def test_registro_conserva_unicode(cfg, tmp_path):
    ruta = tmp_path / "r.jsonl"
    registrar(construir_registro({"nota": "Señal ámbar"}, cfg), ruta)
    assert "Señal ámbar" in ruta.read_text(encoding="utf-8")


def test_leer_registro_inexistente_devuelve_vacio(tmp_path):
    assert leer_registros(tmp_path / "no-existe.jsonl") == []


def test_buscar_por_id(cfg, tmp_path, registro):
    ruta = tmp_path / "r.jsonl"
    registrar(registro, ruta)
    registrar(construir_registro(ENTRADAS, cfg), ruta)
    assert buscar(registro.registro_id, ruta) == registro
    assert buscar("R-no-existe", ruta) is None


# --------------------------------------------------------------------------- #
# logs/salud.jsonl
# --------------------------------------------------------------------------- #

def test_percentil_rango_mas_cercano():
    assert _percentil([], 50) is None
    assert _percentil([10.0], 95) == 10.0
    valores = [float(v) for v in range(1, 101)]
    assert _percentil(valores, 50) == 50.0
    assert _percentil(valores, 95) == 95.0


def test_resumen_de_salud(tmp_path):
    ruta = tmp_path / "salud.jsonl"
    assert resumen(ruta) == {"consultas": 0, "p50": None, "p95": None, "tasa_error": 0.0,
                             "tasa_respaldo": 0.0, "unidad": "ms"}
    anotar(ruta, "consultar", 10, metodo="regla2")
    anotar(ruta, "consultar", 30, metodo="regla2", respaldo=True)
    anotar(ruta, "consultar", 999, error="ErrorServicio")
    anotar(ruta, "cargar_archivo", 5000)  # no cuenta como consulta
    r = resumen(ruta)
    assert r["consultas"] == 3
    assert r["p50"] == 10 and r["p95"] == 30  # las fallidas no entran en la latencia
    assert r["tasa_error"] == 1 / 3
    assert r["tasa_respaldo"] == 1 / 3
