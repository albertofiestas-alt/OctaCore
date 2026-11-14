"""Proveedor de OpenAI con la cuenta del equipo. Dueño: Anderson.

La clave vive SOLO en .env (LLM_API_KEY) y el modelo en LLM_MODEL. Nunca la escribas en el código, en un
mensaje ni en el registro. Si falta algo, ProveedorNoDisponible y el servicio usa la plantilla.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from contratos import Config


class ProveedorNoDisponible(Exception):
    """Falta la clave, el modelo o la red."""


class Proveedor(Protocol):
    def generar(self, sistema: str, usuario: str) -> str: ...


class ProveedorOpenAI:
    """Una llamada corta con timeout y un reintento. Algunos modelos piden max_completion_tokens y no admiten
    temperature [verificar en la documentación de OpenAI]."""

    def __init__(self, cfg: Config) -> None:
        raise NotImplementedError("generativa.ProveedorOpenAI: T0 a T0+60 (Anderson)")

    def generar(self, sistema: str, usuario: str) -> str:
        raise NotImplementedError("generativa.ProveedorOpenAI.generar: T0 a T0+60 (Anderson)")


class Cortacircuitos:
    """Tres fallos seguidos apagan la capa 60 segundos."""

    def __init__(self, fallos: int = 3, pausa_s: float = 60.0) -> None:
        raise NotImplementedError("generativa.Cortacircuitos: T0 a T0+60 (Anderson)")

    def permite(self) -> bool:
        raise NotImplementedError("generativa.Cortacircuitos.permite (Anderson)")

    def registrar(self, ok: bool) -> None:
        raise NotImplementedError("generativa.Cortacircuitos.registrar (Anderson)")


__all__ = ["Cortacircuitos", "Proveedor", "ProveedorNoDisponible", "ProveedorOpenAI"]