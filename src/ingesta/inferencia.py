"""Inferencias sobre movimientos ya limpios (pasos 7, 8 y 9 de `cargar`).

Entrada común: un DataFrame con fecha_hora (datetime), monto (float con signo:
ingreso positivo, gasto negativo), tipo y categoria normalizados, customer_id y
comercio. Ninguna función modifica el DataFrame recibido.

Parámetros en cfg["ingesta"]: mad_k, tol_monto, tol_dia, min_ocurrencias,
ventana_suscripcion_dias y, opcional, atipicos_agrupar (columnas del
agrupamiento de atípicos; por defecto [customer_id, tipo] como dice el plan).
"""

from __future__ import annotations

from itertools import pairwise
from typing import Any

import numpy as np
import pandas as pd

CATEGORIAS_PAGO = ("alquiler", "servicios", "deuda", "suscripcion")
CATEGORIA_SUSCRIPCION = "suscripcion"
COLUMNA_ATIPICO = "atipico_detectado"
_DIAS_CICLO = 31  # período circular del día del mes: 31 y 1 están a un día

_PORDEFECTO: dict[str, Any] = {
    "mad_k": 5,
    "tol_monto": 0.10,
    "tol_dia": 3,
    "min_ocurrencias": 3,
    "ventana_suscripcion_dias": 30,
    "atipicos_agrupar": ["customer_id", "tipo"],
}


def _param(cfg: Any, nombre: str) -> Any:
    try:
        valor = cfg["ingesta"].get(nombre)
    except (KeyError, TypeError, AttributeError):
        valor = None
    return _PORDEFECTO[nombre] if valor is None else valor


def _es_gasto(df: pd.DataFrame) -> pd.Series:
    if "tipo" in df.columns:
        return df["tipo"] == "gasto"
    return df["monto"] < 0


# --- Paso 7: atípicos -------------------------------------------------------


def marcar_atipicos(df: pd.DataFrame, cfg: Any) -> tuple[pd.DataFrame, int]:
    """Agrega la columna bool `atipico_detectado` y devuelve (df, cantidad).

    Por grupo (atipicos_agrupar, por defecto persona y tipo): con m la mediana de
    |monto| y mad = mediana(| |monto| - m |), es atípico si |monto| > m + mad_k * mad.
    Si mad es 0, el umbral es 5 * m.
    """
    k = float(_param(cfg, "mad_k"))
    columnas = list(_param(cfg, "atipicos_agrupar"))
    salida = df.copy()
    if salida.empty:
        salida[COLUMNA_ATIPICO] = pd.Series(dtype=bool)
        return salida, 0

    absoluto = salida["monto"].abs()
    grupos = absoluto.groupby([salida[c] for c in columnas], dropna=False)
    mediana = grupos.transform("median")
    mad = (
        (absoluto - mediana)
        .abs()
        .groupby([salida[c] for c in columnas], dropna=False)
        .transform("median")
    )
    umbral = np.where(mad > 0, mediana + k * mad, 5 * mediana)
    salida[COLUMNA_ATIPICO] = (absoluto > umbral).astype(bool)
    return salida, int(salida[COLUMNA_ATIPICO].sum())


# --- Paso 8: pagos con fecha ------------------------------------------------


def _distancia_dia(dias: np.ndarray, centro: int) -> np.ndarray:
    d = np.abs(dias - centro)
    return np.minimum(d, _DIAS_CICLO - d)


def _dia_central(dias: np.ndarray) -> tuple[int, int]:
    """Día del mes (1..31) que minimiza la desviación circular máxima; desempata por la suma.

    Devuelve (centro, desviación máxima)."""
    mejor: tuple[int, int, int] | None = None
    for centro in range(1, _DIAS_CICLO + 1):
        dist = _distancia_dia(dias, centro)
        clave = (int(dist.max()), int(dist.sum()), centro)
        if mejor is None or clave < mejor:
            mejor = clave
    assert mejor is not None
    return mejor[2], mejor[0]


def pagos_inferidos(df: pd.DataFrame, cfg: Any) -> list[dict]:
    """Pagos con fecha: gastos de alquiler, servicios, deuda y suscripción sin atípicos.

    Por persona + comercio + categoría: se conservan las ocurrencias con |monto| dentro
    de tol_monto de la mediana; es pago si quedan >= min_ocurrencias y ninguna se aleja
    más de tol_dia (distancia circular) del día central. Cada dict sigue PagoInferido.
    """
    tol_monto = float(_param(cfg, "tol_monto"))
    tol_dia = int(_param(cfg, "tol_dia"))
    min_ocurrencias = int(_param(cfg, "min_ocurrencias"))

    if COLUMNA_ATIPICO not in df.columns:
        df, _ = marcar_atipicos(df, cfg)
    base = df[
        _es_gasto(df)
        & df["categoria"].isin(CATEGORIAS_PAGO)
        & ~df[COLUMNA_ATIPICO].astype(bool)
    ]

    pagos: list[dict] = []
    for (cliente, comercio, categoria), grupo in base.groupby(
        ["customer_id", "comercio", "categoria"], sort=True
    ):
        montos = grupo["monto"].abs()
        mediana = float(montos.median())
        cerca = grupo[(montos - mediana).abs() <= tol_monto * mediana + 1e-9]
        if len(cerca) < min_ocurrencias:
            continue
        dias = cerca["fecha_hora"].dt.day.to_numpy()
        centro, desviacion = _dia_central(dias)
        if desviacion > tol_dia:
            continue
        pagos.append(
            {
                "customer_id": str(cliente),
                "comercio": str(comercio),
                "categoria": str(categoria),
                "monto": round(float(cerca["monto"].abs().median()), 2),
                "dia_mes": int(centro),
                "ocurrencias": len(cerca),
            }
        )
    return pagos


# --- Paso 9: suscripciones duplicadas ---------------------------------------


def suscripciones_duplicadas(df: pd.DataFrame, cfg: Any) -> list[dict]:
    """Avisos de cobros de suscripción repetidos: mismo comercio y monto dos veces
    dentro de ventana_suscripcion_dias (diferencia en días de calendario <= ventana).

    Compara cobros consecutivos de cada persona + comercio + monto. No elimina nada.
    """
    ventana = int(_param(cfg, "ventana_suscripcion_dias"))
    base = df[_es_gasto(df) & (df["categoria"] == CATEGORIA_SUSCRIPCION)].copy()
    if base.empty:
        return []
    base["_monto"] = base["monto"].abs().round(2)

    avisos: list[dict] = []
    for (cliente, comercio, monto), grupo in base.groupby(
        ["customer_id", "comercio", "_monto"], sort=True
    ):
        fechas = grupo.sort_values("fecha_hora")["fecha_hora"].tolist()
        for anterior, actual in pairwise(fechas):
            if (actual.normalize() - anterior.normalize()).days <= ventana:
                avisos.append(
                    {
                        "customer_id": str(cliente),
                        "comercio": str(comercio),
                        "monto": float(monto),
                        "fecha_1": anterior.isoformat(),
                        "fecha_2": actual.isoformat(),
                    }
                )
    return avisos
