"""Validación de esquema: sensibles, etiquetas, columnas, tipos, signo y privacidad."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from contratos import ETIQUETAS_REFERENCIA, Movimiento, validar_historia
from ingesta import ErrorIngesta
from ingesta.esquema import (
    descartar_sensibles,
    separar_etiquetas,
    validar_esquema,
    validar_tipos,
)

CFG = {"variables_sensibles": ["edad", "genero", "ubicacion", "distrito", "nombre", "dni", "telefono"]}


def _fila(**kw):
    base = dict(customer_id="P0001", transaction_id="t1", fecha_hora="2025-01-01 10:00:00",
                monto="-10", moneda="PEN", tipo="gasto", categoria="otros", comercio="X", saldo="100")
    base.update(kw)
    return base


def _df(*filas, **extra):
    df = pd.DataFrame(list(filas) or [_fila()])
    for k, v in extra.items():
        df[k] = v
    return df


# ---- sensibles ------------------------------------------------------------ #


def test_descarta_edad_genero_y_distrito_y_las_reporta():
    df = _df(edad="30", Genero="F", distrito="Miraflores")
    limpio, fuera = descartar_sensibles(df, CFG)
    assert set(fuera) == {"edad", "Genero", "distrito"}
    assert not {"edad", "Genero", "distrito"} & set(limpio.columns)


def test_descartar_no_modifica_la_entrada():
    df = _df(edad="30")
    antes = df.copy()
    descartar_sensibles(df, CFG)
    pd.testing.assert_frame_equal(df, antes)


# ---- etiquetas (anti fuga) ------------------------------------------------ #


def test_etiquetas_se_separan_y_no_quedan_en_movimientos():
    df = _df(es_duplicado="False", es_atipico="True", pago_con_fecha="False", arquetipo="conductor")
    mov, etiquetas = separar_etiquetas(df)
    assert not set(ETIQUETAS_REFERENCIA) & set(mov.columns)
    assert set(etiquetas.columns) == set(ETIQUETAS_REFERENCIA)
    assert list(etiquetas.index) == ["t1"]


# ---- esquema -------------------------------------------------------------- #


def test_falta_monto_el_mensaje_lo_nombra():
    with pytest.raises(ErrorIngesta) as e:
        validar_esquema(_df().drop(columns=["monto"]))
    assert "monto" in e.value.mensaje_usuario


def test_columna_extra_se_ignora_y_se_avisa():
    out, extra = validar_esquema(_df(rareza="x"))
    assert extra == ["rareza"] and "rareza" not in out.columns


def test_saldo_opcional_se_agrega_vacio():
    out, _ = validar_esquema(_df().drop(columns=["saldo"]))
    assert out["saldo"].isna().all()


# ---- tipos ---------------------------------------------------------------- #


def test_fila_valida_cumple_el_contrato():
    out, rech, signos = validar_tipos(_df())
    assert rech == {} and signos == 0
    out["atipico_detectado"] = False
    validar_historia(out)
    Movimiento.model_validate({**out.iloc[0].drop("atipico_detectado").to_dict(), "saldo": 100.0})


@pytest.mark.parametrize(
    "campo,valor,motivo",
    [
        ("fecha_hora", "2025-02-30 10:00", "fecha_invalida"),
        ("fecha_hora", "no es fecha", "fecha_invalida"),
        ("monto", "nan", "monto_invalido"),
        ("monto", "inf", "monto_invalido"),
        ("monto", "-1e999", "monto_invalido"),
        ("monto", "abc", "monto_invalido"),
        ("moneda", "USD", "moneda_distinta_de_PEN"),
        ("tipo", "transferencia", "tipo_invalido"),
        ("customer_id", "  ", "identificador_vacio"),
    ],
)
def test_filas_invalidas_se_rechazan_con_motivo(campo, valor, motivo):
    df = _df(_fila(), _fila(transaction_id="t2", **{campo: valor}))
    out, rech, _ = validar_tipos(df)
    assert rech == {motivo: 1} and len(out) == 1


def test_una_fila_con_varias_fallas_cuenta_una_vez():
    out, rech, _ = validar_tipos(_df(_fila(fecha_hora="x", monto="nan", moneda="USD")))
    assert sum(rech.values()) == 1 and out.empty


def test_gasto_positivo_e_ingreso_negativo_se_corrigen_y_se_cuentan():
    df = _df(_fila(monto="25"), _fila(transaction_id="t2", tipo="ingreso", monto="-300"))
    out, rech, signos = validar_tipos(df)
    assert signos == 2 and rech == {}
    assert out.loc[out.tipo == "gasto", "monto"].iloc[0] == -25
    assert out.loc[out.tipo == "ingreso", "monto"].iloc[0] == 300


def test_monto_extremo_finito_se_acepta_y_nada_queda_nan():
    out, rech, _ = validar_tipos(_df(_fila(monto="-1e300")))
    assert rech == {} and math.isfinite(out["monto"].iloc[0])


def test_saldo_invalido_queda_vacio_sin_rechazar_la_fila():
    out, rech, _ = validar_tipos(_df(_fila(saldo="inf")))
    assert rech == {} and out["saldo"].isna().all()


def test_zona_horaria_se_descarta_sin_excepcion():
    out, rech, _ = validar_tipos(_df(_fila(fecha_hora="2025-01-01T10:00:00-05:00")))
    assert rech == {} and out["fecha_hora"].iloc[0] == pd.Timestamp("2025-01-01 10:00")


def test_tildes_y_texto_muy_largo_no_rompen():
    out, rech, _ = validar_tipos(_df(_fila(comercio="Panadería Ñandú", categoria="x" * 5000)))
    assert rech == {} and out["comercio"].iloc[0] == "Panadería Ñandú"


def test_validar_tipos_no_modifica_la_entrada():
    df = _df(_fila(monto="25"))
    antes = df.copy()
    validar_tipos(df)
    pd.testing.assert_frame_equal(df, antes)


def test_entrada_ya_tipada_tambien_funciona():
    df = pd.DataFrame([_fila()])
    df["monto"] = -10.0
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    out, rech, _ = validar_tipos(df)
    assert rech == {} and len(out) == 1


# ---- privacidad ----------------------------------------------------------- #


def test_el_error_de_esquema_no_contiene_valores_de_celdas():
    df = _df(comercio="12345678", monto="987654321").drop(columns=["tipo"])
    with pytest.raises(ErrorIngesta) as e:
        validar_esquema(df)
    texto = e.value.mensaje_usuario + e.value.detalle
    assert "12345678" not in texto and "987654321" not in texto
