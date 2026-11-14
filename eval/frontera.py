"""Frontera de seguridad: (% de pagos descubiertos, gasto permitido) por método y cuantil. Dueño: Rafael.

Implementada por Gino (feat/gino-eval-frontera) a pedido del equipo; Rafael sigue siendo el dueño de eval/.

Qué hace: para cada método y cada cuantil de cfg["cuantiles"] (P5, P20, P50, P80) simula a las personas de PRUEBA
(meses 21-24) con eval/simular.py::simular_persona y agrega: pct_descubiertos = pagos descubiertos / pagos totales
(sobre todas las personas) y gasto_permitido = promedio por persona del gasto permitido por día.
Agrega dos referencias, pedidas al simulador con metodo="gasto_cero" y metodo="gasto_fijo" (cuantil=None): si el
simulador no las soporta se avisa con un warning y se omiten (no se inventan).

Pendiente (necesita el simulador real): los factores 0.5, 0.75 y 1.0 de la regla ingenua que pide el plan.

El modelo se entrena SOLO con personas de entrenamiento y meses 1-16, y se calibra con los meses 17-20 de esas mismas
personas (src/modelo/calibracion.py). Nada de los meses 21-24 ni de las personas de prueba entra al entrenamiento.

Salidas: eval/resultados/frontera.csv (prueba) y eval/resultados/frontera_perturbado.csv (generador perturbado), con
columnas metodo, cuantil, pct_descubiertos, gasto_permitido (el formato que lee eval/adopcion.py).
"""

from __future__ import annotations

import csv
import importlib.util
import warnings
from pathlib import Path

import pandas as pd

from contratos import ETIQUETAS_REFERENCIA
from datos import particion
from datos.generador import INICIO
from modelo import entrenar
from modelo.calibracion import calibrar

RESULTADOS = Path(__file__).resolve().parent / "resultados"
RUTA_SALIDA = RESULTADOS / "frontera.csv"
RUTA_SALIDA_PERTURBADO = RESULTADOS / "frontera_perturbado.csv"
COLUMNAS = ["metodo", "cuantil", "pct_descubiertos", "gasto_permitido"]
REFERENCIAS = ("gasto_cero", "gasto_fijo")
_ERRORES_REFERENCIA = (ValueError, KeyError, NotImplementedError)


