"""Diagnóstico (solo lectura): por qué los asalariados caen en rojo en la serie diaria. Reproduce docs/diagnostico_asalariados_rojo.md.

Uso:  PYTHONPATH=src python eval/_diagnostico_asalariados.py [data/generado/generado/movimientos.csv] [n_procesos=8]

Reconstruye día a día (2026, meses 13-24) a los asalariados con el simulador de RESPALDO, una vez gastando el número de hoy
(factor 1.0, como la serie entregada) y otra sin gastar (factor 0.0), y registra el pago que limita, la cobertura con P5 y
P50 y el pronóstico de regla2 por horizonte. Imprime el resumen y 5 casos concretos. No escribe nada en el repo.
"""

from __future__ import annotations

import calendar
import importlib.util
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

RESPALDO = Path(__file__).resolve().parent / "_simulador_respaldo.py"


def _cargar_sim():
    spec = importlib.util.spec_from_file_location("sim_respaldo", RESPALDO)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _prox_clave(pagos, fecha, ventana=14):
    """[(días hasta el pago, monto, categoría)] de los pagos inferidos que vencen en la ventana."""
    salida = []
    for off in range(ventana + 1):
        dia = fecha + pd.Timedelta(days=off)
        ultimo = calendar.monthrange(dia.year, dia.month)[1]
        salida += [(off, p["monto"], p["clave"][1]) for p in pagos if dia.day == min(p["dia_mes"], ultimo)]
    return salida


def _traza(cid, g, factor):
    warnings.simplefilter("ignore")
    from contratos import ETIQUETAS_REFERENCIA, cargar_config

    sim, cfg = _cargar_sim(), cargar_config()
    etiquetas = g.set_index("transaction_id")[list(ETIQUETAS_REFERENCIA)]
    historia = g.drop(columns=list(ETIQUETAS_REFERENCIA)).sort_values("fecha_hora", kind="stable").reset_index(drop=True)
    ingresos, pagos_reales = sim._flujos_reales(historia, etiquetas)
    hist = historia.drop_duplicates(subset=["customer_id", "fecha_hora", "monto", "comercio", "tipo"]).reset_index(drop=True)
    inicio = sim._inicio_mes(13)
    dias = pd.date_range(inicio, sim._inicio_mes(25) - pd.Timedelta(days=1))
    saldo = float(hist[hist.fecha_hora < inicio].saldo.iloc[-1])
    fechas = hist.fecha_hora.to_numpy()
    filas, inferidos, mes = [], [], None
    for t in dias:
        if (t.year, t.month) != mes:
            mes = (t.year, t.month)
            inferidos = sim._pagos_inferidos(hist, pd.Timestamp(t.year, t.month, 1))
        k = int(np.searchsorted(fechas, t.to_datetime64(), side="left"))
        pron = sim._pronosticar("regla2", hist.iloc[:k], t, None, cfg)
        pc = _prox_clave(inferidos, t)
        prox = [(d, m) for d, m, _ in pc]
        sem = sim._semaforo_ventana(saldo, prox, pron)
        numero = sim._numero_hoy(saldo, prox, pron, "p20", 0.0)
        lim = None
        for d, m, cat in pc:  # el pago con peor cobertura con P50
            acum = sum(mm for dd, mm in prox if dd <= d)
            c50 = saldo + sim._ingreso_conservador(pron, d, "p50") - acum
            c5 = saldo + sim._ingreso_conservador(pron, d, "p5") - acum
            if lim is None or c50 < lim[0]:
                lim = (c50, c5, d, m, cat, acum)
        ing_antes = sum(ingresos.get(t + pd.Timedelta(days=o), 0.0) for o in range(lim[2] + 1)) if lim else 0.0
        h = pron.por_horizonte
        filas.append({
            "cid": cid, "fecha": t, "factor": factor, "saldo": saldo, "sem": sem, "numero": numero,
            **{f"p{q}_h{hh}": getattr(h[hh], f"p{q}") for hh in (3, 7, 14) for q in (5, 50)},
            "lim_cob50": lim[0] if lim else np.nan, "lim_cob5": lim[1] if lim else np.nan,
            "lim_d": lim[2] if lim else np.nan, "lim_monto": lim[3] if lim else np.nan,
            "lim_cat": lim[4] if lim else None, "lim_acum": lim[5] if lim else np.nan, "ing_real_antes": ing_antes,
        })
        s_dia = saldo + ingresos.get(t, 0.0) - numero * factor
        for monto in pagos_reales.get(t, []):
            s_dia -= monto
        saldo = s_dia
    return pd.DataFrame(filas)


