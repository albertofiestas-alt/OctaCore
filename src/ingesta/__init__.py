"""Capa 1: ingesta y calidad.

Dueño: Mathias. Esqueleto V0 (Anexo E): reemplaza el cuerpo, NO la firma.
`cfg` es contratos.cargar_config(); tus parámetros van en config/ingesta.yaml -> cfg["ingesta"].
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    import pandas as pd

    from contratos import Config, PagoConFecha, ReporteCalidad


class ErrorIngesta(Exception):
    """Archivo vacío, ilegible, demasiado grande o sin columnas del contrato."""

    def __init__(self, mensaje_usuario: str, detalle: str = "") -> None:
        super().__init__(mensaje_usuario)
        self.mensaje_usuario = mensaje_usuario  # qué corregir, en palabras simples
        self.detalle = detalle


def cargar(
    origen: str | Path | BinaryIO, cfg: Config
) -> tuple[pd.DataFrame, ReporteCalidad, list[dict[str, Any]]]:
    """(movimientos_limpios con atipico_detectado, ReporteCalidad, pagos_inferidos como dicts)."""
    raise NotImplementedError("ingesta v0 con pagos inferidos: 12:00 (Mathias)")


def proximos_pagos(
    pagos_inferidos: list[dict[str, Any]], customer_id: str, fecha_corte: date, ventana: int = 14
) -> list[PagoConFecha]:
    """Pagos con fecha de la persona entre fecha_corte y fecha_corte + ventana, ordenados por día."""
    raise NotImplementedError("ingesta.proximos_pagos: 12:00 (Mathias)")


def semanas_historia(movimientos: pd.DataFrame, customer_id: str, fecha_corte: date) -> int:
    raise NotImplementedError("ingesta.semanas_historia: 12:00 (Mathias)")


def cargar_etiquetas(origen: str | Path) -> pd.DataFrame:
    """SOLO evaluación: etiquetas de referencia indexadas por transaction_id."""
    raise NotImplementedError("ingesta.cargar_etiquetas (Mathias)")


def detectar_pii(texto: str, cfg: Config) -> list[str]:
    """Tipos de PII encontrados según cfg["patrones_pii"]."""
    raise NotImplementedError("ingesta.detectar_pii: 13:00-16:00 (Mathias)")


def enmascarar_pii(df: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, int]:
    raise NotImplementedError("ingesta.enmascarar_pii: 13:00-16:00 (Mathias)")


__all__ = [
    "ErrorIngesta",
    "cargar",
    "cargar_etiquetas",
    "detectar_pii",
    "enmascarar_pii",
    "proximos_pagos",
    "semanas_historia",
]
