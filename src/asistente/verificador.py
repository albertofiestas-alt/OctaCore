"""Verificador de salida del asistente (extiende al de la opción B). Dueño: Sebastián."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contratos import Config


def verificar_respuesta(
    obj: dict[str, Any], resultados: dict[str, Any], pasajes: list[dict[str, Any]], cfg: Config
) -> tuple[bool, list[str]]:
    """(ok, motivos). Motivos: largo, cifra_inventada, cita_inexistente, falta_cita, nombre_interno,
    prohibida_o_pii, falta_cifra_clave. Si falla, el flujo usa la plantilla."""
    raise NotImplementedError("asistente.verificar_respuesta (Sebastián)")


__all__ = ["verificar_respuesta"]