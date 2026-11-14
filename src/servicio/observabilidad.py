"""Observabilidad (Challenge pack): logs/salud.jsonl y su resumen.

Una línea por operación del servicio con su latencia, método, respaldo y error.
servicio.salud() resume las consultas: p50, p95, tasa de error y tasa de respaldo.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from servicio.registro import agregar_jsonl, leer_jsonl


def anotar(
    ruta: str | Path,
    operacion: str,
    latencia_ms: float,
    metodo: str | None = None,
    respaldo: bool = False,
    error: str | None = None,
) -> None:
    agregar_jsonl(
        {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "operacion": operacion,
            "latencia_ms": round(latencia_ms, 3),
            "metodo": metodo,
            "respaldo": respaldo,
            "error": error,
        },
        ruta,
    )


def _percentil(valores: list[float], p: float) -> float | None:
    """Percentil por rango más cercano (sin interpolar): siempre un valor observado."""
    if not valores:
        return None
    ordenados = sorted(valores)
    k = max(1, math.ceil(p / 100 * len(ordenados)))
    return ordenados[k - 1]


def resumen(ruta: str | Path) -> dict[str, Any]:
    consultas = [e for e in leer_jsonl(ruta) if e.get("operacion") == "consultar"]
    n = len(consultas)
    latencias = [e["latencia_ms"] for e in consultas if not e.get("error")]
    errores = sum(1 for e in consultas if e.get("error"))
    respaldos = sum(1 for e in consultas if e.get("respaldo") and not e.get("error"))
    return {
        "consultas": n,
        "p50": _percentil(latencias, 50),
        "p95": _percentil(latencias, 95),
        "tasa_error": errores / n if n else 0.0,
        "tasa_respaldo": respaldos / n if n else 0.0,
        "unidad": "ms",
    }
