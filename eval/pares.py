"""Pares de semillas: diferencia modelo menos regla2 por semilla, con intervalo bootstrap de 95 %. Dueños: Rafael y Gino."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import yaml

RAIZ = Path(__file__).resolve().parents[1]
RUTA_SALIDA = Path(__file__).resolve().parent / "resultados" / "pares.csv"
REMUESTREOS = 2000
NIVEL = 0.95
SEMILLA_BOOTSTRAP = 20261114  # fija: la misma tabla produce el mismo hash
# Columnas de una medición por semilla (en el cuantil conservador del pre-registro).
METRICAS = {"pct_descubiertos": ("pct_descubiertos_modelo", "pct_descubiertos_regla2"),
            "gasto": ("gasto_modelo", "gasto_regla2")}


def _semillas_minimas() -> int:
    prereg = yaml.safe_load((RAIZ / "config" / "preregistro.yaml").read_text(encoding="utf-8"))
    n = prereg.get("semillas_evaluacion")
    if n is None:
        raise ValueError("pre-registro pendiente: semillas_evaluacion es null en config/preregistro.yaml")
    return int(n)


def _medir_semilla(semilla: int) -> dict:
    """Mide una semilla: genera datos con esa semilla, entrena el modelo y simula modelo y regla2 en el cuantil
    conservador. Devuelve {semilla, pct_descubiertos_modelo, pct_descubiertos_regla2, gasto_modelo, gasto_regla2}.
    Gancho completado por Gino: usa eval/frontera.py (personas de prueba, entrenamiento del modelo solo con personas y
    meses de entrenamiento, agregación) y el simulador que haya (oficial o el de RESPALDO, con aviso). Mide solo regla2 y
    modelo, solo en el cuantil conservador del pre-registro (el protocolo no cambia; se omiten las otras 6 combinaciones)."""
    from contratos import cargar_config

    fr = _frontera()
    cfg = cargar_config()
    cuantil = float(cfg["preregistro"]["cuantil_conservador"])
    df = _generar(semilla)
    simular = fr._cargar_simulador()
    personas = fr._personas_de_prueba(df)
    modelo = fr._entrenar_modelo(df, cfg, semilla)
    medicion = {"semilla": semilla}
    for metodo in ("modelo", "regla2"):
        usa = modelo if metodo == "modelo" else None
        pct, gasto = fr._agregar([simular(h, e, cfg, metodo, cuantil, usa) for h, e in personas])
        medicion[f"pct_descubiertos_{metodo}"] = pct
        medicion[f"gasto_{metodo}"] = gasto
    return medicion


def _frontera():
    """eval/frontera.py (eval/ no es un paquete: se carga por ruta)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("eval_frontera", Path(__file__).resolve().parent / "frontera.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _generar(semilla: int):
    """Datos del generador con esa semilla (400 personas, 24 meses, mundo normal)."""
    import pandas as pd

    from datos import generar

    df = generar(semilla=semilla)[0]
    # generar entrega fecha_hora como texto (igual que el CSV); el simulador y el modelo piden datetime
    return df.assign(fecha_hora=pd.to_datetime(df["fecha_hora"]))


def _bootstrap(diferencias: np.ndarray) -> tuple[float, float, float]:
    """Media y percentiles (2.5, 97.5) de la media remuestreando semillas con reposición, REMUESTREOS veces."""
    rng = np.random.default_rng(SEMILLA_BOOTSTRAP)
    idx = rng.integers(0, len(diferencias), size=(REMUESTREOS, len(diferencias)))
    medias = diferencias[idx].mean(axis=1)
    alfa = (1 - NIVEL) / 2
    inf, sup = np.quantile(medias, [alfa, 1 - alfa])
    return float(diferencias.mean()), float(inf), float(sup)


def resumir(mediciones: list[dict]) -> dict:
    """Diferencia modelo - regla2 por semilla y su intervalo bootstrap, por métrica.
    Devuelve {"pct_descubiertos": {media, ic_inf, ic_sup, n}, "gasto": {...}}. Negativo en descubiertos y positivo
    en gasto favorecen al modelo."""
    if not mediciones:
        raise ValueError("sin mediciones: no hay semillas que resumir")
    salida = {}
    for nombre, (col_modelo, col_regla2) in METRICAS.items():
        dif = np.array([float(m[col_modelo]) - float(m[col_regla2]) for m in mediciones])
        media, inf, sup = _bootstrap(dif)
        salida[nombre] = {"media": media, "ic_inf": inf, "ic_sup": sup, "n": len(dif)}
    return salida


def pares(n_semillas: int = 20):
    """Al menos 20 semillas del generador (con menos personas); 2000 remuestreos bootstrap.

    Corre las semillas 1..n_semillas, mide cada una con _medir_semilla y devuelve resumir(...).
    Escribe eval/resultados/pares.csv (metrica, media, ic_inf, ic_sup, n). Lanza ValueError si n_semillas es menor
    que prereg["semillas_evaluacion"]."""
    minimo = _semillas_minimas()
    if n_semillas < minimo:
        raise ValueError(f"semillas insuficientes: {n_semillas} < {minimo} pre-registradas")
    resumen = resumir([_medir_semilla(s) for s in range(1, n_semillas + 1)])
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with RUTA_SALIDA.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metrica", "media", "ic_inf", "ic_sup", "n"])
        for nombre, v in resumen.items():
            w.writerow([nombre, repr(v["media"]), repr(v["ic_inf"]), repr(v["ic_sup"]), v["n"]])
    return resumen
