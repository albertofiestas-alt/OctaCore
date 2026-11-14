"""Generador sintetico del proyecto (dueno: Rafael).

Uso:  python -m src.datos.generador [--n 400] [--semilla 12345] [--salida data]
Genera data/generado/movimientos.csv, movimientos_perturbado.csv, data/muestra/movimientos.csv y data/REPORTE_DATOS.md.
Todo parametro marcado [SUPUESTO] se ajusta para que la plausibilidad salga razonable (ver verificar()).
Los datos son ficticios: ningun nombre, DNI, telefono ni cuenta reales.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import re
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ARQUETIPOS = ["conductor", "vendedora", "tecnico", "comisionista", "asalariado"]
INICIO = date(2025, 1, 1)                       # ano 1; diciembre = mes 12 y mes 24
MESES = 24
FERIADOS = {(1, 1), (5, 1), (7, 28), (7, 29), (8, 30), (10, 8), (11, 1), (12, 8), (12, 25)}   # [SUPUESTO]
MEZCLA_BASE = [0.25, 0.25, 0.20, 0.20, 0.10]
MEZCLA_PERTURBADA = [0.15, 0.15, 0.30, 0.35, 0.05]
GASTO_SOBRE_INGRESO = 0.84                      # [SUPUESTO] gasto medio sobre ingreso medio
TASAS = {"duplicado": 0.015, "atipico": 0.005, "faltante": 0.02, "susc_doble": 0.20, "cambio_patron": 0.10}
INGRESO_INEI = 1887.0                           # referencia citada en la v8; verificar en su fuente antes del pitch

COM = {   # comercios FICTICIOS
    "alquiler": ["ArrendadorSur", "InmobiliariaCasaClara", "ArrendadorBarrioAlto"],
    "luz": "Luzandina", "agua": "AguaClara", "internet": "NetHogar", "celular": "MovilFacil",
    "deuda": ["FinanCrece", "CajaPrestaYa"],
    "suscripcion": ["StreamPlus", "MusicaYa", "GimnasioFit"],
    "alimentacion": ["BodegaEsquina", "SuperNova", "MercadoCentral"],
    "transporte": ["TransUrbano", "GrifoCentral", "MovilidadYa"],
    "otros": ["FarmaSalud", "TiendaUtil", "LibreriaEscolar"],
}
PAGADOR = {"conductor": "AppViajes", "vendedora": "VentasDelDia", "tecnico": "ClienteProyecto",
           "comisionista": "ComisionesSur", "asalariado": "EmpleadorSA"}
EST = {  # factor estacional por mes calendario (1..12)
    "conductor": {7: 1.10, 12: 1.25},
    "vendedora": {3: 1.30, 7: 1.15, 12: 1.35},        # campana escolar, Fiestas Patrias, Navidad
    "tecnico": {},
    "comisionista": {12: 1.30},
    "asalariado": {},
}
EST = {a: np.array([t.get(m, 1.0) for m in range(1, 13)]) for a, t in EST.items()}
# Contrato de la seccion 6 (src/contratos/modelos.py): 9 columnas + ingreso_recurrente (opcional) + 4 etiquetas.
# Las suscripciones cobradas dos veces NO llevan etiqueta propia en el CSV: sus transaction_id van en meta.json.
COLUMNAS = ["customer_id", "transaction_id", "fecha_hora", "monto", "moneda", "tipo", "categoria", "comercio",
            "saldo", "ingreso_recurrente", "es_duplicado", "es_atipico", "pago_con_fecha", "arquetipo"]
ETIQUETAS = ["es_duplicado", "es_atipico", "pago_con_fecha", "arquetipo"]


def _sumar_meses(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    return date(d.year + y, m + 1, 1)


def _calendario(meses: int) -> dict:
    fin = _sumar_meses(INICIO, meses)
    n = (fin - INICIO).days
    fechas = [INICIO + timedelta(days=i) for i in range(n)]
    return {
        "n": n, "meses": meses,
        "fechas": np.array(fechas, dtype="datetime64[D]"),
        "mes": np.array([f.month for f in fechas]),
        "dom": np.array([f.day for f in fechas]),
        "dow": np.array([f.weekday() for f in fechas]),
        "feriado": np.array([(f.month, f.day) in FERIADOS for f in fechas]),
        "ultimo": np.array([f.day == calendar.monthrange(f.year, f.month)[1] for f in fechas]),
        "mes_idx": np.array([(f.year - INICIO.year) * 12 + f.month for f in fechas]),
    }


def _ingresos(arq, cal, d0, d1, rng, p, nivel, salario):
    """Lista de (dia_idx, monto, recurrente) para los dias en [d0, d1)."""
    idx = np.arange(d0, d1)
    if len(idx) == 0:
        return []
    mes, dow, fer = cal["mes"][idx], cal["dow"][idx], cal["feriado"][idx]
    est, vol, f = EST[arq][mes - 1], p["vol"], p["factor_ingreso"] * nivel
    out = []
    if arq == "conductor":
        m = rng.normal(75 * f * est * np.where(fer, 0.7, 1.0), 25 * vol)
        trabaja = (dow != 6) & (rng.random(len(idx)) > 0.05) & (m >= 5)
        out = [(int(i), round(float(x), 2), False) for i, x, t in zip(idx, m, trabaja) if t]
    elif arq == "vendedora":
        s = 0.5 * vol
        mu = 55 * f * est * np.where(dow >= 5, 1.4, 1.0)
        m = np.exp(rng.normal(np.log(mu) - s * s / 2, s))
        out = [(int(i), round(float(x), 2), False) for i, x in zip(idx, m)]
    elif arq == "tecnico":
        for mi in np.unique(cal["mes_idx"][idx]):
            dias_m = idx[cal["mes_idx"][idx] == mi]
            k = 0 if rng.random() < 0.15 * vol else int(rng.choice([2, 3, 4]))
            for dia in rng.choice(dias_m, size=min(k, len(dias_m)), replace=False):
                out.append((int(dia), round(float(rng.uniform(300, 1200) * f), 2), False))
    elif arq == "comisionista":
        for i in idx:
            if cal["dow"][i] == 4:
                out.append((int(i), round(float(250 * f * (1 + rng.normal(0, 0.1 * vol))), 2), False))
            if cal["ultimo"][i] and rng.random() < 0.5:
                out.append((int(i), round(float(rng.uniform(200, 1800) * f * EST[arq][cal["mes"][i] - 1]), 2), False))
    else:   # asalariado
        for i in idx:
            if cal["dom"][i] == 15 or cal["ultimo"][i]:
                out.append((int(i), round(float(salario * p["factor_ingreso"] / 2 * (1 + rng.normal(0, 0.03))), 2), True))
            if cal["dom"][i] == 15 and cal["mes"][i] in (7, 12):      # gratificacion [SUPUESTO]
                out.append((int(i), round(float(salario * p["factor_ingreso"]), 2), True))
    return out


def _persona(i, arq0, rng, cambia):
    otros = [a for a in ARQUETIPOS if a != arq0]
    return {
        "cid": f"P{i + 1:04d}", "arq0": arq0, "cambia": bool(cambia),
        "arq1": str(rng.choice(otros)) if cambia else arq0,
        "nivel": float(np.clip(np.exp(rng.normal(0, 0.25)), 0.6, 1.6)),
        "salario": float(rng.uniform(1100, 2200)),
        "dom": {"alquiler": int(rng.integers(1, 6)), "luz": int(rng.integers(8, 13)), "agua": int(rng.integers(10, 16)),
                "internet": int(rng.integers(15, 21)), "celular": int(rng.integers(20, 26))},
        "luz": float(rng.uniform(60, 150)), "agua": float(rng.uniform(30, 60)),
        "internet": float(rng.uniform(70, 120)), "celular": float(rng.uniform(30, 60)),
        "deuda": (int(rng.integers(1, 29)), float(round(rng.uniform(100, 400), -1)), str(rng.choice(COM["deuda"])))
        if rng.random() < 0.4 else None,
        "susc": (int(rng.integers(1, 29)), float(round(rng.uniform(15, 40))), str(rng.choice(COM["suscripcion"])))
        if rng.random() < 0.3 else None,
        "escolar": bool(rng.random() < 0.4), "saldo0": float(rng.uniform(300, 1500)),
        "alq_frac": float(rng.uniform(0.18, 0.38)), "disc_ruido": float(rng.uniform(0.8, 1.2)),
        "alquiler_com": str(rng.choice(COM["alquiler"])),
    }


def _simular_persona(pe, cal, rng, p):
    nd = cal["n"]
    corte = 365 if pe["cambia"] and nd > 365 else nd              # cambio de patron al iniciar el ano 2
    ing = _ingresos(pe["arq0"], cal, 0, corte, rng, p, pe["nivel"], pe["salario"])
    if corte < nd:
        ing += _ingresos(pe["arq1"], cal, corte, nd, rng, p, pe["nivel"], pe["salario"])
    media_mensual = sum(m for _, m, _ in ing) / cal["meses"]
    if pe["arq0"] == pe["arq1"] == "asalariado":                  # el gasto se calibra sobre el sueldo base, no sobre las gratificaciones
        media_mensual = pe["salario"] * p["factor_ingreso"]
    alq =float(np.clip(round(pe["alq_frac"] * media_mensual, -1), 350, 900))
    fijos = (alq + pe["luz"] + pe["agua"] + pe["internet"] + pe["celular"]
             + (pe["deuda"][1] if pe["deuda"] else 0) + (pe["susc"][1] if pe["susc"] else 0))
    mu_dia = max(150.0, GASTO_SOBRE_INGRESO * media_mensual - fijos) / 30 * pe["disc_ruido"]

    def arq_en(d):
        return pe["arq0"] if d < corte else pe["arq1"]

    filas = []   # (dia, hora, monto, tipo, categoria, comercio, recurrente, pago_con_fecha, arquetipo)
    for d, m, rec in ing:
        a = arq_en(d)
        filas.append((d, 20, m, "ingreso", "ingreso", PAGADOR[a], rec, False, a))
    for mi in range(cal["meses"]):
        y = INICIO.year + (INICIO.month - 1 + mi) // 12
        mm = (INICIO.month - 1 + mi) % 12 + 1
        base = (date(y, mm, 1) - INICIO).days
        dm = calendar.monthrange(y, mm)[1]

        def dia(dom):
            return base + min(dom, dm) - 1

        a = arq_en(base)
        filas.append((dia(pe["dom"]["alquiler"]), 9, -alq, "gasto", "alquiler", pe["alquiler_com"], False, True, a))
        filas.append((dia(pe["dom"]["luz"]), 10, -round(pe["luz"] * max(0.5, 1 + rng.normal(0, 0.15)), 2), "gasto", "servicios", COM["luz"], False, True, a))
        filas.append((dia(pe["dom"]["agua"]), 10, -round(pe["agua"] * (1 + rng.normal(0, 0.05)), 2), "gasto", "servicios", COM["agua"], False, True, a))
        filas.append((dia(pe["dom"]["internet"]), 11, -round(pe["internet"], 2), "gasto", "servicios", COM["internet"], False, True, a))
        filas.append((dia(pe["dom"]["celular"]), 11, -round(pe["celular"], 2), "gasto", "servicios", COM["celular"], False, True, a))
        if pe["deuda"]:
            filas.append((dia(pe["deuda"][0]), 12, -pe["deuda"][1], "gasto", "deuda", pe["deuda"][2], False, True, a))
        if pe["susc"]:
            filas.append((dia(pe["susc"][0]), 12, -pe["susc"][1], "gasto", "suscripcion", pe["susc"][2], False, True, a))
        if pe["escolar"] and mm == 3:
            filas.append((dia(int(rng.integers(5, 21))), 13, -round(float(rng.uniform(100, 250)), 2), "gasto", "otros", "LibreriaEscolar", False, False, a))
    est_gasto = np.ones(12)
    est_gasto[6], est_gasto[11] = 1.10, 1.30
    hay = rng.random(nd) < 0.88
    s = 0.6
    montos = np.exp(rng.normal(np.log(mu_dia / 0.88) - s * s / 2, s, nd))
    cats = rng.choice(["alimentacion", "transporte", "otros"], size=nd, p=[0.55, 0.30, 0.15])
    cidx = rng.integers(0, 3, nd)
    horas = rng.integers(8, 22, nd)
    for d in np.flatnonzero(hay):
        m = montos[d] * est_gasto[cal["mes"][d] - 1]
        c = str(cats[d])
        filas.append((int(d), int(horas[d]), -round(float(m), 2), "gasto", c, COM[c][int(cidx[d])], False, False, arq_en(int(d))))
    return filas


def generar(n_personas=400, meses=MESES, semilla=None, perturbado=False, parametros=None):
    """Devuelve (DataFrame con el contrato de datos mas las etiquetas, meta). semilla=None usa cfg['semilla_generador']."""
    parametros = parametros or {}
    semilla = _semilla_config() if semilla is None else semilla
    rng = np.random.default_rng(semilla)
    p = {"vol": 1.5 if perturbado else 1.0, "factor_ingreso": 0.8 if perturbado else 1.0,
         "mezcla": MEZCLA_PERTURBADA if perturbado else MEZCLA_BASE}
    p.update({k: v for k, v in parametros.items() if k in p})
    cal = _calendario(meses)
    equilibrada = parametros.get("asignacion") == "equilibrada"
    filas, personas = [], {}
    for i in range(n_personas):
        arq0 = ARQUETIPOS[i % 5] if equilibrada else str(rng.choice(ARQUETIPOS, p=p["mezcla"]))
        pe = _persona(i, arq0, rng, rng.random() < TASAS["cambio_patron"])
        personas[pe["cid"]] = pe
        filas += [(pe["cid"],) + f for f in _simular_persona(pe, cal, rng, p)]
    df = pd.DataFrame(filas, columns=["customer_id", "dia", "hora", "monto", "tipo", "categoria", "comercio",
                                      "ingreso_recurrente", "pago_con_fecha", "arquetipo"])
    minutos = rng.integers(0, 60, len(df))
    df["fecha_hora"] = (pd.to_datetime(cal["fechas"][df["dia"].values]) + pd.to_timedelta(df["hora"], unit="h")
                        + pd.to_timedelta(minutos, unit="m"))
    df["es_duplicado"] = False
    df["es_atipico"] = False
    df["_susc_doble"] = False                      # interna: va a meta.json, no al CSV
    df["orden"] = np.arange(len(df), dtype=float)
    df = df.drop(columns=["hora"])

    # atipicos: 0.5 % de las filas que NO son pagos con fecha
    cand = np.flatnonzero(~df["pago_con_fecha"].values)
    k = int(len(df) * TASAS["atipico"])
    sel = rng.choice(cand, size=k, replace=False)
    df.loc[df.index[sel], "monto"] = (df["monto"].values[sel] * rng.uniform(5, 10, k)).round(2)
    df.loc[df.index[sel], "es_atipico"] = True

    # suscripcion cobrada dos veces: 10 % de las personas con suscripcion, un mes del ano 2
    nuevas = []
    for cid in sorted(personas):
        pe = personas[cid]
        if not pe["susc"] or rng.random() >= TASAS["susc_doble"]:
            continue
        sus = df[(df["customer_id"] == cid) & (df["categoria"] == "suscripcion")].sort_values("dia")
        if len(sus) < 24:
            continue
        fila = sus.iloc[int(rng.integers(12, 24))].copy()
        fila["dia"] = min(int(fila["dia"]) + int(rng.integers(3, 11)), cal["n"] - 1)
        fila["fecha_hora"] = pd.Timestamp(cal["fechas"][fila["dia"]]) + pd.Timedelta(hours=12, minutes=int(rng.integers(0, 60)))
        fila["pago_con_fecha"] = False
        fila["_susc_doble"] = True
        fila["orden"] = float(len(df) + len(nuevas))
        nuevas.append(fila)
    if nuevas:
        df = pd.concat([df, pd.DataFrame(nuevas)], ignore_index=True)

    # saldo despues de cada movimiento (sin duplicados exactos todavia)
    df = df.sort_values(["customer_id", "fecha_hora", "orden"], kind="mergesort").reset_index(drop=True)
    saldo0 = df["customer_id"].map({c: pe["saldo0"] for c, pe in personas.items()})
    df["saldo"] = (df.groupby("customer_id")["monto"].cumsum() + saldo0).round(2)

    # duplicados exactos: copia con otro transaction_id (misma fecha, monto, comercio, tipo y saldo)
    elegibles = np.flatnonzero(~df["es_atipico"].values & ~df["_susc_doble"].values)
    k = int(len(df) * TASAS["duplicado"])
    copia = df.iloc[rng.choice(elegibles, size=k, replace=False)].copy()
    copia["es_duplicado"] = True
    copia["orden"] = copia["orden"] + 0.5
    df = pd.concat([df, copia], ignore_index=True)

    # datos incompletos: 2 % de las filas pierde categoria o comercio
    k = int(len(df) * TASAS["faltante"])
    sel = rng.choice(len(df), size=k, replace=False)
    mitad = len(sel) // 2
    df.loc[df.index[sel[:mitad]], "categoria"] = ""
    df.loc[df.index[sel[mitad:]], "comercio"] = ""

    df = df.sort_values(["customer_id", "fecha_hora", "orden"], kind="mergesort").reset_index(drop=True)
    df["transaction_id"] = [f"T{i + 1:07d}" for i in range(len(df))]
    df["moneda"] = "PEN"
    df["fecha_hora"] = df["fecha_hora"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["monto"] = df["monto"].round(2)
    susc_ids = df.loc[df["_susc_doble"], "transaction_id"].tolist()
    df = df[COLUMNAS]
    contenido = df.to_csv(index=False).encode("utf-8")
    meta = {"semilla": semilla, "version_generador": "1.0", "perturbado": bool(perturbado), "n_personas": n_personas,
            "meses": meses, "filas": len(df), "hash": hashlib.sha256(contenido).hexdigest()[:16],
            "parametros": {"vol": p["vol"], "factor_ingreso": p["factor_ingreso"], "mezcla": p["mezcla"], "tasas": TASAS,
                           "gasto_sobre_ingreso": GASTO_SOBRE_INGRESO},
            "cambio_patron": sorted(c for c, pe in personas.items() if pe["cambia"]),
            "suscripciones_duplicadas": susc_ids}
    return df, meta


def mes_indice(fecha) -> int:
    """Mes 1 = enero del ano 1."""
    return (fecha.year - INICIO.year) * 12 + fecha.month


def particion(df, semilla=None):
    semilla = _semilla_config() if semilla is None else semilla
    personas = np.array(sorted(df["customer_id"].unique()))
    np.random.default_rng(semilla).shuffle(personas)
    n_test = int(0.2 * len(personas))
    return {"test_personas": sorted(personas[:n_test].tolist()), "train_personas": sorted(personas[n_test:].tolist()),
            "meses_train": (1, 16), "meses_val": (17, 20), "meses_test": (21, 24)}


def muestra_de(df, por_arquetipo=4):
    """Subconjunto exacto del dataset completo: personas SIN cambio de patron, cuatro por arquetipo."""
    estables = df.groupby("customer_id")["arquetipo"].nunique()
    estables = estables[estables == 1].index
    primero = df[df["customer_id"].isin(estables)].groupby("customer_id")["arquetipo"].first()
    ids = []
    for a in ARQUETIPOS:
        ids += sorted(primero[primero == a].index)[:por_arquetipo]
    return df[df["customer_id"].isin(ids)].reset_index(drop=True)


PII = [re.compile(r"(?<!\d)\d{8,9}(?!\d)"), re.compile(r"@")]


def verificar(df, meta=None):
    """Devuelve (lista de fallas, dict de medidas). Una lista vacia significa que pasa todo."""
    fallas, med = [], {}
    if list(df.columns) != COLUMNAS:
        fallas.append("columnas distintas del contrato")
    if df["transaction_id"].is_unique is False:
        fallas.append("transaction_id repetido")
    if (df["moneda"] != "PEN").any():
        fallas.append("moneda distinta de PEN")
    if ((df["tipo"] == "ingreso") & (df["monto"] <= 0)).any() or ((df["tipo"] == "gasto") & (df["monto"] >= 0)).any():
        fallas.append("signo del monto incoherente con el tipo")
    f = pd.to_datetime(df["fecha_hora"])
    med["desde"], med["hasta"] = str(f.min().date()), str(f.max().date())
    meses = ((f.dt.year - INICIO.year) * 12 + f.dt.month)
    for m in (12, 24):
        if meses.eq(m).sum() == 0:
            fallas.append(f"no hay movimientos en el mes {m} (diciembre)")
    for col in ("customer_id", "comercio", "categoria"):
        for pat in PII:
            if df[col].astype(str).str.contains(pat).any():
                fallas.append(f"patron de PII en la columna {col}")
    dup = df[df["es_duplicado"]]
    base = df[~df["es_duplicado"]]
    clave = ["customer_id", "fecha_hora", "monto", "tipo"]
    med["duplicados"] = int(len(dup))
    if len(dup.merge(base[clave].drop_duplicates(), on=clave, how="left", indicator=True).query("_merge == 'left_only'")):
        fallas.append("hay duplicados sin su original")
    # plausibilidad
    limpio = df[~df["es_duplicado"]].copy()
    limpio["mes"] = meses[limpio.index]
    ing = limpio[limpio["tipo"] == "ingreso"].groupby(["customer_id", "mes"])["monto"].sum()
    gas = (-limpio[limpio["tipo"] == "gasto"].groupby(["customer_id", "mes"])["monto"].sum())
    mensual = pd.concat([ing.rename("ing"), gas.rename("gas")], axis=1).fillna(0.0)
    por_persona = mensual.groupby("customer_id")["ing"].sum() / meta_meses(df)
    med["ingreso_mensual_medio"] = round(float(por_persona.mean()), 1)
    med["ingreso_mensual_mediana"] = round(float(por_persona.median()), 1)
    med["razon_vs_inei"] = round(med["ingreso_mensual_medio"] / INGRESO_INEI, 2)
    y2 = mensual[mensual.index.get_level_values("mes") > 12]
    deficit = (y2["gas"] > y2["ing"]).groupby("customer_id").any()
    med["pct_personas_con_mes_en_deficit_ano2"] = round(float(deficit.mean()) * 100, 1)
    arq = df.groupby("customer_id")["arquetipo"].first()
    med["personas"] = int(len(arq))
    med["filas"] = int(len(df))
    por_arq = {}
    for a in ARQUETIPOS:
        ids = arq[arq == a].index
        if len(ids):
            por_arq[a] = {"personas": int(len(ids)), "ingreso_mensual_medio": round(float(por_persona.reindex(ids).mean()), 1),
                          "pct_con_deficit": round(float(deficit.reindex(ids).mean()) * 100, 1)}
    med["por_arquetipo"] = por_arq
    med["atipicos"] = int(df["es_atipico"].sum())
    med["suscripciones_duplicadas"] = len((meta or {}).get("suscripciones_duplicadas", []))
    med["faltantes_categoria"] = int((df["categoria"] == "").sum())
    med["faltantes_comercio"] = int((df["comercio"] == "").sum())
    return fallas, med


def meta_meses(df):
    f = pd.to_datetime(df["fecha_hora"])
    return int((f.dt.year.max() - INICIO.year) * 12 + f.dt.month.max())


def _reporte(med, fallas, meta, meta_p, tiempo):
    l = ["# Reporte de calidad de los datos sinteticos", "",
         f"Generado con semilla {meta['semilla']}, version {meta['version_generador']}, hash {meta['hash']}. Tiempo: {tiempo:.0f} s.", "",
         "## Resultado de las comprobaciones", ""]
    l += [f"- FALLA: {x}" for x in fallas] or ["- Todas las comprobaciones pasan (contrato, ids unicos, signos, diciembre en los meses 12 y 24, duplicados con original, sin patrones de PII)."]
    l += ["", "## Medidas", "", f"- Personas: {med['personas']}; filas: {med['filas']}; periodo: {med['desde']} a {med['hasta']}",
          f"- Ingreso mensual medio por persona: S/{med['ingreso_mensual_medio']} (mediana S/{med['ingreso_mensual_mediana']}); "
          f"razon contra la cifra de referencia del INEI (S/{INGRESO_INEI:.0f}, por verificar en su fuente): {med['razon_vs_inei']}",
          f"- Personas con al menos un mes en deficit en el ano 2: {med['pct_personas_con_mes_en_deficit_ano2']} % "
          "(la encuesta de la SBS citada habla de 85 %, por verificar; es una referencia, no un objetivo duro)",
          f"- Duplicados exactos: {med['duplicados']}; atipicos: {med['atipicos']}; suscripciones cobradas dos veces: {med['suscripciones_duplicadas']}; "
          f"sin categoria: {med['faltantes_categoria']}; sin comercio: {med['faltantes_comercio']}",
          f"- Personas que cambian de arquetipo al iniciar el ano 2: {len(meta['cambio_patron'])}", "", "## Por arquetipo (arquetipo de la primera fila)", "",
          "| Arquetipo | Personas | Ingreso mensual medio | % con mes en deficit |", "|---|---|---|---|"]
    for a, v in med["por_arquetipo"].items():
        l.append(f"| {a} | {v['personas']} | S/{v['ingreso_mensual_medio']} | {v['pct_con_deficit']} % |")
    if meta_p:
        l += ["", f"Generador perturbado (volatilidad x1.5, ingreso x0.8, otra mezcla): semilla {meta_p['semilla']}, hash {meta_p['hash']}, filas {meta_p['filas']}."]
    l += ["", "Todos los parametros son [SUPUESTO]. Los datos son ficticios y demuestran el metodo, no la precision en el mundo real."]
    return "\n".join(l) + "\n"


RAIZ = Path(__file__).resolve().parents[2]


def _semilla_config() -> int:
    """La semilla vive en config/config.yaml (semilla_generador). Si no se puede leer, usa la misma del archivo."""
    try:
        from contratos.config import cargar_config
        return int(cargar_config().semilla_generador)
    except Exception:
        return 20261114


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--semilla", type=int, default=None)
    ap.add_argument("--salida", default=str(RAIZ / "data"))
    a = ap.parse_args(argv)
    a.semilla = a.semilla if a.semilla is not None else _semilla_config()
    out = Path(a.salida)
    (out / "generado").mkdir(parents=True, exist_ok=True)
    (out / "muestra").mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    df, meta = generar(a.n, MESES, a.semilla)
    dfp, meta_p = generar(a.n, MESES, a.semilla + 1000, perturbado=True)
    fallas, med = verificar(df, meta)
    fp, _ = verificar(dfp, meta_p)
    df.to_csv(out / "generado" / "movimientos.csv", index=False)
    dfp.to_csv(out / "generado" / "movimientos_perturbado.csv", index=False)
    (out / "generado" / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "generado" / "meta_perturbado.json").write_text(json.dumps(meta_p, indent=2, ensure_ascii=False), encoding="utf-8")
    mu = muestra_de(df)
    mu.to_csv(out / "muestra" / "movimientos.csv", index=False)
    (out / "muestra" / "meta.json").write_text(json.dumps({"origen": "subconjunto del dataset completo", "personas": sorted(mu["customer_id"].unique().tolist()),
                                                           "semilla": meta["semilla"], "hash_completo": meta["hash"]}, indent=2), encoding="utf-8")
    (out / "REPORTE_DATOS.md").write_text(_reporte(med, fallas + [f"(perturbado) {x}" for x in fp], meta, meta_p, time.time() - t0), encoding="utf-8")
    from datos.chat import generar_preguntas        # preguntas de entrenamiento del asistente (opcion C)
    chat = generar_preguntas(out / "chat", a.semilla)
    print(json.dumps({"chat": chat, "filas": med["filas"], "personas": med["personas"], "fallas": fallas + fp, "hash": meta["hash"],
                      "ingreso_medio": med["ingreso_mensual_medio"], "pct_deficit_ano2": med["pct_personas_con_mes_en_deficit_ano2"],
                      "muestra_filas": len(mu), "segundos": round(time.time() - t0)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
