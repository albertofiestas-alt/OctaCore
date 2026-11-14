"""Realismo del generador v1.1 (dueño: Rafael). 40 personas para correr en segundos.

Los umbrales están en config/datos.yaml (comprobaciones) y son [SUPUESTO]. Solo miran los datos:
nunca resultados del modelo ni de las reglas.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import pytest

from contratos import cargar_config
from datos.generador import COLUMNAS, COLUMNAS_VERDAD, filas_con_pii, generar_con_verdad, medir_realismo

N = 40
CFG = cargar_config()
DATOS = CFG["datos"]
LIMITES = DATOS["comprobaciones"]


@pytest.fixture(scope="module")
def datos():
    return generar_con_verdad(N, 24, semilla=7)


@pytest.fixture(scope="module")
def realismo(datos):
    return medir_realismo(datos[0])


# --------------------------------------------------------------------------- #
# Determinismo
# --------------------------------------------------------------------------- #

def test_misma_semilla_mismo_hash_de_datos_y_de_verdad():
    a, b = generar_con_verdad(10, 24, semilla=3), generar_con_verdad(10, 24, semilla=3)
    assert (a[1]["hash"], a[1]["hash_verdad"]) == (b[1]["hash"], b[1]["hash_verdad"])
    pd.testing.assert_frame_equal(a[2], b[2])


def test_version_del_generador(datos):
    """La versión que anota el registro (config/base.yaml) es la del generador (config/datos.yaml)."""
    assert datos[1]["version_generador"] == DATOS["version_generador"] == CFG["version_generador"] == "1.1"


# --------------------------------------------------------------------------- #
# Cambio A: gasto que reacciona al dinero disponible
# --------------------------------------------------------------------------- #

def test_saldo_sin_tendencia_creciente(realismo):
    s = realismo["total"]["saldo_mediano_fin_mes"]
    n = LIMITES["max_razon_saldo_m24_m6"]
    assert s["m6"] > 0, s
    assert s["m24"] <= n * s["m6"], f"saldo mediano mes 24 = S/{s['m24']} supera {n} x mes 6 (S/{s['m6']})"


def test_saldo_en_pocos_dias_de_ingreso(realismo):
    assert realismo["total"]["saldo_en_dias_de_ingreso"] <= LIMITES["max_dias_de_ingreso"]


def test_gasto_discrecional_reacciona_al_ingreso(realismo):
    assert realismo["total"]["corr_semanal_ingreso_gasto"] >= LIMITES["min_corr_ingreso_gasto"]


def test_pagos_con_fecha_no_se_recortan(datos):
    """El alquiler y la cuota de deuda son montos fijos por persona: nunca se ajustan al saldo."""
    df = datos[0]
    fijos = df[df["pago_con_fecha"] & df["categoria"].isin(["alquiler", "deuda"]) & ~df["es_duplicado"]]
    assert fijos.groupby(["customer_id", "categoria"])["monto"].nunique().eq(1).all()


def test_hay_pagos_con_saldo_negativo_y_estan_en_la_verdad(datos):
    df, _, verdad = datos
    neg = df[df["pago_con_fecha"] & ~df["es_duplicado"] & (df["saldo"] < 0)]
    assert len(neg) > 0, "el evento que el producto intenta evitar debe ocurrir"
    declarados = verdad.loc[verdad["evento"] == "pago_con_saldo_negativo", "transaction_id"]
    assert set(declarados) == set(neg["transaction_id"])


def test_saldo_es_la_suma_de_los_montos(datos):
    df = datos[0]
    d = df[~df["es_duplicado"]]
    salto = d.groupby("customer_id")["saldo"].diff()
    ok = salto.isna() | np.isclose(salto, d["monto"], atol=0.011)
    assert ok.all(), d[~ok].head()


# --------------------------------------------------------------------------- #
# Cambio B: horas de ingreso
# --------------------------------------------------------------------------- #

def test_ingresos_sin_reloj_fijo(datos):
    ing = datos[0][datos[0]["tipo"] == "ingreso"]
    horas = pd.to_datetime(ing["fecha_hora"]).dt.hour
    assert horas.value_counts(normalize=True).max() * 100 <= LIMITES["max_pct_ingresos_misma_hora"]


@pytest.mark.parametrize("arquetipo", ["conductor", "vendedora", "tecnico", "comisionista", "asalariado"])
def test_hora_del_ingreso_segun_arquetipo(datos, arquetipo):
    df = datos[0]
    ing = df[(df["tipo"] == "ingreso") & (df["arquetipo"] == arquetipo)]
    if ing.empty:
        pytest.skip(f"sin {arquetipo} en {N} personas")
    desde, hasta = DATOS["horas_ingreso"][arquetipo]
    horas = pd.to_datetime(ing["fecha_hora"]).dt.hour
    assert horas.between(desde, hasta - 1).all()


# --------------------------------------------------------------------------- #
# Cambio C: PII ficticia, solo en las filas declaradas
# --------------------------------------------------------------------------- #

def test_pii_en_la_proporcion_configurada(datos):
    df, meta, verdad = datos
    pii = verdad[verdad["evento"].str.startswith("pii_")]
    assert len(pii) == int(len(df) * DATOS["pii"]["tasa"])
    assert sum(meta["pii_inyectada"].values()) == len(pii)
    assert set(pii["evento"].str.removeprefix("pii_")) == set(DATOS["pii"]["tipos"])


def test_pii_solo_en_comercio_de_las_filas_declaradas(datos):
    df, _, verdad = datos
    declaradas = set(verdad.loc[verdad["evento"].str.startswith("pii_"), "transaction_id"])
    assert set(df.loc[filas_con_pii(df["comercio"]), "transaction_id"]) == declaradas
    for col in ("customer_id", "transaction_id", "categoria", "arquetipo"):
        assert not filas_con_pii(df[col]).any(), col


def test_pii_nunca_en_pagos_con_fecha_ni_en_duplicados(datos):
    df, _, verdad = datos
    filas = df[df["transaction_id"].isin(verdad.loc[verdad["evento"].str.startswith("pii_"), "transaction_id"])]
    assert not filas["pago_con_fecha"].any() and not filas["es_duplicado"].any()


def test_los_patrones_de_la_config_detectan_cada_pii_inyectada(datos):
    """La ingesta enmascara con config/base.yaml (patrones_pii): cada valor inyectado debe caer en su patrón."""
    df, _, verdad = datos
    comercio = df.set_index("transaction_id")["comercio"]
    patrones = {k: re.compile(p) for k, p in CFG["patrones_pii"].items()}
    for fila in verdad[verdad["evento"].str.startswith("pii_")].itertuples():
        tipo = fila.evento.removeprefix("pii_")
        assert fila.valor in comercio[fila.transaction_id]
        assert patrones[tipo].search(comercio[fila.transaction_id]), (tipo, comercio[fila.transaction_id])


def test_correos_en_dominio_reservado(datos):
    verdad = datos[2]
    correos = verdad.loc[verdad["evento"] == "pii_correo", "valor"]
    assert correos.str.endswith("@" + DATOS["pii"]["dominio_correo"]).all()


# --------------------------------------------------------------------------- #
# Anti fuga: la verdad nueva no es parte del contrato ni de las variables del modelo
# --------------------------------------------------------------------------- #

def test_verdad_fuera_del_csv_y_del_modelo(datos):
    import modelo

    df, _, verdad = datos
    assert list(df.columns) == COLUMNAS
    assert list(verdad.columns) == COLUMNAS_VERDAD
    assert not {"evento", "valor"} & set(df.columns)
    assert not {"evento", "valor"} & set(getattr(modelo, "FEATURES", []))
