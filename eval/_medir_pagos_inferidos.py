"""Precisión y recall de los pagos inferidos por `ingesta.cargar` contra la etiqueta `pago_con_fecha` (causal).

Protocolo (el mismo que el respaldo de Pedro): para cada mes calendario de los meses 13 a 24 (2026-01 a 2026-12) se
llama a `ingesta.cargar` solo con los movimientos ANTERIORES al mes; los pares (persona, comercio, categoría) inferidos
se comparan con los pares que de verdad tienen un pago con fecha ese mes. Precisión = aciertos / inferidos; recall =
aciertos / reales (suma de todos los meses). La etiqueta solo se usa para medir, nunca entra en `cargar`.

Uso: python eval/_medir_pagos_inferidos.py <movimientos.csv> [n_personas=100]
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd  # noqa: E402

import ingesta  # noqa: E402
from contratos import cargar_config  # noqa: E402

MESES = [pd.Timestamp(2026, m, 1) for m in range(1, 13)]  # meses 13 a 24 del generador


def medir(ruta: str, n_personas: int = 100) -> dict:
    df = pd.read_csv(ruta)
    ids = sorted(df["customer_id"].unique())[:n_personas]
    df = df[df["customer_id"].isin(ids)].copy()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    cfg = cargar_config()
    aciertos = inferidos = reales = 0
    por_categoria: dict[str, list[int]] = {}
    for inicio in MESES:
        fin = inicio + pd.offsets.MonthBegin(1)
        buf = io.BytesIO(df[df["fecha_hora"] < inicio].to_csv(index=False).encode("utf-8"))
        _, _, pagos = ingesta.cargar(buf, cfg)
        inferido = {(p["customer_id"], p["comercio"], p["categoria"]) for p in pagos}
        real_mes = df[df["pago_con_fecha"].astype(bool) & (df["fecha_hora"] >= inicio) & (df["fecha_hora"] < fin)]
        real = set(zip(real_mes["customer_id"], real_mes["comercio"], real_mes["categoria"], strict=True))
        acierto = inferido & real
        aciertos, inferidos, reales = aciertos + len(acierto), inferidos + len(inferido), reales + len(real)
        for par in real:
            c = por_categoria.setdefault(par[2], [0, 0])
            c[1] += 1
            c[0] += par in acierto
    return {
        "personas": len(ids),
        "aciertos": aciertos,
        "inferidos": inferidos,
        "reales": reales,
        "precision": aciertos / inferidos if inferidos else float("nan"),
        "recall": aciertos / reales if reales else float("nan"),
        "recall_por_categoria": {str(k): round(v[0] / v[1], 4) for k, v in sorted(por_categoria.items(), key=lambda kv: str(kv[0]))},
    }


if __name__ == "__main__":
    if not 2 <= len(sys.argv) <= 3:
        sys.exit("uso: python eval/_medir_pagos_inferidos.py <movimientos.csv> [n_personas]")
    r = medir(sys.argv[1], int(sys.argv[2]) if len(sys.argv) == 3 else 100)
    for k, v in r.items():
        print(f"{k}: {v}")
