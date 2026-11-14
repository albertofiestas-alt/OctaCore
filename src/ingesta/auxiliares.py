"""Funciones auxiliares de la ingesta: próximos pagos, semanas de historia y etiquetas.

`__init__` las expone con estas mismas firmas. Ninguna modifica sus entradas.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from contratos import ETIQUETAS_REFERENCIA, PagoConFecha, cargar_config

from . import esquema, lectura
from .errores import ErrorIngesta

_BOOLEANAS = ("es_duplicado", "es_atipico", "pago_con_fecha")
_VERDADERO = {"true", "1", "si", "sí", "yes", "t", "y"}


def _como_fecha(valor: date | datetime | pd.Timestamp) -> date:
    return valor.date() if isinstance(valor, datetime) else valor


def _campo(pago: Any, nombre: str) -> Any:
    return pago[nombre] if isinstance(pago, dict) else getattr(pago, nombre)


def _fecha_en_mes(anio: int, mes: int, dia_mes: int) -> date:
    return date(anio, mes, min(dia_mes, calendar.monthrange(anio, mes)[1]))


def _proxima_fecha(dia_mes: int, fecha_corte: date) -> date:
    """Primera fecha >= fecha_corte con ese día del mes (el último día si el mes no lo tiene)."""
    actual = _fecha_en_mes(fecha_corte.year, fecha_corte.month, dia_mes)
    if actual >= fecha_corte:
        return actual
    anio, mes = (fecha_corte.year + 1, 1) if fecha_corte.month == 12 else (fecha_corte.year, fecha_corte.month + 1)
    return _fecha_en_mes(anio, mes, dia_mes)


def proximos_pagos(
    pagos_inferidos: list[Any], customer_id: str, fecha_corte: date | datetime, ventana: int = 14
) -> list[PagoConFecha]:
    """Pagos con fecha de la persona entre fecha_corte y fecha_corte + ventana, ordenados por día."""
    corte = _como_fecha(fecha_corte)
    salida: list[PagoConFecha] = []
    for p in pagos_inferidos or []:
        if _campo(p, "customer_id") != customer_id:
            continue
        fecha = _proxima_fecha(int(_campo(p, "dia_mes")), corte)
        dias = (fecha - corte).days
        if 0 <= dias <= ventana:
            comercio = _campo(p, "comercio")
            salida.append(
                PagoConFecha(
                    pago_id=f"{customer_id}:{comercio}:{fecha.isoformat()}",
                    dia=dias,
                    monto=abs(float(_campo(p, "monto"))),
                    categoria=_campo(p, "categoria"),
                )
            )
    return sorted(salida, key=lambda x: x.dia)


def semanas_historia(movimientos: pd.DataFrame, customer_id: str, fecha_corte: date | datetime) -> int:
    """Semanas completas desde el primer movimiento de la persona hasta fecha_corte (0 si no hay)."""
    corte = _como_fecha(fecha_corte)
    m = movimientos[movimientos["customer_id"] == customer_id]
    if m.empty:
        return 0
    fechas = pd.to_datetime(m["fecha_hora"], errors="coerce").dropna().dt.date
    fechas = fechas[fechas <= corte]
    if fechas.empty:
        return 0
    return (corte - min(fechas)).days // 7


def _a_bool(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s
    return s.map(lambda v: (not pd.isna(v)) and str(v).strip().lower() in _VERDADERO).astype(bool)


def cargar_etiquetas(origen: str | Path) -> pd.DataFrame:
    """SOLO evaluación: etiquetas presentes, indexadas por transaction_id (primer registro por id)."""
    df = lectura.leer(origen, cargar_config())
    _, etiquetas = esquema.separar_etiquetas(df)
    if etiquetas.shape[1] == 0 or "transaction_id" not in df.columns:
        raise ErrorIngesta(
            "El archivo no trae etiquetas de referencia (es_duplicado, es_atipico, pago_con_fecha, arquetipo).",
            "sin columnas de etiquetas",
        )
    etiquetas = etiquetas[~etiquetas.index.duplicated(keep="first")]
    for col in _BOOLEANAS:
        if col in etiquetas.columns:
            etiquetas[col] = _a_bool(etiquetas[col])
    if "arquetipo" in etiquetas.columns:
        etiquetas["arquetipo"] = etiquetas["arquetipo"].astype("string").astype(object)
    return etiquetas[[c for c in ETIQUETAS_REFERENCIA if c in etiquetas.columns]]
