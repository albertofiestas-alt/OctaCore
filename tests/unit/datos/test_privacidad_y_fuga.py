"""Anti fuga, PII y variables sensibles en los datos sintéticos (dueño: Rafael)."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd
import pytest

from contratos import COLUMNAS_MOVIMIENTO, ETIQUETAS_REFERENCIA, cargar_config, validar_historia
from contratos.historia import HistoriaInvalida
from datos import generar, separar_etiquetas

N = 40
CFG = cargar_config()
MUESTRA = Path(__file__).resolve().parents[3] / "data" / "muestra" / "movimientos.csv"


@pytest.fixture(scope="module")
def datos():
    return generar(N, 24, semilla=7)


@pytest.fixture(scope="module")
def csv_generado(datos) -> str:
    return datos[0].to_csv(index=False)


def _normalizar(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return sin_tildes.strip().lower()


# --------------------------------------------------------------------------- #
# Anti fuga
# --------------------------------------------------------------------------- #


def test_separar_etiquetas_quita_las_cuatro(datos):
    df, _ = datos
    movs, etiquetas = separar_etiquetas(df)
    assert not set(ETIQUETAS_REFERENCIA) & set(movs.columns)
    assert set(COLUMNAS_MOVIMIENTO) <= set(movs.columns)
    assert list(etiquetas.columns) == list(ETIQUETAS_REFERENCIA)
    assert etiquetas.index.is_unique and len(etiquetas) == len(df)


def test_historia_con_etiquetas_se_rechaza_y_sin_ellas_pasa(datos):
    df, _ = datos
    df = df.assign(fecha_hora=pd.to_datetime(df["fecha_hora"]))
    with pytest.raises(HistoriaInvalida):
        validar_historia(df)
    validar_historia(separar_etiquetas(df)[0])


def test_features_del_modelo_sin_etiquetas():
    import modelo

    features = {_normalizar(f) for f in getattr(modelo, "FEATURES", [])}
    assert not features & set(ETIQUETAS_REFERENCIA)


# --------------------------------------------------------------------------- #
# PII: en TODO el texto del CSV (patrones de config/base.yaml + 8 y 9 dígitos)
# --------------------------------------------------------------------------- #

PATRONES = {
    **{nombre: re.compile(p) for nombre, p in CFG["patrones_pii"].items()},
    "8_digitos": re.compile(r"(?<!\d)\d{8}(?!\d)"),
    "9_digitos": re.compile(r"(?<!\d)\d{9}(?!\d)"),
    "tarjeta_13_19": re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
    "correo": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
}


@pytest.mark.parametrize("nombre", sorted(PATRONES))
def test_sin_pii_en_el_csv_generado(csv_generado, nombre):
    encontrado = PATRONES[nombre].search(csv_generado)
    assert encontrado is None, f"patrón {nombre} encontrado: {encontrado.group()!r}"


@pytest.mark.skipif(not MUESTRA.exists(), reason="sin data/muestra")
@pytest.mark.parametrize("nombre", sorted(PATRONES))
def test_sin_pii_en_la_muestra_publicada(nombre):
    texto = MUESTRA.read_text(encoding="utf-8")
    encontrado = PATRONES[nombre].search(texto)
    assert encontrado is None, f"patrón {nombre} encontrado: {encontrado.group()!r}"


def test_los_patrones_si_detectan_pii():
    """Control positivo: si los patrones no detectan nada, las pruebas anteriores no valen."""
    casos = {
        "8_digitos": "x,12345678,y",
        "9_digitos": "x,987654321,y",
        "tarjeta_13_19": "x,4111 1111 1111 1111,y",
        "correo": "x,ana.ficticia@correo.pe,y",
    }
    for nombre, texto in casos.items():
        assert PATRONES[nombre].search(texto), nombre


# --------------------------------------------------------------------------- #
# Variables sensibles
# --------------------------------------------------------------------------- #

SENSIBLES = {_normalizar(v) for v in CFG["variables_sensibles"]} | {
    "edad", "genero", "sexo", "ubicacion", "distrito", "nombre", "dni", "telefono", "direccion",
}


def test_sin_columnas_sensibles_en_el_generado(datos):
    df, _ = datos
    assert not {_normalizar(c) for c in df.columns} & SENSIBLES


@pytest.mark.skipif(not MUESTRA.exists(), reason="sin data/muestra")
def test_sin_columnas_sensibles_en_la_muestra():
    columnas = pd.read_csv(MUESTRA, nrows=0).columns
    assert not {_normalizar(c) for c in columnas} & SENSIBLES


def test_semilla_falla_claro_si_no_hay_config(monkeypatch):
    import contratos.config as config
    from datos.generador import _semilla_config

    def _rota(*_a, **_k):
        raise FileNotFoundError("base.yaml")

    monkeypatch.setattr(config, "cargar_config", _rota)
    with pytest.raises(RuntimeError, match="semilla_generador"):
        _semilla_config()
