"""Corre los pares de semillas en paralelo (joblib). Lanzador de Gino; pares.py y resumir son de Bartolome.

Uso:  PYTHONPATH=src python eval/_pares_paralelo.py [n_semillas=20] [n_procesos=8]

Mide cada semilla 1..n con eval.pares._medir_semilla (un proceso por semilla), guarda la medición de cada una en
eval/resultados/pares_mediciones.csv apenas llega (si algo falla no se pierde lo hecho) y al final llama a pares.pares(n)
con las mediciones ya hechas, que escribe eval/resultados/pares.csv (media y IC95 bootstrap de modelo - regla2).
No cambia el protocolo: mismas semillas, mismas métricas, mismo bootstrap; solo reparte el trabajo.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
import warnings
from pathlib import Path

from joblib import Parallel, delayed

EVAL = Path(__file__).resolve().parent
RUTA_MEDICIONES = EVAL / "resultados" / "pares_mediciones.csv"
COLUMNAS = ["semilla", "pct_descubiertos_modelo", "pct_descubiertos_regla2", "gasto_modelo", "gasto_regla2"]


def _cargar_pares(eval_dir: Path):
    spec = importlib.util.spec_from_file_location("eval_pares", eval_dir / "pares.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _medir(semilla: int, eval_dir: Path) -> dict:
    warnings.simplefilter("ignore")  # el aviso del respaldo ya se declara en DECISIONES.md
    return _cargar_pares(eval_dir)._medir_semilla(semilla)


def correr(n_semillas: int = 20, n_procesos: int = 8) -> dict:
    pares = _cargar_pares(EVAL)
    RUTA_MEDICIONES.parent.mkdir(parents=True, exist_ok=True)
    medidas: dict[int, dict] = {}
    with RUTA_MEDICIONES.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        tareas = (delayed(_medir)(s, EVAL) for s in range(1, n_semillas + 1))
        for m in Parallel(n_jobs=n_procesos, return_as="generator_unordered")(tareas):
            medidas[m["semilla"]] = m
            w.writerow({k: m[k] for k in COLUMNAS})
            f.flush()
            print(f"semilla {m['semilla']:>2} lista ({len(medidas)}/{n_semillas}): {m}", flush=True)
    pares._medir_semilla = lambda semilla: medidas[semilla]  # pares() reutiliza lo medido, no vuelve a simular
    return pares.pares(n_semillas)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    p = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    print(correr(n, p), flush=True)
