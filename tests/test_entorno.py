"""Prueba de humo del entorno: debe pasar en las 7 laptops antes de las 11:00."""

import importlib
import sys

import pytest

PYTHON_ESPERADO = (3, 11)


def test_version_de_python():
    assert sys.version_info[:2] == PYTHON_ESPERADO, (
        f"Usa Python {PYTHON_ESPERADO[0]}.{PYTHON_ESPERADO[1]} (tienes {sys.version.split()[0]}). "
        "Versiones distintas pueden romper el determinismo."
    )


@pytest.mark.parametrize(
    "paquete",
    ["pydantic", "yaml", "pandas", "numpy", "sklearn", "lightgbm", "streamlit", "hypothesis"],
)
def test_dependencias_instaladas(paquete):
    importlib.import_module(paquete)


@pytest.mark.parametrize(
    "modulo",
    ["contratos", "datos", "ingesta", "reglas", "modelo", "motor", "servicio", "app"],
)
def test_modulos_importables(modulo):
    importlib.import_module(modulo)
