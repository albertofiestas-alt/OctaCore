"""Ablaciones del modelo de cuantiles (eval/ablaciones.py): variantes, parche de FEATURES y deltas a mano.

eval/ no es un paquete: los módulos se cargan por ruta. El entrenamiento real usa data/muestra (20 personas).
"""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from contratos import cargar_config
from modelo import FEATURES
from modelo import features as mod_features
from modelo import modelo as mod_modelo

RAIZ = Path(__file__).resolve().parents[3]
MUESTRA = RAIZ / "data" / "muestra" / "movimientos.csv"
HISTORIA = {"ingreso_28d", "ingreso_56d", "dias_desde_ultimo_ingreso", "n_ingresos_28d", "mediana_ingreso_dia_28d"}


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(f"eval_{nombre}", RAIZ / "eval" / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def ab():
    return _cargar("ablaciones")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(MUESTRA, parse_dates=["fecha_hora"])


@pytest.fixture(scope="module")
def cfg():
    return cargar_config()


def test_hay_una_variante_por_variable_mas_sin_historia(ab):
    v = ab.variantes()
    assert [n for n in v if n not in ("sin_historia",)] == list(FEATURES)
    assert all(v[f] == (f,) for f in FEATURES)
    assert set(v["sin_historia"]) == HISTORIA  # deja solo el calendario


def test_el_parche_quita_las_variables_y_restaura_al_salir(ab):
    antes = list(FEATURES)
    with ab._sin_variables(("ingreso_28d", "mes_sin")):
        assert "ingreso_28d" not in mod_modelo.FEATURES and "mes_sin" not in mod_modelo.FEATURES
        assert "ingreso_28d" not in mod_features.FEATURES
        assert len(mod_modelo.FEATURES) == 7
    assert mod_modelo.FEATURES == antes and mod_features.FEATURES == antes


def test_el_parche_restaura_aunque_falle(ab):
    antes = list(FEATURES)
    with pytest.raises(RuntimeError), ab._sin_variables(("dia_mes",)):
        raise RuntimeError("falla dentro")
    assert mod_modelo.FEATURES == antes


def test_quitar_una_variable_desconocida_falla_claro(ab):
    with pytest.raises(ValueError), ab._sin_variables(("edad",)):
        pass


def test_deltas_a_mano(ab):
    base = {"pinball": 10.0, "pct_descubiertos": 0.05, "gasto_permitido": 80.0}
    otra = {"pinball": 11.5, "pct_descubiertos": 0.07, "gasto_permitido": 78.0}
    d = ab._deltas(otra, base)
    assert d["delta_pinball"] == pytest.approx(1.5)  # positivo: sin la variable el modelo empeora, la variable ayuda
    assert d["delta_descubiertos_pp"] == pytest.approx(2.0)  # puntos porcentuales
    assert d["delta_gasto"] == pytest.approx(-2.0)


def test_el_modelo_entrenado_sin_una_variable_no_la_usa(ab, df, cfg):
    fr = _cargar("frontera")
    with ab._sin_variables(("ingreso_56d",)):
        modelo = fr._entrenar_modelo(df, cfg, 1)
        columnas = next(iter(modelo.modelos.values())).feature_name_
    assert "ingreso_56d" not in columnas and len(columnas) == 8
    assert mod_modelo.FEATURES == list(FEATURES)  # y el parche ya se deshizo


def test_las_ventanas_de_regla2_coinciden_con_las_del_modelo(ab, df, cfg):
    # misma muestra y mismo objetivo: sin esto, el pinball de regla2 y el del modelo no serían comparables
    prueba = df[df["customer_id"].isin(ab._personas_de_prueba(df))]
    ventanas = ab._ventanas(prueba, cfg)
    sin_etiquetas = prueba.drop(columns=["es_duplicado", "es_atipico", "pago_con_fecha", "arquetipo"])
    _, Y = mod_modelo._armar_muestras(sin_etiquetas, cfg, desde=ab.INICIO_PRUEBA)
    assert len(ventanas["y14"]) == len(Y[14]) > 0
    assert list(ventanas["y14"]) == pytest.approx(list(Y[14]))


def test_escribe_los_csv_con_las_columnas_pedidas(ab, tmp_path):
    filas = [{"variable": "dia_mes", "delta_pinball": 0.1, "delta_descubiertos_pp": 0.2, "delta_gasto": -0.3, "n_semillas": 1}]
    ruta = tmp_path / "ablaciones.csv"
    ab._escribir(ruta, filas)
    with open(ruta, encoding="utf-8", newline="") as f:
        leido = list(csv.DictReader(f))
    assert list(leido[0]) == ["variable", "delta_pinball", "delta_descubiertos_pp", "delta_gasto", "n_semillas"]
    assert leido[0]["variable"] == "dia_mes" and leido[0]["n_semillas"] == "1"


def test_medir_variante_devuelve_pinball_pct_y_gasto_con_simulador_de_juguete(ab, df, cfg, monkeypatch):
    fr = _cargar("frontera")
    columnas_vistas = []

    def simular(historia, etiquetas, cfg, metodo, cuantil, modelo=None):
        assert metodo == "modelo" and cuantil == 0.2 and modelo is not None
        columnas_vistas.append(len(mod_modelo.FEATURES))  # el parche sigue activo mientras se simula
        return {"pagos_descubiertos": 1, "pagos_totales": 10, "gasto_permitido_dia": 50.0}

    monkeypatch.setattr(ab, "_frontera", lambda: fr)
    monkeypatch.setattr(fr, "_cargar_simulador", lambda: simular)
    m = ab._medir_variante("sin_dia_mes", ("dia_mes",), df, cfg, 1)
    assert m["pct_descubiertos"] == pytest.approx(0.1) and m["gasto_permitido"] == pytest.approx(50.0)
    assert m["pinball"] > 0 and set(columnas_vistas) == {8}
