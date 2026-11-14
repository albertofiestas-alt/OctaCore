"""Experimento de elegibilidad por semáforo verde sostenido (docs/criterios_elegibilidad_semaforo.md). Dueño: Gino.

Entrada: serie diaria por persona con columnas customer_id, fecha, semaforo (verde/ambar/rojo/sin_pagos),
pago_descubierto (bool), confianza (alta/media/baja), arquetipo y pagos_con_fecha_mes (pagos con fecha distintos del
mes calendario, entero >= 0, el mismo valor todos los días del mes). El arquetipo SOLO se usa para agrupar y reportar
sesgo; nunca entra en el cálculo de quién califica (hay una prueba que lo verifica).

Definiciones (todos los parámetros salen de config/elegibilidad.yaml; con algún null la función se niega a correr):
- Ventana: los ÚLTIMOS N meses calendario completos y consecutivos de la persona (un mes con algún día faltante no
  está completo). Sin N meses seguidos completos, la persona no califica en ningún criterio.
- Criterio 1 (verde): ningún día rojo ni ámbar en la ventana. Los días `sin_pagos` son neutros: ni cuentan como verde ni
  rompen, por eso el criterio 4 exige pagos con fecha.
- Criterio 6 (tolerancia, reemplaza al 1 en la combinación 1+2+4+6): ningún rojo; semanas ámbar <= k (semana = bloque de
  7 días desde el inicio de la ventana con algún ámbar); el último mes de la ventana sin ámbar.
- Criterio 2: cero pagos descubiertos en la ventana.
- Criterio 3: días con confianza `baja` en la ventana <= tolerancia.
- Criterio 4: días de serie observados >= M y PAGOS distintos con fecha >= mínimo, sumando por mes de la ventana el
  valor de `pagos_con_fecha_mes` (pagos con fecha distintos del mes calendario; un pago mensual cuenta una vez por mes).
- Criterio 5 (estabilidad del colchón) NO se evalúa: la serie no trae saldo.
- Arquetipo de una persona = el de su última fila (su estado al final de la serie).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[1]
RUTA_CONFIG = RAIZ / "config" / "elegibilidad.yaml"
DIR_SALIDA = RAIZ / "eval" / "resultados"

COLUMNAS = ("customer_id", "fecha", "semaforo", "pago_descubierto", "confianza", "arquetipo", "pagos_con_fecha_mes")
SEMAFOROS = frozenset({"verde", "ambar", "rojo", "sin_pagos"})
CONFIANZAS = frozenset({"alta", "media", "baja"})
DIAS_POR_SEMANA = 7
CAMPOS = (
    "meses_verde",
    "semanas_ambar_toleradas",
    "historia_minima_dias",
    "pagos_minimos",
    "dias_confianza_baja_toleradas",
    "umbral_brecha",
    "reduccion_gasto_incentivo",
)
# Combinaciones del documento: {1}, {1+2}, {1+2+4}, {1+2+3+4}, {1+2+4+6}.
COMBINACIONES = {
    "1": ("verde",),
    "1+2": ("verde", "sin_descubiertos"),
    "1+2+4": ("verde", "sin_descubiertos", "historia"),
    "1+2+3+4": ("verde", "sin_descubiertos", "confianza", "historia"),
    "1+2+4+6": ("verde_tolerancia", "sin_descubiertos", "historia"),
}
_PENDIENTE = "pre-registro pendiente: {campo} es null en config/elegibilidad.yaml (lo fija Gino antes de evaluar)"


# --------------------------------------------------------------------------- #
# Pre-registro y validación de la serie
# --------------------------------------------------------------------------- #


def cargar_prereg(prereg: dict | None = None) -> dict:
    """Parámetros fijados por Gino. Falla con "pre-registro pendiente" si falta alguno o es null."""
    if prereg is None:
        prereg = yaml.safe_load(RUTA_CONFIG.read_text(encoding="utf-8")) or {}
    for campo in CAMPOS:
        if prereg.get(campo) is None:
            raise ValueError(_PENDIENTE.format(campo=campo))
    if int(prereg["meses_verde"]) < 1:
        raise ValueError("meses_verde debe ser un entero >= 1")
    return {campo: prereg[campo] for campo in CAMPOS}


def _validar(serie: pd.DataFrame) -> pd.DataFrame:
    faltan = [c for c in COLUMNAS if c not in serie.columns]
    if faltan:
        raise ValueError(f"faltan columnas en la serie: {faltan}")
    if malos := set(serie["semaforo"]) - SEMAFOROS:
        raise ValueError(f"semaforo desconocido: {sorted(malos)}")
    if malas := set(serie["confianza"]) - CONFIANZAS:
        raise ValueError(f"confianza desconocida: {sorted(malas)}")
    pagos = pd.to_numeric(serie["pagos_con_fecha_mes"], errors="coerce")
    if pagos.isna().any() or (pagos < 0).any() or (pagos % 1 != 0).any():
        raise ValueError("pagos_con_fecha_mes debe ser un entero >= 0")
    df = serie.loc[:, list(COLUMNAS)].copy()
    df["pagos_con_fecha_mes"] = pagos.astype(int)
    df["fecha"] = pd.to_datetime(df["fecha"])
    if df.duplicated(["customer_id", "fecha"]).any():
        raise ValueError("la serie tiene más de una fila por persona y día")
    return df.sort_values(["customer_id", "fecha"])


# --------------------------------------------------------------------------- #
# Una persona
# --------------------------------------------------------------------------- #


def _ventana(g: pd.DataFrame, n: int) -> pd.DataFrame | None:
    """Filas de los últimos n meses calendario completos y consecutivos, o None."""
    mes = g["fecha"].dt.to_period("M")
    completos = sorted(m for m, c in mes.value_counts().items() if c == m.days_in_month)
    if not completos:
        return None
    ultimo = completos[-1]
    pedidos = [ultimo - i for i in range(n)]
    if not set(pedidos) <= set(completos):
        return None
    return g[mes.isin(pedidos)]


def _evaluar_persona(g: pd.DataFrame, p: dict) -> dict[str, bool]:
    w = _ventana(g, int(p["meses_verde"]))
    if w is None:
        return {c: False for cs in COMBINACIONES.values() for c in cs}
    ambar = w["semaforo"] == "ambar"
    rojo = (w["semaforo"] == "rojo").any()
    semanas_ambar = ((w.loc[ambar, "fecha"] - w["fecha"].min()).dt.days // DIAS_POR_SEMANA).nunique()
    ultimo_mes = w["fecha"].dt.to_period("M").max()
    ambar_en_ultimo_mes = (ambar & (w["fecha"].dt.to_period("M") == ultimo_mes)).any()
    pagos = int(w.groupby(w["fecha"].dt.to_period("M"))["pagos_con_fecha_mes"].max().sum())
    return {
        "verde": not rojo and not ambar.any(),
        "verde_tolerancia": not rojo and semanas_ambar <= p["semanas_ambar_toleradas"] and not ambar_en_ultimo_mes,
        "sin_descubiertos": not bool(w["pago_descubierto"].any()),
        "confianza": int((w["confianza"] == "baja").sum()) <= p["dias_confianza_baja_toleradas"],
        "historia": len(g) >= p["historia_minima_dias"] and pagos >= p["pagos_minimos"],
    }


# --------------------------------------------------------------------------- #
# Población
# --------------------------------------------------------------------------- #


def califican(serie: pd.DataFrame, prereg: dict | None = None) -> pd.DataFrame:
    """Una fila por persona (índice customer_id) y una columna booleana por combinación de criterios."""
    p = cargar_prereg(prereg)
    df = _validar(serie)
    filas = {}
    for cid, g in df.groupby("customer_id", sort=True):
        c = _evaluar_persona(g, p)
        filas[cid] = {nombre: all(c[k] for k in criterios) for nombre, criterios in COMBINACIONES.items()}
    out = pd.DataFrame.from_dict(filas, orient="index", columns=list(COMBINACIONES))
    out.index.name = "customer_id"
    return out


def _arquetipos(serie: pd.DataFrame) -> pd.Series:
    df = serie.assign(fecha=pd.to_datetime(serie["fecha"])).sort_values(["customer_id", "fecha"])
    return df.groupby("customer_id")["arquetipo"].last()


def _tasas(q: pd.DataFrame, arq: pd.Series) -> pd.DataFrame:
    largo = q.join(arq).melt(id_vars="arquetipo", var_name="combinacion", value_name="califica")
    t = largo.groupby(["combinacion", "arquetipo"])["califica"].agg(n_personas="size", n_califican="sum").reset_index()
    t["tasa"] = t["n_califican"] / t["n_personas"]
    t["combinacion"] = pd.Categorical(t["combinacion"], list(COMBINACIONES), ordered=True)
    return t.sort_values(["combinacion", "arquetipo"]).reset_index(drop=True)


def tasas_por_arquetipo(serie: pd.DataFrame, prereg: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(tasas, brechas): tasa de personas que califican por combinación y arquetipo, y la brecha máxima entre
    arquetipos por combinación con su alerta contra umbral_brecha."""
    p = cargar_prereg(prereg)
    tasas = _tasas(califican(serie, p), _arquetipos(serie))
    filas = []
    for comb, g in tasas.groupby("combinacion", observed=True):
        alto, bajo = g.loc[g["tasa"].idxmax()], g.loc[g["tasa"].idxmin()]
        brecha = float(alto["tasa"] - bajo["tasa"])
        filas.append(
            {
                "combinacion": comb,
                "brecha": brecha,
                "arquetipo_mayor_tasa": alto["arquetipo"],
                "arquetipo_menor_tasa": bajo["arquetipo"],
                "umbral_brecha": p["umbral_brecha"],
                "alerta": brecha > p["umbral_brecha"],
                # Métricas relativas complementarias (DECISIONES #35): solo se reportan, sin umbral ni efecto en la alerta.
                "razon_tasas": float(bajo["tasa"] / alto["tasa"]) if alto["tasa"] > 0 else float("nan"),
                "n_arquetipos_tasa_cero": int((g["tasa"] == 0).sum()),
            }
        )
    return tasas, pd.DataFrame(filas)


