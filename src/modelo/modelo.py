"""Modelo de cuantiles: 12 LightGBM (horizontes x cuantiles). Dueño: Gino.

Etiquetas de referencia: nunca entran. entrenar() rechaza un DataFrame que las traiga.
Muestras: cada persona cada `paso_muestreo_dias` días; objetivo = ingreso acumulado en los h días siguientes.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import joblib
import lightgbm
import numpy as np
import pandas as pd

from contratos import ETIQUETAS_REFERENCIA, Cuantiles, Pronostico

from .features import FEATURES, construir_features, features_desde_serie, minimo_dias, serie_diaria


def _nombres(cfg) -> dict[str, float]:
    """{'p5': 0.05, 'p20': 0.2, ...} a partir de cfg["cuantiles"]."""
    return {f"p{round(100 * q)}": float(q) for q in cfg["cuantiles"]}


def _armar_muestras(
    movimientos: pd.DataFrame, cfg, desde: pd.Timestamp | None = None
) -> tuple[pd.DataFrame, dict[int, np.ndarray]]:
    """Una fila por persona cada `paso_muestreo_dias` días. Y[h] = ingreso en los h días siguientes.

    `desde`: solo muestras con día de corte >= desde (la historia anterior igual se usa para las variables).
    El último día de corte es tal que los 14 días siguientes caben en los datos recibidos.
    """
    horizontes = [int(h) for h in cfg["horizontes_dias"]]
    paso = int(cfg["modelo"]["paso_muestreo_dias"])
    primero, ultimo = minimo_dias(cfg), max(horizontes)
    filas: list[dict[str, float]] = []
    objetivos: dict[int, list[float]] = {h: [] for h in horizontes}
    for _, h_persona in movimientos.groupby("customer_id", sort=True):
        inicio, serie = serie_diaria(h_persona)
        # t = índice del día de corte: la serie anterior es serie[:t]; el futuro es serie[t:t+h].
        for t in range(primero, len(serie) - ultimo + 1, paso):
            fecha = inicio + pd.Timedelta(days=t)
            if desde is not None and fecha < desde:
                continue
            filas.append(features_desde_serie(serie[:t], fecha, cfg))
            for h in horizontes:
                objetivos[h].append(float(serie[t : t + h].sum()))
    if not filas:
        raise ValueError("no hay muestras: la historia es demasiado corta para entrenar")
    return pd.DataFrame(filas)[FEATURES], {h: np.asarray(v) for h, v in objetivos.items()}


class Modelo:
    def __init__(
        self,
        modelos: dict[tuple[int, str], lightgbm.LGBMRegressor],
        cfg,
        offsets: dict[tuple[int, str], float] | None = None,
    ) -> None:
        self.modelos = modelos
        self.cfg = cfg
        # Desplazamiento aditivo por (horizonte, cuantil), medido SOLO en validación (calibracion.calibrar).
        self.offsets = {k: float((offsets or {}).get(k, 0.0)) for k in modelos}

    def predecir(self, historia: pd.DataFrame, fecha: date) -> Pronostico:
        """Cuantiles ordenados y no negativos. Puede lanzar HistoriaInsuficiente."""
        x = pd.DataFrame([construir_features(historia, fecha, self.cfg)])[FEATURES]
        nombres = list(_nombres(self.cfg))
        por_h: dict[int, Cuantiles] = {}
        for h in (int(h) for h in self.cfg["horizontes_dias"]):
            crudo = [float(self.modelos[(h, n)].predict(x)[0]) + self.offsets[(h, n)] for n in nombres]
            q = np.sort([max(0.0, v) for v in crudo])
            por_h[h] = Cuantiles(**dict(zip(nombres, (float(v) for v in q), strict=True)))
        return Pronostico(por_horizonte=por_h)

    def guardar(self, ruta: str | Path) -> None:
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, ruta)

    @classmethod
    def cargar(cls, ruta: str | Path) -> Modelo:
        return joblib.load(ruta)


def entrenar(movimientos_train: pd.DataFrame, cfg, semilla: int) -> Modelo:
    fuga = [c for c in ETIQUETAS_REFERENCIA if c in movimientos_train.columns]
    if fuga:
        raise ValueError(f"etiquetas de referencia en los datos de entrenamiento (fuga): {fuga}")
    hp = cfg["modelo"]
    X, Y = _armar_muestras(movimientos_train, cfg)
    modelos: dict[tuple[int, str], lightgbm.LGBMRegressor] = {}
    for h, y in Y.items():
        for nombre, tau in _nombres(cfg).items():
            m = lightgbm.LGBMRegressor(
                objective="quantile",
                alpha=tau,
                n_estimators=int(hp["n_estimators"]),
                learning_rate=float(hp["learning_rate"]),
                num_leaves=int(hp["num_leaves"]),
                min_child_samples=int(hp["min_child_samples"]),
                random_state=semilla,
                n_jobs=1,
                deterministic=True,
                force_row_wise=True,
                verbose=-1,
            )
            m.fit(X, y)
            modelos[(h, nombre)] = m
    return Modelo(modelos, cfg)
