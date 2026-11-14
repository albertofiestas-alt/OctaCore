"""Fixtures compartidas (dueño: Anderson). Cualquier prueba puede pedirlas por nombre.

    def test_algo(decision_verde):
        assert decision_verde.numero_hoy >= 0

Los archivos están en tests/fixtures/ con los nombres que usan los planes. También
se pueden leer directo: Decision.model_validate_json(Path("tests/fixtures/decision_verde.json").read_text("utf-8")).
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


def leer_json(nombre: str) -> dict:
    return json.loads((FIXTURES / nombre).read_text(encoding="utf-8"))


def _fixture(clase, archivo: str):
    @pytest.fixture
    def _f():
        return clase.model_validate(leer_json(archivo))

    _f.__doc__ = f"{clase.__name__} de tests/fixtures/{archivo}"
    return _f


@pytest.fixture
def cfg():
    return cargar_config()


# Caso del orden de pagos (sección 5): saldo 100, pago 300 el día 3, ingreso el día 10.
# Resultado esperado del motor: numero_hoy 0 y "faltan S/200" (decision_sin_alcance).
estado_caso_orden_pagos = _fixture(EstadoPersona, "estado_caso_orden_pagos.json")
pronostico_caso_orden_pagos = _fixture(Pronostico, "pronostico_caso_orden_pagos.json")

# Caso típico (P0002): número 20, pagos en verde y una propuesta (decision_verde).
estado_tipico = _fixture(EstadoPersona, "estado_tipico.json")
pronostico_tipico = _fixture(Pronostico, "pronostico_tipico.json")

# Decisiones para maquetar la interfaz (servicio_falso de Jesús).
decision_verde = _fixture(Decision, "decision_verde.json")
decision_rojo = _fixture(Decision, "decision_rojo.json")
decision_confianza_baja = _fixture(Decision, "decision_confianza_baja.json")
decision_sin_alcance = _fixture(Decision, "decision_sin_alcance.json")

reporte_calidad_ejemplo = _fixture(ReporteCalidad, "reporte_calidad_ejemplo.json")
registro = _fixture(Registro, "registro.json")

# Nombres anteriores (guía de arranque de la v5). Siguen funcionando.
estado_orden_pagos = estado_caso_orden_pagos
pronostico_orden_pagos = pronostico_caso_orden_pagos
decision_orden_pagos = decision_sin_alcance
decision_tipica = decision_verde
decision_sin_historia = decision_confianza_baja
reporte_calidad = reporte_calidad_ejemplo


@pytest.fixture
def ruta_movimientos_minimo() -> Path:
    """CSV crudo con el contrato del generador (incluye etiquetas de referencia)."""
    return FIXTURES / "movimientos_minimo.csv"


@pytest.fixture
def historia_minima(ruta_movimientos_minimo) -> pd.DataFrame:
    """Historia SIN etiquetas de referencia, como la entregaría la ingesta (sin limpiar)."""
    df = pd.read_csv(ruta_movimientos_minimo, parse_dates=["fecha_hora"])
    return df[list(COLUMNAS_MOVIMIENTO)].copy()
