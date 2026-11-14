"""Fuzz de cargar: cualquier entrada produce un resultado válido o un ErrorIngesta, nada más."""

from __future__ import annotations

import pandas as pd
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from contratos import cargar_config, validar_historia
from ingesta import ErrorIngesta, cargar

CFG = cargar_config()
COLS = ["customer_id", "transaction_id", "fecha_hora", "monto", "moneda", "tipo", "categoria", "comercio", "saldo"]

celda_libre = st.one_of(
    st.none(),
    st.text(max_size=40),
    st.text(max_size=5000),
    st.sampled_from(["", " ", "nan", "NaN", "inf", "-inf", "1e999", "-1e999", "1e-999", "0", "-0",
                     "2025-02-30", "0000-00-00", "9999-12-31 23:59:59", "PEN", "USD", "ingreso", "gasto",
                     "12345678", "987654321", "a@b.co", "4111 1111 1111 1111", "ñandú", "\x00", "\u202e"]),
)
monto = st.one_of(st.floats(allow_nan=True, allow_infinity=True).map(repr), celda_libre)
fecha = st.one_of(
    st.datetimes(min_value=pd.Timestamp("1990-01-01").to_pydatetime(),
                 max_value=pd.Timestamp("2040-01-01").to_pydatetime()).map(str),
    celda_libre,
)
tipo = st.one_of(st.sampled_from(["ingreso", "gasto"]), celda_libre)
moneda = st.one_of(st.sampled_from(["PEN", "PEN", "USD"]), celda_libre)
texto = st.one_of(st.sampled_from(["alquiler", "servicios", "suscripcion", "deuda", "otros", "Netflix"]), celda_libre)
ident = st.one_of(st.sampled_from(["P0001", "P0002", "T1", "T2", "T3"]), celda_libre)

fila = st.fixed_dictionaries(
    {"customer_id": ident, "transaction_id": ident, "fecha_hora": fecha, "monto": monto, "moneda": moneda,
     "tipo": tipo, "categoria": texto, "comercio": texto, "saldo": celda_libre}
)


@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(st.lists(fila, min_size=0, max_size=25))
def test_fuzz_solo_resultado_valido_o_error_ingesta(filas):
    df = pd.DataFrame(filas, columns=COLS)
    try:
        out, reporte, pagos = cargar(df, CFG)
    except ErrorIngesta as e:
        assert e.mensaje_usuario
        return
    validar_historia(out)
    assert reporte.filas_salida == len(out) <= reporte.filas_entrada
    assert isinstance(pagos, list)


@settings(max_examples=60, deadline=None)
@given(st.binary(max_size=2000))
def test_fuzz_bytes_arbitrarios(datos):
    import io

    try:
        cargar(io.BytesIO(datos), CFG)
    except ErrorIngesta:
        pass
