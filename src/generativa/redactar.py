"""Orquesta minimizar, proveedor y verificador. Dueño: Sebastián. Devuelve texto o nada (plantilla)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contratos import Config, Decision

    from generativa.proveedores import Proveedor


def redactar(decision: Decision, cfg: Config, proveedor: Proveedor) -> tuple[str | None, list[str]]:
    """(texto verificado, []) o (None, motivos). Cualquier fallo devuelve None: nunca lanza hacia el servicio."""
    raise NotImplementedError("generativa.redactar: T0 a T0+90 (Sebastián)")


__all__ = ["redactar"]