"""Guardia de entrada: ahora SÍ entra texto libre. Dueño: Mathias."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contratos import Config


def revisar(texto: str, cfg: Config) -> tuple[bool, str]:
    """(ok, motivo). Rechaza: vacio, largo (máx. cfg["asistente"]["max_caracteres"]), control, url, pii, inyeccion."""
    raise NotImplementedError("asistente.guardia.revisar (Mathias)")


def enmascarar_para_registro(texto: str, cfg: Config) -> str:
    """La pregunta con *** en lugar de PII, antes de guardarla en el registro."""
    raise NotImplementedError("asistente.guardia.enmascarar_para_registro (Mathias)")


__all__ = ["enmascarar_para_registro", "revisar"]