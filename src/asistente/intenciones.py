"""Intención y parámetros de la pregunta (clasificador ML de TF-IDF y regresión logística, o LLM). Dueño: Gino."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contratos import Config

INTENCIONES = ("explicar_numero", "estado_pago", "que_pasa_si", "propuesta", "concepto", "fuera_de_alcance")


@dataclass(frozen=True)
class Intencion:
    nombre: str
    confianza: float
    monto: float | None = None
    dia: int | None = None


def entrenar_clasificador(csv: str = "data/chat/preguntas.csv", semilla: int = 20261114) -> tuple[Any, float]:
    """(pipeline, exactitud en la partición de prueba 80/20 estratificada)."""
    raise NotImplementedError("asistente.entrenar_clasificador (Gino)")


def clasificar(texto: str, cfg: Config, proveedor: Any | None = None) -> Intencion:
    """Modo 2 con LLM (JSON cerrado, validado en código); si falla o no hay proveedor: clasificador ML y palabras clave."""
    raise NotImplementedError("asistente.clasificar (Gino)")


def parametros(texto: str, intent: Intencion, cfg: Config) -> dict[str, Any]:
    """Escenario validado: día 0..14, monto 0..10000, máximo 3 ingresos extra; gasto_hoy 0..10000."""
    raise NotImplementedError("asistente.parametros (Gino)")


__all__ = ["INTENCIONES", "Intencion", "clasificar", "entrenar_clasificador", "parametros"]