"""Orquestación: guardia, intención, parámetros, herramientas, RAG, redacción, verificación y registro. Dueño: Anderson."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contratos import Respuesta


def preguntar(servicio: Any, customer_id: str, fecha: date, texto: str, contexto: dict[str, Any] | None = None) -> Respuesta:
    """Una pregunta, una Respuesta. Nunca lanza hacia la app: cualquier fallo es un rechazo o una plantilla."""
    raise NotImplementedError("asistente.flujo.preguntar: corte A (Anderson)")


__all__ = ["preguntar"]