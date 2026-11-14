"""eval/sesgos.py con casos de juguete calculados a mano (dueño: Rafael). eval/ no es un paquete: se carga por ruta."""

from __future__ import annotations

import importlib.util
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from contratos import cargar_config

RAIZ = Path(__file__).resolve().parents[3]


def _cargar():
    spec = importlib.util.spec_from_file_location("eval_sesgos", RAIZ / "eval" / "sesgos.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s = _cargar()
CFG = cargar_config()


def _persona(cid: str, arquetipo: str, monto_semanal: float, cada: int = 1, arquetipo_final: str | None = None):
    """Un ingreso cada `cada` semanas durante el año 1, y un gasto fijo mensual."""
    filas = []
    for k in range(0, 52, cada):
        dia = date(2025, 1, 3) + timedelta(weeks=k)
        arq = arquetipo_final if (arquetipo_final and dia.month > 6) else arquetipo
        filas.append({"customer_id": cid, "fecha_hora": f"{dia} 12:00:00", "monto": monto_semanal, "tipo": "ingreso",
                      "arquetipo": arq, "es_duplicado": False, "es_atipico": False})
    filas.append({"customer_id": cid, "fecha_hora": "2025-02-01 09:00:00", "monto": -100.0, "tipo": "gasto",
                  "arquetipo": arquetipo, "es_duplicado": False, "es_atipico": False})
    return filas


@pytest.fixture
def df():
    filas = (_persona("P0001", "conductor", 100) + _persona("P0002", "conductor", 200)
             + _persona("P0003", "vendedora", 300) + _persona("P0004", "vendedora", 400, cada=4))
    return pd.DataFrame(filas)


def _res(cid, desc, tot, gasto, metodo="regla2", q=0.2):
    return {"customer_id": cid, "metodo": metodo, "cuantil": q, "pagos_descubiertos": desc,
            "pagos_totales": tot, "gasto_permitido_dia": gasto}


def _fila(t, dim, grupo, metodo="regla2"):
    f = t[(t.dimension == dim) & (t.grupo == grupo) & (t.metodo == metodo)]
    assert len(f) == 1
    return f.iloc[0]


# --------------------------------------------------------------------------- #
# Brecha y alerta a mano
# --------------------------------------------------------------------------- #


def test_brecha_y_alerta_calculadas_a_mano(df):
    # conductor: (1 + 1) / (10 + 10) = 0,10 ; vendedora: (3 + 3) / (10 + 10) = 0,30 -> brecha 0,20 > 0,05 -> alerta
    # gasto: conductor (30 + 40) / 2 = 35 ; vendedora (20 + 20) / 2 = 20 -> brecha 15
    res = [_res("P0001", 1, 10, 30), _res("P0002", 1, 10, 40), _res("P0003", 3, 10, 20), _res("P0004", 3, 10, 20)]
    t = s.tabla_sesgos(s.grupos_por_persona(df), res, umbral=0.05)
    con, ven = _fila(t, "arquetipo", "conductor"), _fila(t, "arquetipo", "vendedora")
    assert (con.pct_descubiertos, ven.pct_descubiertos) == pytest.approx((0.10, 0.30))
    assert (con.gasto_permitido, ven.gasto_permitido) == (35.0, 20.0)
    assert con.n_personas == 2 and ven.n_personas == 2
    assert con.brecha_pct_descubiertos == pytest.approx(0.20)
    assert con.brecha_gasto_permitido == pytest.approx(15.0)
    assert bool(con.alerta) is True
    peor = s.resumen_sesgos(t)
    assert peor.set_index("dimension").loc["arquetipo", "peor_grupo"] == "vendedora"


def test_brecha_bajo_el_umbral_no_alerta(df):
    # 0,10 contra 0,13 -> brecha 0,03 < 0,05
    res = [_res("P0001", 1, 10, 30), _res("P0002", 1, 10, 30), _res("P0003", 13, 100, 30), _res("P0004", 0, 0, 30)]
    t = s.tabla_sesgos(s.grupos_por_persona(df), res, umbral=0.05)
    fila = _fila(t, "arquetipo", "conductor")
    assert fila.brecha_pct_descubiertos == pytest.approx(0.03)
    assert not t[t.dimension == "arquetipo"]["alerta"].any()


def test_grupo_con_n_cero_no_rompe(df):
    res = [_res(c, 1, 10, 30) for c in ("P0001", "P0002", "P0003", "P0004")]
    t = s.tabla_sesgos(s.grupos_por_persona(df), res, umbral=0.05)
    tec = _fila(t, "arquetipo", "tecnico")
    assert tec.n_personas == 0 and np.isnan(tec.pct_descubiertos) and np.isnan(tec.gasto_permitido)
    # sin variación entre grupos con n > 0 la brecha es 0 (el grupo vacío no cuenta)
    assert _fila(t, "arquetipo", "conductor").brecha_pct_descubiertos == 0.0
    # una sola persona sin pagos: % indefinido, no división entre cero
    t2 = s.tabla_sesgos(s.grupos_por_persona(df), [_res("P0001", 0, 0, 30)], umbral=0.05)
    assert np.isnan(_fila(t2, "arquetipo", "conductor").pct_descubiertos)


# --------------------------------------------------------------------------- #
# Grupos
# --------------------------------------------------------------------------- #


def test_terciles_cubren_a_todas_las_personas():
    filas = []
    for i in range(7):
        filas += _persona(f"P{i + 1:04d}", "tecnico", 50 * (i + 1), cada=1 + i % 3)
    g = s.grupos_por_persona(pd.DataFrame(filas))
    assert len(g) == 7
    for col in ("tercil_ingreso", "tercil_volatilidad"):
        assert g[col].isin(s.TERCILES).all()
        assert set(g[col].value_counts()) <= {2, 3}          # 7 personas -> 3 / 2 / 2 (o 2 / 2 / 3)
    assert g.loc["P0007", "tercil_ingreso"] == "alto" and g.loc["P0001", "tercil_ingreso"] == "bajo"


def test_volatilidad_ingreso_ingreso_y_cambio_de_patron(df):
    extra = pd.DataFrame(_persona("P0005", "tecnico", 100, arquetipo_final="comisionista"))
    g = s.grupos_por_persona(pd.concat([df, extra]), meses=(1, 12))   # 2025: 365 días = 52 semanas completas
    # semanal constante -> CV = 0 ; cada 4 semanas -> CV alto
    assert g.loc["P0001", "cv_semanal"] == 0.0
    assert g.loc["P0004", "cv_semanal"] > 1.0
    assert g.loc["P0004", "tercil_volatilidad"] == "alto"
    # 100 por semana durante 52 semanas, sobre 12 meses de definición
    assert g.loc["P0001", "ingreso_mensual"] == pytest.approx(100 * 52 / 12)
    assert g.loc["P0005", "cambio_patron"] == "si" and g.loc["P0001", "cambio_patron"] == "no"
    assert g.loc["P0005", "arquetipo"] == "tecnico"           # arquetipo inicial


def test_duplicados_y_atipicos_no_cuentan_para_el_ingreso(df):
    raro = df.iloc[[0]].assign(monto=99999.0, es_atipico=True)
    dup = df.iloc[[0]].assign(es_duplicado=True)
    g = s.grupos_por_persona(pd.concat([df, raro, dup]))
    assert g.loc["P0001", "ingreso_mensual"] == pytest.approx(100 * 52 / 20)


# --------------------------------------------------------------------------- #
# Entrada, umbral y archivo
# --------------------------------------------------------------------------- #


def test_umbral_sale_del_preregistro_y_se_guarda_el_csv(df, tmp_path, monkeypatch):
    monkeypatch.setattr(s, "RUTA_SALIDA", tmp_path / "sesgos.csv")
    res = [_res("P0001", 1, 10, 30), _res("P0003", 3, 10, 20)]
    t = s.sesgos(df, res, CFG)
    assert (t["umbral_alerta_sesgo"] == CFG["preregistro"]["umbral_alerta_sesgo"]).all()
    leido = pd.read_csv(tmp_path / "sesgos.csv")
    assert len(leido) == len(t) and b"\r\n" not in (tmp_path / "sesgos.csv").read_bytes()
    assert set(s.resumen_sesgos(leido)["dimension"]) == set(s.DIMENSIONES)


def test_preregistro_pendiente_falla_claro(df):
    cfg = CFG.con(preregistro={"umbral_alerta_sesgo": None})
    with pytest.raises(ValueError, match="pre-registro pendiente"):
        s.sesgos(df, [_res("P0001", 1, 10, 30)], cfg)


def test_columnas_faltantes_y_persona_desconocida(df):
    g = s.grupos_por_persona(df)
    with pytest.raises(ValueError, match="pagos_totales"):
        s.tabla_sesgos(g, [{"customer_id": "P0001", "metodo": "regla2", "cuantil": 0.2,
                            "pagos_descubiertos": 1, "gasto_permitido_dia": 3}], 0.05)
    with pytest.raises(ValueError, match="sin movimientos"):
        s.tabla_sesgos(g, [_res("P9999", 1, 10, 30)], 0.05)


def test_referencias_sin_cuantil_y_varios_metodos(df):
    res = [_res("P0001", 1, 10, 30), _res("P0003", 3, 10, 20),
           _res("P0001", 0, 10, 0, metodo="gasto_cero", q=None), _res("P0003", 0, 10, 0, metodo="gasto_cero", q=None)]
    t = s.tabla_sesgos(s.grupos_por_persona(df), res, 0.05)
    assert set(t["metodo"]) == {"regla2", "gasto_cero"}
    assert t.loc[t.metodo == "gasto_cero", "cuantil"].isna().all()
    assert _fila(t, "arquetipo", "conductor", "gasto_cero").brecha_pct_descubiertos == 0.0


def test_calibracion_p20_opcional_entra_en_la_alerta(df):
    res = [dict(_res("P0001", 1, 10, 30), calibracion_p20=0.80), dict(_res("P0003", 1, 10, 30), calibracion_p20=0.60)]
    t = s.tabla_sesgos(s.grupos_por_persona(df), res, 0.05)
    fila = _fila(t, "arquetipo", "conductor")
    assert fila.brecha_calibracion_p20 == pytest.approx(0.20) and bool(fila.alerta)


def test_demo_queda_marcado(tmp_path):
    t = s.demo(ruta=tmp_path / "demo.csv")
    assert (t["origen"] == "[DEMO]").all()
    assert (tmp_path / "demo.csv").exists()
