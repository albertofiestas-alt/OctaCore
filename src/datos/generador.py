"""Generador sintetico del proyecto (dueno: Rafael). Version 1.1.

Uso:  python -m datos [--n 400] [--semilla N] [--salida data]   (sin --semilla usa semilla_generador de config/base.yaml)
Genera data/generado/movimientos.csv, movimientos_perturbado.csv, verdad_eventos.csv, data/muestra/ y data/REPORTE_DATOS.md.
Los parametros de la v1.1 viven en config/datos.yaml; todos son [SUPUESTO] y se ajustan SOLO con las metricas
de realismo del reporte (medir_realismo), nunca mirando resultados del modelo ni de las reglas.
Los datos son ficticios: ningun nombre, DNI, telefono ni cuenta reales.

Cambios de la v1.1 (DECISIONES.md):
  A. El gasto discrecional reacciona al dinero disponible (_gastar); los pagos con fecha no se recortan.
  B. Horas de ingreso realistas por arquetipo (config/datos.yaml: horas_ingreso).
  C. PII ficticia en ~0.5 % del texto de comercio (_inyectar_pii); la verdad va a verdad_eventos.csv.
Todo lo que ya existia en la v1.0 sale del mismo rng y en el mismo orden: mismas personas, arquetipos,
ingresos y escenarios dificiles. Lo nuevo sale de un segundo rng derivado de la semilla.
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
GASTO_SOBRE_INGRESO = 0.84                      # v1.0; solo se usa para conservar la secuencia del rng
TASAS = {"duplicado": 0.015, "atipico": 0.005, "faltante": 0.02, "susc_doble": 0.20, "cambio_patron": 0.10}
INGRESO_INEI = 1887.0                           # referencia citada en la v8; verificar en su fuente antes del pitch
DEFICIT_SBS = 85.0                              # % con algun mes en deficit; referencia citada, por verificar

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
# Verdad nueva de la v1.1: solo la usa la evaluacion, nunca el modelo, el motor ni la interfaz.
COLUMNAS_VERDAD = ["transaction_id", "customer_id", "evento", "valor"]
# Nombres genericos para correos inventados en un dominio reservado que no existe.
NOMBRES = ["ana", "luis", "rosa", "jorge", "carmen", "pedro", "lucia", "miguel"]
APELLIDOS = ["quispe", "flores", "rojas", "torres", "vargas", "diaz"]


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


def _comportamiento(rng2, g):
    """Parametros de gasto de una persona (v1.1). Salen del rng2 para no mover el rng de la v1.0."""
    def u(rango):
        return float(rng2.uniform(rango[0], rango[1]))
    pe = {"u_propension": u((0.0, 1.0)), "colchon": u(g["colchon_objetivo"]), "prevision": u(g["prevision"]),
          "base_frac": u(g["base_minima"])}
    pe["saldo0_mult"] = u(g["saldo_inicial"])        # el saldo del dia 1 se fija en _gastar con la reserva de ese dia
    return pe


def _simular_persona(pe, cal, rng, p, rng2, prm):
    """Filas de una persona. El gasto discrecional sale con monto NaN: lo fija _gastar() con el saldo del momento."""
    nd = cal["n"]
    corte = 365 if pe["cambia"] and nd > 365 else nd              # cambio de patron al iniciar el ano 2
    pe["corte"] = corte
    ing = _ingresos(pe["arq0"], cal, 0, corte, rng, p, pe["nivel"], pe["salario"])
    if corte < nd:
        ing += _ingresos(pe["arq1"], cal, corte, nd, rng, p, pe["nivel"], pe["salario"])
    media_mensual = sum(m for _, m, _ in ing) / cal["meses"]
    if pe["arq0"] == pe["arq1"] == "asalariado":                  # el gasto se calibra sobre el sueldo base, no sobre las gratificaciones
        media_mensual = pe["salario"] * p["factor_ingreso"]
    alq = float(np.clip(round(pe["alq_frac"] * media_mensual, -1), 350, 900))
    fijos = (alq + pe["luz"] + pe["agua"] + pe["internet"] + pe["celular"]
             + (pe["deuda"][1] if pe["deuda"] else 0) + (pe["susc"][1] if pe["susc"] else 0))
    mu_dia = max(150.0, GASTO_SOBRE_INGRESO * media_mensual - fijos) / 30 * pe["disc_ruido"]
    # Gasto minimo diario (v1.1): una fraccion de lo que queda tras los pagos fijos, con un piso.
    pe["base"] = max(prm["gasto"]["piso_base"], pe["base_frac"] * max(0.0, media_mensual - fijos) / 30)

    def arq_en(d):
        return pe["arq0"] if d < corte else pe["arq1"]

    horas_ing = prm["horas_ingreso"]
    filas = []   # (dia, hora, monto, tipo, categoria, comercio, recurrente, pago_con_fecha, arquetipo, discrecional)
    for d, m, rec in ing:
        a = arq_en(d)
        h = int(rng2.integers(horas_ing[a][0], horas_ing[a][1]))     # cambio B
        filas.append((d, h, m, "ingreso", "ingreso", PAGADOR[a], rec, False, a, False))
    for mi in range(cal["meses"]):
        y = INICIO.year + (INICIO.month - 1 + mi) // 12
        mm = (INICIO.month - 1 + mi) % 12 + 1
        base = (date(y, mm, 1) - INICIO).days
        dm = calendar.monthrange(y, mm)[1]

        def dia(dom):
            return base + min(dom, dm) - 1

        a = arq_en(base)
        filas.append((dia(pe["dom"]["alquiler"]), 9, -alq, "gasto", "alquiler", pe["alquiler_com"], False, True, a, False))
        filas.append((dia(pe["dom"]["luz"]), 10, -round(pe["luz"] * max(0.5, 1 + rng.normal(0, 0.15)), 2), "gasto", "servicios", COM["luz"], False, True, a, False))
        filas.append((dia(pe["dom"]["agua"]), 10, -round(pe["agua"] * (1 + rng.normal(0, 0.05)), 2), "gasto", "servicios", COM["agua"], False, True, a, False))
        filas.append((dia(pe["dom"]["internet"]), 11, -round(pe["internet"], 2), "gasto", "servicios", COM["internet"], False, True, a, False))
        filas.append((dia(pe["dom"]["celular"]), 11, -round(pe["celular"], 2), "gasto", "servicios", COM["celular"], False, True, a, False))
        if pe["deuda"]:
            filas.append((dia(pe["deuda"][0]), 12, -pe["deuda"][1], "gasto", "deuda", pe["deuda"][2], False, True, a, False))
        if pe["susc"]:
            filas.append((dia(pe["susc"][0]), 12, -pe["susc"][1], "gasto", "suscripcion", pe["susc"][2], False, True, a, False))
        if pe["escolar"] and mm == 3:
            filas.append((dia(int(rng.integers(5, 21))), 13, -round(float(rng.uniform(100, 250)), 2), "gasto", "otros", "LibreriaEscolar", False, False, a, False))
    hay = rng.random(nd) < 0.88
    s = 0.6
    rng.normal(np.log(mu_dia / 0.88) - s * s / 2, s, nd)          # montos de la v1.0: se sacan para conservar la secuencia del rng
    cats = rng.choice(["alimentacion", "transporte", "otros"], size=nd, p=[0.55, 0.30, 0.15])
    cidx = rng.integers(0, 3, nd)
    horas = rng.integers(8, 22, nd)
    for d in np.flatnonzero(hay):
        c = str(cats[d])
        filas.append((int(d), int(horas[d]), np.nan, "gasto", c, COM[c][int(cidx[d])], False, False, arq_en(int(d)), True))
    return filas


def _gastar(df, personas, cal, g):
    """Cambio A. Recorre los movimientos de cada persona en orden y fija el gasto discrecional con el saldo del momento:

        gasto = (base * estacional * [recorte si saldo <= 0] + propension[arquetipo] * max(0, saldo - reserva)) * ruido * factor_atipico
        reserva = colchon + prevision * (pagos con fecha + gasto minimo de los proximos dias_prevision dias)

    Los pagos con fecha ya tienen su monto y no se tocan: si no alcanza, el saldo queda negativo.
    Devuelve el df con monto y saldo (saldo despues de cada movimiento).
    """
    monto = df["monto"].to_numpy(dtype=float).copy()
    disc = df["_disc"].to_numpy(dtype=bool)
    factor = df["_factor"].to_numpy(dtype=float)
    ruido = df["_ruido"].to_numpy(dtype=float)
    dia = df["dia"].to_numpy(dtype=np.int64)
    pcf = df["pago_con_fecha"].to_numpy(dtype=bool)
    cids = df["customer_id"].to_numpy()
    est = np.ones(12)
    for m, v in g["estacional"].items():
        est[int(m) - 1] = float(v)
    est_dia = est[cal["mes"] - 1]
    nd, h = cal["n"], int(g["dias_prevision"])
    recorte = float(g["recorte_sin_saldo"])
    saldo = np.empty(len(df))
    inicios = np.flatnonzero(np.r_[True, cids[1:] != cids[:-1]])
    fines = np.r_[inicios[1:], len(df)]
    dias = np.arange(nd)
    for s, e in zip(inicios, fines):
        pe = personas[cids[s]]
        pagos = np.zeros(nd + h + 2)
        sel = np.flatnonzero(pcf[s:e]) + s
        np.add.at(pagos, dia[sel], -monto[sel])
        pagos[nd:] = pagos[nd - 31:nd - 31 + len(pagos) - nd]       # despues del ultimo dia los pagos siguen (sin borde)
        acum = np.concatenate([[0.0], np.cumsum(pagos)])
        base_dia = pe["base"] * est_dia
        reserva = (pe["colchon"] + pe["prevision"] * (acum[dias + 1 + h] - acum[dias + 1] + base_dia * h)).tolist()
        base = base_dia.tolist()
        p0, p1 = (lo + pe["u_propension"] * (hi - lo) for lo, hi in (g["propension"][pe["arq0"]], g["propension"][pe["arq1"]]))
        prop = np.where(dias < pe["corte"], p0, p1).tolist()
        # Arranque sin borde: la persona empieza como en regimen, con lo que su propia regla aparta el dia 1
        # (con colchon fijo el 55 % de los pagos del mes 1 quedaba en negativo frente a ~14 % en regimen).
        sal = pe["saldo0"] = round(reserva[0] * pe["saldo0_mult"], 2)
        m_l, d_l, disc_l = monto[s:e].tolist(), dia[s:e].tolist(), disc[s:e].tolist()
        r_l, f_l = ruido[s:e].tolist(), factor[s:e].tolist()
        for j in range(e - s):
            if disc_l[j]:
                dj = d_l[j]
                b = base[dj] * (recorte if sal <= 0 else 1.0)
                gasto = (b + prop[dj] * max(0.0, sal - reserva[dj])) * r_l[j] * f_l[j]
                m_l[j] = -max(0.5, round(gasto, 2))
            sal += m_l[j]
            saldo[s + j] = sal
        monto[s:e] = m_l
    df["monto"] = monto
    df["saldo"] = np.round(saldo, 2)
    return df


def _inyectar_pii(df, rng2, cfg_pii):
    """Cambio C. Inserta un DNI, telefono o correo FICTICIO en el texto de comercio de ~tasa de las filas.

    Solo en filas que no son pagos con fecha ni suscripciones dobles, con comercio no vacio y fuera de un par
    original-duplicado (asi ningun otro escenario borra o desincroniza la PII). Devuelve las filas de verdad.
    """
    copias = set((df.loc[df["es_duplicado"], "orden"] - 0.5).tolist())
    en_par = df["es_duplicado"].to_numpy(dtype=bool) | df["orden"].isin(copias).to_numpy()
    ok = (~df["pago_con_fecha"].to_numpy(dtype=bool) & ~df["_susc_doble"].to_numpy(dtype=bool)
          & (df["comercio"] != "").to_numpy() & ~en_par)
    cand = np.flatnonzero(ok)
    k = min(int(len(df) * cfg_pii["tasa"]), len(cand))
    sel = np.sort(rng2.choice(cand, size=k, replace=False))
    tipos = list(cfg_pii["tipos"])
    pesos = np.array([float(cfg_pii["tipos"][t]) for t in tipos])
    elegidos = rng2.choice(tipos, size=k, p=pesos / pesos.sum())
    comercio = df["comercio"].to_numpy(dtype=object).copy()
    tid, cid = df["transaction_id"].to_numpy(), df["customer_id"].to_numpy()
    verdad = []
    for i, t in zip(sel, elegidos):
        if t == "dni":
            v = str(int(rng2.integers(10_000_000, 80_000_000)))
            comercio[i] = f"{comercio[i]} DNI {v}"
        elif t == "telefono":
            v = str(int(rng2.integers(900_000_000, 1_000_000_000)))
            comercio[i] = f"{comercio[i]} Yape {v}"
        else:
            v = f"{rng2.choice(NOMBRES)}.{rng2.choice(APELLIDOS)}{int(rng2.integers(10, 100))}@{cfg_pii['dominio_correo']}"
            comercio[i] = f"{comercio[i]} {v}"
        verdad.append((tid[i], cid[i], f"pii_{t}", v))
    df["comercio"] = comercio
    return verdad


def _params_datos():
    """config/datos.yaml (cfg["datos"]). Sin ese archivo el generador falla claro: no hay valores por defecto."""
    from contratos.config import DIR_CONFIG, cargar_config
    try:
        return cargar_config()["datos"]
    except Exception as e:
        raise RuntimeError(f"No se pudo leer {DIR_CONFIG / 'datos.yaml'}: {e}") from e


def generar(n_personas=400, meses=MESES, semilla=None, perturbado=False, parametros=None):
    """Devuelve (DataFrame con el contrato de datos mas las etiquetas, meta). semilla=None usa cfg['semilla_generador']."""
    df, meta, _ = generar_con_verdad(n_personas, meses, semilla, perturbado, parametros)
    return df, meta


def generar_con_verdad(n_personas=400, meses=MESES, semilla=None, perturbado=False, parametros=None):
    """Como generar(), mas la verdad de eventos (PII inyectada, pagos con saldo negativo) para la evaluacion."""
    parametros = parametros or {}
    semilla = _semilla_config() if semilla is None else semilla
    prm = parametros.get("datos") or _params_datos()
    rng = np.random.default_rng(semilla)                # todo lo de la v1.0, en el mismo orden
    rng2 = np.random.default_rng([semilla, 11])         # lo nuevo de la v1.1
    p = {"vol": 1.5 if perturbado else 1.0, "factor_ingreso": 0.8 if perturbado else 1.0,
         "mezcla": MEZCLA_PERTURBADA if perturbado else MEZCLA_BASE}
    p.update({k: v for k, v in parametros.items() if k in p})
    cal = _calendario(meses)
    equilibrada = parametros.get("asignacion") == "equilibrada"
    filas, personas = [], {}
    for i in range(n_personas):
        arq0 = ARQUETIPOS[i % 5] if equilibrada else str(rng.choice(ARQUETIPOS, p=p["mezcla"]))
        pe = _persona(i, arq0, rng, rng.random() < TASAS["cambio_patron"])
        pe.update(_comportamiento(rng2, prm["gasto"]))
        personas[pe["cid"]] = pe
        filas += [(pe["cid"],) + f for f in _simular_persona(pe, cal, rng, p, rng2, prm)]
    df = pd.DataFrame(filas, columns=["customer_id", "dia", "hora", "monto", "tipo", "categoria", "comercio",
                                      "ingreso_recurrente", "pago_con_fecha", "arquetipo", "_disc"])
    minutos = rng.integers(0, 60, len(df))
    df["fecha_hora"] = (pd.to_datetime(cal["fechas"][df["dia"].values]) + pd.to_timedelta(df["hora"], unit="h")
                        + pd.to_timedelta(minutos, unit="m"))
    df["es_duplicado"] = False
    df["es_atipico"] = False
    df["_susc_doble"] = False                      # interna: va a meta.json, no al CSV
    df["orden"] = np.arange(len(df), dtype=float)
    df = df.drop(columns=["hora"])

    # atipicos: 0.5 % de las filas que NO son pagos con fecha. En el gasto discrecional el factor se aplica en _gastar.
    cand = np.flatnonzero(~df["pago_con_fecha"].values)
    k = int(len(df) * TASAS["atipico"])
    sel = rng.choice(cand, size=k, replace=False)
    df["_factor"] = 1.0
    df.loc[df.index[sel], "_factor"] = rng.uniform(5, 10, k)
    fijo = ~df["_disc"].values
    df.loc[fijo, "monto"] = (df.loc[fijo, "monto"] * df.loc[fijo, "_factor"]).round(2)
    df.loc[df.index[sel], "es_atipico"] = True

    # suscripcion cobrada dos veces: 20 % de las personas con suscripcion, un mes del ano 2
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

    # gasto que reacciona al dinero disponible y saldo despues de cada movimiento (sin duplicados exactos todavia)
    sigma = float(prm["gasto"]["ruido_sigma"])
    df["_ruido"] = np.exp(rng2.normal(-sigma * sigma / 2, sigma, len(df)))
    df = df.sort_values(["customer_id", "fecha_hora", "orden"], kind="mergesort").reset_index(drop=True)
    df = _gastar(df, personas, cal, prm["gasto"])

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
    verdad = _inyectar_pii(df, rng2, prm["pii"])
    negativos = df[df["pago_con_fecha"] & ~df["es_duplicado"] & (df["saldo"] < 0)]
    verdad += [(t, c, "pago_con_saldo_negativo", f"{s:.2f}")
               for t, c, s in zip(negativos["transaction_id"], negativos["customer_id"], negativos["saldo"])]
    verdad = pd.DataFrame(verdad, columns=COLUMNAS_VERDAD).sort_values("transaction_id", kind="mergesort").reset_index(drop=True)
    df["moneda"] = "PEN"
    df["fecha_hora"] = df["fecha_hora"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["monto"] = df["monto"].round(2)
    susc_ids = df.loc[df["_susc_doble"], "transaction_id"].tolist()
    df = df[COLUMNAS]
    contenido = df.to_csv(index=False).encode("utf-8")
    pii = verdad[verdad["evento"].str.startswith("pii_")]["evento"].str.removeprefix("pii_").value_counts()
    meta = {"semilla": semilla, "version_generador": str(prm["version_generador"]), "perturbado": bool(perturbado),
            "n_personas": n_personas, "meses": meses, "filas": len(df), "hash": hashlib.sha256(contenido).hexdigest()[:16],
            "hash_verdad": hashlib.sha256(verdad.to_csv(index=False).encode("utf-8")).hexdigest()[:16],
            "parametros": {"vol": p["vol"], "factor_ingreso": p["factor_ingreso"], "mezcla": p["mezcla"], "tasas": TASAS,
                           "datos": json.loads(json.dumps(prm))},
            "cambio_patron": sorted(c for c, pe in personas.items() if pe["cambia"]),
            "suscripciones_duplicadas": susc_ids,
            "pii_inyectada": {t: int(pii.get(t, 0)) for t in prm["pii"]["tipos"]}}
    return df, meta, verdad


def separar_etiquetas(df):
    """(movimientos SIN etiquetas de referencia, etiquetas indexadas por transaction_id).

    Regla anti fuga: lo primero sale al modelo, al motor y a la interfaz; lo segundo solo a eval/.
    """
    etiquetas = df[["transaction_id"] + ETIQUETAS].set_index("transaction_id")
    return df.drop(columns=ETIQUETAS), etiquetas


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


def filas_con_pii(texto: pd.Series) -> pd.Series:
    """True donde el texto tiene un patron de PII (8 o 9 digitos seguidos, o una arroba)."""
    t = texto.fillna("").astype(str)
    return t.str.contains(PII[0]) | t.str.contains(PII[1])


def verificar(df, meta=None, verdad=None):
    """Devuelve (lista de fallas, dict de medidas). Una lista vacia significa que pasa todo.

    PII (v1.1): solo puede aparecer en el texto de comercio de las filas declaradas en verdad_eventos
    (o, sin verdad, en tantas filas como dice meta['pii_inyectada']).
    """
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
    for col in ("customer_id", "categoria"):
        if filas_con_pii(df[col]).any():
            fallas.append(f"patron de PII en la columna {col}")
    con_pii = filas_con_pii(df["comercio"])
    med["pii_detectada"] = int(con_pii.sum())
    if verdad is not None:
        declaradas = set(verdad.loc[verdad["evento"].str.startswith("pii_"), "transaction_id"])
        if set(df.loc[con_pii, "transaction_id"]) != declaradas:
            fallas.append("PII en comercio fuera de las filas declaradas en verdad_eventos (o declarada y ausente)")
    elif meta and "pii_inyectada" in meta:
        if med["pii_detectada"] != sum(meta["pii_inyectada"].values()):
            fallas.append("PII en comercio distinta de la inyectada")
    elif med["pii_detectada"]:
        fallas.append("patron de PII en la columna comercio")
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


# --------------------------------------------------------------------------- #
# Realismo (v1.1). Solo mira los datos; nunca resultados del modelo ni de las reglas.
# --------------------------------------------------------------------------- #

MESES_SALDO = (1, 6, 12, 18, 24)
FRANJAS_HORA = {"0-5 h": (0, 6), "6-9 h": (6, 10), "10-13 h": (10, 14), "14-17 h": (14, 18), "18-21 h": (18, 22), "22-23 h": (22, 24)}


def medir_realismo(df):
    """Metricas de realismo por arquetipo (arquetipo de la primera fila) y total. Ignora los duplicados exactos."""
    d = df[~df["es_duplicado"].astype(bool)].copy()
    f = pd.to_datetime(d["fecha_hora"])
    d["mes"] = (f.dt.year - INICIO.year) * 12 + f.dt.month
    d["fecha"] = f.dt.normalize()
    d["semana"] = (f.dt.normalize() - pd.Timestamp(INICIO)).dt.days // 7
    d["hora"] = f.dt.hour
    gasto, pcf = d["tipo"] == "gasto", d["pago_con_fecha"].astype(bool)
    n_dias = int((d["fecha"].max() - d["fecha"].min()).days) + 1
    semanas = np.arange(n_dias // 7)                               # solo semanas completas
    arq = d.groupby("customer_id")["arquetipo"].first()

    fin_mes = d.groupby(["customer_id", "mes"])["saldo"].last().unstack()
    fin_dia = d.groupby(["customer_id", "fecha"])["saldo"].last()
    ing = d[d["tipo"] == "ingreso"]
    ing_dia = (ing.groupby("customer_id")["monto"].sum() / n_dias).reindex(arq.index).fillna(0.0)
    dias_ing = fin_dia.groupby("customer_id").median() / ing_dia.where(ing_dia > 0)
    disc = d[gasto & ~pcf & (d["categoria"] != "suscripcion")]
    si = ing.groupby(["customer_id", "semana"])["monto"].sum().unstack(fill_value=0.0).reindex(index=arq.index, columns=semanas, fill_value=0.0)
    sg = (-disc.groupby(["customer_id", "semana"])["monto"].sum()).unstack(fill_value=0.0).reindex(index=arq.index, columns=semanas, fill_value=0.0)
    corr = pd.Series({c: (np.corrcoef(si.loc[c], sg.loc[c])[0, 1] if si.loc[c].std() > 0 and sg.loc[c].std() > 0 else np.nan)
                      for c in arq.index})
    pagos = d[pcf]
    neg_persona = (pagos["saldo"] < 0).groupby(pagos["customer_id"]).any().reindex(arq.index).fillna(False)
    neg_pagos = (pagos["saldo"] < 0).groupby(pagos["customer_id"]).mean().reindex(arq.index)
    mensual = pd.concat([ing.groupby(["customer_id", "mes"])["monto"].sum().rename("ing"),
                         (-d[gasto].groupby(["customer_id", "mes"])["monto"].sum()).rename("gas")], axis=1).fillna(0.0)
    ing_mes = mensual.groupby("customer_id")["ing"].sum().reindex(arq.index).fillna(0.0) / max(1, int(d["mes"].max()))
    y2 = mensual[mensual.index.get_level_values("mes") > 12]
    deficit = (y2["gas"] > y2["ing"]).groupby("customer_id").any().reindex(arq.index).fillna(False)
    neg_filas = (d["saldo"] < 0).groupby(d["customer_id"]).mean().reindex(arq.index)
    a_las_20 = (ing["hora"] == 20).groupby(ing["customer_id"]).mean().reindex(arq.index)
    hora_med = ing.groupby("customer_id")["hora"].median().reindex(arq.index)

    def r(x, n=1):
        return None if pd.isna(x) else round(float(x), n)

    def resumen(ids):
        return {"personas": int(len(ids)),
                "saldo_mediano_fin_mes": {f"m{m}": (r(fin_mes.loc[ids, m].median(), 0) if m in fin_mes.columns else None)
                                          for m in MESES_SALDO},
                "saldo_en_dias_de_ingreso": r(dias_ing.reindex(ids).median()),
                "corr_semanal_ingreso_gasto": r(corr.reindex(ids).median(), 2),
                "pct_personas_saldo_negativo_en_pago": r(neg_persona.reindex(ids).mean() * 100),
                "pct_pagos_con_saldo_negativo": r(neg_pagos.reindex(ids).mean() * 100),
                "pct_filas_saldo_negativo": r(neg_filas.reindex(ids).mean() * 100),
                "ingreso_mensual_medio": r(ing_mes.reindex(ids).mean(), 0),
                "pct_con_mes_en_deficit_ano2": r(deficit.reindex(ids).mean() * 100),
                "pct_ingresos_a_las_20h": r(a_las_20.reindex(ids).mean() * 100),
                "hora_mediana_ingreso": r(hora_med.reindex(ids).median(), 0)}

    horas = {k: r(((ing["hora"] >= a) & (ing["hora"] < b)).mean() * 100) for k, (a, b) in FRANJAS_HORA.items()}
    return {"total": resumen(arq.index), "por_arquetipo": {a: resumen(arq[arq == a].index) for a in ARQUETIPOS if (arq == a).any()},
            "horas_ingreso": horas, "pii_detectada": int(filas_con_pii(df["comercio"]).sum())}


def _fmt(x, pre="", suf="", dec=None):
    if x is None:
        return "s/d"
    dec = (0 if float(x).is_integer() else 1) if dec is None else dec
    return f"{pre}{x:,.{dec}f}{suf}"


def _reporte(med, real, real_mu, antes, fallas, meta, meta_p, tiempo):
    t, ta = real["total"], (antes or {}).get("completo", {}).get("total")
    l = ["# Reporte de calidad de los datos sinteticos", "",
         f"Generado con semilla {meta['semilla']}, version {meta['version_generador']}, hash {meta['hash']} "
         f"(verdad de eventos: hash {meta['hash_verdad']}). Tiempo: {tiempo:.0f} s.", "",
         "## Resultado de las comprobaciones", ""]
    l += [f"- FALLA: {x}" for x in fallas] or ["- Todas las comprobaciones pasan (contrato, ids unicos, signos, diciembre en los meses 12 y 24, "
                                               "duplicados con original, PII solo en las filas declaradas en verdad_eventos.csv)."]
    l += ["", "## Antes (v1.0) y despues (v1.1): las 400 personas", "",
          "El usuario objetivo vive al dia y sin colchon: el saldo debe rondar valores bajos, subir al cobrar y bajar antes del "
          "siguiente ingreso, sin tendencia creciente. Las referencias externas son orientativas, no objetivos.", "",
          "| Medida | v1.0 | v1.1 | Que se espera |", "|---|---|---|---|"]

    def fila(nombre, clave, esperado, pre="", suf="", sub=None, dec=None):
        a = (ta or {}).get(clave) if sub is None else ((ta or {}).get(clave) or {}).get(sub)
        b = t.get(clave) if sub is None else t[clave][sub]
        l.append(f"| {nombre} | {_fmt(a, pre, suf, dec) if ta else 's/d'} | {_fmt(b, pre, suf, dec)} | {esperado} |")

    for m in MESES_SALDO:
        fila(f"Saldo mediano a fin del mes {m}", "saldo_mediano_fin_mes", "sin tendencia creciente" if m == 24 else "", "S/", sub=f"m{m}")
    fila("Saldo mediano en dias de ingreso tipico", "saldo_en_dias_de_ingreso", "bajo (pocos dias)")
    fila("Correlacion semanal ingreso vs gasto discrecional (mediana por persona)", "corr_semanal_ingreso_gasto", "claramente positiva", dec=2)
    fila("% de personas con saldo negativo al menos una vez tras un pago con fecha", "pct_personas_saldo_negativo_en_pago",
         "mayor que 0: es el evento que el producto intenta evitar", suf=" %")
    fila("% de pagos con fecha que dejan el saldo negativo (media por persona)", "pct_pagos_con_saldo_negativo", "", suf=" %")
    fila("% de filas con saldo negativo (media por persona)", "pct_filas_saldo_negativo", "", suf=" %")
    fila("Ingreso mensual medio", "ingreso_mensual_medio", f"referencia INEI S/{INGRESO_INEI:,.0f} [por verificar en su fuente]", "S/")
    fila("% de personas con algun mes en deficit (ano 2)", "pct_con_mes_en_deficit_ano2", f"referencia SBS {DEFICIT_SBS:.0f} % [por verificar en su fuente]", suf=" %")
    fila("% de ingresos a las 20:00", "pct_ingresos_a_las_20h", "bajo: horas repartidas segun el arquetipo", suf=" %")
    pa = (antes or {}).get("completo", {}).get("pii_detectada")
    l.append(f"| Filas con PII en comercio | {pa if pa is not None else 's/d'} | {real['pii_detectada']} | ~0.5 % de las filas, todas ficticias |")

    if real_mu is not None:
        mu_a = (antes or {}).get("muestra", {}).get("total", {}).get("saldo_mediano_fin_mes", {})
        mu_b = real_mu["total"]["saldo_mediano_fin_mes"]
        l += ["", "Muestra publicada (las mismas 20 personas): saldo mediano a fin de mes, v1.0 -> v1.1: "
              + "; ".join(f"mes {m}: {_fmt(mu_a.get(f'm{m}'), 'S/')} -> {_fmt(mu_b[f'm{m}'], 'S/')}" for m in MESES_SALDO) + "."]

    l += ["", "## Por arquetipo (v1.1; entre parentesis la v1.0)", "",
          "| Arquetipo | Personas | Saldo mediano fin de mes 1 / 6 / 12 / 18 / 24 | Dias de ingreso | Corr. ingreso-gasto | "
          "% personas con saldo negativo tras un pago | Ingreso mensual medio | % con mes en deficit (ano 2) | Hora mediana del ingreso |",
          "|---|---|---|---|---|---|---|---|---|"]
    pa_arq = (antes or {}).get("completo", {}).get("por_arquetipo", {})
    for a, v in real["por_arquetipo"].items():
        w = pa_arq.get(a, {})

        def c(clave, pre="", suf="", dec=None):
            return f"{_fmt(v[clave], pre, suf, dec)} ({_fmt(w.get(clave), pre, suf, dec)})" if w else _fmt(v[clave], pre, suf, dec)
        saldos = " / ".join(_fmt(v["saldo_mediano_fin_mes"][f"m{m}"], "S/") for m in MESES_SALDO)
        saldos_a = " / ".join(_fmt(w.get("saldo_mediano_fin_mes", {}).get(f"m{m}"), "S/") for m in MESES_SALDO) if w else ""
        l.append(f"| {a} | {v['personas']} | {saldos}" + (f" ({saldos_a})" if w else "") + f" | {c('saldo_en_dias_de_ingreso')} | "
                 f"{c('corr_semanal_ingreso_gasto', dec=2)} |{c('pct_personas_saldo_negativo_en_pago', suf=' %')} | "
                 f"{c('ingreso_mensual_medio', 'S/')} | {c('pct_con_mes_en_deficit_ano2', suf=' %')} | {c('hora_mediana_ingreso', suf=' h')} |")

    ha = (antes or {}).get("completo", {}).get("horas_ingreso", {})
    l += ["", "## Hora de los ingresos (% de los ingresos)", "", "| Franja | v1.0 | v1.1 |", "|---|---|---|"]
    l += [f"| {k} | {_fmt(ha.get(k), suf=' %')} | {_fmt(v, suf=' %')} |" for k, v in real["horas_ingreso"].items()]
    l += ["", "Ventas y viajes repartidos en el dia; sueldos en la manana; comisiones y honorarios en horario de oficina "
          "(config/datos.yaml: horas_ingreso)."]

    pii = meta["pii_inyectada"]
    l += ["", "## PII ficticia inyectada", "",
          f"- {sum(pii.values())} filas ({sum(pii.values()) / meta['filas'] * 100:.2f} %): " + ", ".join(f"{k} {v}" for k, v in pii.items()) + ".",
          "- Va dentro del texto de comercio, nunca en pagos con fecha ni en pares original-duplicado. DNI y telefono son "
          "numeros al azar sin vinculo con nadie; los correos usan un dominio reservado que no existe.",
          "- La verdad (que fila y que patron) esta en data/generado/verdad_eventos.csv, junto con los pagos con fecha que dejan "
          "el saldo negativo. Ese archivo solo lo usa la evaluacion."]

    l += ["", "## Escenarios dificiles y medidas generales", "",
          f"- Personas: {med['personas']}; filas: {med['filas']}; periodo: {med['desde']} a {med['hasta']}",
          f"- Ingreso mensual medio por persona: S/{med['ingreso_mensual_medio']} (mediana S/{med['ingreso_mensual_mediana']}); "
          f"razon contra la cifra de referencia del INEI (S/{INGRESO_INEI:.0f}, por verificar en su fuente): {med['razon_vs_inei']}",
          f"- Duplicados exactos: {med['duplicados']}; atipicos: {med['atipicos']}; suscripciones cobradas dos veces: {med['suscripciones_duplicadas']}; "
          f"sin categoria: {med['faltantes_categoria']}; sin comercio: {med['faltantes_comercio']}",
          f"- Personas que cambian de arquetipo al iniciar el ano 2: {len(meta['cambio_patron'])}"]
    if meta_p:
        l += ["", f"Generador perturbado (volatilidad x1.5, ingreso x0.8, otra mezcla): semilla {meta_p['semilla']}, hash {meta_p['hash']}, filas {meta_p['filas']}."]
    l += ["", "## Como se calibro", "",
          "Todos los parametros nuevos estan en config/datos.yaml y son [SUPUESTO]. Se ajustaron solo con las medidas de este reporte "
          "(saldo, dias de ingreso, correlacion, horas, referencias INEI y SBS); nunca mirando resultados del modelo ni de las reglas, "
          "porque eso seria fabricar evidencia a favor del modelo.", "",
          "Los datos son ficticios y demuestran el metodo, no la precision en el mundo real."]
    return "\n".join(l) + "\n"


RAIZ = Path(__file__).resolve().parents[2]
MEDIDAS_V1_0 = RAIZ / "data" / "medidas_v1_0.json"     # foto fija de la v1.0 para la tabla antes/despues


def _semilla_config() -> int:
    """La semilla vive en config/base.yaml (semilla_generador). Si no se puede leer, falla: nunca hay semilla por defecto."""
    from contratos.config import RUTA_CONFIG, cargar_config
    try:
        return int(cargar_config()["semilla_generador"])
    except Exception as e:
        raise RuntimeError(
            f"No se pudo leer semilla_generador de {RUTA_CONFIG}: {e}. "
            "Corrige la configuración o pasa la semilla explícita (generar(..., semilla=...))."
        ) from e


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
    df, meta, verdad = generar_con_verdad(a.n, MESES, a.semilla)
    dfp, meta_p, verdad_p = generar_con_verdad(a.n, MESES, a.semilla + 1000, perturbado=True)
    fallas, med = verificar(df, meta, verdad)
    fp, _ = verificar(dfp, meta_p, verdad_p)
    df.to_csv(out / "generado" / "movimientos.csv", index=False)
    dfp.to_csv(out / "generado" / "movimientos_perturbado.csv", index=False)
    verdad.to_csv(out / "generado" / "verdad_eventos.csv", index=False)
    verdad_p.to_csv(out / "generado" / "verdad_eventos_perturbado.csv", index=False)
    (out / "generado" / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "generado" / "meta_perturbado.json").write_text(json.dumps(meta_p, indent=2, ensure_ascii=False), encoding="utf-8")
    part = particion(df, a.semilla) | {"semilla": a.semilla, "hash_datos": meta["hash"]}
    (out / "generado" / "particion.json").write_text(json.dumps(part, indent=2, ensure_ascii=False), encoding="utf-8")
    mu = muestra_de(df)
    ids_mu = sorted(mu["customer_id"].unique().tolist())
    mu.to_csv(out / "muestra" / "movimientos.csv", index=False)
    verdad[verdad["customer_id"].isin(ids_mu)].to_csv(out / "muestra" / "verdad_eventos.csv", index=False)
    (out / "muestra" / "meta.json").write_text(json.dumps({"origen": "subconjunto del dataset completo", "personas": ids_mu,
                                                           "semilla": meta["semilla"], "version_generador": meta["version_generador"],
                                                           "hash_completo": meta["hash"]}, indent=2), encoding="utf-8")
    real, real_mu = medir_realismo(df), medir_realismo(mu)
    antes = json.loads(MEDIDAS_V1_0.read_text(encoding="utf-8")) if MEDIDAS_V1_0.exists() else None
    (out / "REPORTE_DATOS.md").write_text(_reporte(med, real, real_mu, antes, fallas + [f"(perturbado) {x}" for x in fp],
                                                   meta, meta_p, time.time() - t0), encoding="utf-8")
    from datos.chat import generar_preguntas        # preguntas de entrenamiento del asistente (opcion C)
    chat = generar_preguntas(out / "chat", a.semilla)
    print(json.dumps({"chat": chat, "filas": med["filas"], "personas": med["personas"], "fallas": fallas + fp, "hash": meta["hash"],
                      "ingreso_medio": med["ingreso_mensual_medio"], "pct_deficit_ano2": med["pct_personas_con_mes_en_deficit_ano2"],
                      "realismo": real["total"], "pii": meta["pii_inyectada"],
                      "muestra_filas": len(mu), "segundos": round(time.time() - t0)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
