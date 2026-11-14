"""Capa de datos: generador sintético, arquetipos, escenarios difíciles, perturbado, muestra.

Dueño: Rafael. Salida: data/*.csv con el contrato de datos (sección 6).
Esqueleto V0 (Anexo E): reemplaza el cuerpo, NO la firma. Puedes mover el código a
generador.py / particion.py y reexportarlo aquí con el mismo nombre.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd


def generar(
    n_personas: int = 400,
    meses: int = 24,
    semilla: int | None = None,
    perturbado: bool = False,
    parametros: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Movimientos sintéticos con etiquetas de referencia y su meta (semilla, versión, hash).

    semilla=None usa cfg["semilla_generador"] de config/base.yaml.
    """
    raise NotImplementedError("datos.generar: generador completo a las 12:30 (Rafael)")


def particion(df: pd.DataFrame, semilla: int | None = None) -> dict[str, Any]:
    """Partición por fecha y por personas (meses 1-16 / 17-20 / 21-24; 20 % de personas en prueba)."""
    raise NotImplementedError("datos.particion (Rafael)")


__all__ = ["generar", "particion"]
