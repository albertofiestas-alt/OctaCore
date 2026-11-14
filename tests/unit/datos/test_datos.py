"""Pruebas del generador sintetico (dueno: Rafael). Usan 40 personas para correr en segundos."""

from __future__ import annotations

import pandas as pd
import pytest

from contratos import COLUMNAS_MOVIMIENTO, ETIQUETAS_REFERENCIA
from datos import generar, mes_indice, muestra_de, particion, verificar
from datos.chat import generar_preguntas

N = 40


@pytest.fixture(scope="module")
def datos():
    return generar(N, 24, semilla=7)


def test_cumple_el_contrato_y_las_comprobaciones(datos):
    df, meta = datos
    assert set(COLUMNAS_MOVIMIENTO) <= set(df.columns)
    assert set(ETIQUETAS_REFERENCIA) <= set(df.columns)
    fallas, _ = verificar(df, meta)
    assert fallas == []


def test_misma_semilla_mismo_hash_y_otra_semilla_otro():
    a = generar(N, 24, semilla=7)[1]["hash"]
    assert a == generar(N, 24, semilla=7)[1]["hash"]
    assert a != generar(N, 24, semilla=8)[1]["hash"]


def test_hay_diciembre_en_el_mes_12_y_en_el_24(datos):
    df, _ = datos
    meses = (pd.to_datetime(df["fecha_hora"]).map(lambda f: mes_indice(f))).unique()
    assert 12 in meses and 24 in meses


def test_los_escenarios_dificiles_estan_inyectados(datos):
    df, meta = datos
    assert df["es_duplicado"].sum() > 0
    assert df["es_atipico"].sum() > 0
    assert (df["categoria"] == "").sum() > 0 and (df["comercio"] == "").sum() > 0
    assert len(meta["cambio_patron"]) > 0
    # la categoria puede venir vacia: es el escenario "datos incompletos"
    assert df[df["pago_con_fecha"]]["categoria"].isin(["alquiler", "servicios", "deuda", "suscripcion", ""]).all()


def test_las_etiquetas_no_incluyen_columnas_fuera_del_contrato(datos):
    df, _ = datos
    assert not [c for c in df.columns if c.startswith("es_") and c not in ETIQUETAS_REFERENCIA]


def test_particion_no_mezcla_personas(datos):
    df, _ = datos
    p = particion(df, semilla=7)
    assert not set(p["test_personas"]) & set(p["train_personas"])
    assert len(p["test_personas"]) == int(0.2 * N)
    assert p["meses_test"] == (21, 24)


def test_muestra_es_subconjunto_exacto_sin_cambio_de_patron(datos):
    df, meta = datos
    mu = muestra_de(df, por_arquetipo=1)
    assert set(mu["customer_id"]) <= set(df["customer_id"])
    assert not set(mu["customer_id"]) & set(meta["cambio_patron"])
    assert mu.groupby("customer_id")["arquetipo"].nunique().eq(1).all()


def test_el_generador_perturbado_cambia_los_datos():
    base = generar(N, 24, semilla=7)[0]
    pert = generar(N, 24, semilla=7, perturbado=True)[0]
    assert base["monto"].sum() != pert["monto"].sum()


def test_preguntas_del_chat(tmp_path):
    r = generar_preguntas(tmp_path)
    assert all(v >= 20 for v in r["por_intencion"].values())
    df = pd.read_csv(tmp_path / "preguntas.csv")
    assert list(df.columns) == ["texto", "intencion"] and df["texto"].is_unique
    assert r["ataques"] >= 10