def prueba_incentivo(serie_base: pd.DataFrame, serie_menor_gasto: pd.DataFrame, prereg: dict | None = None) -> pd.DataFrame:
    """Misma población con gasto menor (la serie la genera el simulador): ¿cuánta gente pasa a calificar?"""
    p = cargar_prereg(prereg)
    if set(serie_base["customer_id"]) != set(serie_menor_gasto["customer_id"]):
        raise ValueError("la prueba de incentivo exige las mismas personas en ambas series")
    base, menos = califican(serie_base, p), califican(serie_menor_gasto, p)
    arq = _arquetipos(serie_base)
    t_base, t_menos = _tasas(base, arq), _tasas(menos, arq)
    cambian = (menos & ~base).join(arq).melt(id_vars="arquetipo", var_name="combinacion", value_name="c")
    cambian = cambian.groupby(["combinacion", "arquetipo"])["c"].sum().rename("personas_que_cambian").reset_index()
    out = t_base.rename(columns={"tasa": "tasa_base", "n_califican": "n_califican_base"})
    out["tasa_menor_gasto"] = t_menos["tasa"].to_numpy()
    out["delta"] = out["tasa_menor_gasto"] - out["tasa_base"]
    out["combinacion"] = out["combinacion"].astype(str)
    out = out.merge(cambian, on=["combinacion", "arquetipo"])
    out["reduccion_gasto"] = p["reduccion_gasto_incentivo"]
    return out


def evaluar_elegibilidad(
    serie: pd.DataFrame, serie_menor_gasto: pd.DataFrame | None = None, prereg: dict | None = None
) -> dict:
    """Tasas y brechas por arquetipo y, si hay serie de menor gasto, la prueba de incentivo."""
    p = cargar_prereg(prereg)  # primero el pre-registro: sin él no se mira ningún dato
    tasas, brechas = tasas_por_arquetipo(serie, p)
    return {
        "parametros": p,
        "tasas": tasas,
        "brechas": brechas,
        "incentivo": None if serie_menor_gasto is None else prueba_incentivo(serie, serie_menor_gasto, p),
    }


def main(argv: list[str]) -> int:
    if not 2 <= len(argv) <= 3:
        print("uso: python eval/elegibilidad.py serie.csv [serie_menor_gasto.csv]")
        return 2
    menor = pd.read_csv(argv[2]) if len(argv) == 3 else None
    r = evaluar_elegibilidad(pd.read_csv(argv[1]), menor)
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre in ("tasas", "brechas", "incentivo"):
        if r[nombre] is not None:
            r[nombre].to_csv(DIR_SALIDA / f"elegibilidad_{nombre}.csv", index=False)
    print(r["brechas"].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
