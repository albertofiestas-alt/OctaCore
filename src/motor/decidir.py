"""Motor de decisión: número de hoy por fecha de pago, semáforo, confianza y propuesta. Dueño: Sebastián.

Plan de Sebastián, secciones 5 y 6. Función pura: no lee archivos, ni la hora, ni usa
aleatoriedad, y no cambia sus entradas (los contratos son inmutables). Todo parámetro sale de cfg.

Redondeo: numero_hoy hacia ABAJO (floor) y faltante hacia ARRIBA (ceil). Nunca a favor del gasto.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from contratos import Decision, DecisionPago, EstadoPersona, PagoConFecha, Propuesta, Pronostico
from motor import plantillas

HORIZONTE_MAXIMO = 14
TIPO_PROPUESTA = "apartar_p5"
# Cuantil (redondeado a 2 decimales) -> atributo de Cuantiles.
ATRIBUTO: dict[float, str] = {0.05: "p5", 0.2: "p20", 0.5: "p50", 0.8: "p80"}
P5, P50 = 0.05, 0.5


# --------------------------------------------------------------------------- #
# Piezas de la fórmula
# --------------------------------------------------------------------------- #


def _atributo(cuantil: float) -> str:
    clave = round(float(cuantil), 2)
    if clave not in ATRIBUTO:
        raise ValueError(f"cuantil no soportado: {cuantil} (usa 0.05, 0.2, 0.5 u 0.8)")
    return ATRIBUTO[clave]


def _horizontes(cfg: Any) -> tuple[int, ...]:
    try:
        return tuple(cfg["horizontes_dias"])
    except (KeyError, TypeError):
        return (3, 7, 14)


def _h_para_dia(d: int, horizontes: tuple[int, ...]) -> int:
    """Mayor horizonte h con h <= min(d, 14); 0 si ninguno."""
    candidatos = [h for h in horizontes if h <= min(d, HORIZONTE_MAXIMO)]
    return max(candidatos) if candidatos else 0


def ingreso_conservador(
    pronostico: Pronostico, d: int, cuantil: float, horizontes: tuple[int, ...] = (3, 7, 14)
) -> float:
    """Ingreso acumulado del cuantil en el mayor horizonte <= d (0 si d < 3). Subestima a propósito."""
    h = _h_para_dia(d, tuple(horizontes))
    if h == 0:
        return 0.0
    return float(getattr(pronostico.por_horizonte[h], _atributo(cuantil)))


def _pagos_hasta(estado: EstadoPersona, d: int) -> float:
    return float(sum(p.monto for p in estado.pagos if p.dia <= d))


def numerador(
    estado: EstadoPersona,
    pronostico: Pronostico,
    d: int,
    cuantil: float,
    cfg: Any,
    con_colchon: bool = True,
) -> float:
    """saldo + ingreso(d, q) - pagos con día <= d - colchón (si con_colchon)."""
    colchon = estado.colchon if con_colchon else 0.0
    return (
        estado.saldo
        + ingreso_conservador(pronostico, d, cuantil, _horizontes(cfg))
        - _pagos_hasta(estado, d)
        - colchon
    )


def permitido(estado: EstadoPersona, pronostico: Pronostico, d: int, cuantil: float, cfg: Any) -> float:
    """Gasto diario que todavía cubre los pagos hasta el día d (divisor max(d, 1))."""
    return numerador(estado, pronostico, d, cuantil, cfg) / max(d, 1)


def puntos_de_control(estado: EstadoPersona) -> list[int]:
    """Cada día distinto con un pago, más el día 14."""
    return sorted({p.dia for p in estado.pagos} | {HORIZONTE_MAXIMO})


def _minimo(estado: EstadoPersona, pronostico: Pronostico, cuantil: float, cfg: Any) -> tuple[int, float]:
    """(día que limita, permitido mínimo). Empate: el día menor."""
    perm = {d: permitido(estado, pronostico, d, cuantil, cfg) for d in puntos_de_control(estado)}
    d_lim = min(perm, key=lambda d: (perm[d], d))
    return d_lim, perm[d_lim]


def _color(cobertura: Callable[[float], float]) -> str:
    if cobertura(P5) >= 0:
        return "verde"
    if cobertura(P50) >= 0:
        return "ambar"
    return "rojo"


def semaforo_con_gasto(estado: EstadoPersona, pronostico: Pronostico, d: int, gasto: float, cfg: Any) -> str:
    """Semáforo del día d si se gastan `gasto` soles por día (sin colchón)."""

    def cobertura(q: float) -> float:
        return numerador(estado, pronostico, d, q, cfg, con_colchon=False) - gasto * max(d, 1)

    return _color(cobertura)


def semaforo(estado: EstadoPersona, pronostico: Pronostico, d: int, cfg: Any) -> str:
    """Semáforo del pago del día d: verde si se cubre con P5, ámbar si con P50, rojo si no (sin colchón)."""
    return semaforo_con_gasto(estado, pronostico, d, 0.0, cfg)


def _ancho_relativo(pronostico: Pronostico) -> float:
    c = pronostico.por_horizonte[HORIZONTE_MAXIMO]
    return (c.p80 - c.p5) / max(c.p50, 1.0)


def _historia_suficiente(estado: EstadoPersona, cfg: Any) -> bool:
    return estado.semanas_historia >= cfg["umbral_historia_semanas"]


def confianza(estado: EstadoPersona, pronostico: Pronostico, cfg: Any) -> str:
    """alta / media / baja según el ancho relativo a 14 días y las semanas de historia."""
    umbrales = cfg["motor"]["umbrales_confianza"]
    ancho = _ancho_relativo(pronostico)
    if not _historia_suficiente(estado, cfg) or ancho > umbrales["ancho_bajo"]:
        return "baja"
    if ancho < umbrales["ancho_alto"]:
        return "alta"
    return "media"


def _pago_del_dia(estado: EstadoPersona, d: int) -> PagoConFecha | None:
    """El pago de mayor monto que vence el día d (empate: el primero de la lista)."""
    del_dia = [p for p in estado.pagos if p.dia == d]
    return max(del_dia, key=lambda p: p.monto) if del_dia else None


def _pago_limite(estado: EstadoPersona, d: int) -> PagoConFecha | None:
    """Pago que se nombra para el punto d. Si es el 14 sin pago, el último pago <= 14."""
    pago = _pago_del_dia(estado, d)
    if pago is not None:
        return pago
    anteriores = [p.dia for p in estado.pagos if p.dia <= HORIZONTE_MAXIMO]
    return _pago_del_dia(estado, max(anteriores)) if anteriores else None


# --------------------------------------------------------------------------- #
# Propuesta
# --------------------------------------------------------------------------- #


def proponer(
    estado: EstadoPersona,
    pronostico: Pronostico,
    cfg: Any,
    numero_hoy: int,
    confianza_decision: str,
    texto: Callable[[dict[str, Any]], str] | None = None,
) -> list[Propuesta]:
    """Una propuesta 'apartar_p5' si 0 <= g5 < numero_hoy y hay historia suficiente; si no, []."""
    if texto is None:

        def texto(datos: dict[str, Any]) -> str:
            return plantillas.texto_propuesta(TIPO_PROPUESTA, datos)

    if not _historia_suficiente(estado, cfg):
        return []
    q5 = cfg["motor"]["cuantil_propuesta"]
    d_lim5, g5 = _minimo(estado, pronostico, q5, cfg)
    g20 = int(numero_hoy)
    if not (0 <= g5 < g20):
        return []
    pago = _pago_limite(estado, d_lim5)
    if pago is None:
        return []
    g5_entero = int(math.floor(g5))

    # Verificación obligatoria: gastando floor(g5) por día, ningún punto queda descubierto en P5.
    for d in puntos_de_control(estado):
        assert numerador(estado, pronostico, d, q5, cfg) - g5_entero * max(d, 1) >= -1e-9, (
            f"propuesta no cubre el punto {d} en P5"
        )

    apartar = g20 - g5_entero
    datos = {
        "g5": g5_entero,
        "numero_hoy": g20,
        "apartar": apartar,
        "pago_id": pago.pago_id,
        "dia": pago.dia,
        "monto": pago.monto,
        "categoria": pago.categoria,
    }
    return [
        Propuesta(
            propuesta_id=f"{estado.customer_id}:{estado.fecha_corte.isoformat()}:{TIPO_PROPUESTA}:{pago.pago_id}",
            texto=texto(datos),
            monto=apartar,
            pago_id=pago.pago_id,
            antes={
                "numero_hoy": g20,
                "semaforo_pago_limite": semaforo_con_gasto(estado, pronostico, pago.dia, g20, cfg),
            },
            despues={
                "numero_hoy": g5_entero,
                "semaforo_pago_limite": semaforo_con_gasto(estado, pronostico, pago.dia, g5_entero, cfg),
            },
            confianza=confianza_decision,
        )
    ]


# --------------------------------------------------------------------------- #
# Desglose y evidencia
# --------------------------------------------------------------------------- #


def _numero_y_faltante(estado: EstadoPersona, pronostico: Pronostico, cfg: Any) -> tuple[int, int, int | None]:
    """(numero_hoy, dia_limitante, faltante o None)."""
    q = cfg["cuantil_conservador"]
    d_lim, minimo = _minimo(estado, pronostico, q, cfg)
    numero = int(math.floor(max(0.0, minimo)))
    faltante = None
    if minimo < 0:
        faltante = int(math.ceil(-numerador(estado, pronostico, d_lim, q, cfg)))
    return numero, d_lim, faltante


def construir_desglose(estado: EstadoPersona, pronostico: Pronostico, cfg: Any) -> dict[str, Any]:
    """Desglose con las claves exactas que dibuja la pantalla Por qué."""
    q = cfg["cuantil_conservador"]
    numero, d_lim, faltante = _numero_y_faltante(estado, pronostico, cfg)
    puntos = [
        {
            "dia": d,
            "ingreso_conservador": float(ingreso_conservador(pronostico, d, q, _horizontes(cfg))),
            "pagos_acumulados": round(_pagos_hasta(estado, d), 2),
            "numerador": round(numerador(estado, pronostico, d, q, cfg), 2),
            "permitido": round(permitido(estado, pronostico, d, q, cfg), 2),
        }
        for d in puntos_de_control(estado)
    ]
    return {
        "saldo": float(estado.saldo),
        "colchon": float(estado.colchon),
        "cuantil": _atributo(q),
        "numero_hoy": numero,
        "puntos_de_control": puntos,
        "dia_limitante": d_lim,
        "faltante": faltante,
        "registro_id": "",
    }


def construir_evidencia(estado: EstadoPersona, pronostico: Pronostico, cfg: Any) -> dict[str, Any]:
    """Evidencia de la decisión (sección 4, tarea 2)."""
    q = cfg["cuantil_conservador"]
    d_lim, minimo = _minimo(estado, pronostico, q, cfg)
    c14 = pronostico.por_horizonte[HORIZONTE_MAXIMO]
    pago = _pago_del_dia(estado, d_lim)
    return {
        "semanas_historia": int(estado.semanas_historia),
        "pagos_detectados": len(estado.pagos),
        "rango_14d": {"p5": float(c14.p5), "p20": float(c14.p20), "p50": float(c14.p50), "p80": float(c14.p80)},
        "cuantil_usado": _atributo(q),
        "ancho_relativo": round(_ancho_relativo(pronostico), 2),
        "punto_limite": {
            "dia": d_lim,
            "pago_id": pago.pago_id if pago is not None else None,
            "permitido": round(minimo, 2),
        },
    }


# --------------------------------------------------------------------------- #
# Función pública
# --------------------------------------------------------------------------- #


def decidir(estado: EstadoPersona, pronostico: Pronostico, cfg: Any) -> Decision:
    """Decision completa. El servicio pone respaldo y registro_id (ver con_registro_id)."""
    q = cfg["cuantil_conservador"]
    desglose = construir_desglose(estado, pronostico, cfg)
    evidencia = construir_evidencia(estado, pronostico, cfg)
    numero = desglose["numero_hoy"]
    d_lim = desglose["dia_limitante"]
    faltante = desglose["faltante"]
    mensaje_falta = (
        f"no alcanza para el pago del dia {d_lim}: faltan S/{faltante}" if faltante is not None else None
    )

    por_pago = [
        DecisionPago(
            pago_id=p.pago_id,
            dia=p.dia,
            monto=p.monto,
            permitido=round(permitido(estado, pronostico, p.dia, q, cfg), 2),
            semaforo=semaforo(estado, pronostico, p.dia, cfg),
        )
        for p in estado.pagos
    ]
    nivel = confianza(estado, pronostico, cfg)
    propuestas = proponer(estado, pronostico, cfg, numero, nivel)

    return Decision(
        numero_hoy=numero,
        por_pago=por_pago,
        confianza=nivel,
        desglose=desglose,
        limites=list(plantillas.limites(evidencia, cfg)),
        supuestos=list(plantillas.supuestos(estado, evidencia)),
        evidencia=evidencia,
        propuestas=propuestas,
        respaldo=False,
        registro_id="",
        mensaje_falta=mensaje_falta,
        explicacion=plantillas.explicar(estado, numero, mensaje_falta, por_pago, nivel, desglose),
        explicacion_fuente="plantilla",
    )


def con_registro_id(decision: Decision, registro_id: str) -> Decision:
    """Copia de la Decision con registro_id en la Decision y en su desglose (lo genera el servicio)."""
    desglose = {**decision.desglose, "registro_id": registro_id}
    return decision.model_copy(update={"registro_id": registro_id, "desglose": desglose})


__all__ = [
    "con_registro_id",
    "confianza",
    "construir_desglose",
    "construir_evidencia",
    "decidir",
    "ingreso_conservador",
    "numerador",
    "permitido",
    "proponer",
    "puntos_de_control",
    "semaforo",
    "semaforo_con_gasto",
]
