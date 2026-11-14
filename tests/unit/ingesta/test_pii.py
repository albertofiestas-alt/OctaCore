"""PII: detección, enmascarado, falsos positivos e inmutabilidad."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ingesta.pii import detectar_pii, enmascarar_pii

CFG = {
    "patrones_pii": {
        "tarjeta": r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)",
        "telefono": r"(?<!\d)9\d{8}(?!\d)",
        "dni": r"(?<!\d)\d{8}(?!\d)",
        "correo": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    }
}
FIXTURE = Path(__file__).parent / "fixtures" / "pii_ejemplo.csv"


def _df():
    return pd.read_csv(FIXTURE, dtype=str)


def test_detecta_cada_tipo_en_orden_de_config():
    assert detectar_pii("4111 1111 1111 1111", CFG) == ["tarjeta"]
    assert detectar_pii("987654321", CFG) == ["telefono"]
    assert detectar_pii("Cliente 12345678", CFG) == ["dni"]
    assert detectar_pii("ana@correo.pe", CFG) == ["correo"]
    assert detectar_pii("12345678 y ana@correo.pe", CFG) == ["dni", "correo"]


@pytest.mark.parametrize("valor", [None, 123, 4.5, ["x"], ""])
def test_no_texto_devuelve_vacio(valor):
    assert detectar_pii(valor, CFG) == []


@pytest.mark.parametrize("texto", ["1234567", "123456789", "P0001", "Bodega Sol"])
def test_falsos_positivos_no_se_detectan(texto):
    assert detectar_pii(texto, CFG) == []


def test_enmascara_todos_los_patrones_y_cuenta():
    sal, n = enmascarar_pii(_df(), CFG)
    assert sal.loc[1, "comercio"].startswith("Pago ***")  # el espacio final depende del patrón
    assert sal.loc[2, "comercio"] == "Cliente *** Lima"
    assert sal.loc[3, "comercio"] == "Yape ***"
    assert sal.loc[4, "comercio"] == "***"
    assert sal.loc[5, "comercio"] == "Tarjeta ***"
    assert sal.loc[6, "customer_id"] == "***"
    assert sal.loc[6, "categoria"] == "***"
    assert n == 7


def test_falsos_positivos_intactos():
    original = _df()
    sal, _ = enmascarar_pii(original, CFG)
    assert sal.loc[0, "monto"] == "12345678"
    assert sal.loc[0, "customer_id"] == "P0001"
    assert sal.loc[7, "comercio"] == "Ref 1234567 y 123456789"
    for col in ("monto", "fecha_hora", "transaction_id", "tipo", "moneda"):
        assert sal[col].tolist() == original[col].tolist()


def test_no_modifica_la_entrada():
    original = _df()
    copia = original.copy(deep=True)
    sal, _ = enmascarar_pii(original, CFG)
    pd.testing.assert_frame_equal(original, copia)
    assert sal is not original


def test_columnas_ausentes_y_valores_nulos():
    df = pd.DataFrame({"customer_id": ["P0001", None], "monto": [12345678, 1.0]})
    sal, n = enmascarar_pii(df, CFG)
    assert n == 0
    assert sal["customer_id"].tolist()[0] == "P0001"
    assert sal["monto"].tolist() == [12345678, 1.0]


def test_cuenta_repeticiones_de_un_valor_unico():
    df = pd.DataFrame({"comercio": ["Cliente 12345678"] * 3 + ["Bodega"]})
    sal, n = enmascarar_pii(df, CFG)
    assert n == 3
    assert sal["comercio"].tolist() == ["Cliente ***"] * 3 + ["Bodega"]


CFG_ARREGLO = {
    "patrones_pii": {
        "correo": CFG["patrones_pii"]["correo"],
        "tarjeta": r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)",
        "telefono": CFG["patrones_pii"]["telefono"],
        "dni": CFG["patrones_pii"]["dni"],
    }
}


def test_arreglo_propuesto_correo_primero_y_tarjeta_sin_espacio_final():
    df = pd.DataFrame({"comercio": ["12345678@mail.com", "4111 1111 1111 1111 gracias"]})
    sal, n = enmascarar_pii(df, CFG_ARREGLO)
    assert sal["comercio"].tolist() == ["***", "*** gracias"]
    assert n == 2


def test_defectos_de_config_base_medidos():
    """Documenta los dos defectos de config/base.yaml (de Anderson); si se arreglan, borrar."""
    df = pd.DataFrame({"comercio": ["12345678@mail.com", "4111 1111 1111 1111 gracias"]})
    sal, _ = enmascarar_pii(df, CFG)
    assert sal["comercio"].tolist()[0] != "***"  # el DNI parte el correo
    assert sal["comercio"].tolist()[1] == "***gracias"  # la tarjeta se come el espacio
