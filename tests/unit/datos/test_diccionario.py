"""El diccionario de datos describe cada columna real del CSV (dueño: Rafael)."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from contratos import COLUMNAS_MOVIMIENTO, ETIQUETAS_REFERENCIA
from datos import generar

RAIZ = Path(__file__).resolve().parents[3]
DICCIONARIO = RAIZ / "docs" / "diccionario_datos.md"
MUESTRA = RAIZ / "data" / "muestra" / "movimientos.csv"


def _columnas_documentadas(texto: str) -> set[str]:
    """Nombres en `código` de la PRIMERA celda de cada fila de tabla."""
    nombres = set()
    for linea in texto.splitlines():
        if linea.startswith("|") and not set(linea) <= set("|-: "):
            primera = linea.split("|")[1]
            nombres |= set(re.findall(r"`([^`]+)`", primera))
    return nombres


def _seccion(texto: str, titulo: str) -> str:
    partes = re.split(r"(?m)^## ", texto)
    return next(p for p in partes if p.startswith(titulo))


@pytest.fixture(scope="module")
def texto() -> str:
    return DICCIONARIO.read_text(encoding="utf-8")


def test_cada_columna_del_generador_esta_documentada(texto):
    df, _ = generar(5, 24, semilla=7)
    faltan = set(df.columns) - _columnas_documentadas(texto)
    assert not faltan, f"columnas sin describir en docs/diccionario_datos.md: {sorted(faltan)}"


@pytest.mark.skipif(not MUESTRA.exists(), reason="sin data/muestra")
def test_cada_columna_de_la_muestra_esta_documentada(texto):
    columnas = pd.read_csv(MUESTRA, nrows=0).columns
    faltan = set(columnas) - _columnas_documentadas(texto)
    assert not faltan, f"columnas sin describir en docs/diccionario_datos.md: {sorted(faltan)}"


def test_contrato_y_etiquetas_en_su_seccion(texto):
    contrato = _columnas_documentadas(_seccion(texto, "Columnas del contrato"))
    etiquetas = _columnas_documentadas(_seccion(texto, "Etiquetas de referencia"))
    assert set(COLUMNAS_MOVIMIENTO) <= contrato
    assert set(ETIQUETAS_REFERENCIA) == etiquetas
    assert "SOLO para evaluación" in texto


def test_detecta_una_columna_sin_describir():
    """Control: si el parser no detecta lo que falta, las pruebas anteriores no valen."""
    assert _columnas_documentadas("| Columna | Tipo |\n|---|---|\n| `a` | x |\n") == {"a"}
    assert "b" not in _columnas_documentadas("| `a` | menciona `b` en otra celda |\n")
