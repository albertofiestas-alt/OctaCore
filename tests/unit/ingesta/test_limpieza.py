"""Pruebas de aplicar_defaults y quitar_duplicados."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from contratos import cargar_config
from ingesta import ErrorIngesta, cargar
from ingesta.limpieza import aplicar_defaults, quitar_duplicados

FIXTURE = Path(__file__).parent / "fixtures" / "diez_filas.csv"


def _df(**cols):
    base = {
        "customer_id": ["P1"] * 3,
        "transaction_id": ["a", "b", "c"],
        "fecha_hora": pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
        "monto": [-10.0, -20.0, -30.0],
        "moneda": ["PEN"] * 3,
        "tipo": ["gasto"] * 3,
        "categoria": ["otros"] * 3,
        "comercio": ["X", "Y", "Z"],
        "saldo": [100.0, 80.0, 50.0],
    }
    base.update(cols)
    return pd.DataFrame(base)


def test_defaults_categoria_y_comercio():
    df = _df(
        categoria=["Suscripción", None, "viajes"],
        comercio=[None, "  ", "Tienda"],
    )
    out, f = aplicar_defaults(df, {})
    assert list(out["categoria"]) == ["suscripcion", "otros", "otros"]
    assert list(out["comercio"]) == ["SIN_COMERCIO", "SIN_COMERCIO", "Tienda"]
    assert f["categoria"] == 1 and f["comercio"] == 2
    assert f["categoria_desconocida"] == 1
    assert f["monto"] == 0


def test_defaults_normaliza_mayusculas_y_tildes():
    out, f = aplicar_defaults(_df(categoria=["ALIMENTACIÓN", " Transporte ", "Alquiler"]), {})
    assert list(out["categoria"]) == ["alimentacion", "transporte", "alquiler"]
    assert f["categoria_desconocida"] == 0


def test_defaults_sin_vacios_da_ceros():
    out, f = aplicar_defaults(_df(), {})
    assert f["categoria"] == 0 and f["comercio"] == 0 and f["categoria_desconocida"] == 0
    pd.testing.assert_frame_equal(out, _df())


def test_defaults_no_modifica_la_entrada():
    df = _df(categoria=[None, "Viajes", "otros"], comercio=[None, "A", "B"])
    copia = df.copy(deep=True)
    aplicar_defaults(df, {})
    pd.testing.assert_frame_equal(df, copia)


def test_defaults_sin_columna_lanza_error_sin_valores():
    with pytest.raises(ErrorIngesta) as e:
        aplicar_defaults(_df().drop(columns="comercio"), {})
    assert "comercio" in e.value.detalle


@pytest.mark.parametrize("n", [0, 1, 4])
def test_n_duplicados_inyectados_dan_total_n(n):
    base = _df()
    extra = [base.iloc[[0]].assign(transaction_id=f"d{i}") for i in range(n)]
    df = pd.concat([base, *extra], ignore_index=True)
    out, total, det = quitar_duplicados(df)
    assert total == n and det == {"transaction_id_repetido": 0, "duplicado_exacto": n, "duplicado_sin_comercio": 0}
    assert list(out["transaction_id"]) == ["a", "b", "c"]


def test_transaction_id_repetido_se_cuenta_aparte():
    df = pd.concat([_df(), _df().iloc[[1]].assign(monto=-99.0)], ignore_index=True)  # mismo id, otro monto
    out, total, det = quitar_duplicados(df)
    assert total == 1 and det == {"transaction_id_repetido": 1, "duplicado_exacto": 0, "duplicado_sin_comercio": 0}
    assert out.loc[out["transaction_id"] == "b", "monto"].item() == -20.0  # se conserva el primero


def test_ambos_tipos_juntos():
    base = _df()
    df = pd.concat(
        [base, base.iloc[[0]].assign(transaction_id="z"), base.iloc[[2]].assign(monto=-1.0)], ignore_index=True
    )
    _, total, det = quitar_duplicados(df)
    assert (total, det["transaction_id_repetido"], det["duplicado_exacto"]) == (2, 1, 1)


def test_monto_se_redondea_a_dos_decimales():
    df = pd.concat([_df(), _df().iloc[[0]].assign(transaction_id="z", monto=-10.004)], ignore_index=True)
    assert quitar_duplicados(df)[1] == 1
    df = pd.concat([_df(), _df().iloc[[0]].assign(transaction_id="z", monto=-10.02)], ignore_index=True)
    assert quitar_duplicados(df)[1] == 0


def test_duplicado_exacto_distingue_persona_y_tipo():
    base = _df()
    df = pd.concat(
        [base, base.iloc[[0]].assign(transaction_id="p", customer_id="P2"),
         base.iloc[[0]].assign(transaction_id="q", tipo="ingreso")],
        ignore_index=True,
    )
    assert quitar_duplicados(df)[1] == 0


def test_duplicados_no_modifica_la_entrada():
    df = pd.concat([_df(), _df().iloc[[0]].assign(transaction_id="z")], ignore_index=True)
    copia = df.copy(deep=True)
    quitar_duplicados(df)
    pd.testing.assert_frame_equal(df, copia)


def _par(comercio_original, comercio_copia):
    base = _df().iloc[[0]]
    return pd.concat(
        [base.assign(comercio=comercio_original), base.assign(transaction_id="z", comercio=comercio_copia)],
        ignore_index=True,
    )


def test_sin_comercio_en_la_copia_se_quita():
    df = pd.concat([_df(), _par("Mercado", "SIN_COMERCIO").iloc[[1]]], ignore_index=True)
    df.loc[0, "comercio"] = "Mercado"
    out, total, det = quitar_duplicados(df)
    assert total == 1 and det == {"transaction_id_repetido": 0, "duplicado_exacto": 0, "duplicado_sin_comercio": 1}
    assert list(out["transaction_id"]) == ["a", "b", "c"] and out.loc[0, "comercio"] == "Mercado"


def test_sin_comercio_en_el_original_conserva_la_fila_con_comercio():
    df = pd.concat([_par("SIN_COMERCIO", "Mercado"), _df().iloc[1:]], ignore_index=True)
    out, total, det = quitar_duplicados(df)
    assert total == 1 and det["duplicado_sin_comercio"] == 1
    assert list(out["transaction_id"]) == ["z", "b", "c"] and out.loc[0, "comercio"] == "Mercado"


def test_dos_comercios_reales_con_la_misma_clave_no_se_tocan():
    out, total, det = quitar_duplicados(_par("Mercado", "Bodega"))
    assert total == 0 and len(out) == 2 and det["duplicado_sin_comercio"] == 0


def test_dos_reales_y_un_sin_comercio_no_se_toca_nada():
    base = _df().iloc[[0]]
    df = pd.concat(
        [base.assign(comercio="Mercado"), base.assign(transaction_id="y", comercio="Bodega"),
         base.assign(transaction_id="z", comercio="SIN_COMERCIO")],
        ignore_index=True,
    )
    assert quitar_duplicados(df)[1] == 0


def test_todos_sin_comercio_lo_cubre_el_duplicado_exacto():
    _, total, det = quitar_duplicados(_par("SIN_COMERCIO", "SIN_COMERCIO"))
    assert total == 1 and det["duplicado_exacto"] == 1 and det["duplicado_sin_comercio"] == 0


def test_sin_comercio_solo_se_agrupa_con_misma_persona_fecha_monto_y_tipo():
    base = _df().iloc[[0]].assign(comercio="Mercado")
    otros = [
        base.assign(transaction_id="p", customer_id="P2", comercio="SIN_COMERCIO"),
        base.assign(transaction_id="q", monto=-11.0, comercio="SIN_COMERCIO"),
        base.assign(transaction_id="r", tipo="ingreso", comercio="SIN_COMERCIO"),
    ]
    assert quitar_duplicados(pd.concat([base, *otros], ignore_index=True))[1] == 0


def test_defaults_mas_duplicados_atrapa_el_caso_del_comercio_vacio():
    base = _df().iloc[[0]]
    df = pd.concat([base.assign(comercio="Mercado"), base.assign(transaction_id="z", comercio=None)], ignore_index=True)
    rellenado, _ = aplicar_defaults(df, {})
    assert quitar_duplicados(rellenado)[1] == 1


def test_fixture_diez_filas_de_punta_a_punta():
    df, reporte, _ = cargar(FIXTURE, cargar_config())
    assert reporte.filas_entrada == 10 and reporte.filas_salida == 9
    assert reporte.duplicados_eliminados == 1
    assert reporte.atipicos >= 1
    assert "edad" in reporte.columnas_sensibles_descartadas and "edad" not in df.columns
