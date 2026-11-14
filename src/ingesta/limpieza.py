"""Limpieza de la ingesta (pasos 5 y 6 de `cargar`): valores por defecto y duplicados.

Garantías:
- Ninguna función modifica su entrada; ambas devuelven objetos nuevos.
- Los conteos y errores nunca incluyen valores de celdas.
"""

from __future__ import annotations

import unicodedata
from typing import Any

import pandas as pd

from contratos import CATEGORIAS, COLUMNAS_MOVIMIENTO

from .errores import ErrorIngesta

CATEGORIA_POR_DEFECTO = "otros"
COMERCIO_POR_DEFECTO = "SIN_COMERCIO"
CATEGORIA_DESCONOCIDA = "categoria_desconocida"
CATEGORIA_IMPUTADA = "categoria_imputada_por_comercio"
ID_REPETIDO = "transaction_id_repetido"
DUPLICADO_EXACTO = "duplicado_exacto"
DUPLICADO_SIN_COMERCIO = "duplicado_sin_comercio"


def _exigir(df: Any, columnas: tuple[str, ...]) -> None:
    if not isinstance(df, pd.DataFrame):
        raise ErrorIngesta("Los datos a limpiar no son una tabla válida.", "entrada no es DataFrame")
    faltan = [c for c in columnas if c not in df.columns]
    if faltan:
        raise ErrorIngesta(
            "Faltan columnas necesarias para limpiar los datos.", f"columnas faltantes: {faltan}"
        )


def _vacio(s: pd.Series) -> pd.Series:
    """Nulo o texto en blanco."""
    return s.isna() | (s.astype("string").str.strip() == "").fillna(False)


def _normalizar(valor: str) -> str:
    """Minúsculas, sin espacios en los bordes y sin tildes."""
    base = unicodedata.normalize("NFKD", valor.strip().lower())
    return "".join(c for c in base if not unicodedata.combining(c))


def aplicar_defaults(df: pd.DataFrame, cfg: Any) -> tuple[pd.DataFrame, dict[str, int]]:
    """Rellena categoria y comercio vacíos y devuelve (df nuevo, faltantes).

    `categoria` vacía o fuera de CATEGORIAS pasa a "otros" (antes se normaliza: minúsculas y
    sin tildes). `comercio` vacío pasa a "SIN_COMERCIO". `faltantes` cuenta los vacíos de cada
    columna del contrato presente en `df`, antes del default, más "categoria_desconocida"
    (categorías con texto que no están en el contrato).
    """
    _exigir(df, ("categoria", "comercio"))
    out = df.copy()

    faltantes = {c: int(_vacio(df[c]).sum()) for c in COLUMNAS_MOVIMIENTO if c in df.columns}

    cat_vacia = _vacio(out["categoria"])
    norm = out["categoria"].where(~cat_vacia).map(lambda v: _normalizar(str(v)) if pd.notna(v) else None)
    desconocida = ~cat_vacia & ~norm.isin(CATEGORIAS)
    categoria = norm.where(~cat_vacia & ~desconocida, CATEGORIA_POR_DEFECTO)

    com_vacio = _vacio(out["comercio"])
    imputada = _imputar_por_comercio(out, norm, cat_vacia, com_vacio)
    categoria = categoria.where(imputada.isna(), imputada)
    out["categoria"] = categoria.astype(object)

    out["comercio"] = out["comercio"].where(~com_vacio, COMERCIO_POR_DEFECTO).astype(object)

    faltantes[CATEGORIA_DESCONOCIDA] = int(desconocida.sum())
    faltantes[CATEGORIA_IMPUTADA] = int(imputada.notna().sum())
    return out, faltantes


def _imputar_por_comercio(
    df: pd.DataFrame, norm: pd.Series, cat_vacia: pd.Series, com_vacio: pd.Series
) -> pd.Series:
    """Categoría para las filas con categoria vacía, tomada de la misma persona y comercio.

    Solo si en las otras filas de esa persona y ese comercio hay exactamente UNA categoría válida
    (un dato faltante del alquiler sigue siendo alquiler). Si no hay ninguna o hay varias, queda NA
    y rige el default "otros". Sin customer_id o con el comercio vacío no se imputa nada.
    """
    vacia = pd.Series(pd.NA, index=df.index, dtype=object)
    if "customer_id" not in df.columns:
        return vacia
    validas = ~cat_vacia & norm.isin(CATEGORIAS) & ~com_vacio
    if not validas.any() or not (cat_vacia & ~com_vacio).any():
        return vacia
    claves = ["customer_id", "comercio"]
    conocidas = pd.DataFrame({"customer_id": df["customer_id"], "comercio": df["comercio"], "cat": norm})[validas]
    unicas = conocidas.groupby(claves)["cat"].agg(lambda s: s.iloc[0] if s.nunique() == 1 else pd.NA)
    objetivo = df.loc[cat_vacia & ~com_vacio, claves]
    cruce = objetivo.merge(unicas.rename("cat").reset_index(), on=claves, how="left")
    vacia.loc[objetivo.index] = cruce["cat"].to_numpy()
    return vacia.where(vacia.notna(), pd.NA)


def quitar_duplicados(df: pd.DataFrame) -> tuple[pd.DataFrame, int, dict[str, int]]:
    """Quita duplicados y devuelve (df nuevo, total, detalle).

    Primero los `transaction_id` repetidos (se conserva el primero); después las filas que repiten
    customer_id + fecha_hora + monto (redondeado a 2) + comercio + tipo con otro id (se conserva
    la primera). Por último, dentro de cada grupo customer_id + fecha_hora + monto (redondeado a 2)
    + tipo, si hay filas con SIN_COMERCIO y un único comercio real, se quitan las de SIN_COMERCIO
    (la copia con el comercio vacío no coincide con su original por la clave anterior). Con dos o más
    comercios reales distintos no se toca nada. El detalle es {"transaction_id_repetido": n,
    "duplicado_exacto": m, "duplicado_sin_comercio": k} y el total suma los tres.
    """
    _exigir(df, ("customer_id", "transaction_id", "fecha_hora", "monto", "comercio", "tipo"))
    out = df.copy()

    por_id = out.duplicated(subset="transaction_id", keep="first")
    n_id = int(por_id.sum())
    out = out[~por_id]

    clave = pd.DataFrame(
        {
            "customer_id": out["customer_id"],
            "fecha_hora": out["fecha_hora"],
            "monto": pd.to_numeric(out["monto"], errors="coerce").round(2),
            "comercio": out["comercio"],
            "tipo": out["tipo"],
        }
    )
    exacto = clave.duplicated(keep="first")
    n_exacto = int(exacto.sum())
    out = out[~exacto]

    sin = out["comercio"] == COMERCIO_POR_DEFECTO
    grupo = pd.DataFrame(
        {
            "customer_id": out["customer_id"],
            "fecha_hora": out["fecha_hora"],
            "monto": pd.to_numeric(out["monto"], errors="coerce").round(2),
            "tipo": out["tipo"],
        }
    )
    reales = out["comercio"].where(~sin & out["comercio"].notna())
    n_reales = reales.groupby([grupo[c] for c in grupo.columns], dropna=False).transform("nunique")
    huerfana = sin & (n_reales == 1)
    n_sin = int(huerfana.sum())
    out = out[~huerfana].reset_index(drop=True)

    detalle = {ID_REPETIDO: n_id, DUPLICADO_EXACTO: n_exacto, DUPLICADO_SIN_COMERCIO: n_sin}
    return out, n_id + n_exacto + n_sin, detalle


__all__ = ["aplicar_defaults", "quitar_duplicados"]
