"""Lectura segura (paso 1 de cargar): vacío, ilegible, tamaño, UTF-8 y errores sin PII."""

from __future__ import annotations

import io

import pandas as pd
import pytest

from ingesta import ErrorIngesta
from ingesta.lectura import leer

CFG = {"ingesta": {"max_mb": 1, "max_filas": 5, "max_columnas": 4}}
PII = "12345678"  # DNI falso: no debe aparecer jamás en un error


def _csv(tmp_path, contenido: bytes, nombre="a.csv"):
    ruta = tmp_path / nombre
    ruta.write_bytes(contenido)
    return ruta


def test_lee_csv_valido_como_texto(tmp_path):
    df = leer(_csv(tmp_path, b"a,b\n1,x\n2,y\n"), CFG)
    assert list(df.columns) == ["a", "b"]
    assert df["a"].tolist() == ["1", "2"]


def test_acepta_bom_y_flujo_binario():
    df = leer(io.BytesIO("﻿a,b\n1,ñ\n".encode("utf-8")), CFG)
    assert list(df.columns) == ["a", "b"] and df["b"][0] == "ñ"


@pytest.mark.parametrize("contenido", [b"", b"   \n", b"a,b\n"])
def test_vacio(tmp_path, contenido):
    with pytest.raises(ErrorIngesta):
        leer(_csv(tmp_path, contenido), CFG)


def test_demasiado_grande(tmp_path):
    with pytest.raises(ErrorIngesta) as e:
        leer(_csv(tmp_path, b"a\n" + b"1\n" * (1024 * 1024)), CFG)
    assert "MB" in e.value.mensaje_usuario


def test_flujo_demasiado_grande():
    with pytest.raises(ErrorIngesta):
        leer(io.BytesIO(b"a\n" + b"1\n" * (1024 * 1024)), CFG)


def test_no_utf8_no_filtra_el_valor():
    with pytest.raises(ErrorIngesta) as e:
        leer(io.BytesIO(f"a\n{PII}\xff\n".encode("latin-1")), CFG)
    assert PII not in e.value.mensaje_usuario + e.value.detalle
    assert "posición" in e.value.detalle


def test_binario_con_nulos():
    with pytest.raises(ErrorIngesta):
        leer(io.BytesIO(b"PK\x03\x04\x00\x00"), CFG)


def test_fila_mal_formada_solo_cita_la_fila():
    with pytest.raises(ErrorIngesta) as e:
        leer(io.BytesIO(f"a,b\n1,2\n{PII},2,3,4\n".encode()), CFG)
    assert PII not in e.value.mensaje_usuario + e.value.detalle
    assert "fila" in e.value.detalle


def test_limites_de_forma():
    with pytest.raises(ErrorIngesta):
        leer(io.BytesIO(b"a\n" + b"1\n" * 6), CFG)
    with pytest.raises(ErrorIngesta):
        leer(io.BytesIO(b"a,b,c,d,e\n1,2,3,4,5\n"), CFG)


def test_encabezados_repetidos_o_vacios():
    with pytest.raises(ErrorIngesta):
        leer(io.BytesIO(b"a,A\n1,2\n"), CFG)
    with pytest.raises(ErrorIngesta):
        leer(io.BytesIO(b"a,\n1,2\n"), CFG)


def test_ruta_inexistente_directorio_y_enlace(tmp_path):
    with pytest.raises(ErrorIngesta):
        leer(tmp_path / "no_existe.csv", CFG)
    with pytest.raises(ErrorIngesta):
        leer(tmp_path, CFG)
    real = _csv(tmp_path, b"a\n1\n")
    enlace = tmp_path / "enlace.csv"
    try:
        enlace.symlink_to(real)
    except (OSError, NotImplementedError):
        # Windows sin modo desarrollador no deja crear enlaces simbólicos; lo anterior ya se probó.
        pytest.skip("el sistema no permite crear enlaces simbólicos")
    with pytest.raises(ErrorIngesta):
        leer(enlace, CFG)


def test_origen_no_soportado():
    with pytest.raises(ErrorIngesta):
        leer(123, CFG)  # type: ignore[arg-type]


def test_dataframe_no_se_modifica():
    entrada = pd.DataFrame({"a": ["1"], "b": ["x"]})
    copia = entrada.copy(deep=True)
    salida = leer(entrada, CFG)
    salida.loc[0, "a"] = "9"
    pd.testing.assert_frame_equal(entrada, copia)


def test_celdas_no_se_interpretan():
    df = leer(io.BytesIO(b"a,b\n=1+1,007\n"), CFG)
    assert df.loc[0].tolist() == ["=1+1", "007"]
