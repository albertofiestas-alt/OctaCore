"""Frontera de seguridad (eval/frontera.py) con un simulador de juguete y valores calculados a mano.

eval/ no es un paquete: el módulo se carga por ruta. Mientras no existan motor.decidir y eval/simular.py de verdad,
la frontera recibe el simulador por import perezoso (frontera._cargar_simulador) y aquí se sustituye por uno de juguete.
Juguete: cada persona de prueba tiene 10 pagos; descubiertos por cuantil {P5: 0, P20: 1, P50: 3, P80: 6};
gasto permitido = 100 * cuantil (+10 si hay modelo). Referencias: gasto_cero (2 de 10, gasto 0), gasto_fijo (2 de 10, gasto 15).
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from contratos import ETIQUETAS_REFERENCIA, cargar_config
from datos import particion
from datos.generador import INICIO

RAIZ = Path(__file__).resolve().parents[3]
MUESTRA = RAIZ / "data" / "muestra" / "movimientos.csv"
COLUMNAS = ["metodo", "cuantil", "pct_descubiertos", "gasto_permitido"]
DESCUBIERTOS = {0.05: 0, 0.2: 1, 0.5: 3, 0.8: 6}


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(f"eval_{nombre}", RAIZ / "eval" / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(MUESTRA, parse_dates=["fecha_hora"])


@pytest.fixture(scope="module")
def cfg():
    return cargar_config()


class Juguete:
    """Simulador de juguete: registra con qué lo llamaron."""

    def __init__(self):
        self.llamadas = []

    def __call__(self, historia, etiquetas, cfg, metodo, cuantil, modelo=None):
        self.llamadas.append({"historia": historia, "etiquetas": etiquetas, "metodo": metodo, "cuantil": cuantil,
                              "modelo": modelo})
        if metodo == "gasto_cero":
            return {"pagos_descubiertos": 2, "pagos_totales": 10, "gasto_permitido_dia": 0.0}
        if metodo == "gasto_fijo":
            return {"pagos_descubiertos": 2, "pagos_totales": 10, "gasto_permitido_dia": 15.0}
        return {"pagos_descubiertos": DESCUBIERTOS[round(cuantil, 2)], "pagos_totales": 10,
                "gasto_permitido_dia": 100 * cuantil + (10 if modelo is not None else 0)}


@pytest.fixture
def fr(tmp_path, monkeypatch):
    mod = _cargar("frontera")
    juguete = Juguete()
    monkeypatch.setattr(mod, "RUTA_SALIDA", tmp_path / "frontera.csv")
    monkeypatch.setattr(mod, "RUTA_SALIDA_PERTURBADO", tmp_path / "frontera_perturbado.csv")
    monkeypatch.setattr(mod, "_cargar_simulador", lambda: juguete)
    monkeypatch.setattr(mod, "_entrenar_modelo", lambda df, cfg: "MODELO")
    mod.juguete = juguete
    return mod


def _leer(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_agregar_pondera_pagos_y_promedia_el_gasto(fr):
    # 4 descubiertos de 40 pagos = 0.1 (no el promedio de 0.1 y 0.1 por persona); gasto = promedio de personas
    pct, gasto = fr._agregar([
        {"pagos_descubiertos": 1, "pagos_totales": 10, "gasto_permitido_dia": 100.0},
        {"pagos_descubiertos": 3, "pagos_totales": 30, "gasto_permitido_dia": 200.0},
    ])
    assert pct == pytest.approx(0.1)
    assert gasto == pytest.approx(150.0)


def test_agregar_pondera_distinto_que_promediar_porcentajes(fr):
    pct, _ = fr._agregar([
        {"pagos_descubiertos": 0, "pagos_totales": 2, "gasto_permitido_dia": 0.0},
        {"pagos_descubiertos": 9, "pagos_totales": 18, "gasto_permitido_dia": 0.0},
    ])
    assert pct == pytest.approx(9 / 20)  # promediar porcentajes daría 0.25


def test_agregar_sin_pagos_da_cero_descubiertos(fr):
    pct, gasto = fr._agregar([{"pagos_descubiertos": 0, "pagos_totales": 0, "gasto_permitido_dia": 40.0}])
    assert (pct, gasto) == (0.0, 40.0)


def test_agregar_sin_personas_falla_claro(fr):
    with pytest.raises(ValueError):
        fr._agregar([])


def test_escribe_csv_con_las_columnas_y_los_puntos_a_mano(fr, df, cfg):
    filas = fr.frontera(df, cfg)
    leidas = _leer(fr.RUTA_SALIDA)
    assert list(leidas[0].keys()) == COLUMNAS
    assert len(filas) == len(leidas) == 3 * 4 + 2  # 3 métodos x 4 cuantiles + gasto cero y gasto fijo
    for metodo in ("regla1", "regla2", "modelo"):
        for q, desc in DESCUBIERTOS.items():
            f = next(x for x in filas if x["metodo"] == metodo and abs(x["cuantil"] - q) < 1e-9)
            assert f["pct_descubiertos"] == pytest.approx(desc / 10)
            assert f["gasto_permitido"] == pytest.approx(100 * q + (10 if metodo == "modelo" else 0))
    cero = next(x for x in filas if x["metodo"] == "gasto_cero")
    fijo = next(x for x in filas if x["metodo"] == "gasto_fijo")
    assert (cero["pct_descubiertos"], cero["gasto_permitido"]) == (0.2, 0.0)
    assert (fijo["pct_descubiertos"], fijo["gasto_permitido"]) == (0.2, 15.0)
    assert cero["cuantil"] is None and fijo["cuantil"] is None


def test_solo_se_simula_a_las_personas_de_prueba(fr, df, cfg):
    fr.frontera(df, cfg)
    vistas = {c["historia"]["customer_id"].iloc[0] for c in fr.juguete.llamadas}
    assert vistas == set(particion(df)["test_personas"])


def test_el_simulador_recibe_historia_sin_etiquetas_y_etiquetas_por_transaction_id(fr, df, cfg):
    fr.frontera(df, cfg, metodos=("regla2",))
    for c in fr.juguete.llamadas:
        assert not set(ETIQUETAS_REFERENCIA) & set(c["historia"].columns)
        assert list(c["etiquetas"].columns) == list(ETIQUETAS_REFERENCIA)
        assert c["etiquetas"].index.name == "transaction_id"
        assert set(c["etiquetas"].index) == set(c["historia"]["transaction_id"])
        assert c["modelo"] is None  # las reglas no reciben modelo


def test_solo_el_metodo_modelo_recibe_el_modelo(fr, df, cfg):
    fr.frontera(df, cfg, metodos=("regla1", "modelo"))
    con_modelo = {c["metodo"] for c in fr.juguete.llamadas if c["modelo"] == "MODELO"}
    assert con_modelo == {"modelo"}


def test_metodos_a_pedido_solo_incluye_esos_mas_las_referencias(fr, df, cfg):
    filas = fr.frontera(df, cfg, metodos=("regla2",))
    assert {f["metodo"] for f in filas} == {"regla2", "gasto_cero", "gasto_fijo"}


def test_no_se_entrena_el_modelo_si_no_se_pide(fr, df, cfg, monkeypatch):
    def prohibido(df, cfg):
        raise AssertionError("no debía entrenar")

    monkeypatch.setattr(fr, "_entrenar_modelo", prohibido)
    fr.frontera(df, cfg, metodos=("regla1", "regla2"))


def test_frontera_perturbado_escribe_en_otro_archivo(fr, df, cfg):
    fr.frontera_perturbado(df, cfg)
    assert fr.RUTA_SALIDA_PERTURBADO.exists() and not fr.RUTA_SALIDA.exists()
    assert list(_leer(fr.RUTA_SALIDA_PERTURBADO)[0].keys()) == COLUMNAS


def test_referencias_no_soportadas_avisan_y_no_rompen(fr, df, cfg, monkeypatch):
    base = fr.juguete

    def sin_referencias(historia, etiquetas, cfg, metodo, cuantil, modelo=None):
        if metodo.startswith("gasto_"):
            raise ValueError(f"metodo desconocido: {metodo}")
        return base(historia, etiquetas, cfg, metodo, cuantil, modelo)

    monkeypatch.setattr(fr, "_cargar_simulador", lambda: sin_referencias)
    with pytest.warns(UserWarning, match="gasto_cero"):
        filas = fr.frontera(df, cfg)
    assert {f["metodo"] for f in filas} == {"regla1", "regla2", "modelo"}


def test_la_regla_de_adopcion_lee_esta_frontera(fr, df, cfg, tmp_path, monkeypatch):
    adopcion = _cargar("adopcion")
    monkeypatch.setattr(adopcion, "RUTA_SALIDA", tmp_path / "adopcion.json")
    prueba = fr.frontera(df, cfg)
    perturbado = fr.frontera_perturbado(df, cfg)
    prereg = cfg["preregistro"]
    veredicto = adopcion.decidir_adopcion(prueba, perturbado, None, prereg)
    assert veredicto["adopta"] is True  # el juguete le da al modelo +10 a igual % de descubiertos (umbral pre-registrado 2)
    assert json.loads((tmp_path / "adopcion.json").read_text(encoding="utf-8"))["adopta"] is True


# --- _entrenar_modelo: solo personas de entrenamiento, sin etiquetas, sin meses de validación ni de prueba ---

def _inicio_mes(n):
    return pd.Timestamp(INICIO.year + (n - 1) // 12, (n - 1) % 12 + 1, 1)


def test_entrena_solo_con_personas_de_entrenamiento_y_meses_1_a_16(df, cfg, monkeypatch):
    mod = _cargar("frontera")
    visto = {}

    def espia_entrenar(movs, cfg, semilla):
        visto["train"] = movs
        return "ENTRENADO"

    def espia_calibrar(modelo, val, desde):
        visto["val"], visto["desde"], visto["modelo"] = val, desde, modelo
        return "CALIBRADO"

    monkeypatch.setattr(mod, "entrenar", espia_entrenar)
    monkeypatch.setattr(mod, "calibrar", espia_calibrar)
    assert mod._entrenar_modelo(df, cfg) == "CALIBRADO"

    train_ids = set(particion(df)["train_personas"])
    for clave in ("train", "val"):
        movs = visto[clave]
        assert set(movs["customer_id"]) <= train_ids, f"{clave} tiene personas de prueba"
        assert not set(ETIQUETAS_REFERENCIA) & set(movs.columns), f"{clave} trae etiquetas"
    assert visto["train"]["fecha_hora"].max() < _inicio_mes(17)  # meses 1-16
    assert visto["val"]["fecha_hora"].max() < _inicio_mes(21)  # hasta el mes 20: nunca el 21 al 24
    assert visto["desde"] == _inicio_mes(17)
    assert visto["modelo"] == "ENTRENADO"


def test_entrenar_modelo_real_con_la_muestra_da_un_modelo_utilizable(df, cfg):
    mod = _cargar("frontera")
    modelo = mod._entrenar_modelo(df, cfg)
    historia = df[df["customer_id"] == df["customer_id"].iloc[0]].drop(columns=list(ETIQUETAS_REFERENCIA))
    p = modelo.predecir(historia, _inicio_mes(22).date())
    assert set(p.por_horizonte) == {3, 7, 14}
