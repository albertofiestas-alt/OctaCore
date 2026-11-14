"""Invariantes del generador: los escenarios contados coinciden con lo inyectado (dueño: Rafael)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from datos import generar, mes_indice, particion
from datos.generador import TASAS, main

N = 40


@pytest.fixture(scope="module")
def datos():
    return generar(N, 24, semilla=7)


def test_cubre_los_24_meses(datos):
    df, _ = datos
    meses = set(pd.to_datetime(df["fecha_hora"]).map(mes_indice))
    assert meses == set(range(1, 25))


def test_duplicados_coinciden_con_la_tasa(datos):
    # Se inyectan int(filas_antes * tasa) copias exactas.
    df, _ = datos
    dup = int(df["es_duplicado"].sum())
    assert dup == int((len(df) - dup) * TASAS["duplicado"])


def test_atipicos_coinciden_con_la_tasa(datos):
    # Se inyectan antes de la suscripción doble y de los duplicados.
    df, meta = datos
    base = len(df) - int(df["es_duplicado"].sum()) - len(meta["suscripciones_duplicadas"])
    assert int(df["es_atipico"].sum()) == int(base * TASAS["atipico"])


def test_faltantes_coinciden_con_la_tasa(datos):
    df, _ = datos
    vacios = int((df["categoria"] == "").sum() + (df["comercio"] == "").sum())
    assert vacios == int(len(df) * TASAS["faltante"])


def test_suscripcion_doble_listada_en_meta_existe(datos):
    df, meta = datos
    ids = set(meta["suscripciones_duplicadas"])
    assert ids <= set(df["transaction_id"])
    sus = df[df["transaction_id"].isin(ids)]
    assert not sus["pago_con_fecha"].any()


def test_cambio_de_patron_coincide_con_meta(datos):
    df, meta = datos
    cambian = df.groupby("customer_id")["arquetipo"].nunique()
    assert set(cambian[cambian > 1].index) == set(meta["cambio_patron"])


def test_particion_cubre_a_todas_las_personas_una_sola_vez(datos):
    df, _ = datos
    p = particion(df, semilla=7)
    assert sorted(p["test_personas"] + p["train_personas"]) == sorted(df["customer_id"].unique())
    assert (p["meses_train"], p["meses_val"], p["meses_test"]) == ((1, 16), (17, 20), (21, 24))


def test_main_guarda_la_particion(tmp_path):
    main(["--n", "10", "--semilla", "3", "--salida", str(tmp_path)])
    guardada = json.loads((tmp_path / "generado" / "particion.json").read_text(encoding="utf-8"))
    meta = json.loads((tmp_path / "generado" / "meta.json").read_text(encoding="utf-8"))
    assert guardada["semilla"] == 3 and guardada["hash_datos"] == meta["hash"]
    assert not set(guardada["test_personas"]) & set(guardada["train_personas"])
