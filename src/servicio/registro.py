"""Registro de cada recomendación: una línea JSON por recomendación (sección 8).

Guarda el identificador, las entradas, la versión del generador y del modelo, la
semilla, el hash de la configuración y la decisión, para poder reproducir y
auditar cualquier recomendación (servicio.auditar, scripts/auditar_recomendacion.py).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from contratos import Registro, hash_config
from contratos.config import RAIZ


def ruta_absoluta(ruta: str | Path) -> Path:
    ruta = Path(ruta)
    return ruta if ruta.is_absolute() else RAIZ / ruta


def nuevo_id() -> str:
    return "R-" + uuid.uuid4().hex[:12]


def construir_registro(
    entradas: dict[str, Any],
    cfg: dict[str, Any],
    registro_id: str | None = None,
    decision: dict[str, Any] | None = None,
) -> Registro:
    return Registro(
        registro_id=registro_id or nuevo_id(),
        entradas=entradas,
        version_generador=cfg["version_generador"],
        version_modelo=cfg["version_modelo"],
        semilla=cfg["semilla_generador"],
        hash_config=hash_config(cfg),
        decision=decision,
    )


def linea(registro: Registro) -> str:
    """Serialización estable: mismas entradas, misma línea (claves ordenadas)."""
    return json.dumps(registro.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)


def agregar_jsonl(obj: dict[str, Any], ruta: str | Path) -> Path:
    """Agrega un objeto como una línea al archivo JSONL. Crea la carpeta si falta."""
    ruta = ruta_absoluta(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")
    return ruta


def leer_jsonl(ruta: str | Path) -> list[dict[str, Any]]:
    ruta = ruta_absoluta(ruta)
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def registrar(registro: Registro, ruta: str | Path) -> Path:
    return agregar_jsonl(registro.model_dump(mode="json"), ruta)


def leer_registros(ruta: str | Path) -> list[Registro]:
    return [Registro.model_validate(d) for d in leer_jsonl(ruta)]


def buscar(registro_id: str, ruta: str | Path) -> Registro | None:
    for r in reversed(leer_registros(ruta)):
        if r.registro_id == registro_id:
            return r
    return None
