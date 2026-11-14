"""Gancho eval.pares._medir_semilla: una medición por semilla con simulador y modelo de juguete.

Cada persona de prueba del juguete tiene 10 pagos: regla2 deja 1 descubierto en P20 (10 %) con gasto 20 y el modelo
2 descubiertos (20 %) con gasto 30 (juguete: gasto = 100 * cuantil, +10 con modelo; descubiertos 1, y 2 con modelo).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from contratos import cargar_config

RAIZ = Path(__file__).resolve().parents[3]
MUESTRA = RAIZ / "data" / "muestra" / "movimientos.csv"


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(f"eval_{nombre}", RAIZ / "eval" / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def pares():
    mod = _cargar("pares")
    frontera = _cargar("frontera")
    visto = {"metodos": [], "cuantiles": set(), "semillas": [], "modelo_semilla": []}

    def simular(historia, etiquetas, cfg, metodo, cuantil, modelo=None):
        visto["metodos"].append(metodo)
        visto["cuantiles"].add(cuantil)
        es_modelo = modelo is not None
        return {"pagos_descubiertos": 2 if es_modelo else 1, "pagos_totales": 10,
                "gasto_permitido_dia": 100 * cuantil + (10 if es_modelo else 0)}

    def generar(semilla):
        visto["semillas"].append(semilla)
        return pd.read_csv(MUESTRA, parse_dates=["fecha_hora"])

    frontera._cargar_simulador = lambda: simular
    frontera._entrenar_modelo = lambda df, cfg, semilla=None: (visto["modelo_semilla"].append(semilla) or "MODELO")
    mod._frontera = lambda: frontera
    mod._generar = generar
    mod.visto = visto
    return mod


def test_devuelve_las_cinco_claves_con_valores_a_mano(pares):
    m = pares._medir_semilla(7)
    assert set(m) == {"semilla", "pct_descubiertos_modelo", "pct_descubiertos_regla2", "gasto_modelo", "gasto_regla2"}
    assert m["semilla"] == 7
    assert m["pct_descubiertos_modelo"] == pytest.approx(0.2)
    assert m["pct_descubiertos_regla2"] == pytest.approx(0.1)
    assert m["gasto_modelo"] == pytest.approx(30.0)  # 100 * 0.20 + 10
    assert m["gasto_regla2"] == pytest.approx(20.0)


def test_usa_el_cuantil_conservador_del_preregistro_y_solo_regla2_y_modelo(pares):
    pares._medir_semilla(1)
    assert pares.visto["cuantiles"] == {float(cargar_config()["preregistro"]["cuantil_conservador"])}
    assert set(pares.visto["metodos"]) == {"modelo", "regla2"}


def test_genera_con_la_semilla_y_entrena_con_la_misma_semilla(pares):
    pares._medir_semilla(13)
    assert pares.visto["semillas"] == [13]
    assert pares.visto["modelo_semilla"] == [13]


def test_generar_entrega_fechas_como_datetime(monkeypatch):
    # el generador real devuelve fecha_hora como texto: sin convertir, el simulador y el modelo fallan
    import datos

    texto = pd.read_csv(MUESTRA).head(20)
    assert not pd.api.types.is_datetime64_any_dtype(texto["fecha_hora"])  # texto (object o string según pandas)
    monkeypatch.setattr(datos, "generar", lambda semilla=None, **kw: (texto, {}))
    df = _cargar("pares")._generar(5)
    assert pd.api.types.is_datetime64_any_dtype(df["fecha_hora"])


def test_el_resumen_se_arma_con_la_medicion(pares):
    mediciones = [pares._medir_semilla(s) for s in (1, 2, 3)]
    r = pares.resumir(mediciones)
    assert r["gasto"]["media"] == pytest.approx(10.0)  # 30 - 20 en cada semilla
    assert r["pct_descubiertos"]["media"] == pytest.approx(0.1)  # 0.2 - 0.1
