"""Contrato de la muestra que publica Rafael en data/muestra/movimientos.csv (sección 6).

Se salta mientras el archivo no exista. En cuanto se publica, debe cumplir el contrato.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from contratos import COLUMNAS_MOVIMIENTO, ETIQUETAS_REFERENCIA, Movimiento

MUESTRA = Path(__file__).resolve().parents[2] / "data" / "muestra" / "movimientos.csv"

pytestmark = pytest.mark.skipif(not MUESTRA.exists(), reason="muestra aún no publicada (Rafael, 11:00)")


@pytest.fixture(scope="module")
def muestra() -> pd.DataFrame:
    return pd.read_csv(MUESTRA, parse_dates=["fecha_hora"])


def test_columnas(muestra):
    faltan = set(COLUMNAS_MOVIMIENTO) - set(muestra.columns)
    assert not faltan, f"faltan columnas del contrato: {faltan}"
    assert set(ETIQUETAS_REFERENCIA) <= set(muestra.columns), "faltan etiquetas de referencia para evaluar"


def test_veinte_personas_y_24_meses(muestra):
    assert muestra["customer_id"].nunique() == 20
    meses = muestra["fecha_hora"].dt.to_period("M").nunique()
    assert meses >= 24, f"la muestra cubre {meses} meses; se esperan 24"


def test_transaction_id_unico(muestra):
    assert muestra["transaction_id"].is_unique


def test_moneda_y_tipo(muestra):
    assert set(muestra["moneda"].unique()) == {"PEN"}
    assert set(muestra["tipo"].unique()) <= {"ingreso", "gasto"}


def test_filas_limpias_cumplen_movimiento(muestra):
    """Las filas no marcadas como difíciles deben validar contra Movimiento."""
    limpias = muestra[~muestra["es_duplicado"].astype(bool) & ~muestra["es_atipico"].astype(bool)]
    limpias = limpias.dropna(subset=["categoria", "comercio"]).head(500)
    for fila in limpias[list(COLUMNAS_MOVIMIENTO)].to_dict("records"):
        if pd.isna(fila["saldo"]):
            fila["saldo"] = None
        Movimiento.model_validate(fila)


def test_sin_datos_personales(muestra):
    """Identificadores ficticios: sin DNI (8 dígitos) ni teléfonos (9 dígitos) en texto libre."""
    texto = muestra["comercio"].fillna("").astype(str)
    assert not texto.str.contains(r"\b\d{8,9}\b", regex=True).any()