def _resumen(d: pd.DataFrame) -> None:
    for f, g in d.groupby("factor"):
        r = g.groupby("cid")["sem"].agg(rojo=lambda x: (x == "rojo").sum(), verde=lambda x: (x == "verde").sum())
        print(f"factor {f}: rojo mediana {r.rojo.median()} (min {r.rojo.min()} max {r.rojo.max()}), "
              f"verde mediana {r.verde.median()} de 365")
    a = d[d.factor == 1.0]
    mes = lambda x: x.assign(mes=x.fecha.dt.month).groupby("mes").saldo.median().round(0).to_dict()  # noqa: E731
    print("saldo mediano por mes, gastando el número:", mes(a))
    print("saldo mediano por mes, sin gastar:", mes(d[d.factor == 0.0]))
    rojo = a[a["sem"] == "rojo"]
    falta = -rojo.lim_cob50
    print(f"días rojo {len(rojo)} de {len(a)} ({len(rojo) / len(a):.1%}); saldo >= 0 en {(rojo.saldo >= 0).mean():.1%}")
    print("pago que limita:", rojo.lim_cat.value_counts(normalize=True).round(3).to_dict(),
          "| días hasta el pago (p25/p50/p75):", rojo.lim_d.quantile([.25, .5, .75]).tolist())
    print(f"falta con P50: mediana {falta.median():.0f} (p25 {falta.quantile(.25):.0f}, p75 {falta.quantile(.75):.0f}); "
          f"pagos acumulados mediana {rojo.lim_acum.median():.0f} vs saldo mediano {rojo.saldo.median():.0f}")
    print(f"rojos con p50_h3 == 0: {(rojo.p50_h3 == 0).mean():.1%}; con p50_h7 == 0: {(rojo.p50_h7 == 0).mean():.1%}; "
          f"con p5_h14 == 0: {(rojo.p5_h14 == 0).mean():.1%}; con el pago a < 14 días: {(rojo.lim_d < 14).mean():.1%}")
    print(f"rojos con sueldo real antes del pago limitante: {(rojo.ing_real_antes > 0).mean():.1%}; "
          f"se evitan contando ese sueldo: {(rojo.ing_real_antes >= falta).mean():.1%}")


def _casos(d: pd.DataFrame) -> None:
    a, cero = d[d.factor == 1.0], d[d.factor == 0.0].set_index(["cid", "fecha"])
    r = a.groupby("cid")["sem"].apply(lambda x: (x == "rojo").sum()).sort_values()
    for c in [r.index[1], r.index[len(r) // 4], r.index[len(r) // 2], r.index[-8], r.index[-1]]:
        g = a[a.cid == c]
        rojo = g[g["sem"] == "rojo"]
        f = rojo.iloc[len(rojo) // 2]
        sin_gasto = cero.loc[(c, f.fecha)]
        print(f"{c}: {len(rojo)} días rojo; {f.fecha.date()}: saldo {f.saldo:.0f}, limita {f.lim_cat} {f.lim_monto:.0f} a "
              f"{int(f.lim_d)} días (acumulado {f.lim_acum:.0f}), falta con P50 {-f.lim_cob50:.0f}; h3 {f.p5_h3:.0f}/{f.p50_h3:.0f}, "
              f"h7 {f.p5_h7:.0f}/{f.p50_h7:.0f}, h14 {f.p5_h14:.0f}/{f.p50_h14:.0f}; sueldo antes del pago {f.ing_real_antes:.0f}; "
              f"sin gastar el número ese día: saldo {sin_gasto.saldo:.0f}, {sin_gasto['sem']}")


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/generado/generado/movimientos.csv"
    procesos = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    df = pd.read_csv(ruta, parse_dates=["fecha_hora"])
    asalariados = sorted(df[df.arquetipo == "asalariado"].customer_id.unique())
    grupos = {c: df[df.customer_id == c] for c in asalariados}
    trazas = Parallel(n_jobs=procesos)(delayed(_traza)(c, grupos[c], f) for c in asalariados for f in (1.0, 0.0))
    resultado = pd.concat(trazas)
    print(f"asalariados: {len(asalariados)}")
    _resumen(resultado)
    _casos(resultado)
