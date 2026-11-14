"""Ablaciones del modelo de cuantiles: qué variable aporta y cuál no. Escrito por Gino por delegación; Rafael puede reemplazarlo.

Para cada una de las 9 variables de src/modelo/features.py se entrena el modelo SIN esa variable con el mismo protocolo
que eval/frontera.py (personas de entrenamiento, meses 1-16, calibrado con los meses 17-20, semilla del pre-registro) y
se mide en la PRUEBA (meses 21-24):
  - pinball a 14 días en el P20 (eval/metricas.py), sobre las mismas ventanas que el modelo completo;
  - % de pagos descubiertos y gasto permitido al P20 con el simulador (el de RESPALDO mientras simular.py sea un esqueleto).
Referencias: "completo" (las 9 variables), "sin_historia" (solo el calendario) y "regla2" (sin modelo).
Cada delta es variante MENOS modelo completo: delta_pinball > 0 significa que sin la variable el modelo empeora, o sea que
la variable ayuda; delta_descubiertos_pp en puntos porcentuales; delta_gasto en soles por día.

Uso:  PYTHONPATH=src python eval/ablaciones.py DIR_DATOS [n_procesos=8] [semilla]
  DIR_DATOS  carpeta de `python -m datos --salida DIR_DATOS` (con generado/movimientos.csv)
Escribe eval/resultados/ablaciones.csv (variable, delta_pinball, delta_descubiertos_pp, delta_gasto, n_semillas) y
eval/resultados/ablaciones_absolutos.csv (variante, pinball, pct_descubiertos, gasto_permitido, n_semillas).
"""

from __future__ import annotations

import csv
import importlib.util
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from contratos import ETIQUETAS_REFERENCIA
from datos import particion
from datos.generador import INICIO
from modelo import FEATURES
from modelo import features as mod_features
from modelo import modelo as mod_modelo
from modelo.features import minimo_dias, serie_diaria

EVAL = Path(__file__).resolve().parent
RESULTADOS = EVAL / "resultados"
INICIO_PRUEBA = pd.Timestamp(INICIO.year + 20 // 12, 20 % 12 + 1, 1)  # primer día del mes 21
HISTORIA = ("ingreso_28d", "ingreso_56d", "dias_desde_ultimo_ingreso", "n_ingresos_28d", "mediana_ingreso_dia_28d")
COLUMNAS = ["variable", "delta_pinball", "delta_descubiertos_pp", "delta_gasto", "n_semillas"]
COLUMNAS_ABSOLUTAS = ["variante", "pinball", "pct_descubiertos", "gasto_permitido", "n_semillas"]


def _cargar_modulo(nombre: str):
    spec = importlib.util.spec_from_file_location(f"eval_{nombre}", EVAL / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _frontera():
    return _cargar_modulo("frontera")


def variantes() -> dict[str, tuple[str, ...]]:
    """{nombre: variables que se QUITAN}: una por variable y 'sin_historia' (queda solo el calendario)."""
    salida = {f: (f,) for f in FEATURES}
    salida["sin_historia"] = HISTORIA
    return salida


@contextmanager
def _sin_variables(quitar: tuple[str, ...]):
    """Parche temporal de FEATURES en modelo.modelo y modelo.features (el modelo lo lee al armar muestras y al predecir)."""
    desconocidas = [v for v in quitar if v not in FEATURES]
    if desconocidas:
        raise ValueError(f"variables desconocidas: {desconocidas}")
    originales = (mod_modelo.FEATURES, mod_features.FEATURES)
    reducidas = [f for f in originales[0] if f not in quitar]
    mod_modelo.FEATURES, mod_features.FEATURES = reducidas, reducidas
    try:
        yield
    finally:
        mod_modelo.FEATURES, mod_features.FEATURES = originales


def _personas_de_prueba(df: pd.DataFrame) -> set:
    return set(particion(df)["test_personas"])


def _sin_etiquetas(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in ETIQUETAS_REFERENCIA if c in df.columns])


def _ventanas(prueba: pd.DataFrame, cfg) -> dict:
    """Mismas ventanas que mod_modelo._armar_muestras(..., desde=INICIO_PRUEBA): (persona, día de corte, ingreso a 14 días)."""
    sin = _sin_etiquetas(prueba)
    paso = int(cfg["modelo"]["paso_muestreo_dias"])
    primero, ultimo = minimo_dias(cfg), max(int(h) for h in cfg["horizontes_dias"])
    cids, fechas, y14 = [], [], []
    for cid, g in sin.groupby("customer_id", sort=True):
        inicio, serie = serie_diaria(g)
        for t in range(primero, len(serie) - ultimo + 1, paso):
            fecha = inicio + pd.Timedelta(days=t)
            if fecha < INICIO_PRUEBA:
                continue
            cids.append(cid)
            fechas.append(fecha)
            y14.append(float(serie[t : t + 14].sum()))
    return {"cid": cids, "fecha": fechas, "y14": np.array(y14)}


def _pinball_modelo(modelo, prueba: pd.DataFrame, cfg) -> float:
    """Pinball a 14 días en el cuantil conservador, con cuantiles ordenados y no negativos como en Modelo.predecir."""
    metricas = _cargar_modulo("metricas")
    X, Y = mod_modelo._armar_muestras(_sin_etiquetas(prueba), cfg, desde=INICIO_PRUEBA)
    nombres = list(mod_modelo._nombres(cfg))
    crudo = np.column_stack([np.maximum(0.0, modelo.modelos[(14, n)].predict(X) + modelo.offsets[(14, n)]) for n in nombres])
    q = np.sort(crudo, axis=1)[:, nombres.index(f"p{round(100 * float(cfg['cuantil_conservador']))}")]
    return metricas.pinball(Y[14], q, float(cfg["cuantil_conservador"]))


def _pinball_regla2(prueba: pd.DataFrame, cfg) -> float:
    import reglas  # las de Rafael

    metricas = _cargar_modulo("metricas")
    ventanas = _ventanas(prueba, cfg)
    sin = _sin_etiquetas(prueba)
    por_persona = {cid: g.sort_values("fecha_hora", kind="stable").reset_index(drop=True) for cid, g in sin.groupby("customer_id")}
    atributo = f"p{round(100 * float(cfg['cuantil_conservador']))}"
    q = []
    for cid, fecha in zip(ventanas["cid"], ventanas["fecha"], strict=True):
        historia = por_persona[cid]
        previa = historia.iloc[: int(np.searchsorted(historia["fecha_hora"].to_numpy(), fecha.to_datetime64(), side="left"))]
        q.append(getattr(reglas.regla2(previa, fecha.date(), cfg).por_horizonte[14], atributo))
    return metricas.pinball(ventanas["y14"], np.array(q), float(cfg["cuantil_conservador"]))


def _simular(fr, df, cfg, metodo: str, modelo=None) -> tuple[float, float]:
    simular = fr._cargar_simulador()
    cuantil = float(cfg["preregistro"]["cuantil_conservador"])
    resultados = [simular(h, e, cfg, metodo, cuantil, modelo) for h, e in fr._personas_de_prueba(df)]
    return fr._agregar(resultados)


def _medir_variante(nombre: str, quitar: tuple[str, ...], df: pd.DataFrame, cfg, semilla: int) -> dict:
    """Entrena sin las variables `quitar` y mide pinball, % descubiertos y gasto en la prueba."""
    fr = _frontera()
    prueba = df[df["customer_id"].isin(_personas_de_prueba(df))]
    with _sin_variables(quitar):
        modelo = fr._entrenar_modelo(df, cfg, semilla)
        pinball = _pinball_modelo(modelo, prueba, cfg)
        pct, gasto = _simular(fr, df, cfg, "modelo", modelo)
    return {"variante": nombre, "pinball": pinball, "pct_descubiertos": pct, "gasto_permitido": gasto}


def _medir_regla2(df: pd.DataFrame, cfg) -> dict:
    prueba = df[df["customer_id"].isin(_personas_de_prueba(df))]
    pct, gasto = _simular(_frontera(), df, cfg, "regla2")
    return {"variante": "regla2", "pinball": _pinball_regla2(prueba, cfg), "pct_descubiertos": pct, "gasto_permitido": gasto}


def _deltas(otra: dict, base: dict) -> dict:
    """variante menos modelo completo; los puntos porcentuales salen de multiplicar por 100 la diferencia de fracciones."""
    return {
        "delta_pinball": otra["pinball"] - base["pinball"],
        "delta_descubiertos_pp": 100 * (otra["pct_descubiertos"] - base["pct_descubiertos"]),
        "delta_gasto": otra["gasto_permitido"] - base["gasto_permitido"],
    }


def _escribir(ruta: Path, filas: list[dict], columnas: list[str] = COLUMNAS) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)


