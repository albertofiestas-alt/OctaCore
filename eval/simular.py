"""Simulación día a día de la decisión sobre los meses de prueba (21 a 24). Dueño: Rafael. OFICIAL.

Usa solo piezas oficiales:
    - ingesta.cargar          limpia la historia (duplicados, PII, atipico_detectado) e infiere los pagos con fecha;
    - ingesta.proximos_pagos  pagos conocidos de los próximos cfg["ventana_dias"] días;
    - reglas.regla1 / regla2 y modelo.predecir   el pronóstico (escalera modelo -> regla2 si HistoriaInsuficiente);
    - motor.decidir           el número de hoy, con cfg["cuantil_conservador"] = cuantil.
La lógica de la simulación sigue la del simulador de respaldo de Gino (eval/_simulador_respaldo.py), que sirvió de
referencia; aquí no se reimplementa ni la fórmula del número ni la inferencia de pagos.

Para cada día t de los meses de prueba:
    1) sin mirar el futuro: la ingesta corre el primer día de cada mes sobre lo anterior a ese mes (así sus atípicos y
       pagos inferidos no ven el resto del mes); los movimientos del mes hasta t − 1 se agregan sin duplicados exactos
       y con la PII enmascarada por la misma ingesta;
    2) pronóstico del método con esa historia; motor.decidir con el saldo SIMULADO → numero_hoy;
    3) la persona gasta exactamente numero_hoy [SUPUESTO del plan]: el gasto discrecional observado se reemplaza;
    4) saldo += ingresos reales del día − gasto − otros gastos no discrecionales reales − pagos con fecha reales;
       un pago queda descubierto si, al pagarlo, el saldo del día es menor que cero.

Gasto discrecional (el que se reemplaza): gasto que NO es pago con fecha y NO es de categoría suscripción, la misma
definición que datos.generador.medir_realismo. Las etiquetas (es_duplicado, pago_con_fecha) se usan SOLO para medir
los flujos reales, nunca en lo que ve el método.

Métodos: regla1, regla2, modelo (con `cuantil` en cfg["cuantiles"]) y las referencias gasto_cero, gasto_fijo
(cuantil=None) que pide eval/frontera.py. gasto_observado (cuantil=None) repite el gasto discrecional real: sirve
para validar el simulador contra data/generado/verdad_eventos.csv.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

METODOS = ("regla1", "regla2", "modelo")
REFERENCIAS = ("gasto_cero", "gasto_fijo", "gasto_observado")
MESES_PRUEBA = (21, 24)                 # igual que datos.particion()["meses_test"]
MESES_GASTO_FIJO = 6                    # la referencia gasto_fijo promedia los 6 meses previos a la prueba [SUPUESTO]
HORIZONTE_CALIBRACION = 14              # calibración del P20 sobre el ingreso acumulado a 14 días
CLAVE_DUPLICADO = ["customer_id", "fecha_hora", "monto", "comercio", "tipo"]
INICIO_ANIO = 2025                      # mes 1 = enero de 2025 (datos.generador.INICIO)

_CACHE: dict[Any, Any] = {}


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #


def _inicio_mes(n: int) -> pd.Timestamp:
    return pd.Timestamp(INICIO_ANIO + (n - 1) // 12, (n - 1) % 12 + 1, 1)


def _validar(metodo: str, cuantil) -> None:
    if metodo in METODOS:
        if cuantil is None:
            raise ValueError(f"el método {metodo!r} necesita un cuantil")
    elif metodo not in REFERENCIAS:
        raise ValueError(f"método desconocido: {metodo!r}; válidos: {METODOS + REFERENCIAS}")


def _colchon(cfg) -> float:
    prereg = cfg["preregistro"] if "preregistro" in cfg else {}
    valor = prereg.get("colchon") if prereg else None
    if valor is None:
        valor = cfg.get("colchon")
    return float(valor or 0.0)


def _cfg_con_cuantil(cfg, cuantil: float):
    return cfg.con(cuantil_conservador=float(cuantil)) if hasattr(cfg, "con") else {**cfg, "cuantil_conservador": float(cuantil)}


# --------------------------------------------------------------------------- #
# Preparación por persona (flujos reales e ingesta mensual)
# --------------------------------------------------------------------------- #


class _Persona:
    """Lo que no depende del método: flujos reales del período de prueba e ingesta por mes (con caché)."""

    def __init__(self, historia_completa: pd.DataFrame, etiquetas: pd.DataFrame, cfg) -> None:
        h = historia_completa.copy()
        h["fecha_hora"] = pd.to_datetime(h["fecha_hora"])
        h = h.sort_values(["fecha_hora", "transaction_id"], kind="mergesort").reset_index(drop=True)
        self.cid = str(h["customer_id"].iloc[0])
        self.cfg = cfg
        self.crudo = h                                   # lo que vería la ingesta (sin etiquetas)
        self.fechas = h["fecha_hora"].to_numpy()

        lab = etiquetas.reindex(h["transaction_id"]).reset_index(drop=True)
        real = ~lab["es_duplicado"].fillna(False).astype(bool).to_numpy()
        pcf = lab["pago_con_fecha"].fillna(False).astype(bool).to_numpy()
        dia = h["fecha_hora"].dt.normalize()
        ingreso = real & (h["tipo"] == "ingreso").to_numpy()
        gasto = real & (h["tipo"] == "gasto").to_numpy()
        suscripcion = (h["categoria"].fillna("") == "suscripcion").to_numpy()
        pago = gasto & pcf
        discrecional = gasto & ~pcf & ~suscripcion
        otro_fijo = gasto & ~pcf & suscripcion            # p. ej. la segunda cobranza de una suscripción doble

        self.ingresos = h.loc[ingreso, "monto"].groupby(dia[ingreso]).sum()
        self.discrecional = (-h.loc[discrecional, "monto"]).groupby(dia[discrecional]).sum()
        self.otro_fijo = (-h.loc[otro_fijo, "monto"]).groupby(dia[otro_fijo]).sum()
        self.pagos = {d: list(zip(g["transaction_id"], -g["monto"])) for d, g in h[pago].groupby(dia[pago])}

        self.inicio = _inicio_mes(MESES_PRUEBA[0])
        fin = min(_inicio_mes(MESES_PRUEBA[1] + 1) - pd.Timedelta(days=1), dia.max())
        self.dias = pd.date_range(self.inicio, fin, freq="D")
        if len(self.dias) == 0:
            raise ValueError(f"{self.cid}: no tiene movimientos en los meses de prueba")
        previos = h[(h["fecha_hora"] < self.inicio) & real]
        self.saldo0 = float(previos["saldo"].iloc[-1]) if len(previos) else 0.0
        desde = self.inicio - pd.DateOffset(months=MESES_GASTO_FIJO)
        dias_previos = max((self.inicio - desde).days, 1)
        ventana = self.discrecional[(self.discrecional.index >= desde) & (self.discrecional.index < self.inicio)]
        self.gasto_fijo = float(ventana.sum() / dias_previos)
        self._mes: dict[pd.Timestamp, tuple[pd.DataFrame, list[dict]]] = {}
        self._dia: dict[pd.Timestamp, tuple[pd.DataFrame, list, int]] = {}

    def ingesta_del_mes(self, inicio_mes: pd.Timestamp) -> tuple[pd.DataFrame, list[dict]]:
        """(movimientos limpios anteriores al mes, pagos inferidos con ellos), con ingesta.cargar."""
        if inicio_mes not in self._mes:
            import ingesta

            k = int(np.searchsorted(self.fechas, inicio_mes.to_datetime64(), side="left"))
            limpio, _reporte, pagos = ingesta.cargar(self.crudo.iloc[:k].reset_index(drop=True), self.cfg)
            limpio = limpio.copy()
            limpio["fecha_hora"] = pd.to_datetime(limpio["fecha_hora"])
            self._mes[inicio_mes] = (limpio, pagos)
        return self._mes[inicio_mes]

    def historia(self, t: pd.Timestamp) -> tuple[pd.DataFrame, list[dict]]:
        """Movimientos con fecha_hora < t: limpios hasta el inicio del mes + los del mes hasta t − 1."""
        import ingesta

        inicio_mes = pd.Timestamp(t.year, t.month, 1)
        limpio, pagos = self.ingesta_del_mes(inicio_mes)
        a = int(np.searchsorted(self.fechas, inicio_mes.to_datetime64(), side="left"))
        b = int(np.searchsorted(self.fechas, t.to_datetime64(), side="left"))
        if b <= a:
            return limpio, pagos
        nuevos = self.crudo.iloc[a:b].drop_duplicates(subset=CLAVE_DUPLICADO)
        nuevos, _ = ingesta.enmascarar_pii(nuevos, self.cfg)
        nuevos = nuevos.assign(atipico_detectado=False)
        return pd.concat([limpio, nuevos[limpio.columns]], ignore_index=True), pagos

    def contexto(self, t: pd.Timestamp) -> tuple[pd.DataFrame, list, int]:
        """(historia < t, pagos conocidos de la ventana, semanas de historia): no depende del método ni del cuantil."""
        if t not in self._dia:
            import ingesta

            hist, pagos = self.historia(t)
            proximos = ingesta.proximos_pagos(pagos, self.cid, t.date(), int(self.cfg["ventana_dias"]))
            self._dia[t] = (hist, proximos, ingesta.semanas_historia(hist, self.cid, t.date()))
        return self._dia[t]

    def ingreso_real(self, desde: pd.Timestamp, dias: int) -> float:
        hasta = desde + pd.Timedelta(days=dias)
        s = self.ingresos
        return float(s[(s.index >= desde) & (s.index < hasta)].sum())


def _persona(historia_completa, etiquetas, cfg) -> _Persona:
    if historia_completa is None or etiquetas is None or cfg is None or len(historia_completa) == 0:
        raise ValueError("simular_persona necesita historia_completa, etiquetas y cfg")
    clave = ("persona", str(historia_completa["customer_id"].iloc[0]), len(historia_completa),
             str(historia_completa["transaction_id"].iloc[-1]), id(cfg))
    if clave not in _CACHE:
        _CACHE[clave] = _Persona(historia_completa, etiquetas, cfg)
    return _CACHE[clave]


# --------------------------------------------------------------------------- #
# Pronóstico y decisión
# --------------------------------------------------------------------------- #


def _pronosticar(p: _Persona, metodo: str, t: pd.Timestamp, modelo):
    clave = ("pron", p.cid, metodo, t, id(modelo), id(p))
    if clave not in _CACHE:
        hist, _, _ = p.contexto(t)
        if metodo == "modelo":
            if modelo is None:
                raise ValueError("el método 'modelo' necesita un modelo entrenado")
            from modelo import HistoriaInsuficiente

            try:
                pron = modelo.predecir(hist, t.date())
            except HistoriaInsuficiente:
                import reglas

                pron = reglas.regla2(hist, t.date(), p.cfg)       # la escalera del servicio: modelo -> regla2
        else:
            import reglas

            pron = getattr(reglas, metodo)(hist, t.date(), p.cfg)
        _CACHE[clave] = pron
    return _CACHE[clave]


def _decidir(p: _Persona, t: pd.Timestamp, saldo: float, pron, cfg_q):
    import motor
    from contratos import EstadoPersona

    _, proximos, semanas = p.contexto(t)
    estado = EstadoPersona(
        customer_id=p.cid,
        fecha_corte=t.date(),
        saldo=round(float(saldo), 2),
        pagos=proximos,
        colchon=_colchon(p.cfg),
        semanas_historia=semanas,
    )
    return motor.decidir(estado, pron, cfg_q)


# --------------------------------------------------------------------------- #
# API (contrato de eval/frontera.py)
# --------------------------------------------------------------------------- #


def simular_persona(historia_completa, etiquetas, cfg, metodo: str, cuantil: float, modelo=None) -> dict:
    """{"pagos_descubiertos": n, "pagos_totales": m, "gasto_permitido_dia": promedio} más customer_id, metodo,
    cuantil, calibracion_p20, motor_usado y eventos (uno por pago real: fecha, pago, monto, saldo, numero, descubierto)."""
    _validar(metodo, cuantil)
    p = _persona(historia_completa, etiquetas, cfg)
    cfg_q = _cfg_con_cuantil(cfg, cuantil) if metodo in METODOS else None

    saldo = p.saldo0
    descubiertos = total = 0
    gastos: list[float] = []
    eventos: list[dict] = []
    aciertos_p20: list[bool] = []
    ultimo_dia = p.dias[-1]
    for t in p.dias:
        numero = None
        if metodo == "gasto_cero":
            gasto = 0.0
        elif metodo == "gasto_fijo":
            gasto = p.gasto_fijo
        elif metodo == "gasto_observado":
            gasto = float(p.discrecional.get(t, 0.0))
        else:
            pron = _pronosticar(p, metodo, t, modelo)
            numero = float(_decidir(p, t, saldo, pron, cfg_q).numero_hoy)
            gasto = numero
            if t + pd.Timedelta(days=HORIZONTE_CALIBRACION - 1) <= ultimo_dia:
                p20 = pron.por_horizonte[HORIZONTE_CALIBRACION].p20
                aciertos_p20.append(p.ingreso_real(t, HORIZONTE_CALIBRACION) >= p20)
        gastos.append(gasto)
        saldo_dia = saldo + float(p.ingresos.get(t, 0.0)) - gasto - float(p.otro_fijo.get(t, 0.0))
        for tid, monto in p.pagos.get(t, []):
            total += 1
            saldo_dia -= float(monto)
            falla = saldo_dia < 0
            descubiertos += int(falla)
            eventos.append({"fecha": t.date().isoformat(), "pago": str(tid), "monto": round(float(monto), 2),
                            "saldo": round(saldo_dia, 2), "numero": numero, "descubierto": bool(falla)})
        saldo = saldo_dia

    return {
        "customer_id": p.cid,
        "metodo": metodo,
        "cuantil": None if cuantil is None else float(cuantil),
        "pagos_descubiertos": int(descubiertos),
        "pagos_totales": int(total),
        "gasto_permitido_dia": float(np.mean(gastos)),
        "calibracion_p20": float(np.mean(aciertos_p20)) if aciertos_p20 else math.nan,
        "motor_usado": "motor.decidir" if metodo in METODOS else None,
        "eventos": eventos,
    }


def limpiar_cache() -> None:
    _CACHE.clear()
