"""Pares de semillas (eval/pares.py): diferencia modelo - regla2 por semilla, con IC bootstrap de 95 %.

Se trabaja con mediciones de juguete: la medición real (generar + entrenar + simular) la aporta Rafael.
"""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]


def _cargar():
    spec = importlib.util.spec_from_file_location("eval_pares", RAIZ / "eval" / "pares.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def pares_mod(tmp_path, monkeypatch):
    mod = _cargar()
    monkeypatch.setattr(mod, "RUTA_SALIDA", tmp_path / "pares.csv")
    return mod


def medicion(semilla, desc_modelo, desc_regla2, gasto_modelo, gasto_regla2):
    return {"semilla": semilla, "pct_descubiertos_modelo": desc_modelo, "pct_descubiertos_regla2": desc_regla2,
            "gasto_modelo": gasto_modelo, "gasto_regla2": gasto_regla2}


def test_intervalo_contiene_una_diferencia_conocida(pares_mod):
    # diferencia constante de +5 soles en cada semilla: el intervalo es exactamente 5
    datos = [medicion(s, 0.10, 0.10, 105.0, 100.0) for s in range(1, 21)]
    g = pares_mod.resumir(datos)["gasto"]
    assert g["media"] == pytest.approx(5.0)
    assert g["ic_inf"] <= 5.0 <= g["ic_sup"]
    assert g["n"] == 20


def test_intervalo_con_ruido_contiene_la_media_verdadera(pares_mod):
    # diferencias 1..5 repetidas: media 3, el intervalo debe contenerla y no ser degenerado
    datos = [medicion(s, 0.1, 0.1, 100 + (s % 5) + 1, 100.0) for s in range(1, 21)]
    g = pares_mod.resumir(datos)["gasto"]
    assert g["ic_inf"] < g["media"] < g["ic_sup"]
    assert g["ic_inf"] <= 3.0 <= g["ic_sup"]


def test_descubiertos_y_gasto_son_metricas_separadas(pares_mod):
    datos = [medicion(s, 0.08, 0.10, 100.0, 100.0) for s in range(1, 21)]
    r = pares_mod.resumir(datos)
    assert r["pct_descubiertos"]["media"] == pytest.approx(-0.02)
    assert r["gasto"]["media"] == pytest.approx(0.0)


def test_bootstrap_es_determinista(pares_mod):
    datos = [medicion(s, 0.1, 0.1, 100 + (s * 7 % 11), 100.0) for s in range(1, 21)]
    assert pares_mod.resumir(datos) == pares_mod.resumir(datos)


def test_resumir_sin_mediciones_es_error(pares_mod):
    with pytest.raises(ValueError, match="sin mediciones"):
        pares_mod.resumir([])


def test_pares_corre_las_semillas_y_escribe_la_tabla(pares_mod, monkeypatch):
    vistas = []

    def falsa(semilla):
        vistas.append(semilla)
        return medicion(semilla, 0.10, 0.10, 104.0, 100.0)

    monkeypatch.setattr(pares_mod, "_medir_semilla", falsa)
    r = pares_mod.pares(20)
    assert vistas == list(range(1, 21))
    assert r["gasto"]["media"] == pytest.approx(4.0)
    filas = list(csv.DictReader(pares_mod.RUTA_SALIDA.open(encoding="utf-8")))
    assert [f["metrica"] for f in filas] == ["pct_descubiertos", "gasto"]
    assert float(filas[1]["media"]) == pytest.approx(4.0)


def test_menos_semillas_que_el_preregistro_es_error(pares_mod, monkeypatch):
    monkeypatch.setattr(pares_mod, "_medir_semilla", lambda s: medicion(s, 0.1, 0.1, 100, 100))
    with pytest.raises(ValueError, match="semillas"):
        pares_mod.pares(5)
    assert not pares_mod.RUTA_SALIDA.exists()


def test_sin_medicion_real_falla_claro(pares_mod, monkeypatch):
    # si el gancho de medición falla (aquí simulado: _medir_semilla aún sin implementar), pares no inventa resultados.
    # Adaptada por Gino: el gancho ya existe en esta rama, así que se simula el esqueleto.
    def esqueleto(semilla):
        raise NotImplementedError("gancho sin implementar")

    monkeypatch.setattr(pares_mod, "_medir_semilla", esqueleto)
    with pytest.raises(NotImplementedError):
        pares_mod.pares(20)
