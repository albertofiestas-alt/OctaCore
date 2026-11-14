"""Escalones 1 y 2: regla ingenua y regla robusta (misma forma que el modelo).

Dueño: Rafael. Esqueleto V0 (Anexo E): reemplaza el cuerpo, NO la firma.

Convención de la serie diaria (la misma que usa servicio.consultar):
    - `historia` son movimientos limpios de UNA persona con fecha_hora < fecha.
    - Solo cuentan las filas con tipo == "ingreso"; si existe `atipico_detectado`
      (lo agrega la ingesta) esas filas se excluyen.
    - La serie va día a día hasta fecha - 1 y lleva 0 los días sin ingreso.
    - Días de historia = (fecha - fecha del primer movimiento de cualquier tipo).

Regla 1 (ingenua):
    base = (suma de los últimos 90 días / 3) / 30      [ingreso diario medio]
    P_q(h) = base * h * FACTORES_REGLA1[q]

Regla 2 (robusta):
    con menos de DIAS_MINIMOS_REGLA2 días de historia devuelve la regla 1 (y lo anota en el log);
    si no, percentiles empíricos de las sumas móviles de h días dentro de las últimas
    cfg["ventana_regla_robusta_semanas"] semanas, ordenados y no negativos.

Las versiones `*_lote` hacen lo mismo para una matriz persona x día y las usa el arnés eval/.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from contratos import NOMBRES_CUANTILES, Cuantiles, Pronostico

if TYPE_CHECKING:
    from contratos import Config

log = logging.getLogger(__name__)

# Parámetros que NO están en config/base.yaml. [SUPUESTO] fijados antes de medir (plan de Rafael).
DIAS_VENTANA_REGLA1 = 90                 # la regla ingenua mira los últimos 90 días
MESES_VENTANA_REGLA1 = 3                 # 90 días = 3 meses
DIAS_POR_MES = 30
DIAS_MINIMOS_REGLA2 = 63                 # con menos historia, la regla 2 cae en la regla 1
FACTORES_REGLA1: dict[float, float] = {0.05: 0.5, 0.20: 0.75, 0.50: 1.0, 0.80: 1.0}
DECIMALES = 2


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #


def _parametros(cfg: Config) -> tuple[tuple[int, ...], tuple[float, ...], int]:
    horizontes = tuple(int(h) for h in cfg["horizontes_dias"])
    cuantiles = tuple(float(q) for q in cfg["cuantiles"])
    ventana = int(cfg["ventana_regla_robusta_semanas"]) * 7
    faltan = [q for q in cuantiles if q not in FACTORES_REGLA1]
    if faltan:
        raise ValueError(f"FACTORES_REGLA1 no define el factor de los cuantiles {faltan}")
    if len(cuantiles) != len(NOMBRES_CUANTILES):
        raise ValueError(f"se esperan {len(NOMBRES_CUANTILES)} cuantiles; cfg trae {cuantiles}")
    return horizontes, cuantiles, ventana


def _ordenar(valores: np.ndarray) -> np.ndarray:
    """No negativos y ordenados a lo largo del último eje (p5 <= p20 <= p50 <= p80)."""
    return np.maximum.accumulate(np.maximum(valores, 0.0), axis=-1)


def _a_pronostico(valores: np.ndarray, horizontes: tuple[int, ...]) -> Pronostico:
    """valores: (H, Q) -> Pronostico."""
    valores = np.round(_ordenar(valores), DECIMALES)
    return Pronostico(
        por_horizonte={
            h: Cuantiles(**{n: float(v) for n, v in zip(NOMBRES_CUANTILES, valores[i])})
            for i, h in enumerate(horizontes)
        }
    )


def serie_diaria(historia: pd.DataFrame, fecha: date) -> tuple[np.ndarray, int]:
    """(ingreso diario desde el primer movimiento hasta fecha - 1, días de historia).

    Se ignoran filas con fecha_hora >= fecha aunque lleguen (sin mirar el futuro).
    """
    corte = pd.Timestamp(fecha).normalize()
    if historia is None or len(historia) == 0:
        return np.zeros(0), 0
    fechas = pd.to_datetime(historia["fecha_hora"])
    previas = fechas < corte
    if not previas.any():
        return np.zeros(0), 0
    inicio = fechas[previas].min().normalize()
    dias = int((corte - inicio).days)

    es_ingreso = (historia["tipo"] == "ingreso") & previas
    if "atipico_detectado" in historia.columns:
        es_ingreso &= ~historia["atipico_detectado"].fillna(False).astype(bool)
    serie = np.zeros(dias)
    if es_ingreso.any():
        idx = (fechas[es_ingreso].dt.normalize() - inicio).dt.days.to_numpy()
        np.add.at(serie, idx, historia.loc[es_ingreso, "monto"].to_numpy(dtype=float))
    return serie, dias


# --------------------------------------------------------------------------- #
# Núcleo por lotes: matriz persona x día
# --------------------------------------------------------------------------- #


def _acumulado(ingresos: np.ndarray) -> np.ndarray:
    """C[:, t] = suma de los días < t. Forma (P, D + 1)."""
    ingresos = np.asarray(ingresos, dtype=float)
    return np.concatenate([np.zeros((ingresos.shape[0], 1)), np.cumsum(ingresos, axis=1)], axis=1)


def regla1_lote(ingresos: np.ndarray, cfg: Config) -> np.ndarray:
    """Regla 1 para cada persona y cada día de corte t (usa solo los días < t).

    ingresos: matriz (P, D) de ingreso diario (0 si no hubo ingreso).
    Devuelve (P, D, H, Q) en el orden de cfg["horizontes_dias"] y cfg["cuantiles"].
    """
    horizontes, cuantiles, _ = _parametros(cfg)
    c = _acumulado(ingresos)
    _, d1 = c.shape
    t = np.arange(d1 - 1)
    suma90 = c[:, t] - c[:, np.maximum(t - DIAS_VENTANA_REGLA1, 0)]
    base = suma90 / MESES_VENTANA_REGLA1 / DIAS_POR_MES                     # (P, D)
    h = np.array(horizontes, dtype=float)
    f = np.array([FACTORES_REGLA1[q] for q in cuantiles])
    return _ordenar(base[:, :, None, None] * h[None, None, :, None] * f[None, None, None, :])


def regla2_lote(ingresos: np.ndarray, primer_dia: np.ndarray, cfg: Config) -> np.ndarray:
    """Regla 2 para cada persona y cada día de corte t (usa solo los días < t).

    ingresos: matriz (P, D). primer_dia: (P,) índice del primer movimiento (de cualquier tipo)
    de cada persona; los días de historia en t son t - primer_dia.
    Devuelve (P, D, H, Q). Donde la historia es corta usa la regla 1.
    """
    horizontes, cuantiles, ventana = _parametros(cfg)
    ingresos = np.asarray(ingresos, dtype=float)
    p, d = ingresos.shape
    primer_dia = np.asarray(primer_dia, dtype=int).reshape(p)
    salida = regla1_lote(ingresos, cfg)
    if d <= ventana:
        return salida
    c = _acumulado(ingresos)
    qs = np.array(cuantiles)
    t_validos = np.arange(ventana, d)                       # cortes con 56 días previos completos
    for i, h in enumerate(horizontes):
        # R[:, j] = suma de los días j .. j+h-1
        r = c[:, h:] - c[:, :-h]                            # (P, D - h + 1)
        n_ventanas = ventana - h + 1
        vistas = sliding_window_view(r, n_ventanas, axis=1)  # (P, D - h + 1 - n + 1, n)
        # Para el corte t, las ventanas empiezan en t - ventana ... t - h  -> fila t - ventana
        bloque = vistas[:, t_validos - ventana, :]          # (P, T, n)
        pct = np.quantile(bloque, qs, axis=-1)              # (Q, P, T)
        salida[:, t_validos, i, :] = np.moveaxis(pct, 0, -1)
    dias_historia = np.arange(d)[None, :] - primer_dia[:, None]
    corta = dias_historia < DIAS_MINIMOS_REGLA2
    r1 = regla1_lote(ingresos, cfg)
    salida = np.where(corta[:, :, None, None], r1, salida)
    return _ordenar(salida)


# --------------------------------------------------------------------------- #
# API del Anexo A (firmas fijas)
# --------------------------------------------------------------------------- #


def regla1(historia: pd.DataFrame, fecha: date, cfg: Config) -> Pronostico:
    """Ingreso promedio mensual / 30 * h."""
    horizontes, _, _ = _parametros(cfg)
    serie, _ = serie_diaria(historia, fecha)
    # regla1_lote(t) usa días < t: se agrega un día ficticio al final para que el corte
    # "fecha" (t = len(serie)) sea la última fila. Sin historia, el pronóstico es 0.
    valores = regla1_lote(np.append(serie, 0.0)[None, :], cfg)[0, -1]
    return _a_pronostico(valores, horizontes)


def regla2(historia: pd.DataFrame, fecha: date, cfg: Config) -> Pronostico:
    """Percentiles empíricos del ingreso acumulado en ventanas de h días de las últimas 8 semanas."""
    horizontes, _, _ = _parametros(cfg)
    serie, dias = serie_diaria(historia, fecha)
    if dias < DIAS_MINIMOS_REGLA2:
        log.info(
            "regla2 -> regla1 (respaldo): %d días de historia < %d", dias, DIAS_MINIMOS_REGLA2
        )
        return regla1(historia, fecha, cfg)
    # Se agrega un día ficticio al final para que el corte t = len(serie) sea la fila -1.
    valores = regla2_lote(np.append(serie, 0.0)[None, :], np.array([0]), cfg)[0, -1]
    return _a_pronostico(valores, horizontes)


__all__ = [
    "DIAS_MINIMOS_REGLA2",
    "DIAS_VENTANA_REGLA1",
    "FACTORES_REGLA1",
    "regla1",
    "regla1_lote",
    "regla2",
    "regla2_lote",
    "serie_diaria",
]
