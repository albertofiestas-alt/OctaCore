"""Validación del DataFrame de movimientos que circula entre ingesta, reglas y modelo."""

from __future__ import annotations

import pandas as pd

from contratos.modelos import COLUMNAS_MOVIMIENTO, ETIQUETAS_REFERENCIA


class HistoriaInvalida(ValueError):
    """La historia no cumple el contrato. El mensaje dice qué corregir."""


def validar_historia(df: pd.DataFrame) -> pd.DataFrame:
    """Comprueba columnas, tipos básicos y la regla anti fuga. Devuelve el mismo df."""
    faltan = [c for c in COLUMNAS_MOVIMIENTO if c not in df.columns]
    if faltan:
        raise HistoriaInvalida(f"faltan columnas: {faltan}")

    fuga = [c for c in ETIQUETAS_REFERENCIA if c in df.columns]
    if fuga:
        raise HistoriaInvalida(
            f"etiquetas de referencia en la historia (fuga): {fuga}. "
            "Solo se usan en eval/, nunca en modelo, motor ni interfaz."
        )

    if not pd.api.types.is_datetime64_any_dtype(df["fecha_hora"]):
        raise HistoriaInvalida("fecha_hora debe ser datetime (usa pd.to_datetime)")
    if not pd.api.types.is_numeric_dtype(df["monto"]):
        raise HistoriaInvalida("monto debe ser numérico")
    if df["monto"].isna().any():
        raise HistoriaInvalida("monto tiene valores vacíos")

    tipos = set(df["tipo"].dropna().unique()) - {"ingreso", "gasto"}
    if tipos:
        raise HistoriaInvalida(f"tipo solo admite 'ingreso' o 'gasto'; llegó {sorted(tipos)}")
    return df
