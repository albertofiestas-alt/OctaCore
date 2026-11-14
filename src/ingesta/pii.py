"""Detección y enmascarado de PII (privacidad P0).

Los patrones salen de cfg["patrones_pii"] y se aplican en ese orden. El enmascarado
solo toca customer_id, comercio y categoria; nunca monto, fechas ni saldo.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

MASCARA = "***"
COLUMNAS_TEXTO = ("customer_id", "comercio", "categoria")


@lru_cache(maxsize=16)
def _compilar(items: tuple[tuple[str, str], ...]) -> tuple[tuple[str, re.Pattern[str]], ...]:
    return tuple((tipo, re.compile(patron)) for tipo, patron in items)


def _patrones(cfg: Any) -> tuple[tuple[str, re.Pattern[str]], ...]:
    return _compilar(tuple((str(k), str(v)) for k, v in cfg["patrones_pii"].items()))


def detectar_pii(texto: str, cfg: Any) -> list[str]:
    """Tipos de PII presentes en `texto`, en el orden de cfg["patrones_pii"].

    Cada patrón se evalúa sobre el texto original. None o un valor que no sea texto -> [].
    """
    if not isinstance(texto, str):
        return []
    return [tipo for tipo, rx in _patrones(cfg) if rx.search(texto)]


def _enmascarar_valor(
    valor: str, patrones: tuple[tuple[str, re.Pattern[str]], ...]
) -> tuple[str, int]:
    total = 0
    for _, rx in patrones:
        valor, n = rx.subn(MASCARA, valor)
        total += n
    return valor, total


def enmascarar_pii(df: pd.DataFrame, cfg: Any) -> tuple[pd.DataFrame, int]:
    """Copia de `df` con cada coincidencia reemplazada por "***" y el número de coincidencias.

    Aplica los regex solo a los valores únicos de cada columna y mapea el resultado.
    """
    patrones = _patrones(cfg)
    salida = df.copy()
    total = 0
    for col in COLUMNAS_TEXTO:
        if col not in salida.columns:
            continue
        serie = salida[col]
        mapa: dict[str, str] = {}
        conteo: dict[str, int] = {}
        for u in serie.dropna().unique():
            if not isinstance(u, str):
                continue
            nuevo, n = _enmascarar_valor(u, patrones)
            if n:
                mapa[u] = nuevo
                conteo[u] = n
        if not mapa:
            continue
        for valor, veces in serie[serie.isin(list(mapa))].value_counts().items():
            total += conteo[valor] * int(veces)
        salida[col] = serie.map(lambda v: mapa.get(v, v) if isinstance(v, str) else v)
    return salida, total
