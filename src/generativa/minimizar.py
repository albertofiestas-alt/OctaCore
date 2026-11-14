"""Lista blanca: lo ÚNICO que ve el modelo de lenguaje. Dueño: Sebastián."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contratos import Decision

# Nada fuera de estas claves sale de la laptop: sin customer_id, comercios, fechas absolutas ni texto libre.
CLAVES_PERMITIDAS = frozenset(
    {"numero_hoy", "ventana_dias", "pagos", "punto_limite", "confianza", "evidencia", "supuestos", "limites", "propuesta"}
)


def minimizar(decision: Decision) -> dict[str, Any]:
    """EntradaGenerativa: números, días ("día 3") y frases fijas del motor."""
    raise NotImplementedError("generativa.minimizar: T0 a T0+90 (Sebastián)")


__all__ = ["CLAVES_PERMITIDAS", "minimizar"]