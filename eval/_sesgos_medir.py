"""Mide los sesgos por grupo con el simulador de RESPALDO: regla2 y modelo al P20, por persona. Hecho por Bartolome por
delegación de Gino (DECISIONES #40); Rafael es el dueño de eval/ y puede reemplazarlo.

Uso:  PYTHONPATH=src python eval/_sesgos_medir.py DIR_DATOS [n_procesos=5]
  DIR_DATOS  carpeta de `python -m datos --salida DIR_DATOS` (con generado/movimientos.csv, generador 1.1)

Protocolo (el de eval/frontera.py): el modelo se entrena SOLO con las personas de entrenamiento (datos.particion) y los
meses 1-16 y se calibra con los 17-20; se simula en los meses de prueba 21-24 con eval/_simulador_respaldo.py.
Se simulan las 400 personas (una sola vez) y se escribe:
  eval/resultados/sesgos.csv       las personas de PRUEBA de datos.particion (las que el modelo nunca vio): resultado principal
  eval/resultados/sesgos_400.csv   las 400 personas, solo complementario: el modelo vio a 320 en los meses 1-16
  eval/resultados/sesgos_resultados_por_persona.csv   la entrada de eval.sesgos.sesgos (origen "medido")
Sin calibración del P20 (el simulador no la devuelve). Umbral: el pre-registrado, sin tocar.
"""

from __future__ import annotations

import importlib.util
import sys
import warnings
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

EVAL = Path(__file__).resolve().parent
RESULTADOS = EVAL / "resultados"
METODOS = ("regla2", "modelo")
CUANTIL = 0.20  # el cuantil conservador pre-registrado


def _cargar(nombre: str):
    spec = importlib.util.spec_from_file_location(f"eval_{nombre}", EVAL / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _persona(cid, historia, etiquetas, modelo):
    warnings.simplefilter("ignore")
    from contratos import cargar_config

    cfg = cargar_config()
    sim = _cargar("_simulador_respaldo")
    filas = []
    for metodo in METODOS:
        r = sim.simular_persona(historia, etiquetas, cfg, metodo, CUANTIL, modelo if metodo == "modelo" else None)
        filas.append({"customer_id": cid, "metodo": metodo, "cuantil": CUANTIL, **r, "origen": "medido"})
    return filas


def medir(dir_datos: str, n_procesos: int = 5) -> pd.DataFrame:
    warnings.simplefilter("ignore")
    from contratos import ETIQUETAS_REFERENCIA, cargar_config
    from datos import particion

    cfg = cargar_config()
    fr, sg = _cargar("frontera"), _cargar("sesgos")
    df = pd.read_csv(Path(dir_datos) / "generado" / "movimientos.csv", parse_dates=["fecha_hora"])
    prueba = set(particion(df)["test_personas"])
    print(f"{df.customer_id.nunique()} personas, {len(prueba)} de prueba; entrenando el modelo (solo entrenamiento)...", flush=True)
    modelo = fr._entrenar_modelo(df, cfg)

    tareas = []
    for cid, g in df.groupby("customer_id", sort=True):
        g = g.sort_values("fecha_hora").reset_index(drop=True)
        etiquetas = g.set_index("transaction_id")[list(ETIQUETAS_REFERENCIA)]
        tareas.append(delayed(_persona)(cid, fr._sin_etiquetas(g), etiquetas, modelo))
    filas = [f for lote in Parallel(n_jobs=n_procesos, verbose=5)(tareas) for f in lote]
    res = pd.DataFrame(filas)
    res["es_prueba"] = res["customer_id"].isin(prueba)
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    res.to_csv(RESULTADOS / "sesgos_resultados_por_persona.csv", index=False, lineterminator="\n")

    entrada = res.drop(columns="es_prueba")
    sg.RUTA_SALIDA = RESULTADOS / "sesgos.csv"
    sg.sesgos(df[df["customer_id"].isin(prueba)], entrada[res["es_prueba"]], cfg)
    sg.RUTA_SALIDA = RESULTADOS / "sesgos_400.csv"
    sg.sesgos(df, entrada, cfg)
    return res


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    r = medir(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5)
    print(r.groupby(["es_prueba", "metodo"])[["pagos_descubiertos", "pagos_totales"]].sum(), flush=True)
