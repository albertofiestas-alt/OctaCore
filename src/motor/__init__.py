"""Capa 2: motor de decisión (número de hoy por fecha de pago, semáforo, confianza, propuestas).

Dueño: Sebastián. Esqueleto V0 (Anexo E): reemplaza el cuerpo, NO la firma.
Función pura: no lee archivos ni la hora. El servicio pone respaldo y registro_id.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contratos import Config, Decision, EstadoPersona, Pronostico


def decidir(estado: EstadoPersona, pronostico: Pronostico, cfg: Config) -> Decision:
    raise NotImplementedError("motor con el caso del orden de pagos: 12:30 (Sebastián)")


__all__ = ["decidir"]
