"""Diccionario de datos de la ingesta (config/ingesta.yaml -> cfg["ingesta"]["diccionario"]).

Fuente de verdad de qué columnas son sensibles, cuáles son etiquetas de referencia y
cuáles son obligatorias. Si el diccionario no está en `cfg`, rige solo la lista
`variables_sensibles` de config/base.yaml, que además se une siempre al diccionario:
una columna se descarta si cualquiera de las dos fuentes la marca como sensible.
"""

from __future__ import annotations

from typing import Any


def _entradas(cfg: Any) -> dict[str, Any]:
    try:
        d = cfg["ingesta"]["diccionario"]
    except (KeyError, TypeError):
        return {}
    return dict(d) if d else {}


def _con_rol(cfg: Any, rol: str) -> list[str]:
    return [c for c, e in _entradas(cfg).items() if e.get("rol") == rol]


def sensibles(cfg: Any) -> set[str]:
    """Nombres en minúsculas: unión del diccionario y de cfg["variables_sensibles"]."""
    base = cfg["variables_sensibles"] if _tiene(cfg, "variables_sensibles") else ()
    return {str(c).strip().lower() for c in [*_con_rol(cfg, "sensible"), *base]}


def etiquetas(cfg: Any) -> list[str]:
    return _con_rol(cfg, "etiqueta")


def obligatorias(cfg: Any) -> list[str]:
    return [c for c, e in _entradas(cfg).items() if e.get("obligatoria") is True]


def _tiene(cfg: Any, clave: str) -> bool:
    try:
        cfg[clave]
    except (KeyError, TypeError):
        return False
    return True
