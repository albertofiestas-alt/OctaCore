"""Simulación de escenarios hipotéticos (opción C): "¿y si cobro S/200 el día 5?". Dueño: Sebastián.

Cuando se llegue al corte A, motor.decidir recibe el parámetro OPCIONAL ingresos_extra=() (compatible con todo lo
anterior; hay que actualizar FIRMAS en contratos/firmas.py con la aprobación de Anderson y Gino) y simular lo usa.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contratos import Config, Decision, Escenario, EstadoPersona, Pronostico


def simular(estado: EstadoPersona, pronostico: Pronostico, escenario: Escenario, cfg: Config) -> Decision:
    """Una Decision completa con el saldo menos gasto_hoy y los ingresos extra como ingreso CONOCIDO (sin cuantiles)."""
    raise NotImplementedError("motor.simular: corte A (Sebastián)")


__all__ = ["simular"]