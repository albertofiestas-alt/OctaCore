"""Reporte de calidad del dataset: aplica `ingesta.cargar` al dataset completo y escribe eval/resultados/calidad_datos.json.

Lo lee la pantalla Evaluación (src/app/pages/5_Evaluacion.py). Solo CONTEOS: ningún identificador de persona, comercio
ni monto de una persona. Hecho por delegación de Gino; el dueño es Mathias y puede reemplazarlo (DECISIONES.md #38).

Uso: python eval/_calidad_datos.py [movimientos.csv] [n_personas_medicion=100]
     (por defecto data/generado/movimientos.csv; si no existe, la muestra data/muestra/movimientos.csv)
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd  # noqa: E402

import ingesta  # noqa: E402
from contratos import CATEGORIAS, cargar_config  # noqa: E402
from ingesta.limpieza import _normalizar  # noqa: E402

COMPLETO = RAIZ / "data" / "generado" / "movimientos.csv"
MUESTRA = RAIZ / "data" / "muestra" / "movimientos.csv"
SALIDA = RAIZ / "eval" / "resultados" / "calidad_datos.json"
MAX_MB_INTERNO = 500
# Medición de pagos inferidos tras el parche de atípicos y ANTES del PR #4 de Mathias (DECISIONES.md #31; 100 personas).
ANTES_PR4 = {"precision": 0.9784087548062703, "recall": 0.9621873182082606}


def _medir_pagos(ruta: Path, n_personas: int) -> dict:
    spec = importlib.util.spec_from_file_location("_medir_pagos_inferidos", RAIZ / "eval" / "_medir_pagos_inferidos.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    m = mod.medir(str(ruta), n_personas)
    return {
        "protocolo": "ingesta.cargar causal mes a mes (meses 13 a 24), pares (persona, comercio, categoria) contra pago_con_fecha",
        "personas": m["personas"],
        "precision": round(m["precision"], 4),
        "recall": round(m["recall"], 4),
        "recall_por_categoria": m["recall_por_categoria"],
        "antes_del_pr4": {k: round(v, 4) for k, v in ANTES_PR4.items()},
        "cambio_tras_el_pr4": {k: round(m[k] - v, 4) for k, v in ANTES_PR4.items()},
    }


def _desconocidas_por_valor(crudo: pd.DataFrame) -> dict[str, int]:
    """Categorías de la entrada que no están en CATEGORIAS (y pasan a "otros"), contadas por valor. Son nombres de
    categoría, no datos de personas."""
    normalizadas = crudo["categoria"].dropna().astype(str).map(_normalizar)
    desconocidas = normalizadas[~normalizadas.isin(CATEGORIAS)]
    return {str(k): int(v) for k, v in desconocidas.value_counts().items()}


def _dobles_sembrados(ruta: Path) -> int | None:
    """Cobros dobles que el generador sembró a propósito (solo el conteo; None si no hay meta.json)."""
    meta = ruta.parent / "meta.json"
    if not meta.exists():
        return None
    return len(json.loads(meta.read_text(encoding="utf-8")).get("suscripciones_duplicadas", []))


def _version_generador(ruta: Path) -> dict:
    meta = ruta.parent / "meta.json"
    if not meta.exists():
        return {}
    m = json.loads(meta.read_text(encoding="utf-8"))
    return {"generador_version": m.get("version_generador"), "generador_hash": m.get("hash")}


def calidad(ruta: str | Path, n_personas_medicion: int = 100) -> dict:
    """Reporte de calidad (solo conteos). Con n_personas_medicion = 0 no mide precisión y recall de los pagos inferidos."""
    ruta = Path(ruta)
    crudo = pd.read_csv(ruta)
    cfg = cargar_config()
    # El dataset completo pesa más que max_mb de config/ingesta.yaml (50, pensado para un archivo subido): para esta
    # medición interna se sube el límite en una copia de la configuración; config/ingesta.yaml no se toca.
    cfg = cfg.con(ingesta={**cfg["ingesta"], "max_mb": max(cfg["ingesta"]["max_mb"], MAX_MB_INTERNO)})
    movimientos, reporte, pagos = ingesta.cargar(ruta, cfg)
    f = reporte.faltantes
    vacias, por_comercio, desconocidas = f.get("categoria", 0), f.get("categoria_imputada_por_comercio", 0), f.get("categoria_desconocida", 0)
    por_categoria: dict[str, int] = {}
    for p in pagos:
        por_categoria[p["categoria"]] = por_categoria.get(p["categoria"], 0) + 1
    try:
        fuente = str(ruta.resolve().relative_to(RAIZ))
    except ValueError:
        fuente = ruta.name
    return {
        "fuente": fuente.replace("\\", "/"),
        **_version_generador(ruta),
        "personas": int(movimientos["customer_id"].nunique()),
        "filas_entrada": reporte.filas_entrada,
        "filas_salida": reporte.filas_salida,
        "filas_rechazadas": int(sum(reporte.rechazos.values())),
        "rechazos": dict(reporte.rechazos),
        "duplicados_eliminados": reporte.duplicados_eliminados,
        "duplicados_en_entrada": {
            "transaction_id_repetido": int(crudo["transaction_id"].duplicated().sum()),
            "filas_identicas": int(crudo.duplicated().sum()),
        },
        "atipicos": reporte.atipicos,
        "faltantes": {k: int(v) for k, v in f.items()},
        "categorias_imputadas": {
            "categoria_vacia": int(vacias),
            "categoria_imputada_por_comercio": int(por_comercio),
            "categoria_por_defecto": int(vacias - por_comercio + desconocidas),
            "categoria_desconocida": int(desconocidas),
            "desconocidas_por_valor": _desconocidas_por_valor(crudo),
        },
        "pii_enmascarado": reporte.pii_enmascarado,
        "columnas_sensibles_descartadas": list(reporte.columnas_sensibles_descartadas),
        # sin customer_id ni comercio: solo el monto y los días entre los dos cobros
        "suscripciones_duplicadas": [
            {
                "monto": a["monto"],
                "dias_entre_cobros": (pd.Timestamp(a["fecha_2"]).normalize() - pd.Timestamp(a["fecha_1"]).normalize()).days,
            }
            for a in reporte.suscripciones_duplicadas
        ],
        "suscripciones_duplicadas_contexto": {
            "avisos": len(reporte.suscripciones_duplicadas),
            # un cobro mensual normal separa 28 a 30 días (febrero incluido): esos avisos no son cobros dobles
            "avisos_a_28_o_30_dias": sum(
                28 <= (pd.Timestamp(a["fecha_2"]).normalize() - pd.Timestamp(a["fecha_1"]).normalize()).days <= 30
                for a in reporte.suscripciones_duplicadas
            ),
            "dobles_sembrados_por_el_generador": _dobles_sembrados(ruta),
        },
        "pagos_inferidos": {"total": len(pagos), "por_categoria": dict(sorted(por_categoria.items()))},
        "pagos_inferidos_calidad": _medir_pagos(ruta, n_personas_medicion) if n_personas_medicion > 0 else None,
    }


def main(argv: list[str]) -> int:
    ruta = Path(argv[1]) if len(argv) > 1 else (COMPLETO if COMPLETO.exists() else MUESTRA)
    n = int(argv[2]) if len(argv) > 2 else 100
    r = calidad(ruta, n)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k != "suscripciones_duplicadas"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
