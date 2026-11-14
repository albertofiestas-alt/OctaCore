"""Variables del modelo de cuantiles (dueño: Gino).

Solo se usan datos ANTERIORES a `fecha` (estrictamente: fecha_hora < fecha a las 00:00).
La serie diaria de ingresos es propia de este módulo (no se importa de reglas/ ni de otras carpetas).

Decisión de entrada (la ingesta aún no existe): `historia` es el CSV del generador SIN las 4 columnas
de etiqueta (es_duplicado, es_atipico, pago_con_fecha, arquetipo) y con fecha_hora parseada;
contratos.validar_historia lo valida. Las etiquetas nunca llegan aquí.
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np
import pandas as pd

FEATURES: list[str] = [
    "dia_semana",
    "dia_mes",
    "mes_sin",
    "mes_cos",
    "ingreso_28d",
    "ingreso_56d",
    "dias_desde_ultimo_ingreso",
    "n_ingresos_28d",
    "mediana_ingreso_dia_28d",
]


class HistoriaInsuficiente(Exception):
    """Menos de cfg["umbral_historia_semanas"] semanas de historia: el servicio usa la regla 2."""


def serie_diaria(movimientos: pd.DataFrame, hasta: pd.Timestamp | None = None) -> tuple[pd.Timestamp, np.ndarray]:
    """Ingreso por día de UNA persona: (primer día, arreglo diario).

    Va desde el primer movimiento (de cualquier tipo) hasta el último día con datos, o hasta el día
    anterior a `hasta` si se da (sin incluirlo). Si no hay datos devuelve un arreglo vacío.
    """
    if hasta is not None:
        movimientos = movimientos[movimientos["fecha_hora"] < hasta]
    if movimientos.empty:
        return pd.Timestamp.min, np.zeros(0)
    dias = movimientos["fecha_hora"].dt.normalize()
    inicio = dias.min()
    fin = hasta - pd.Timedelta(days=1) if hasta is not None else dias.max()
    ingresos = movimientos[(movimientos["tipo"] == "ingreso") & (movimientos["monto"] > 0)]
    por_dia = ingresos.groupby(ingresos["fecha_hora"].dt.normalize())["monto"].sum()
    completo = por_dia.reindex(pd.date_range(inicio, fin, freq="D"), fill_value=0.0)
    return inicio, completo.to_numpy(dtype=float)


def _dias_desde_ultimo(serie: np.ndarray) -> int:
    positivos = np.flatnonzero(serie > 0)
    return len(serie) if positivos.size == 0 else int(len(serie) - 1 - positivos[-1])


def features_desde_serie(serie: np.ndarray, fecha: date | pd.Timestamp, cfg) -> dict[str, float]:
    """Variables en `fecha` a partir de la serie diaria que termina el día anterior."""
    corta = int(cfg["modelo"]["ventana_corta_dias"])
    larga = int(cfg["modelo"]["ventana_larga_dias"])
    ultimos = serie[-corta:]
    angulo = 2 * math.pi * fecha.month / 12
    return {
        "dia_semana": fecha.weekday(),
        "dia_mes": fecha.day,
        "mes_sin": math.sin(angulo),
        "mes_cos": math.cos(angulo),
        "ingreso_28d": float(ultimos.sum()),
        "ingreso_56d": float(serie[-larga:].sum()),
        "dias_desde_ultimo_ingreso": _dias_desde_ultimo(serie),
        "n_ingresos_28d": int((ultimos > 0).sum()),
        "mediana_ingreso_dia_28d": float(np.median(ultimos)),
    }


def minimo_dias(cfg) -> int:
    """Días de historia mínimos para construir variables."""
    return 7 * int(cfg["umbral_historia_semanas"])


def construir_features(historia: pd.DataFrame, fecha: date, cfg) -> dict[str, float]:
    """Variables del modelo para UNA persona en `fecha`. Lanza HistoriaInsuficiente si falta historia."""
    corte = pd.Timestamp(fecha).normalize()
    _, serie = serie_diaria(historia, hasta=corte)
    if len(serie) < minimo_dias(cfg):
        raise HistoriaInsuficiente(f"{len(serie)} días de historia; se necesitan {minimo_dias(cfg)}")
    return features_desde_serie(serie, corte, cfg)
