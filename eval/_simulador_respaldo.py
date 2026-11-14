"""SIMULADOR DE RESPALDO de la decisión día a día. NO es el oficial.

RESPALDO hasta que existan eval/simular.py (Rafael) y motor.decidir (Sebastián). No toca simular.py, src/motor ni
src/reglas: reimplementa solo la fórmula del plan para poder medir la frontera. Cuando lleguen los oficiales, se borra.

Qué simula (plan de Rafael, sección eval/simular.py): para cada día de los meses de prueba (21 a 24)
  1) historia = movimientos limpios (sin duplicados exactos) con fecha_hora < día (sin mirar el futuro);
  2) pronóstico = método(historia, día); número de hoy con la fórmula del plan:
        permitido(d) = (saldo + ingreso_conservador(d) - pagos_hasta(d) - colchón) / max(d, 1)
     mínimo sobre los días de pago (d <= 14) y el día 14; ingreso_conservador(d) usa el mayor horizonte h de los del
     pronóstico con h <= d (0 si d < 3) al cuantil del método; numero_hoy = floor(max(0, mínimo));
  3) la persona gasta exactamente numero_hoy [SUPUESTO del plan]; los gastos discrecionales observados se reemplazan;
  4) saldo += ingresos reales del día - gasto - pagos reales del día; un pago real queda descubierto si, al pagarlo,
     el saldo del día (ingresos - gasto incluidos) es menor que cero.

Pagos con fecha que ve el método: INFERIDOS del historial anterior a cada mes (sin etiquetas, como pide el plan:
la ingesta oficial no existe todavía), con una regla propia mínima: un (comercio, categoría) que aparece en al menos
3 de los 6 meses previos, a lo sumo 1.5 veces por mes, con el día del mes estable y el monto estable. Se re-infieren
el primer día de cada mes. Las etiquetas se usan SOLO para medir (pagos reales y copias duplicadas), nunca en lo
que ve el método. Limitaciones: no detecta atípicos (no existe atipico_detectado) y la inferencia es más simple que
la de ingesta; todo método ve la misma historia y los mismos pagos inferidos.

Referencias (metodo="gasto_cero" y "gasto_fijo"): gasto cero no gasta; gasto fijo gasta cada día el promedio diario de
sus gastos discrecionales (los que no son pagos inferidos) de los 6 meses previos al inicio de la prueba.
"""

from __future__ import annotations

import calendar
import math

import numpy as np
import pandas as pd

from contratos import NOMBRES_CUANTILES
from datos.generador import INICIO

MESES_PRUEBA = (21, 24)  # igual que datos.particion()["meses_test"]
METODOS = ("regla1", "regla2", "modelo")
REFERENCIAS = ("gasto_cero", "gasto_fijo")
VENTANA_DIAS = 14  # días hacia adelante del número de hoy (cfg["ventana_dias"])

# Inferencia mínima de pagos con fecha [SUPUESTO de respaldo, no son umbrales del pre-registro].
MESES_MIRADOS = 6
MIN_MESES_CON_PAGO = 3
MAX_VECES_POR_MES = 1.5
MAX_DISPERSION_DIAS = 6
MAX_CV_MONTO = 0.35

_CACHE: dict = {}


