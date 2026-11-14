"""Reporte de calidad del dataset (eval/_calidad_datos.py): esquema, sin datos personales y página Evaluación."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[3]
MUESTRA = RAIZ / "data" / "muestra" / "movimientos.csv"
JSON_OFICIAL = RAIZ / "eval" / "resultados" / "calidad_datos.json"

# Lo que lee src/app/pages/5_Evaluacion.py
CAMPOS_PAGINA = {
    "filas_entrada": int,
    "filas_salida": int,
    "duplicados_eliminados": int,
    "atipicos": int,
    "suscripciones_duplicadas": list,
    "faltantes": dict,
    "pii_enmascarado": int,
    "columnas_sensibles_descartadas": list,
}
# Lo que pidió Gino además
CAMPOS_EXTRA = {
    "fuente": str,
    "personas": int,
    "filas_rechazadas": int,
    "rechazos": dict,
    "duplicados_en_entrada": dict,
    "categorias_imputadas": dict,
    "pagos_inferidos": dict,
    "pagos_inferidos_calidad": (dict, type(None)),
}


@pytest.fixture(scope="module")
def cd():
    spec = importlib.util.spec_from_file_location("eval_calidad_datos", RAIZ / "eval" / "_calidad_datos.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def reporte(cd):
    return cd.calidad(MUESTRA, n_personas_medicion=0)  # sin medir precisión y recall: la muestra es solo para el esquema


def test_trae_los_campos_que_lee_la_pagina_con_su_tipo(reporte):
    for campo, tipo in CAMPOS_PAGINA.items():
        assert isinstance(reporte[campo], tipo), campo


def test_trae_los_campos_pedidos_por_gino(reporte):
    for campo, tipo in CAMPOS_EXTRA.items():
        assert isinstance(reporte[campo], tipo), campo
    assert set(reporte["duplicados_en_entrada"]) == {"transaction_id_repetido", "filas_identicas"}
    assert set(reporte["pagos_inferidos"]) == {"total", "por_categoria"}
    assert {"categoria_imputada_por_comercio", "categoria_por_defecto"} <= set(reporte["categorias_imputadas"])


def test_los_conteos_son_coherentes(reporte):
    assert 0 <= reporte["filas_salida"] <= reporte["filas_entrada"]
    assert reporte["filas_rechazadas"] == sum(reporte["rechazos"].values())
    assert reporte["pagos_inferidos"]["total"] == sum(reporte["pagos_inferidos"]["por_categoria"].values())
    assert all(isinstance(v, int) and v >= 0 for v in reporte["faltantes"].values())


def test_el_json_no_lleva_valores_personales_ni_comercios(reporte):
    texto = json.dumps(reporte, ensure_ascii=False)
    df = pd.read_csv(MUESTRA)
    for valor in list(df["customer_id"].unique()[:20]) + list(df["comercio"].dropna().unique()[:30]):
        assert str(valor) not in texto, f"el reporte contiene un valor del dataset: {valor}"
    assert all(set(a) <= {"monto", "dias_entre_cobros"} for a in reporte["suscripciones_duplicadas"])


def test_la_pagina_evaluacion_carga_el_json_oficial_sin_error(monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    assert JSON_OFICIAL.exists(), "genera el reporte con: python eval/_calidad_datos.py"
    monkeypatch.setenv("APP_FAKE", "1")
    at = AppTest.from_file(str(RAIZ / "src" / "app" / "pages" / "5_Evaluacion.py"), default_timeout=30).run()
    assert not at.exception
    assert "Filas de entrada" in [m.label for m in at.metric]
    esperado = json.loads(JSON_OFICIAL.read_text(encoding="utf-8"))
    valores = {m.label: m.value for m in at.metric}
    assert str(esperado["filas_entrada"]) == str(valores["Filas de entrada"]).replace(",", "")


def test_las_categorias_desconocidas_se_reportan_por_valor_sin_datos_personales(reporte):
    por_valor = reporte["categorias_imputadas"]["desconocidas_por_valor"]
    assert isinstance(por_valor, dict) and sum(por_valor.values()) == reporte["categorias_imputadas"]["categoria_desconocida"]
    assert all(isinstance(k, str) and isinstance(v, int) for k, v in por_valor.items())


def test_las_suscripciones_duplicadas_traen_contexto_para_leerlas(reporte):
    c = reporte["suscripciones_duplicadas_contexto"]
    assert set(c) == {"avisos", "avisos_a_28_o_30_dias", "dobles_sembrados_por_el_generador"}
    assert c["avisos"] == len(reporte["suscripciones_duplicadas"]) and 0 <= c["avisos_a_28_o_30_dias"] <= c["avisos"]
