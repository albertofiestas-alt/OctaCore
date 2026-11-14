"""Fixtures compartidas. Cualquier prueba puede pedirlas por nombre.

Ejemplo:
    def test_algo(decision_tipica):
        assert decision_tipica.numero_hoy >= 0
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from contratos import (
    COLUMNAS_MOVIMIENTO,
    Decision,
    EstadoPersona,
    Pronostico,
    Registro,
    ReporteCalidad,
    cargar_config,
)

FIXTURES = Path(__file__).parent / "fixtures"
CONTRATOS = FIXTURES / "contratos"


def leer_json(nombre: str) -> dict:
    return json.loads((CONTRATOS / nombre).read_text(encoding="utf-8"))


@pytest.fixture
def cfg():
    return cargar_config()


# Caso del orden de pagos (sección 5): saldo 100, pago 300 el día 3, ingreso 400 el día 10.
@pytest.fixture
def estado_orden_pagos() -> EstadoPersona:
    return EstadoPersona.model_validate(leer_json("estado_orden_pagos.json"))


@pytest.fixture
def pronostico_orden_pagos() -> Pronostico:
    return Pronostico.model_validate(leer_json("pronostico_orden_pagos.json"))


@pytest.fixture
def decision_orden_pagos() -> Decision:
    return Decision.model_validate(leer_json("decision_orden_pagos.json"))


# Caso típico con propuesta, para maquetas de la interfaz.
@pytest.fixture
def estado_tipico() -> EstadoPersona:
    return EstadoPersona.model_validate(leer_json("estado_tipico.json"))


@pytest.fixture
def pronostico_tipico() -> Pronostico:
    return Pronostico.model_validate(leer_json("pronostico_tipico.json"))


@pytest.fixture
def decision_tipica() -> Decision:
    return Decision.model_validate(leer_json("decision_tipica.json"))


@pytest.fixture
def decision_sin_historia() -> Decision:
    return Decision.model_validate(leer_json("decision_sin_historia.json"))


@pytest.fixture
def reporte_calidad() -> ReporteCalidad:
    return ReporteCalidad.model_validate(leer_json("reporte_calidad.json"))


@pytest.fixture
def registro() -> Registro:
    return Registro.model_validate(leer_json("registro.json"))


@pytest.fixture
def ruta_movimientos_minimo() -> Path:
    """CSV crudo con el contrato del generador (incluye etiquetas de referencia)."""
    return FIXTURES / "movimientos_minimo.csv"


@pytest.fixture
def historia_minima(ruta_movimientos_minimo) -> pd.DataFrame:
    """Historia SIN etiquetas de referencia, como la entregaría la ingesta (sin limpiar)."""
    df = pd.read_csv(ruta_movimientos_minimo, parse_dates=["fecha_hora"])
    return df[list(COLUMNAS_MOVIMIENTO)].copy()
