"""Registro de cada recomendación: una línea JSON por recomendación (sección 8).

Guarda entradas, versión del generador y del modelo, semilla y hash de la
configuración, para poder reproducir cualquier recomendación.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from contratos import Config, Registro, hash_config
from contratos.config import RAIZ


def construir_registro(entradas: dict[str, Any], cfg: Config) -> Registro:
    return Registro(
        entradas=entradas,
        version_generador=cfg.version_generador,
        version_modelo=cfg.version_modelo,
        semilla=cfg.semilla_generador,
        hash_config=hash_config(cfg),
    )


def linea(registro: Registro) -> str:
    """Serialización estable: mismas entradas, misma línea (claves ordenadas)."""
    return json.dumps(registro.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)


def registrar(registro: Registro, ruta: str | Path) -> Path:
    """Agrega el registro como una línea al archivo JSONL. Crea la carpeta si falta."""
    ruta = Path(ruta)
    if not ruta.is_absolute():
        ruta = RAIZ / ruta
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "a", encoding="utf-8", newline="\n") as f:
        f.write(linea(registro) + "\n")
    return ruta


def leer_registros(ruta: str | Path) -> list[Registro]:
    ruta = Path(ruta)
    if not ruta.is_absolute():
        ruta = RAIZ / ruta
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8") as f:
        return [Registro.model_validate_json(l) for l in f if l.strip()]
