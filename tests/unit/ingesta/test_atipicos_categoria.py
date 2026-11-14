"""Defecto de los atípicos: la mediana y la MAD se calculaban por (persona, tipo), así que un alquiler de 400 entre
gastos de 20 salía "atípico" y `pagos_inferidos` (que excluye atípicos) no inferia el alquiler ni la deuda.
Parche: config/ingesta.yaml fija atipicos_agrupar = [customer_id, tipo, categoria] (el código ya aceptaba la clave y su
valor por defecto, el del plan, no cambia). Los atípicos reales siguen marcándose."""

from __future__ import annotations

import pandas as pd

from ingesta.inferencia import marcar_atipicos, pagos_inferidos

CFG = {"ingesta": {"mad_k": 5, "tol_monto": 0.10, "tol_dia": 3, "min_ocurrencias": 3, "atipicos_agrupar": ["customer_id", "tipo", "categoria"]}}
CFG_PLAN = {"ingesta": {"mad_k": 5, "tol_monto": 0.10, "tol_dia": 3, "min_ocurrencias": 3}}  # sin la clave: el defecto del plan
MESES = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]


def _mov(filas):
    df = pd.DataFrame(filas, columns=["customer_id", "fecha_hora", "monto", "categoria", "comercio"])
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    df["tipo"] = ["gasto" if m < 0 else "ingreso" for m in df["monto"]]
    return df


def _alquiler_entre_gastos_de_20(extra=()):
    filas = []
    for mes in MESES:
        filas.append(("P0001", f"{mes}-03 09:00", -400.0, "alquiler", "Arrendador"))
        for dia in (5, 10, 15, 20, 25):
            filas.append(("P0001", f"{mes}-{dia:02d} 12:00", -20.0, "alimentacion", "Bodega"))
    return _mov(filas + list(extra))


def test_un_alquiler_mensual_de_400_entre_gastos_de_20_no_es_atipico_y_se_infiere():
    df, _ = marcar_atipicos(_alquiler_entre_gastos_de_20(), CFG)
    assert not df.loc[df["categoria"] == "alquiler", "atipico_detectado"].any()
    pagos = pagos_inferidos(df, CFG)
    assert [(p["comercio"], p["categoria"], p["monto"], p["dia_mes"]) for p in pagos if p["categoria"] == "alquiler"] == [
        ("Arrendador", "alquiler", 400.0, 3)
    ]


def test_una_deuda_mensual_entre_gastos_de_20_tambien_se_infiere():
    filas = [("P0001", f"{mes}-08 10:00", -250.0, "deuda", "Banco") for mes in MESES]
    filas += [("P0001", f"{mes}-{d:02d} 12:00", -20.0, "alimentacion", "Bodega") for mes in MESES for d in (4, 14, 24)]
    pagos = pagos_inferidos(marcar_atipicos(_mov(filas), CFG)[0], CFG)
    assert any(p["categoria"] == "deuda" and p["monto"] == 250.0 for p in pagos)


def test_un_gasto_unico_de_5000_entre_gastos_de_20_sigue_siendo_atipico():
    df, n = marcar_atipicos(
        _alquiler_entre_gastos_de_20([("P0001", "2025-04-12 18:00", -5000.0, "alimentacion", "Restaurante")]), CFG
    )
    assert n == 1 and df.loc[df["monto"] == -5000.0, "atipico_detectado"].item()
    # y el alquiler sigue sin contarse como atípico ni quedando fuera de lo inferido
    assert any(p["categoria"] == "alquiler" for p in pagos_inferidos(df, CFG))


def test_un_atipico_dentro_de_la_misma_categoria_sigue_marcado():
    df, n = marcar_atipicos(
        _alquiler_entre_gastos_de_20([("P0001", "2025-05-03 09:00", -3200.0, "alquiler", "Arrendador")]), CFG
    )
    assert n == 1 and df.loc[df["monto"] == -3200.0, "atipico_detectado"].item()


def test_sin_la_clave_el_defecto_del_plan_no_cambia():
    cfg = CFG_PLAN
    df, _ = marcar_atipicos(_alquiler_entre_gastos_de_20(), cfg)
    assert df.loc[df["categoria"] == "alquiler", "atipico_detectado"].all()  # el defecto del plan, intacto (test_inferencia.py)


def test_la_config_real_de_la_ingesta_agrupa_por_categoria():
    from contratos import cargar_config

    assert list(cargar_config()["ingesta"]["atipicos_agrupar"]) == ["customer_id", "tipo", "categoria"]
