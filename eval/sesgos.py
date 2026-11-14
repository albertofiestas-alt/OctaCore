"""Sesgos por grupo: arquetipo, tercil de ingreso, tercil de volatilidad y cambio de patrón. Dueño: Rafael.

Entrada `resultados_por_persona` (formato provisional hasta que Gino publique eval/simular.py y eval/correr.py):
un DataFrame o una lista de dicts con una fila por (persona, método, cuantil):

    customer_id, metodo, cuantil, pagos_descubiertos, pagos_totales, gasto_permitido_dia
    [opcional] calibracion_p20   fracción de ventanas con ingreso real >= P20 (debería rondar 0.80)
    [opcional] origen            "medido" (por defecto) o "[DEMO]"

Son las mismas claves que devuelve eval/simular.py::simular_persona (y que agrega eval/frontera.py), más la persona,
el método y el cuantil.

Los grupos se calculan SOLO con `df` (movimientos más etiquetas de referencia): esto es evaluación, nunca entra al
modelo ni al motor. Ingreso y volatilidad se miden en los meses ANTERIORES a la prueba (1 a 20), para que el grupo
no dependa del resultado que se evalúa [SUPUESTO].

Salida: DataFrame largo (dimensión, grupo, método, cuantil) con n de personas, % de pagos descubiertos (suma de
descubiertos / suma de totales), gasto permitido medio, calibración del P20 si viene, la brecha (máximo − mínimo
entre los grupos con n > 0 de la dimensión) y la alerta contra cfg["preregistro"]["umbral_alerta_sesgo"].
Se guarda en eval/resultados/sesgos.csv.

    python eval/sesgos.py --demo     escribe eval/resultados/sesgos_demo.csv con resultados FALSOS marcados [DEMO]
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
RESULTADOS = Path(__file__).resolve().parent / "resultados"
RUTA_SALIDA = RESULTADOS / "sesgos.csv"
RUTA_DEMO = RESULTADOS / "sesgos_demo.csv"

INICIO = date(2025, 1, 1)                 # mes 1 (el mismo de src/datos/generador.py)
MESES_DEFINICION = (1, 20)                # meses que definen ingreso y volatilidad: todo lo anterior a la prueba
ARQUETIPOS = ("conductor", "vendedora", "tecnico", "comisionista", "asalariado")
TERCILES = ("bajo", "medio", "alto")
DIMENSIONES: dict[str, tuple[str, ...]] = {
    "arquetipo": ARQUETIPOS,
    "tercil_ingreso": TERCILES,
    "tercil_volatilidad": TERCILES,
    "cambio_patron": ("no", "si"),
}
COLUMNAS_RESULTADO = ("customer_id", "metodo", "cuantil", "pagos_descubiertos", "pagos_totales", "gasto_permitido_dia")
# Métricas que son fracciones (0 a 1): su brecha se compara con el umbral del pre-registro.
# La brecha de gasto está en soles por día y no se compara con un umbral en fracción [SUPUESTO].
METRICAS_CON_ALERTA = ("pct_descubiertos", "calibracion_p20")


# --------------------------------------------------------------------------- #
# Grupos por persona (solo evaluación)
# --------------------------------------------------------------------------- #


def _mes(fechas: pd.Series) -> pd.Series:
    return (fechas.dt.year - INICIO.year) * 12 + fechas.dt.month


def _tercil(valores: pd.Series) -> pd.Series:
    """Tercil por rango (empates resueltos por orden de customer_id): cubre a todas las personas con cualquier n."""
    rango = valores.rank(method="first", na_option="bottom")
    n = len(valores)
    idx = np.ceil(rango * 3 / n).astype(int).clip(1, 3) - 1
    return pd.Series([TERCILES[i] for i in idx], index=valores.index)


def grupos_por_persona(df: pd.DataFrame, meses: tuple[int, int] = MESES_DEFINICION) -> pd.DataFrame:
    """Una fila por persona con arquetipo, tercil_ingreso, tercil_volatilidad, cambio_patron e insumos medidos.

    df: movimientos con las etiquetas de referencia (arquetipo, es_duplicado, es_atipico).
    Ingreso y volatilidad se calculan sin duplicados ni atípicos inyectados, en los meses `meses`.
    """
    faltan = [c for c in ("customer_id", "fecha_hora", "monto", "tipo", "arquetipo") if c not in df.columns]
    if faltan:
        raise ValueError(f"sesgos necesita las columnas {faltan} (incluida la etiqueta arquetipo)")
    d = df.copy()
    d["fecha_hora"] = pd.to_datetime(d["fecha_hora"])
    d = d.sort_values(["customer_id", "fecha_hora"], kind="mergesort")
    personas = sorted(d["customer_id"].unique())

    arq = d.groupby("customer_id")["arquetipo"]
    salida = pd.DataFrame(index=pd.Index(personas, name="customer_id"))
    salida["arquetipo"] = arq.first()
    salida["cambio_patron"] = np.where(arq.nunique() > 1, "si", "no")

    limpio = d
    for etiqueta in ("es_duplicado", "es_atipico"):
        if etiqueta in limpio.columns:
            limpio = limpio[~limpio[etiqueta].astype(bool)]
    mes = _mes(limpio["fecha_hora"])
    ventana = limpio[(mes >= meses[0]) & (mes <= meses[1]) & (limpio["tipo"] == "ingreso")]
    n_meses = meses[1] - meses[0] + 1
    salida["ingreso_mensual"] = (ventana.groupby("customer_id")["monto"].sum() / n_meses).reindex(personas).fillna(0.0)

    # Coeficiente de variación del ingreso semanal, con ceros en las semanas sin ingreso.
    ini = pd.Timestamp(INICIO.year + (meses[0] - 1) // 12, (meses[0] - 1) % 12 + 1, 1)
    fin = pd.Timestamp(INICIO.year + meses[1] // 12, meses[1] % 12 + 1, 1)
    # Solo semanas COMPLETAS: una semana final recortada parecería de ingreso bajo e inflaría el CV [SUPUESTO].
    n_semanas = max(int((fin - ini).days // 7), 1)
    semana = ((ventana["fecha_hora"] - ini).dt.days // 7).rename("semana")
    completas = semana < n_semanas
    semanal = ventana[completas].groupby([ventana.loc[completas, "customer_id"], semana[completas]])["monto"].sum()
    semanal = semanal.unstack(fill_value=0.0)
    semanal = semanal.reindex(index=personas, columns=range(n_semanas), fill_value=0.0)
    media = semanal.mean(axis=1)
    cv = semanal.std(axis=1, ddof=0) / media.replace(0.0, np.nan)
    salida["cv_semanal"] = cv.fillna(np.inf)             # sin ingreso: la máxima volatilidad posible
    salida["tercil_ingreso"] = _tercil(salida["ingreso_mensual"])
    salida["tercil_volatilidad"] = _tercil(salida["cv_semanal"])
    return salida


# --------------------------------------------------------------------------- #
# Tabla de sesgos
# --------------------------------------------------------------------------- #


def _como_tabla(resultados) -> pd.DataFrame:
    r = pd.DataFrame(resultados).copy()
    faltan = [c for c in COLUMNAS_RESULTADO if c not in r.columns]
    if faltan:
        raise ValueError(f"resultados_por_persona necesita las columnas {faltan}")
    if "origen" not in r.columns:
        r["origen"] = "medido"
    r["cuantil"] = pd.to_numeric(r["cuantil"], errors="coerce")      # referencias (gasto_cero...) -> NaN
    return r


def _umbral(cfg) -> float:
    prereg = cfg["preregistro"] if "preregistro" in cfg else {}
    umbral = prereg.get("umbral_alerta_sesgo") if prereg else None
    if umbral is None:
        raise ValueError("pre-registro pendiente: umbral_alerta_sesgo es null en config/preregistro.yaml")
    return float(umbral)


def tabla_sesgos(grupos: pd.DataFrame, resultados, umbral: float) -> pd.DataFrame:
    """Cálculo puro (sin archivos). Ver sesgos()."""
    r = _como_tabla(resultados)
    con_cal = "calibracion_p20" in r.columns
    r = r.merge(grupos[list(DIMENSIONES)], left_on="customer_id", right_index=True, how="left")
    sin_grupo = sorted(r.loc[r["arquetipo"].isna(), "customer_id"].unique())
    if sin_grupo:
        raise ValueError(f"personas con resultados pero sin movimientos en df: {sin_grupo[:5]}")

    filas = []
    for (metodo, cuantil), rm in r.groupby(["metodo", "cuantil"], sort=True, dropna=False):
        origen = "[DEMO]" if (rm["origen"] == "[DEMO]").any() else "medido"
        for dim, valores in DIMENSIONES.items():
            for grupo in valores:
                g = rm[rm[dim] == grupo]
                totales = float(g["pagos_totales"].sum())
                fila = {
                    "dimension": dim, "grupo": grupo, "metodo": metodo, "cuantil": cuantil,
                    "n_personas": int(g["customer_id"].nunique()),
                    "pagos_descubiertos": int(g["pagos_descubiertos"].sum()),
                    "pagos_totales": int(totales),
                    "pct_descubiertos": float(g["pagos_descubiertos"].sum()) / totales if totales else np.nan,
                    "gasto_permitido": float(g["gasto_permitido_dia"].mean()) if len(g) else np.nan,
                    "origen": origen,
                }
                if con_cal:
                    fila["calibracion_p20"] = float(g["calibracion_p20"].mean()) if len(g) else np.nan
                filas.append(fila)
    t = pd.DataFrame(filas)

    metricas = ["pct_descubiertos", "gasto_permitido"] + (["calibracion_p20"] if con_cal else [])
    clave = ["dimension", "metodo", "cuantil"]
    for m in metricas:
        validos = t[t["n_personas"] > 0]
        rango = validos.groupby(clave, dropna=False)[m].agg(lambda s: s.max() - s.min() if s.notna().any() else np.nan)
        t = t.merge(rango.rename(f"brecha_{m}"), left_on=clave, right_index=True, how="left")
    t["umbral_alerta_sesgo"] = umbral
    con_alerta = [f"brecha_{m}" for m in METRICAS_CON_ALERTA if f"brecha_{m}" in t.columns]
    t["alerta"] = (t[con_alerta].fillna(0.0) > umbral).any(axis=1)
    orden = {d: i for i, d in enumerate(DIMENSIONES)}
    t = t.sort_values(["metodo", "cuantil", "dimension"], key=lambda s: s.map(orden) if s.name == "dimension" else s,
                      kind="mergesort").reset_index(drop=True)
    return t


def sesgos(df, resultados_por_persona, cfg):
    """Por grupo y método: % descubiertos, gasto permitido y calibración del P20. Brecha = máximo menos mínimo;
    alerta si supera cfg["preregistro"]["umbral_alerta_sesgo"]. Guarda eval/resultados/sesgos.csv."""
    tabla = tabla_sesgos(grupos_por_persona(df), resultados_por_persona, _umbral(cfg))
    _guardar(tabla, RUTA_SALIDA)
    return tabla


def resumen_sesgos(tabla: pd.DataFrame | None = None) -> pd.DataFrame:
    """Peor grupo por (dimensión, método, cuantil): el de mayor % de pagos descubiertos (empate: menor gasto).

    Sin argumento lee eval/resultados/sesgos.csv. Columnas: dimension, metodo, cuantil, peor_grupo,
    pct_descubiertos, gasto_permitido, n_personas, brecha_pct_descubiertos, brecha_gasto_permitido, alerta, origen.
    """
    if tabla is None:
        tabla = pd.read_csv(RUTA_SALIDA, keep_default_na=False, na_values=["nan", "NaN"])
    validos = tabla[(tabla["n_personas"] > 0) & tabla["pct_descubiertos"].notna()]
    ordenado = validos.sort_values(["pct_descubiertos", "gasto_permitido"], ascending=[False, True], kind="mergesort")
    peor = ordenado.groupby(["dimension", "metodo", "cuantil"], sort=True, dropna=False).head(1)
    columnas = ["dimension", "metodo", "cuantil", "grupo", "pct_descubiertos", "gasto_permitido", "n_personas",
                "brecha_pct_descubiertos", "brecha_gasto_permitido", "alerta", "origen"]
    return peor[columnas].rename(columns={"grupo": "peor_grupo"}).reset_index(drop=True)


def _guardar(tabla: pd.DataFrame, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(ruta, index=False, lineterminator="\n")


# --------------------------------------------------------------------------- #
# Demo con resultados FALSOS (no es la tabla final)
# --------------------------------------------------------------------------- #


def demo(ruta_datos: Path = RAIZ / "data" / "muestra" / "movimientos.csv", ruta: Path = RUTA_DEMO) -> pd.DataFrame:
    """Grupos REALES de la muestra con resultados INVENTADOS, marcados [DEMO]. Solo para maquetar la pantalla."""
    sys.path.insert(0, str(RAIZ / "src"))
    from contratos import cargar_config

    df = pd.read_csv(ruta_datos, keep_default_na=False, na_values=[""])
    rng = np.random.default_rng(0)
    filas = []
    for cid in sorted(df["customer_id"].unique()):
        for metodo in ("regla1", "regla2", "modelo"):
            totales = int(rng.integers(10, 20))
            filas.append({"customer_id": cid, "metodo": metodo, "cuantil": 0.2,
                          "pagos_descubiertos": int(rng.integers(0, 4)), "pagos_totales": totales,
                          "gasto_permitido_dia": round(float(rng.uniform(10, 60)), 2), "origen": "[DEMO]"})
    tabla = tabla_sesgos(grupos_por_persona(df), filas, _umbral(cargar_config()))
    _guardar(tabla, ruta)
    return tabla


if __name__ == "__main__":
    if "--demo" in sys.argv:
        t = demo()
        print(f"{RUTA_DEMO} [DEMO]: {len(t)} filas")
        print(resumen_sesgos(t).to_string(index=False))
    else:
        print("Uso: python eval/sesgos.py --demo   (la tabla real la produce eval/correr.py con la simulación)")
