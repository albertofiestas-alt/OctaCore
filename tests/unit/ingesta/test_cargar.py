"""cargar de punta a punta: conteos, idempotencia, inmutabilidad, anti fuga y errores sin PII.

"""

from __future__ import annotations

import pandas as pd
import pytest

from contratos import (
    COLUMNAS_MOVIMIENTO,
    ETIQUETAS_REFERENCIA,
    ReporteCalidad,
    cargar_config,
    validar_historia,
)
from ingesta import ErrorIngesta, cargar

PII = "12345678"  # DNI falso: no debe aparecer jamás en un error


@pytest.fixture(scope="module")
def cfg():
    return cargar_config()


def _f(tid, fecha, monto, tipo="gasto", comercio="Mercado", moneda="PEN", categoria="alimentacion", cid="P0001"):
    return {
        "customer_id": cid, "transaction_id": tid, "fecha_hora": fecha, "monto": monto, "moneda": moneda,
        "tipo": tipo, "categoria": categoria, "comercio": comercio, "saldo": "100",
        "edad": "30", "genero": "F", "distrito": "Miraflores",
        "es_duplicado": "False", "es_atipico": "False", "pago_con_fecha": "False", "arquetipo": "conductor",
    }


FILAS = [
    _f("t1", "2025-01-01 10:00:00", "-50"),
    _f("t2", "2025-01-02 10:00:00", "1000", tipo="ingreso", comercio="Sueldo", categoria="otros"),
    _f("t3", "2025-01-01 10:00:00", "-50"),                               # duplicado exacto con otro id
    _f("t1", "2025-01-03 10:00:00", "-70"),                               # transaction_id repetido
    _f("t4", "2025-01-04 10:00:00", "25"),                                # gasto positivo: se corrige
    _f("t5", "2025-01-05 10:00:00", "-5", moneda="USD"),                  # rechazo por moneda
    _f("t6", "2025-02-30 10:00:00", "-5"),                                # rechazo por fecha
    _f("t7", "2025-01-07 10:00:00", "-9", comercio=f"Tienda {PII}"),      # DNI en el comercio
    _f("t8", "2025-01-08 10:00:00", f"-{PII}"),                           # monto igual a un DNI: no se toca
]


def _csv(tmp_path, filas=FILAS, nombre="mov.csv"):
    ruta = tmp_path / nombre
    pd.DataFrame(filas).to_csv(ruta, index=False)
    return ruta


def test_devuelve_tupla_con_tipos_correctos(tmp_path, cfg):
    df, reporte, pagos = cargar(_csv(tmp_path), cfg)
    assert isinstance(df, pd.DataFrame) and isinstance(reporte, ReporteCalidad) and isinstance(pagos, list)


def test_conteos_del_reporte(tmp_path, cfg):
    df, r, _ = cargar(_csv(tmp_path), cfg)
    assert r.filas_entrada == len(FILAS)
    assert r.duplicados_eliminados == 2
    assert r.rechazos == {"fecha_invalida": 1, "moneda_distinta_de_PEN": 1}
    assert set(r.columnas_sensibles_descartadas) == {"edad", "genero", "distrito"}
    assert r.pii_enmascarado >= 1
    assert r.filas_salida == len(df) == len(FILAS) - 2 - 2


def test_pii_enmascarada_y_monto_intacto(tmp_path, cfg):
    df, _, _ = cargar(_csv(tmp_path), cfg)
    assert PII not in " ".join(df["comercio"].astype(str))
    assert (df["monto"] == -float(PII)).sum() == 1


def test_signo_corregido(tmp_path, cfg):
    df, _, _ = cargar(_csv(tmp_path), cfg)
    assert df.loc[df.transaction_id == "t4", "monto"].iloc[0] == -25


def test_anti_fuga_y_columnas(tmp_path, cfg):
    df, _, _ = cargar(_csv(tmp_path), cfg)
    assert not set(ETIQUETAS_REFERENCIA) & set(df.columns)
    assert not {"edad", "genero", "distrito"} & set(df.columns)
    assert list(df.columns)[: len(COLUMNAS_MOVIMIENTO)] == list(COLUMNAS_MOVIMIENTO)
    assert "atipico_detectado" in df.columns and df["atipico_detectado"].dtype == bool
    validar_historia(df)


def test_idempotencia(tmp_path, cfg):
    ruta = _csv(tmp_path)
    d1, r1, p1 = cargar(ruta, cfg)
    d2, r2, p2 = cargar(ruta, cfg)
    pd.testing.assert_frame_equal(d1, d2)
    assert r1 == r2 and p1 == p2


def test_inmutabilidad_de_dataframe_y_archivo(tmp_path, cfg):
    ruta = _csv(tmp_path)
    antes_bytes = ruta.read_bytes()
    df = pd.DataFrame(FILAS)
    copia = df.copy(deep=True)
    cargar(df, cfg)
    cargar(ruta, cfg)
    pd.testing.assert_frame_equal(df, copia)
    assert ruta.read_bytes() == antes_bytes


def test_acepta_dataframe_y_ruta_con_el_mismo_resultado(tmp_path, cfg):
    d1, r1, _ = cargar(_csv(tmp_path), cfg)
    d2, r2, _ = cargar(pd.DataFrame(FILAS), cfg)
    assert r1 == r2 and len(d1) == len(d2)


# ---- errores: solo ErrorIngesta, sin valores de celdas --------------------- #


def test_archivo_vacio(tmp_path, cfg):
    ruta = tmp_path / "v.csv"
    ruta.write_bytes(b"")
    with pytest.raises(ErrorIngesta) as e:
        cargar(ruta, cfg)
    assert e.value.mensaje_usuario


def test_falta_monto_y_el_mensaje_lo_nombra(tmp_path, cfg):
    df = pd.DataFrame(FILAS).drop(columns=["monto"])
    with pytest.raises(ErrorIngesta) as e:
        cargar(df, cfg)
    assert "monto" in e.value.mensaje_usuario


def test_error_no_contiene_el_valor_pii(tmp_path, cfg):
    df = pd.DataFrame(FILAS).drop(columns=["monto"])
    df["comercio"] = PII
    with pytest.raises(ErrorIngesta) as e:
        cargar(df, cfg)
    assert PII not in e.value.mensaje_usuario + e.value.detalle + str(e.value)


def test_fallo_interno_sale_como_error_ingesta_sin_su_mensaje(tmp_path, cfg, monkeypatch):
    from ingesta import esquema

    def roto(df):
        raise ValueError(f"celda {PII}")

    monkeypatch.setattr(esquema, "validar_tipos", roto)
    with pytest.raises(ErrorIngesta) as e:
        cargar(_csv(tmp_path), cfg)
    assert e.value.detalle == "ValueError"
    assert PII not in e.value.mensaje_usuario + e.value.detalle + str(e.value)
    assert e.value.__cause__ is None


def test_archivo_de_otro_formato_se_procesa_sin_tocar_codigo(tmp_path, cfg):
    # Cinco personas nuevas, mismo contrato, otras columnas extra y otro orden de columnas.
    filas = [
        {**_f(f"n{p}-{i}", f"2025-03-{i + 1:02d} 09:00:00", "-10", cid=f"Q{p:04d}"), "nota": "x"}
        for p in range(5) for i in range(4)
    ]
    df = pd.DataFrame(filas)[::-1].reset_index(drop=True)
    out, r, _ = cargar(df.reindex(columns=sorted(df.columns)), cfg)
    assert r.filas_salida == 20 and out["customer_id"].nunique() == 5