def _cargar_modulo(nombre: str):
    spec = importlib.util.spec_from_file_location(f"eval_{nombre}", Path(__file__).resolve().parent / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _es_esqueleto(simular) -> bool:
    """El esqueleto de V0 lanza NotImplementedError de inmediato; uno real falla distinto con argumentos vacíos."""
    try:
        simular(None, None, None, "regla2", 0.20)
    except NotImplementedError:
        return True
    except Exception:  # noqa: BLE001 - cualquier otro error indica código real
        return False
    return False


def _cargar_simulador():
    """Import perezoso de eval/simular.py (eval/ no es un paquete).

    Si todavía es un esqueleto usa eval/_simulador_respaldo.py y lo avisa con un warning: los números salen del
    RESPALDO, no del simulador oficial. Para nada: se borra el respaldo cuando exista simular.py.
    """
    oficial = _cargar_modulo("simular").simular_persona
    if not _es_esqueleto(oficial):
        return oficial
    warnings.warn("eval/simular.py sigue en esqueleto: la frontera usa el simulador de RESPALDO "
                  "(eval/_simulador_respaldo.py), no el oficial", UserWarning, stacklevel=2)
    return _cargar_modulo("_simulador_respaldo").simular_persona


def _inicio_mes(n: int) -> pd.Timestamp:
    """Primer día del mes n (mes 1 = mes de datos.generador.INICIO)."""
    return pd.Timestamp(INICIO.year + (n - 1) // 12, (n - 1) % 12 + 1, 1)


def _sin_etiquetas(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in ETIQUETAS_REFERENCIA if c in df.columns])


def _entrenar_modelo(df: pd.DataFrame, cfg):
    """Modelo entrenado con personas de entrenamiento y meses 1-16, calibrado con los meses 17-20 (mismas personas)."""
    part = particion(df)
    ini_val = _inicio_mes(part["meses_val"][0])
    fin_val = _inicio_mes(part["meses_val"][1] + 1)
    sin = _sin_etiquetas(df)
    de_entrenamiento = sin[sin["customer_id"].isin(part["train_personas"])]
    train = de_entrenamiento[de_entrenamiento["fecha_hora"] < ini_val]
    val = de_entrenamiento[de_entrenamiento["fecha_hora"] < fin_val]
    modelo = entrenar(train, cfg, int(cfg["semillas_evaluacion"][0]))
    return calibrar(modelo, val, ini_val)


def _personas_de_prueba(df: pd.DataFrame) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """[(historia_completa sin etiquetas, etiquetas indexadas por transaction_id)] de cada persona de prueba."""
    faltan = [c for c in ETIQUETAS_REFERENCIA if c not in df.columns]
    if faltan:
        raise ValueError(f"la frontera necesita las etiquetas de referencia para medir; faltan {faltan}")
    prueba = set(particion(df)["test_personas"])
    personas = []
    for cid, g in df[df["customer_id"].isin(prueba)].groupby("customer_id", sort=True):
        g = g.sort_values("fecha_hora").reset_index(drop=True)
        etiquetas = g.set_index("transaction_id")[list(ETIQUETAS_REFERENCIA)]
        personas.append((_sin_etiquetas(g), etiquetas))
    if not personas:
        raise ValueError("no hay personas de prueba en los datos")
    return personas


def _agregar(resultados: list[dict]) -> tuple[float, float]:
    """(pct_descubiertos, gasto_permitido): descubiertos / pagos de todas las personas; gasto = promedio por persona."""
    if not resultados:
        raise ValueError("no hay resultados que agregar")
    totales = sum(r["pagos_totales"] for r in resultados)
    descubiertos = sum(r["pagos_descubiertos"] for r in resultados)
    pct = descubiertos / totales if totales else 0.0
    gasto = sum(r["gasto_permitido_dia"] for r in resultados) / len(resultados)
    return float(pct), float(gasto)


def _escribir(ruta: Path, filas: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for fila in filas:
            w.writerow({**fila, "cuantil": "" if fila["cuantil"] is None else fila["cuantil"]})


def _calcular(df, cfg, metodos, ruta: Path, df_modelo=None) -> list[dict]:
    simular = _cargar_simulador()
    personas = _personas_de_prueba(df)
    modelo = _entrenar_modelo(df if df_modelo is None else df_modelo, cfg) if "modelo" in metodos else None

    filas = []
    for metodo in metodos:
        for q in cfg["cuantiles"]:
            usa = modelo if metodo == "modelo" else None
            resultados = [simular(h, e, cfg, metodo, float(q), usa) for h, e in personas]
            pct, gasto = _agregar(resultados)
            filas.append({"metodo": metodo, "cuantil": float(q), "pct_descubiertos": pct, "gasto_permitido": gasto})
    for ref in REFERENCIAS:
        try:
            resultados = [simular(h, e, cfg, ref, None, None) for h, e in personas]
        except _ERRORES_REFERENCIA as exc:
            warnings.warn(f"referencia {ref} omitida: el simulador no la soporta ({exc})", UserWarning, stacklevel=2)
            continue
        pct, gasto = _agregar(resultados)
        filas.append({"metodo": ref, "cuantil": None, "pct_descubiertos": pct, "gasto_permitido": gasto})
    _escribir(ruta, filas)
    return filas


def frontera(df, cfg, metodos=("regla1", "regla2", "modelo")):
    """Cuatro puntos por método (cuantil conservador P5, P20, P50 y P80), más las referencias de gasto cero y gasto fijo.
    Guarda eval/resultados/frontera.csv."""
    return _calcular(df, cfg, metodos, RUTA_SALIDA)


def frontera_perturbado(df, cfg, metodos=("regla1", "regla2", "modelo"), df_entrenamiento=None):
    """Lo mismo con el dataset del generador perturbado. Guarda eval/resultados/frontera_perturbado.csv.

    Robustez: pasa `df_entrenamiento` (el dataset normal) para que el modelo se entrene con el mundo normal y se mida
    en el perturbado; sin él se entrena con `df` (mismo mundo que se mide, no mide robustez)."""
    return _calcular(df, cfg, metodos, RUTA_SALIDA_PERTURBADO, df_entrenamiento)
