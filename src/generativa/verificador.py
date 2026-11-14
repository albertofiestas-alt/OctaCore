"""Verificador determinista de la salida del modelo (sin modelo de lenguaje). Dueño: Sebastián."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contratos import Config


def cifras_de(entrada: dict[str, Any]) -> set[float]:
    """Cifras permitidas: numero_hoy, días y montos de pagos, semanas, rango, faltante y ventana_dias."""
    raise NotImplementedError("generativa.cifras_de: T0 a T0+90 (Sebastián)")


def verificar(texto_json: str, entrada: dict[str, Any], cfg: Config) -> tuple[bool, list[str]]:
    """(ok, motivos). Motivos: json_invalido, largo, cifra_inventada, falta_numero_hoy, falta_dia_limite,
    falta_confianza, prohibida, contradiccion, pii_o_url. La primera comprobación que falla corta."""
    raise NotImplementedError("generativa.verificar: T0 a T0+90 (Sebastián)")


__all__ = ["cifras_de", "verificar"]