def _inicio_mes(n: int) -> pd.Timestamp:
    return pd.Timestamp(INICIO.year + (n - 1) // 12, (n - 1) % 12 + 1, 1)


# --- fórmula del número de hoy ---

def _ingreso_conservador(pron, d: int, nombre: str) -> float:
    """Ingreso conservador hasta el día d: mayor horizonte h con h <= d, 0 si ninguno cabe."""
    cabe = [h for h in pron.por_horizonte if h <= d]
    return float(getattr(pron.por_horizonte[max(cabe)], nombre)) if cabe else 0.0


def _numero_hoy(saldo: float, pagos: list[tuple[int, float]], pron, nombre: str, colchon: float) -> int:
    """pagos: [(días hasta el pago, monto)]. Mínimo de permitido(d) sobre cada día de pago y el último horizonte."""
    ultimo = max(pron.por_horizonte)
    dias = sorted({d for d, _ in pagos if d <= ultimo} | {ultimo})
    minimo = min(
        (saldo + _ingreso_conservador(pron, d, nombre) - sum(m for dd, m in pagos if dd <= d) - colchon) / max(d, 1)
        for d in dias
    )
    return int(math.floor(max(0.0, minimo)))


# --- pagos inferidos sin etiquetas ---

def _pagos_inferidos(hist: pd.DataFrame, mes_inicio: pd.Timestamp) -> list[dict]:
    """[{dia_mes, monto, clave}] de los pagos que se repiten cada mes, con datos anteriores a mes_inicio."""
    desde = mes_inicio - pd.DateOffset(months=MESES_MIRADOS)
    g = hist[(hist["fecha_hora"] < mes_inicio) & (hist["fecha_hora"] >= desde) & (hist["monto"] < 0)]
    pagos = []
    for clave, grupo in g.groupby(["comercio", "categoria"]):
        n_meses = grupo["fecha_hora"].dt.to_period("M").nunique()
        if n_meses < MIN_MESES_CON_PAGO or len(grupo) / n_meses > MAX_VECES_POR_MES:
            continue
        dias = grupo["fecha_hora"].dt.day
        montos = grupo["monto"].abs()
        if dias.max() - dias.min() > MAX_DISPERSION_DIAS or montos.std(ddof=0) > MAX_CV_MONTO * montos.mean():
            continue
        pagos.append({"dia_mes": int(dias.median()), "monto": float(montos.median()), "clave": clave})
    return sorted(pagos, key=lambda p: (p["dia_mes"], p["monto"]))


def _proximos(pagos: list[dict], fecha: pd.Timestamp, ventana: int = VENTANA_DIAS) -> list[tuple[int, float]]:
    """[(días hasta el pago, monto)] de los pagos esperados en [fecha, fecha + ventana]."""
    salida = []
    for offset in range(ventana + 1):
        dia = fecha + pd.Timedelta(days=offset)
        ultimo_dia_mes = calendar.monthrange(dia.year, dia.month)[1]
        salida += [(offset, p["monto"]) for p in pagos if dia.day == min(p["dia_mes"], ultimo_dia_mes)]
    return salida


# --- pronóstico ---

def _regla(nombre: str, hist: pd.DataFrame, fecha: pd.Timestamp, cfg):
    import reglas  # las de Rafael; el simulador no las duplica

    return getattr(reglas, nombre)(hist, fecha.date(), cfg)


def _pronosticar(metodo: str, hist: pd.DataFrame, fecha: pd.Timestamp, modelo, cfg):
    if metodo != "modelo":
        return _regla(metodo, hist, fecha, cfg)
    if modelo is None:
        raise ValueError("el método 'modelo' necesita un modelo entrenado")
    from modelo import HistoriaInsuficiente

    try:
        return modelo.predecir(hist, fecha.date())
    except HistoriaInsuficiente:
        return _regla("regla2", hist, fecha, cfg)  # la escalera del servicio: modelo -> regla2


# --- simulación ---

def _flujos_reales(historia: pd.DataFrame, etiquetas: pd.DataFrame):
    """(ingresos por día, pagos por día) reales, sin copias duplicadas. Aquí sí se usan las etiquetas, solo para medir."""
    lab = etiquetas.reindex(historia["transaction_id"]).reset_index(drop=True)
    reales = historia.reset_index(drop=True)[~lab["es_duplicado"].astype(bool)]
    pago = lab.loc[reales.index, "pago_con_fecha"].astype(bool)
    dia = reales["fecha_hora"].dt.normalize()
    ingresos = reales[reales["tipo"] == "ingreso"].groupby(dia)["monto"].sum().to_dict()
    pagos = {d: g["monto"].abs().tolist() for d, g in reales[pago].groupby(dia[pago])}
    return ingresos, pagos


def _gasto_fijo(hist: pd.DataFrame, inicio: pd.Timestamp, pagos: list[dict]) -> float:
    desde = inicio - pd.DateOffset(months=MESES_MIRADOS)
    g = hist[(hist["fecha_hora"] < inicio) & (hist["fecha_hora"] >= desde) & (hist["monto"] < 0)]
    claves = {p.get("clave") for p in pagos}
    discrecional = g[[(c, k) not in claves for c, k in zip(g["comercio"], g["categoria"])]]
    return float(discrecional["monto"].abs().sum() / max((inicio - desde).days, 1))


def simular_persona(historia_completa, etiquetas, cfg, metodo: str, cuantil, modelo=None) -> dict:
    """{"pagos_descubiertos": n, "pagos_totales": m, "gasto_permitido_dia": promedio}. Misma firma que eval/simular.py."""
    if metodo not in METODOS + REFERENCIAS:
        raise ValueError(f"método desconocido: {metodo!r}; válidos: {METODOS + REFERENCIAS}")
    nombre = None
    if metodo in METODOS:
        nombre = f"p{round(100 * float(cuantil))}"
        if nombre not in NOMBRES_CUANTILES:
            raise ValueError(f"cuantil {cuantil!r} no está en {NOMBRES_CUANTILES}")
    colchon = float(cfg["preregistro"]["colchon"] or 0.0)

    historia = historia_completa.sort_values("fecha_hora", kind="stable").reset_index(drop=True)
    ingresos, pagos_reales = _flujos_reales(historia, etiquetas)
    hist = historia.drop_duplicates(subset=["customer_id", "fecha_hora", "monto", "comercio", "tipo"]).reset_index(drop=True)
    inicio = _inicio_mes(MESES_PRUEBA[0])
    fin = min(_inicio_mes(MESES_PRUEBA[1] + 1) - pd.Timedelta(days=1), hist["fecha_hora"].max().normalize())
    dias = pd.date_range(inicio, fin, freq="D")
    if len(dias) == 0:
        raise ValueError("la persona no tiene movimientos en los meses de prueba")

    previos = hist[hist["fecha_hora"] < inicio]
    saldo = float(previos["saldo"].iloc[-1]) if len(previos) else 0.0
    fechas = hist["fecha_hora"].to_numpy()
    cid = hist["customer_id"].iloc[0]
    gasto_ref = 0.0
    if metodo == "gasto_fijo":
        gasto_ref = _gasto_fijo(hist, inicio, _pagos_inferidos(hist, inicio))

    inferidos, mes_actual = [], None
    descubiertos = total = 0
    gastos = []
    for t in dias:
        if (t.year, t.month) != mes_actual:
            mes_actual = (t.year, t.month)
            inferidos = _pagos_inferidos(hist, pd.Timestamp(t.year, t.month, 1))
        if metodo in REFERENCIAS:
            gasto = gasto_ref
        else:
            k = int(np.searchsorted(fechas, t.to_datetime64(), side="left"))  # solo movimientos con fecha_hora < t
            clave = (cid, metodo, id(modelo), t, k)
            if clave not in _CACHE:
                _CACHE[clave] = _pronosticar(metodo, hist.iloc[:k], t, modelo, cfg)
            gasto = _numero_hoy(saldo, _proximos(inferidos, t), _CACHE[clave], nombre, colchon)
        gastos.append(gasto)
        saldo_dia = saldo + ingresos.get(t, 0.0) - gasto
        for monto in pagos_reales.get(t, []):
            total += 1
            saldo_dia -= monto
            descubiertos += saldo_dia < 0
        saldo = saldo_dia
    return {"pagos_descubiertos": int(descubiertos), "pagos_totales": int(total),
            "gasto_permitido_dia": float(np.mean(gastos))}


# --- series diarias para el experimento de elegibilidad (Judas): solo regla2, meses 13-24 ---
# Misma simulación de arriba (regla2 al cuantil conservador del pre-registro, pagos inferidos, gasto = numero_hoy), pero
# registra una fila por persona y día. RESPALDO: sale de este simulador y no del motor oficial.

MESES_SERIE = (13, 24)
FACTOR_MENOR_GASTO = 0.75  # "gasto 25 % menor" para la prueba de incentivo (pedido de Gino)
COLUMNAS_SERIE = ["customer_id", "fecha", "semaforo", "pago_descubierto", "confianza", "arquetipo",
                  "pagos_con_fecha_mes"]
_GRAVEDAD = {"verde": 0, "ambar": 1, "rojo": 2}


def _semaforo_ventana(saldo: float, proximos: list[tuple[int, float]], pron) -> str:
    """Peor semáforo entre los pagos de la ventana (plan del motor, sin colchón): cobertura(q) = saldo + ingreso(d, q)
    - pagos con día <= d. Verde si cubre con P5; ámbar si cubre con P50 y no con P5; rojo si ni así; sin_pagos si no hay."""
    if not proximos:
        return "sin_pagos"
    peor = "verde"
    for d, _ in proximos:
        acumulado = sum(m for dd, m in proximos if dd <= d)

        def cubre(nombre: str, d=d, acumulado=acumulado) -> bool:
            return saldo + _ingreso_conservador(pron, d, nombre) - acumulado >= 0

        estado = "verde" if cubre("p5") else "ambar" if cubre("p50") else "rojo"
        if _GRAVEDAD[estado] > _GRAVEDAD[peor]:
            peor = estado
    return peor


def _confianza(pron, semanas_historia: int, cfg) -> str:
    """Confianza como el plan del motor, con los umbrales del pre-registro: ancho = (p80 - p5) / max(p50, 1) a 14 días.
    Baja si hay menos semanas de historia que el umbral o el ancho supera ancho_bajo; alta si el ancho es menor que
    ancho_alto con historia suficiente; media en los demás casos."""
    prereg = cfg["preregistro"]
    c = pron.por_horizonte[max(pron.por_horizonte)]
    ancho = (c.p80 - c.p5) / max(c.p50, 1.0)
    if semanas_historia < int(prereg["umbral_historia_semanas"]) or ancho > float(prereg["umbrales_confianza"]["ancho_bajo"]):
        return "baja"
    return "alta" if ancho < float(prereg["umbrales_confianza"]["ancho_alto"]) else "media"


def _serie_persona(historia_completa, etiquetas, cfg, factores=(1.0,), meses=MESES_SERIE) -> list[pd.DataFrame]:
    """Una serie diaria por factor de gasto (gasto del día = numero_hoy * factor), compartiendo el pronóstico por día."""
    nombre = f"p{round(100 * float(cfg['preregistro']['cuantil_conservador']))}"
    colchon = float(cfg["preregistro"]["colchon"] or 0.0)
    historia = historia_completa.sort_values("fecha_hora", kind="stable").reset_index(drop=True)
    ingresos, pagos_reales = _flujos_reales(historia, etiquetas)
    hist = historia.drop_duplicates(subset=["customer_id", "fecha_hora", "monto", "comercio", "tipo"]).reset_index(drop=True)
    inicio = _inicio_mes(meses[0])
    dias = pd.date_range(inicio, _inicio_mes(meses[1] + 1) - pd.Timedelta(days=1), freq="D")

    previos = hist[hist["fecha_hora"] < inicio]
    saldo0 = float(previos["saldo"].iloc[-1]) if len(previos) else 0.0
    fechas = hist["fecha_hora"].to_numpy()
    cid = hist["customer_id"].iloc[0]
    primer_dia = hist["fecha_hora"].min().normalize()
    # etiqueta de arquetipo vigente cada día (solo para reportar): la del último movimiento hasta ese día
    arq_filas = etiquetas["arquetipo"].reindex(historia["transaction_id"]).to_numpy()
    por_dia = pd.Series(arq_filas, index=historia["fecha_hora"].dt.normalize()).groupby(level=0).last()
    arquetipos = por_dia.reindex(pd.date_range(min(por_dia.index.min(), dias[0]), dias[-1])).ffill().reindex(dias)
    pagos_mes: dict[tuple[int, int], int] = {}
    for d, montos in pagos_reales.items():
        pagos_mes[(d.year, d.month)] = pagos_mes.get((d.year, d.month), 0) + len(montos)

    saldo = {f: saldo0 for f in factores}
    filas: dict[float, list] = {f: [] for f in factores}
    gastos: dict[float, list] = {f: [] for f in factores}
    inferidos, mes_actual = [], None
    for t in dias:
        if (t.year, t.month) != mes_actual:
            mes_actual = (t.year, t.month)
            inferidos = _pagos_inferidos(hist, pd.Timestamp(t.year, t.month, 1))
        k = int(np.searchsorted(fechas, t.to_datetime64(), side="left"))  # solo movimientos con fecha_hora < t
        clave = (cid, "regla2", id(None), t, k)
        if clave not in _CACHE:
            _CACHE[clave] = _pronosticar("regla2", hist.iloc[:k], t, None, cfg)
        pron = _CACHE[clave]
        proximos = _proximos(inferidos, t)
        confianza = _confianza(pron, int((t - primer_dia).days // 7), cfg)
        for f in factores:
            s = saldo[f]
            semaforo = _semaforo_ventana(s, proximos, pron)
            gasto = _numero_hoy(s, proximos, pron, nombre, colchon) * f
            gastos[f].append(gasto)
            s_dia = s + ingresos.get(t, 0.0) - gasto
            descubierto = False
            for monto in pagos_reales.get(t, []):
                s_dia -= monto
                descubierto = descubierto or s_dia < 0
            saldo[f] = s_dia
            filas[f].append((cid, t.strftime("%Y-%m-%d"), semaforo, bool(descubierto), confianza, arquetipos[t],
                             pagos_mes.get((t.year, t.month), 0)))
    series = []
    for f in factores:
        df = pd.DataFrame(filas[f], columns=COLUMNAS_SERIE)
        df.attrs["gasto_medio_dia"] = float(np.mean(gastos[f]))
        series.append(df)
    return series


def serie_diaria(historia_completa, etiquetas, cfg, factor_gasto: float = 1.0, meses=MESES_SERIE) -> pd.DataFrame:
    """Una fila por día (completo) de los meses `meses`: customer_id, fecha, semaforo, pago_descubierto, confianza,
    arquetipo, pagos_con_fecha_mes. Solo regla2, con historia anterior a cada día. RESPALDO (no es el motor oficial)."""
    return _serie_persona(historia_completa, etiquetas, cfg, (factor_gasto,), meses)[0]


def serie_menor_gasto(historia_completa, etiquetas, cfg, meses=MESES_SERIE) -> pd.DataFrame:
    """Lo mismo con la persona gastando 25 % menos que el número de hoy (prueba de incentivo)."""
    return serie_diaria(historia_completa, etiquetas, cfg, FACTOR_MENOR_GASTO, meses)


def _trabajo_persona(historia, etiquetas):
    """Un proceso por persona: ambas series con un solo pronóstico por día."""
    from contratos import cargar_config

    normal, menor = _serie_persona(historia, etiquetas, cargar_config(), (1.0, FACTOR_MENOR_GASTO))
    return normal, menor


def generar_series(df: pd.DataFrame, n_procesos: int = 8, destino=None, sufijo: str = "") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Series de todas las personas de `df` (con etiquetas y fecha_hora datetime) en paralelo; escribe serie_diaria.csv
    y serie_menor_gasto.csv en `destino` (por defecto eval/resultados). Falla si hay (customer_id, fecha) repetidos."""
    from pathlib import Path

    from joblib import Parallel, delayed

    from contratos import ETIQUETAS_REFERENCIA

    destino = Path(destino) if destino else Path(__file__).resolve().parent / "resultados"
    personas = []
    for _, g in df.groupby("customer_id", sort=True):
        personas.append((g.drop(columns=list(ETIQUETAS_REFERENCIA)).reset_index(drop=True),
                         g.set_index("transaction_id")[list(ETIQUETAS_REFERENCIA)]))
    pares = Parallel(n_jobs=n_procesos)(delayed(_trabajo_persona)(h, e) for h, e in personas)
    normal = pd.concat([p[0] for p in pares], ignore_index=True)
    menor = pd.concat([p[1] for p in pares], ignore_index=True)
    for nombre, serie in ((f"serie_diaria{sufijo}.csv", normal), (f"serie_menor_gasto{sufijo}.csv", menor)):
        if serie.duplicated(["customer_id", "fecha"]).any():
            raise ValueError(f"{nombre}: hay filas repetidas por persona y día")
        destino.mkdir(parents=True, exist_ok=True)
        serie.to_csv(destino / nombre, index=False, lineterminator="\n")
    return normal, menor


if __name__ == "__main__":
    import sys
    import warnings

    warnings.simplefilter("ignore")
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/generado/generado/movimientos.csv"
    procesos = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    sufijo = sys.argv[3] if len(sys.argv) > 3 else ""  # p. ej. _v11 para no pisar las series de otra versión de datos
    datos = pd.read_csv(ruta, parse_dates=["fecha_hora"])
    n, m = generar_series(datos, procesos, sufijo=sufijo)
    print(f"serie_diaria.csv {len(n)} filas; serie_menor_gasto.csv {len(m)} filas; "
          f"personas {n['customer_id'].nunique()}", flush=True)
