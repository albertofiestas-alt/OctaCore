"""Respuestas de plantilla por intención (modo 1 y respaldo del modo 2). Dueño: Sebastián."""

from __future__ import annotations

from typing import Any


def plantilla(intencion: str, resultados: dict[str, Any]) -> tuple[str, list[str]]:
    """(texto, acciones) con tres bloques: Datos, Qué significa, Qué puedes hacer (acciones simuladas, nunca operaciones).
    Toda cifra del texto sale de `resultados`."""
    raise NotImplementedError("asistente.plantilla (Sebastián)")


__all__ = ["plantilla"]