"""Fachada única, configuración, registro, orquestación y modo de respaldo.

Dueño: Anderson. Firmas: consultar(id, fecha, metodo) -> Decision; responder(propuesta_id, accion).
La app solo importa este módulo (y contratos).
"""

from __future__ import annotations

from datetime import date

from contratos import Accion, Decision, Metodo


def consultar(id: str, fecha: date, metodo: Metodo) -> Decision:
    """Orquesta ingesta -> (reglas | modelo) -> motor y registra la recomendación."""
    raise NotImplementedError("servicio.consultar con la regla 2: meta de las 13:00 (control 1)")


def responder(propuesta_id: str, accion: Accion) -> None:
    """Registra si la persona aprueba o rechaza una propuesta. No ejecuta nada."""
    raise NotImplementedError("servicio.responder: meta del control 2 (16:00)")


__all__ = ["consultar", "responder"]
