"""Validación de esquema de la ingesta (pasos 2 a 4 de `cargar`, sección 5 del plan).

Orden de uso: descartar_sensibles -> separar_etiquetas -> validar_esquema -> validar_tipos.

Garantías:
- Ninguna función modifica su entrada; todas devuelven objetos nuevos.
- Las columnas sensibles (diccionario de datos y cfg["variables_sensibles"], sin distinguir
  mayúsculas) se eliminan
  antes de cualquier otro paso y se listan para el ReporteCalidad.
- Las cuatro etiquetas de referencia se separan y NO viajan en los movimientos limpios.
- Los errores y avisos solo nombran columnas o conteos, nunca el valor de una celda.
- Cada fila rechazada cuenta una sola vez, bajo el primer motivo que falla.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from contratos import COLUMNAS_MOVIMIENTO, ETIQUETAS_REFERENCIA

from . import diccionario
from .errores import ErrorIngesta

OBLIGATORIAS: tuple[str, ...] = (
    "customer_id",
    "transaction_id",
    "fecha_hora",
    "monto",
    "moneda",
    "tipo",
    "categoria",
    "comercio",
)
OPCIONALES: tuple[str, ...] = ("saldo", "ingreso_recurrente")

# Motivos de rechazo (claves de ReporteCalidad.rechazos).
FECHA_INVALIDA = "fecha_invalida"
MONTO_INVALIDO = "monto_invalido"
MONEDA_NO_PEN = "moneda_distinta_de_PEN"
TIPO_INVALIDO = "tipo_invalido"
ID_VACIO = "identificador_vacio"


def descartar_sensibles(df: pd.DataFrame, cfg: Any) -> tuple[pd.DataFrame, list[str]]:
    """Elimina las columnas sensibles del diccionario y de cfg["variables_sensibles"]. Devuelve (df, nombres descartados)."""
    sensibles = diccionario.sensibles(cfg)
    fuera = [c for c in df.columns if str(c).strip().lower() in sensibles]
    return df.drop(columns=fuera).copy(), fuera


def separar_etiquetas(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa es_duplicado, es_atipico, pago_con_fecha y arquetipo.

    Devuelve (movimientos sin etiquetas, etiquetas por transaction_id). Solo
    `cargar_etiquetas` entrega las etiquetas, y solo la evaluación las usa.
    """
    columnas = [c for c in df.columns if c in ETIQUETAS_REFERENCIA]
    etiquetas = df[columnas].copy()
    if columnas and "transaction_id" in df.columns:
        etiquetas.index = df["transaction_id"]
    return df.drop(columns=columnas).copy(), etiquetas


def validar_esquema(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Exige las columnas obligatorias y deja solo las del contrato.

    Devuelve (df con COLUMNAS_MOVIMIENTO [+ ingreso_recurrente], columnas extra ignoradas).
    Falta una obligatoria: ErrorIngesta cuyo mensaje las nombra.
    """
    faltan = [c for c in OBLIGATORIAS if c not in df.columns]
    if faltan:
        raise ErrorIngesta(
            f"Faltan columnas obligatorias: {', '.join(faltan)}. Agrégalas al archivo e inténtalo de nuevo.",
            f"columnas faltantes: {faltan}",
        )
    conocidas = set(OBLIGATORIAS) | set(OPCIONALES)
    extra = [c for c in df.columns if c not in conocidas]
    out = df[[c for c in COLUMNAS_MOVIMIENTO if c in df.columns]].copy()
    if "saldo" not in out.columns:
        out["saldo"] = np.nan
    out = out[list(COLUMNAS_MOVIMIENTO)]
    if "ingreso_recurrente" in df.columns:
        out["ingreso_recurrente"] = df["ingreso_recurrente"].to_numpy()
    return out, extra


def _texto(s: pd.Series) -> pd.Series:
    """Serie de texto sin espacios en los bordes; los vacíos quedan como NA."""
    t = s.astype("string").str.strip()
    return t.mask(t == "", pd.NA)


def _fechas(s: pd.Series) -> pd.Series:
    try:
        f = pd.to_datetime(_texto(s), errors="coerce", format="mixed")
    except (ValueError, TypeError, OverflowError):
        f = pd.Series(pd.NaT, index=s.index)
    if getattr(f.dtype, "tz", None) is not None:
        f = f.dt.tz_localize(None)
    return f


def _numero(s: pd.Series) -> pd.Series:
    n = pd.to_numeric(_texto(s), errors="coerce").astype("float64")
    return n.where(np.isfinite(n))  # NaN e infinito pasan a NaN


def validar_tipos(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int], int]:
    """Convierte tipos, rechaza filas inválidas y corrige el signo.

    Devuelve (df limpio con fecha_hora datetime y monto float, rechazos por motivo,
    signos corregidos). El conteo de signos corregidos es aparte porque no es un rechazo.
    """
    out = df.copy()
    vivo = pd.Series(True, index=out.index)
    rechazos: dict[str, int] = {}

    def rechazar(malas: pd.Series, motivo: str) -> None:
        nonlocal vivo
        malas = malas.fillna(True) & vivo
        if malas.any():
            rechazos[motivo] = int(malas.sum())
            vivo = vivo & ~malas

    for col in ("customer_id", "transaction_id"):
        out[col] = _texto(out[col])
    rechazar(out["customer_id"].isna() | out["transaction_id"].isna(), ID_VACIO)

    out["fecha_hora"] = _fechas(out["fecha_hora"])
    rechazar(out["fecha_hora"].isna(), FECHA_INVALIDA)

    out["monto"] = _numero(out["monto"])
    rechazar(out["monto"].isna(), MONTO_INVALIDO)

    moneda = _texto(out["moneda"]).str.upper()
    rechazar(moneda != "PEN", MONEDA_NO_PEN)
    out["moneda"] = "PEN"

    tipo = _texto(out["tipo"]).str.lower()
    rechazar(~tipo.isin(["ingreso", "gasto"]), TIPO_INVALIDO)
    out["tipo"] = tipo

    out["saldo"] = _numero(out["saldo"])
    out = out[vivo].copy()

    # Ingreso positivo y gasto negativo; si no, se corrige el signo y se cuenta.
    mal = ((out["tipo"] == "ingreso") & (out["monto"] < 0)) | ((out["tipo"] == "gasto") & (out["monto"] > 0))
    out.loc[mal, "monto"] = -out.loc[mal, "monto"]

    for col in ("customer_id", "transaction_id", "tipo"):
        out[col] = out[col].astype(object)
    for col in ("categoria", "comercio"):
        out[col] = _texto(out[col]).astype(object)
        out[col] = out[col].where(out[col].notna(), None)
    return out.reset_index(drop=True), rechazos, int(mal.sum())


__all__ = [
    "OBLIGATORIAS",
    "descartar_sensibles",
    "separar_etiquetas",
    "validar_esquema",
    "validar_tipos",
]
