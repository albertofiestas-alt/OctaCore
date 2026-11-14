"""Elegibilidad por semáforo verde sostenido (eval/elegibilidad.py) con series de juguete hechas a mano.

eval/ no es un paquete: el módulo se carga por ruta. Los parámetros de las pruebas son de JUGUETE; los reales los fija
Gino en config/elegibilidad.yaml antes de correr (hoy todo es null y la función falla con "pre-registro pendiente").
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[3]

PREREG = {
    "meses_verde": 6,
    "semanas_ambar_toleradas": 1,
    "historia_minima_dias": 150,
    "pagos_minimos": 3,
    "dias_confianza_baja_toleradas": 0,
    "umbral_brecha": 0.2,
    "reduccion_gasto_incentivo": 0.25,
}
COMBOS = ["1", "1+2", "1+2+4", "1+2+3+4", "1+2+4+6"]


@pytest.fixture(scope="module")
def eleg():
    spec = importlib.util.spec_from_file_location("eval_elegibilidad", RAIZ / "eval" / "elegibilidad.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def persona(cid, arq="A", inicio="2025-01-01", meses=6, semaforo=None, descubierto=None, confianza=None, pagos=None, saltar=()):
    """Serie diaria de `meses` meses calendario completos. Las funciones reciben la fecha (Timestamp)."""
    fin = pd.Timestamp(inicio) + pd.DateOffset(months=meses) - pd.Timedelta(days=1)
    filas = []
    for f in pd.date_range(inicio, fin):
        if f.strftime("%Y-%m-%d") in saltar:
            continue
        filas.append(
            {
                "customer_id": cid,
                "fecha": f.strftime("%Y-%m-%d"),
                "semaforo": semaforo(f) if semaforo else "verde",
                "pago_descubierto": bool(descubierto(f)) if descubierto else False,
                "confianza": confianza(f) if confianza else "alta",
                "pagos_con_fecha_mes": pagos(f) if pagos else 1,
                "arquetipo": arq,
            }
        )
    return pd.DataFrame(filas)


def serie(*personas):
    return pd.concat(personas, ignore_index=True)


def califica(eleg, df, cid, combo, prereg=PREREG):
    return bool(eleg.califican(df, prereg).loc[cid, combo])


def en(*fechas, valor="ambar", otro="verde"):
    """Función de semáforo: `valor` en esas fechas y `otro` el resto."""
    return lambda f: valor if f.strftime("%Y-%m-%d") in fechas else otro


# ---------------------------------------------------------------- casos de una persona
def test_seis_meses_verde_exactos_califican_en_todas_las_combinaciones(eleg):
    df = serie(persona("P1"))
    r = eleg.califican(df, PREREG)
    assert list(r.columns) == COMBOS and r.loc["P1"].all()


def test_cinco_meses_es_historia_corta_y_no_califica(eleg):
    df = serie(persona("P1", meses=5))
    assert not eleg.califican(df, PREREG).loc["P1"].any()


def test_un_dia_faltante_en_un_mes_lo_vuelve_incompleto(eleg):
    df = serie(persona("P1", saltar=("2025-03-10",)))  # el mes 3 queda incompleto: no hay 6 meses completos seguidos
    assert not califica(eleg, df, "P1", "1")


def test_un_ambar_tolerado_solo_con_tolerancia(eleg):
    df = serie(persona("P1", semaforo=en("2025-03-10")))
    assert not califica(eleg, df, "P1", "1")  # criterio 1 estricto: ningún ámbar
    assert califica(eleg, df, "P1", "1+2+4+6")  # con tolerancia de 1 semana ámbar


def test_dos_semanas_ambar_superan_la_tolerancia_de_una(eleg):
    df = serie(persona("P1", semaforo=en("2025-02-03", "2025-03-17")))
    assert not califica(eleg, df, "P1", "1+2+4+6")


def test_dos_dias_ambar_en_la_misma_semana_cuentan_una_sola_semana(eleg):
    df = serie(persona("P1", semaforo=en("2025-02-03", "2025-02-04")))
    assert califica(eleg, df, "P1", "1+2+4+6")


def test_el_ultimo_mes_debe_ir_en_verde_aunque_haya_tolerancia(eleg):
    df = serie(persona("P1", semaforo=en("2025-06-10")))
    assert not califica(eleg, df, "P1", "1+2+4+6")


def test_un_rojo_descalifica_aun_con_tolerancia(eleg):
    df = serie(persona("P1", semaforo=en("2025-02-10", valor="rojo")))
    assert not califica(eleg, df, "P1", "1+2+4+6")


def test_un_pago_descubierto_rompe_el_criterio_2_pero_no_el_1(eleg):
    df = serie(persona("P1", descubierto=lambda f: f.strftime("%Y-%m-%d") == "2025-04-15"))
    assert califica(eleg, df, "P1", "1")
    assert not califica(eleg, df, "P1", "1+2")
    assert not califica(eleg, df, "P1", "1+2+4")


def test_confianza_baja_rompe_solo_las_combinaciones_con_criterio_3(eleg):
    df = serie(persona("P1", confianza=lambda f: "baja" if f.strftime("%Y-%m-%d") == "2025-05-02" else "alta"))
    assert califica(eleg, df, "P1", "1+2+4")
    assert not califica(eleg, df, "P1", "1+2+3+4")
    assert califica(eleg, df, "P1", "1+2+3+4", {**PREREG, "dias_confianza_baja_toleradas": 1})


def test_sin_pagos_todo_el_tiempo_pasa_el_1_pero_no_el_4(eleg):
    df = serie(persona("P1", semaforo=lambda f: "sin_pagos", pagos=lambda f: 0))
    assert califica(eleg, df, "P1", "1") and califica(eleg, df, "P1", "1+2")
    assert not califica(eleg, df, "P1", "1+2+4")


def test_pagos_distintos_se_suman_por_mes_de_la_ventana(eleg):
    # 1 pago por mes en 6 meses = 6 pagos >= 3
    assert califica(eleg, serie(persona("P1")), "P1", "1+2+4")
    # exactamente 3: un pago en cada uno de tres meses y ninguno en los otros tres
    tres = serie(persona("P1", pagos=lambda f: 1 if f.month <= 3 else 0))
    assert califica(eleg, tres, "P1", "1+2+4")
    # 2 pagos en total
    dos = serie(persona("P1", pagos=lambda f: 1 if f.month <= 2 else 0))
    assert not califica(eleg, dos, "P1", "1+2+4")


def test_varios_pagos_en_un_mes_cuentan_todos(eleg):
    uno_y_tres = serie(persona("P1", pagos=lambda f: 3 if f.month == 1 else 0))
    assert califica(eleg, uno_y_tres, "P1", "1+2+4")


def test_los_pagos_de_meses_fuera_de_la_ventana_no_cuentan(eleg):
    # 12 meses: pagos solo en enero a junio; la ventana es julio a diciembre
    df = serie(persona("P1", meses=12, pagos=lambda f: 2 if f.month <= 6 else 0))
    assert not califica(eleg, df, "P1", "1+2+4")


def test_los_dias_con_semaforo_ya_no_deciden_el_criterio_4(eleg):
    # todos los días 'sin_pagos' pero la columna dice que hubo 1 pago por mes: cuenta la columna
    df = serie(persona("P1", semaforo=lambda f: "sin_pagos", pagos=lambda f: 1))
    assert califica(eleg, df, "P1", "1+2+4")


def test_pagos_con_fecha_mes_negativo_o_no_entero_se_rechaza(eleg):
    with pytest.raises(ValueError, match="pagos_con_fecha_mes"):
        eleg.califican(serie(persona("P1", pagos=lambda f: -1)), PREREG)
    with pytest.raises(ValueError, match="pagos_con_fecha_mes"):
        eleg.califican(serie(persona("P1", pagos=lambda f: 1.5)), PREREG)


def test_historia_minima_total_en_dias(eleg):
    df = serie(persona("P1"))
    assert not califica(eleg, df, "P1", "1+2+4", {**PREREG, "historia_minima_dias": 365})


def test_la_ventana_es_la_de_los_ultimos_n_meses_completos(eleg):
    # 12 meses; un rojo en febrero queda FUERA de la ventana de 6 meses (julio a diciembre)
    fuera = serie(persona("P1", meses=12, semaforo=en("2025-02-10", valor="rojo")))
    assert califica(eleg, fuera, "P1", "1+2+4")
    dentro = serie(persona("P1", meses=12, semaforo=en("2025-09-10", valor="rojo")))
    assert not califica(eleg, dentro, "P1", "1")


def test_semaforo_desconocido_se_rechaza(eleg):
    with pytest.raises(ValueError, match="semaforo"):
        eleg.califican(serie(persona("P1", semaforo=lambda f: "azul")), PREREG)


# ---------------------------------------------------------------- por arquetipo y brecha
def _rojo_dia_5(f):
    return "rojo" if f.day == 5 else "verde"


def _poblacion():
    ok = [persona(f"A{i}", "estable") for i in range(10)]
    mal = [persona(f"B{i}", "irregular", semaforo=_rojo_dia_5) for i in range(10)]
    mixto = [persona(f"C{i}", "mixto", semaforo=_rojo_dia_5 if i < 5 else None) for i in range(10)]
    return serie(*ok, *mal, *mixto)


def test_tasa_por_arquetipo_y_brecha_maxima(eleg):
    tasas, brechas = eleg.tasas_por_arquetipo(_poblacion(), PREREG)
    t = tasas[tasas.combinacion == "1+2+4"].set_index("arquetipo").tasa
    assert t["estable"] == 1.0 and t["irregular"] == 0.0 and t["mixto"] == 0.5
    b = brechas.set_index("combinacion").loc["1+2+4"]
    assert b.brecha == 1.0 and bool(b.alerta) is True
    assert tasas.n_personas.min() == 10


def test_sin_brecha_no_hay_alerta(eleg):
    df = serie(*[persona(f"A{i}", "x") for i in range(5)], *[persona(f"B{i}", "y") for i in range(5)])
    _, brechas = eleg.tasas_por_arquetipo(df, PREREG)
    assert (brechas.brecha == 0).all() and not brechas.alerta.any()


def test_el_arquetipo_nunca_influye_en_quien_califica(eleg):
    df = _poblacion()
    barajado = df.copy()
    barajado["arquetipo"] = barajado.arquetipo.map({"estable": "irregular", "irregular": "mixto", "mixto": "estable"})
    pd.testing.assert_frame_equal(eleg.califican(df, PREREG), eleg.califican(barajado, PREREG))


# ---------------------------------------------------------------- prueba de incentivo
def test_incentivo_mide_cuanta_gente_cambia_a_calificar_con_menos_gasto(eleg):
    base = serie(persona("P1", "x", semaforo=_rojo_dia_5), persona("P2", "x"), persona("P3", "y", semaforo=_rojo_dia_5))
    menos = serie(persona("P1", "x"), persona("P2", "x"), persona("P3", "y", semaforo=_rojo_dia_5))
    r = eleg.prueba_incentivo(base, menos, PREREG).query("combinacion == '1+2+4'").set_index("arquetipo")
    assert r.loc["x", "tasa_base"] == 0.5 and r.loc["x", "tasa_menor_gasto"] == 1.0
    assert r.loc["x", "delta"] == 0.5 and r.loc["x", "personas_que_cambian"] == 1
    assert r.loc["y", "delta"] == 0.0
    assert (r.reduccion_gasto == 0.25).all()


def test_incentivo_exige_las_mismas_personas(eleg):
    with pytest.raises(ValueError, match="mismas personas"):
        eleg.prueba_incentivo(serie(persona("P1")), serie(persona("P2")), PREREG)


# ---------------------------------------------------------------- pre-registro
@pytest.mark.parametrize("campo", list(PREREG))
def test_pre_registro_pendiente_si_algun_valor_es_null(eleg, campo):
    with pytest.raises(ValueError, match=f"pre-registro pendiente.*{campo}"):
        eleg.califican(serie(persona("P1")), {**PREREG, campo: None})


# Valores confirmados por Gino (DECISIONES #29). Los que siguen en null son los que aún no fijó.
FIJADOS_POR_GINO = {
    "meses_verde": 6,
    "semanas_ambar_toleradas": 2,  # 1 semana por cada 3 meses, N = 6 meses
    "historia_minima_dias": 182,  # 26 semanas
    "pagos_minimos": 3,  # PAGOS distintos con fecha en los 6 meses (suma de pagos_con_fecha_mes), no días
    "dias_confianza_baja_toleradas": 14,
    "umbral_brecha": 0.20,
    "reduccion_gasto_incentivo": 0.25,
}


def test_el_yaml_real_tiene_los_valores_de_gino_y_ninguno_inventado(eleg):
    cfg = yaml.safe_load((RAIZ / "config" / "elegibilidad.yaml").read_text(encoding="utf-8"))
    assert set(cfg) == set(PREREG)
    fijados = {k: v for k, v in cfg.items() if v is not None}
    assert {k: v for k, v in fijados.items() if k in FIJADOS_POR_GINO} == FIJADOS_POR_GINO
    # cualquier otro valor lo pone Gino y debe quedar declarado en DECISIONES.md


def test_con_un_campo_null_en_el_yaml_real_la_funcion_se_niega_a_correr(eleg):
    cfg = yaml.safe_load((RAIZ / "config" / "elegibilidad.yaml").read_text(encoding="utf-8"))
    if all(v is not None for v in cfg.values()):
        pytest.skip("el pre-registro está completo")
    with pytest.raises(ValueError, match="pre-registro pendiente"):
        eleg.evaluar_elegibilidad(serie(persona("P1")))


def test_faltan_columnas_se_rechaza(eleg):
    with pytest.raises(ValueError, match="columnas"):
        eleg.califican(serie(persona("P1")).drop(columns=["confianza"]), PREREG)


def test_con_el_yaml_real_completo_corre_de_punta_a_punta(eleg):
    r = eleg.evaluar_elegibilidad(serie(persona("P1", "x"), persona("P2", "y")))
    assert r["parametros"]["pagos_minimos"] == 3 and r["parametros"]["dias_confianza_baja_toleradas"] == 14
    assert set(r["tasas"].combinacion) == set(COMBOS) and r["incentivo"] is None


def test_brecha_relativa_razon_de_tasas_y_arquetipos_en_cero(eleg):
    _, brechas = eleg.tasas_por_arquetipo(_poblacion(), PREREG)
    b = brechas.set_index("combinacion").loc["1+2+4"]
    # tasas: estable 1.0, irregular 0.0, mixto 0.5 -> razón = menor / mayor = 0.0 / 1.0
    assert b.razon_tasas == 0.0 and b.n_arquetipos_tasa_cero == 1


def test_razon_de_tasas_es_uno_si_no_hay_brecha_y_es_nan_si_nadie_califica(eleg):
    iguales = serie(*[persona(f"A{i}", "x") for i in range(5)], *[persona(f"B{i}", "y") for i in range(5)])
    _, b = eleg.tasas_por_arquetipo(iguales, PREREG)
    assert (b.razon_tasas == 1.0).all() and (b.n_arquetipos_tasa_cero == 0).all()
    nadie = serie(*[persona(f"A{i}", "x", semaforo=_rojo_dia_5) for i in range(5)], *[persona(f"B{i}", "y", semaforo=_rojo_dia_5) for i in range(5)])
    _, b0 = eleg.tasas_por_arquetipo(nadie, PREREG)
    assert b0.razon_tasas.isna().all() and (b0.n_arquetipos_tasa_cero == 2).all()
    # la métrica relativa es solo informativa: no cambia la alerta (que sigue siendo la brecha absoluta)
    assert not b0.alerta.any()
