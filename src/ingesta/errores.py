"""Errores de la ingesta.

Privacidad: `detalle` solo puede nombrar columnas, números de fila o posiciones de byte;
nunca el valor de una celda (plan de Mathias, tarea 3 de privacidad).
"""

from __future__ import annotations


class ErrorIngesta(Exception):
    """Archivo vacío, ilegible, demasiado grande o sin columnas del contrato."""

    def __init__(self, mensaje_usuario: str, detalle: str = "") -> None:
        super().__init__(mensaje_usuario)
        self.mensaje_usuario = mensaje_usuario
        self.detalle = detalle
