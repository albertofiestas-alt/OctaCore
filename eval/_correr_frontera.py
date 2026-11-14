"""Corre frontera + frontera_perturbado + decidir_adopcion sobre un dataset y guarda los resultados con sufijo.

Uso:  PYTHONPATH=src python eval/_correr_frontera.py DIR_DATOS SUFIJO [respaldo|ingesta]
  DIR_DATOS  carpeta de `python -m datos --salida DIR_DATOS` (con generado/movimientos.csv y generado/movimientos_perturbado.csv)
  SUFIJO     p. ej. _v11: escribe eval/resultados/frontera_v11.csv, frontera_perturbado_v11.csv y adopcion_v11.json
  pagos      respaldo (por defecto): pagos con fecha inferidos por eval/_simulador_respaldo.py;
             ingesta: los inferidos por ingesta.inferencia (oficial, tal como está en main)

RESPALDO: usa eval/_simulador_respaldo.py mientras eval/simular.py siga en esqueleto. Mismo pre-registro
(config/preregistro.yaml, sin tocar) y misma regla de adopción (eval/adopcion.py). La prueba y el perturbado corren en
2 procesos en paralelo.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import warnings
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

EVAL = Path(__file__).resolve().parent
RESULTADOS = EVAL / "resultados"


def _cargar(nombre: str):
    spec = importlib.util.spec_from_file_location(f"eval_{nombre}", EVAL / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _pagos_ingesta(cfg):
    """Reemplazo de _simulador_respaldo._pagos_inferidos con los pagos de la ingesta oficial (causal: solo antes del mes)."""
    from ingesta.inferencia import marcar_atipicos, pagos_inferidos

    cache: dict = {}

    def oficiales(hist, mes_inicio):
        clave = (hist["customer_id"].iloc[0], mes_inicio)
        if clave not in cache:
            previo, _ = marcar_atipicos(hist[hist["fecha_hora"] < mes_inicio].copy(), cfg)
            cache[clave] = sorted(
                ({"dia_mes": int(p["dia_mes"]), "monto": float(p["monto"]), "clave": (p["comercio"], p["categoria"])}
                 for p in pagos_inferidos(previo, cfg)),
                key=lambda p: (p["dia_mes"], p["monto"]),
            )
        return cache[clave]

    return oficiales


def _trabajo(modo: str, dir_datos: str, sufijo: str, pagos: str) -> list[dict]:
    warnings.simplefilter("ignore")
    from contratos import cargar_config

    cfg = cargar_config()
    fr, sim = _cargar("frontera"), _cargar("_simulador_respaldo")
    if pagos == "ingesta":
        sim._pagos_inferidos = _pagos_ingesta(cfg)
    fr._cargar_simulador = lambda: sim.simular_persona
    fr.RUTA_SALIDA = RESULTADOS / f"frontera{sufijo}.csv"
    fr.RUTA_SALIDA_PERTURBADO = RESULTADOS / f"frontera_perturbado{sufijo}.csv"
    normal = pd.read_csv(Path(dir_datos) / "generado" / "movimientos.csv", parse_dates=["fecha_hora"])
    if modo == "prueba":
        return fr.frontera(normal, cfg)
    perturbado = pd.read_csv(Path(dir_datos) / "generado" / "movimientos_perturbado.csv", parse_dates=["fecha_hora"])
    return fr.frontera_perturbado(perturbado, cfg, df_entrenamiento=normal)  # el modelo se entrena con el mundo normal


def correr(dir_datos: str, sufijo: str, pagos: str = "respaldo") -> dict:
    if pagos not in ("respaldo", "ingesta"):
        raise ValueError("pagos debe ser 'respaldo' o 'ingesta'")
    from contratos import cargar_config

    prueba, perturbado = Parallel(n_jobs=2)(delayed(_trabajo)(m, dir_datos, sufijo, pagos) for m in ("prueba", "perturbado"))
    adopcion = _cargar("adopcion")
    adopcion.RUTA_SALIDA = RESULTADOS / f"adopcion{sufijo}.json"
    return adopcion.decidir_adopcion(prueba, perturbado, None, cargar_config()["preregistro"])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    veredicto = correr(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "respaldo")
    print(json.dumps(veredicto, ensure_ascii=False), flush=True)
