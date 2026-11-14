"""Pasos 7, 8 y 9 de cargar: atípicos, pagos con fecha y suscripciones duplicadas."""

from __future__ import annotations

import pandas as pd

from contratos.modelos import PagoInferido
from ingesta.inferencia import (
    marcar_atipicos,
    pagos_inferidos,
    suscripciones_duplicadas,
)

CFG = {
    "ingesta": {
        "mad_k": 5,
        "tol_monto": 0.10,
        "tol_dia": 3,
        "min_ocurrencias": 3,
        "ventana_suscripcion_dias": 30,
    }
}


def _mov(filas):
    df = pd.DataFrame(
        filas, columns=["customer_id", "fecha_hora", "monto", "categoria", "comercio"]
    )
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    df["tipo"] = ["gasto" if m < 0 else "ingreso" for m in df["monto"]]
    return df


def _alquiler(dias, monto=-420.0, cliente="P0001"):
    meses = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
    return [
        (cliente, f"{meses[i]}-{d:02d} 09:00", monto, "alquiler", "Arrendador")
        for i, d in enumerate(dias)
    ]


# --- atípicos ---------------------------------------------------------------


def test_atipico_ocho_veces_la_mediana_marcado_y_fuera_de_recurrentes():
    filas = _alquiler([3, 3, 3, 3]) + [
        ("P0001", "2025-05-03 09:00", -3360.0, "alquiler", "Arrendador")
    ]
    df, n = marcar_atipicos(_mov(filas), CFG)
    assert n == 1
    assert df.loc[df["monto"] == -3360.0, "atipico_detectado"].item()
    pagos = pagos_inferidos(df, CFG)
    assert (
        len(pagos) == 1 and pagos[0]["ocurrencias"] == 4 and pagos[0]["monto"] == 420.0
    )


def test_atipico_no_modifica_la_entrada_y_agrega_columna_bool():
    entrada = _mov(_alquiler([3, 3, 3]))
    df, n = marcar_atipicos(entrada, CFG)
    assert "atipico_detectado" not in entrada.columns
    assert df["atipico_detectado"].dtype == bool and n == 0


def test_atipico_con_mad_cero_usa_cinco_veces_la_mediana():
    filas = [
        ("P0001", f"2025-01-{d:02d} 10:00", -10.0, "otros", "X") for d in range(1, 8)
    ]
    filas += [
        ("P0001", "2025-01-20 10:00", -49.0, "otros", "X"),
        ("P0001", "2025-01-21 10:00", -51.0, "otros", "X"),
    ]
    df, n = marcar_atipicos(_mov(filas), CFG)
    assert n == 1 and df.loc[df["monto"] == -51.0, "atipico_detectado"].item()


def test_atipico_agrupamiento_configurable():
    chicos = [
        ("P0001", f"2025-01-{d:02d} 10:00", -10.0 - d % 3, "alimentacion", "M")
        for d in range(1, 21)
    ]
    df_mov = _mov(chicos + _alquiler([3, 3, 3]))
    _, n_plan = marcar_atipicos(df_mov, CFG)
    cfg_cat = {
        "ingesta": {
            **CFG["ingesta"],
            "atipicos_agrupar": ["customer_id", "tipo", "categoria"],
        }
    }
    _, n_cat = marcar_atipicos(df_mov, cfg_cat)
    assert n_plan == 3  # el alquiler parece atípico frente a gastos chicos (riesgo 1)
    assert n_cat == 0


def test_atipicos_df_vacio():
    df, n = marcar_atipicos(_mov([]), CFG)
    assert n == 0 and "atipico_detectado" in df.columns


# --- pagos con fecha --------------------------------------------------------


def test_cuatro_meses_de_alquiler_con_ruido_de_un_dia_dan_un_pago():
    filas = _alquiler([5, 6, 4, 5], monto=-420.0)
    filas[1] = (*filas[1][:2], -425.0, *filas[1][3:])
    pagos = pagos_inferidos(_mov(filas), CFG)
    assert len(pagos) == 1
    p = pagos[0]
    assert (p["dia_mes"], p["monto"], p["ocurrencias"]) == (5, 420.0, 4)
    PagoInferido.model_validate(p)


def test_dia_circular_fin_e_inicio_de_mes_son_el_mismo_pago():
    pagos = pagos_inferidos(_mov(_alquiler([30, 1, 31, 1])), CFG)
    assert len(pagos) == 1 and pagos[0]["dia_mes"] in (31, 1)


def test_dia_demasiado_disperso_no_es_pago():
    assert pagos_inferidos(_mov(_alquiler([2, 10, 18, 26])), CFG) == []


def test_pocas_ocurrencias_o_montos_lejanos_no_son_pago():
    assert pagos_inferidos(_mov(_alquiler([5, 5])), CFG) == []
    filas = _alquiler([5, 5, 5, 5])
    filas[0] = (*filas[0][:2], -200.0, *filas[0][3:])
    filas[1] = (*filas[1][:2], -600.0, *filas[1][3:])
    assert pagos_inferidos(_mov(filas), CFG) == []


def test_solo_categorias_de_pago_y_gastos():
    filas = [
        ("P0001", f"2025-0{m}-05 10:00", -30.0, "alimentacion", "M")
        for m in range(1, 5)
    ]
    filas += [
        ("P0001", f"2025-0{m}-05 10:00", 1500.0, "ingreso", "Empleador")
        for m in range(1, 5)
    ]
    assert pagos_inferidos(_mov(filas), CFG) == []


# --- suscripciones duplicadas -----------------------------------------------


def _sus(fechas, monto=-18.0):
    return _mov([("P0005", f, monto, "suscripcion", "MusicaYa") for f in fechas])


def test_dos_cobros_iguales_en_pocos_dias_dan_aviso():
    avisos = suscripciones_duplicadas(
        _sus(["2025-03-10 12:00", "2025-03-13 08:00"]), CFG
    )
    assert avisos == [
        {
            "customer_id": "P0005",
            "comercio": "MusicaYa",
            "monto": 18.0,
            "fecha_1": "2025-03-10T12:00:00",
            "fecha_2": "2025-03-13T08:00:00",
        }
    ]


def test_montos_distintos_o_lejanos_no_avisan_y_no_elimina():
    df = _sus(["2025-03-10 12:00", "2025-05-13 08:00"])
    assert suscripciones_duplicadas(df, CFG) == []
    df2 = _mov(
        [
            ("P0005", "2025-03-10", -18.0, "suscripcion", "A"),
            ("P0005", "2025-03-11", -25.0, "suscripcion", "A"),
        ]
    )
    assert suscripciones_duplicadas(df2, CFG) == []
    assert len(df2) == 2


def test_ventana_de_30_dias_avisa_suscripcion_mensual_normal_en_febrero():
    # Documenta el riesgo 2: 15-feb -> 15-mar son 28 días y cae dentro de la ventana.
    avisos = suscripciones_duplicadas(
        _sus(["2025-01-15", "2025-02-15", "2025-03-15"]), CFG
    )
    assert [a["fecha_1"][:10] for a in avisos] == ["2025-02-15"]
