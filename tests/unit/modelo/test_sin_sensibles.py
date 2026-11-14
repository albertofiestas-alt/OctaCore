"""Anti fuga y variables sensibles (Responsible AI)."""

from __future__ import annotations

import pytest

from contratos import ETIQUETAS_REFERENCIA
from modelo import FEATURES

PROHIBIDAS_EN_NOMBRE = ("edad", "genero", "ubicacion")


def _prohibidas(variables, sensibles):
    """Variables que comparten nombre con una sensible o contienen una palabra prohibida."""
    return [v for v in variables if v in sensibles or any(p in v.lower() for p in PROHIBIDAS_EN_NOMBRE)]


def test_ninguna_etiqueta_entre_las_variables():
    assert not set(FEATURES) & set(ETIQUETAS_REFERENCIA)


def test_ninguna_variable_sensible_entre_las_variables(cfg_modelo):
    assert not set(FEATURES) & set(cfg_modelo["variables_sensibles"])


@pytest.mark.parametrize("palabra", PROHIBIDAS_EN_NOMBRE)
def test_ningun_nombre_contiene_palabra_prohibida(palabra):
    assert not [f for f in FEATURES if palabra in f.lower()]


def test_el_detector_atrapa_una_variable_prohibida(cfg_modelo):
    sensibles = cfg_modelo["variables_sensibles"]
    assert _prohibidas([*FEATURES, "edad"], sensibles) == ["edad"]
    assert _prohibidas([*FEATURES, "ubicacion_cliente"], sensibles) == ["ubicacion_cliente"]
    assert _prohibidas(FEATURES, sensibles) == []