def _tarea(nombre: str, quitar: tuple[str, ...], dir_datos: str, semilla: int) -> dict:
    """Un proceso por variante: lee los datos, mide y devuelve la fila absoluta."""
    warnings.simplefilter("ignore")
    from contratos import cargar_config

    cfg = cargar_config()
    df = pd.read_csv(Path(dir_datos) / "generado" / "movimientos.csv", parse_dates=["fecha_hora"])
    if nombre == "regla2":
        return _medir_regla2(df, cfg)
    return _medir_variante(nombre, quitar, df, cfg, semilla)


def ablaciones(dir_datos: str, n_procesos: int = 8, semilla: int | None = None, destino: Path | None = None) -> list[dict]:
    """Corre completo + una variante por variable + sin_historia + regla2 en paralelo y escribe los dos CSV."""
    from contratos import cargar_config

    cfg = cargar_config()
    semilla = int(cfg["semillas_evaluacion"][0] if semilla is None else semilla)
    destino = Path(destino) if destino else RESULTADOS
    tareas = [("completo", ())] + list(variantes().items()) + [("regla2", ())]
    absolutas = Parallel(n_jobs=n_procesos)(delayed(_tarea)(n, q, str(dir_datos), semilla) for n, q in tareas)
    por_nombre = {a["variante"]: a for a in absolutas}
    base = por_nombre["completo"]
    filas = [{"variable": n, **_deltas(por_nombre[n], base), "n_semillas": 1} for n in [*variantes(), "regla2"]]
    _escribir(destino / "ablaciones.csv", filas)
    _escribir(destino / "ablaciones_absolutos.csv", [{**a, "n_semillas": 1} for a in absolutas], COLUMNAS_ABSOLUTAS)
    return filas


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    resultado = ablaciones(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8,
                           int(sys.argv[3]) if len(sys.argv) > 3 else None)
    for fila in resultado:
        print(fila, flush=True)
