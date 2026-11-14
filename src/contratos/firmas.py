"""Firmas de las funciones públicas de cada módulo (Anexo A).

Son Protocols: documentan la forma exacta de entrada y salida. La prueba de
contrato (tests/contract/test_firmas.py) comprueba que cada módulo, cuando ya
expone su función, use estos mismos nombres de parámetros.

`historia` y `movimientos_limpios` son un pandas.DataFrame con las columnas
COLUMNAS_MOVIMIENTO (más ingreso_recurrente si existe) y SIN etiquetas de
referencia. Ver contratos.historia.validar_historia.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from contratos.modelos import (
    Accion,
    Decision,
    EstadoPersona,
    Metodo,
    PagoInferido,
    Pronostico,
    ReporteCalidad,
)

if TYPE_CHECKING:
    import pandas as pd

    from contratos.config import Config


class Cargar(Protocol):
    """ingesta.cargar"""

    def __call__(
        self, origen: str | Path
    ) -> tuple[pd.DataFrame, ReporteCalidad, list[PagoInferido]]: ...


class Predecir(Protocol):
    """modelo.predecir, reglas.regla1 y reglas.regla2 (misma firma)."""

    def __call__(self, historia: pd.DataFrame, fecha: date) -> Pronostico: ...


class Decidir(Protocol):
    """motor.decidir"""

    def __call__(self, estado: EstadoPersona, pronostico: Pronostico, cfg: Config) -> Decision: ...


class Consultar(Protocol):
    """servicio.consultar"""

    def __call__(self, id: str, fecha: date, metodo: Metodo) -> Decision: ...


class Responder(Protocol):
    """servicio.responder"""

    def __call__(self, propuesta_id: str, accion: Accion) -> None: ...


# Módulo -> función -> nombres de parámetros, en orden. Fuente para la prueba de contrato.
FIRMAS: dict[str, dict[str, tuple[str, ...]]] = {
    "ingesta": {"cargar": ("origen",)},
    "modelo": {"predecir": ("historia", "fecha")},
    "reglas": {"regla1": ("historia", "fecha"), "regla2": ("historia", "fecha")},
    "motor": {"decidir": ("estado", "pronostico", "cfg")},
    "servicio": {"consultar": ("id", "fecha", "metodo"), "responder": ("propuesta_id", "accion")},
}
