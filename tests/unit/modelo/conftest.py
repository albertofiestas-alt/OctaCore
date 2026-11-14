"""Fixtures del modelo (dueño: Gino).

La ingesta aún no existe, así que `historia` se arma a mano: se lee el CSV del generador,
se QUITAN las 4 columnas de etiqueta (ETIQUETAS_REFERENCIA) y se parsea fecha_hora.
contratos.validar_historia comprueba que el resultado cumple el contrato (sin fuga).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from contratos import ETIQUETAS_REFERENCIA, cargar_config, validar_historia

MUESTRA = Path(__file__).resolve().parents[3] / "data" / "muestra" / "movimientos.csv"


@pytest.fixture(scope="session")
def movimientos() -> pd.DataFrame:
    df = pd.read_csv(MUESTRA, parse_dates=["fecha_hora"])
    df = df.drop(columns=list(ETIQUETAS_REFERENCIA))
    return validar_historia(df)


@pytest.fixture(scope="session")
def historia(movimientos) -> pd.DataFrame:
    """Historia de UNA persona (la de más movimientos)."""
    cid = movimientos["customer_id"].value_counts().index[0]
    return movimientos[movimientos["customer_id"] == cid].reset_index(drop=True)


@pytest.fixture(scope="session")
def cfg_modelo():
    return cargar_config()


@pytest.fixture(scope="session")
def modelo_entrenado(movimientos, cfg_modelo):
    from modelo import entrenar

    return entrenar(movimientos, cfg_modelo, 12345)
