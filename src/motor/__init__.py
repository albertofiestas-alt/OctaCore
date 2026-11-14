"""Capa 2: motor de decisión (número de hoy por fecha de pago, semáforo, confianza, propuestas).

Dueño: Sebastián. RESPALDO hecho por delegación de Gino (DECISIONES.md #28): si Sebastián sube su motor real,
el suyo reemplaza a este. Fórmula del Plan 04, sección 5.
Función pura: no lee archivos ni la hora ni cambia sus entradas. El servicio pone respaldo y registro_id.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from contratos import Decision, DecisionPago, Propuesta

if TYPE_CHECKING:
    from contratos import Config, EstadoPersona, Pronostico

_ATRIBUTO = {0.05: "p5", 0.20: "p20", 0.50: "p50", 0.80: "p80"}
_LIMITES = (
    "Es una orientación educativa y no sustituye asesoría financiera.",
    "No promete resultados.",
    "El futuro puede diferir del pronóstico.",
)
_EPS = 1e-9


def _atributo(cuantil: float) -> str:
    for q, nombre in _ATRIBUTO.items():
        if abs(q - cuantil) < _EPS:
            return nombre
    raise ValueError(f"cuantil_conservador {cuantil} no es uno de {sorted(_ATRIBUTO)}")


def _soles(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:.2f}"


def _ingreso(pron: Pronostico, d: int, nombre: str, horizontes: tuple[int, ...]) -> float:
    """Ingreso conservador hasta el día d: cuantil del mayor horizonte h <= d (h=14 si d > 14); 0 si d < 3."""
    cabe = [h for h in horizontes if h <= min(d, max(horizontes))]
    return float(getattr(pron.por_horizonte[max(cabe)], nombre)) if cabe else 0.0


def _numerador(estado, pron, d, nombre, horizontes, colchon: float) -> float:
    pagos = sum(p.monto for p in estado.pagos if p.dia <= d)
    return estado.saldo + _ingreso(pron, d, nombre, horizontes) - pagos - colchon


def _umbrales(cfg) -> tuple[float, float]:
    u = cfg.get("umbrales_confianza") or (cfg.get("preregistro") or {}).get("umbrales_confianza")
    if not u:
        raise ValueError("umbrales_confianza sin fijar: ni config/base.yaml ni config/preregistro.yaml los traen")
    return float(u["ancho_alto"]), float(u["ancho_bajo"])


def _confianza(estado, pron, cfg, horizontes) -> str:
    alto, bajo = _umbrales(cfg)
    r = pron.por_horizonte[max(horizontes)]
    ancho = (r.p80 - r.p5) / max(r.p50, 1.0)
    if estado.semanas_historia < cfg["umbral_historia_semanas"] or ancho > bajo:
        return "baja"
    return "alta" if ancho < alto else "media"


def _semaforo(estado, pron, dia: int, horizontes) -> str:
    def cobertura(nombre: str) -> float:
        return _numerador(estado, pron, dia, nombre, horizontes, 0.0)  # sin colchón
    if cobertura("p5") >= 0:
        return "verde"
    return "ambar" if cobertura("p50") >= 0 else "rojo"


def _proponer(estado, pron, cfg, horizontes, puntos, numero, confianza) -> list[Propuesta]:
    """Gastar g5 = floor(mínimo permitido en P5) por día y apartar el resto. Verifica la cobertura en P5."""
    perm5 = {d: _numerador(estado, pron, d, "p5", horizontes, estado.colchon) / max(d, 1) for d in puntos}
    d5 = min(perm5, key=perm5.get)
    if perm5[d5] < 0:
        return []
    g5 = int(math.floor(perm5[d5]))
    pagos_limite = [p for p in estado.pagos if p.dia == d5]
    if g5 >= numero or not pagos_limite:
        return []
    pago = max(pagos_limite, key=lambda p: p.monto)
    for d in puntos:  # el verificador del plan: solo se muestra lo que aguanta el escenario pesimista
        assert _numerador(estado, pron, d, "p5", horizontes, estado.colchon) - g5 * d >= -_EPS, "propuesta no cubierta en P5"
    return [Propuesta(
        propuesta_id=f"{estado.customer_id}-{estado.fecha_corte.isoformat()}-1",
        texto=f"Gasta hasta S/{g5} por día y aparta S/{numero - g5} por día para el pago de {pago.categoria} del día {d5}.",
        monto=float(numero - g5), pago_id=pago.pago_id,
        antes={"numero_hoy": numero, "cubierto_en_p5": False},
        despues={"numero_hoy": g5, "cubierto_en_p5": True},
        confianza=confianza)]


def _supuestos(estado) -> list[str]:
    return [
        "Gastas cada día lo que indica el número de hoy.",
        f"Los pagos con fecha son los {len(estado.pagos)} detectados en tu historial.",
        f"El ingreso futuro se parece al de las últimas {estado.semanas_historia} semanas.",
        "No se consideran gastos imprevistos.",
        "El escenario P20 es una semana mala y el P5 una semana muy mala.",
    ]


def _explicar(estado, numero, faltante, d_lim, ultimo, confianza, poca_historia) -> str:
    en_limite = [p for p in estado.pagos if p.dia == d_lim]
    total = sum(p.monto for p in en_limite)
    if faltante is not None:
        if en_limite:
            texto = f"Hoy no conviene gastar: el pago de S/{_soles(total)} del día {d_lim} no alcanza; faltan S/{faltante}."
        else:
            texto = f"Hoy no conviene gastar: para llegar al día {d_lim} faltan S/{faltante}."
    elif numero == 0:
        texto = "Hoy no conviene gastar: lo que tienes alcanza justo para tus pagos."
    else:
        texto = f"Hoy puedes gastar hasta S/{numero}."
        if not estado.pagos:
            texto += f" No hay pagos con fecha en los próximos {ultimo} días."
        else:
            n = len(estado.pagos)
            cubiertos = "Tu pago" if n == 1 else f"Tus {n} pagos"
            verbo = "queda cubierto" if n == 1 else "quedan cubiertos"
            limite = f"el pago de S/{_soles(total)} del día {d_lim}" if en_limite else f"llegar al día {d_lim}"
            texto += f" {cubiertos} de los próximos {ultimo} días {verbo}; lo que más limita es {limite}."
    if poca_historia:
        texto += f" Con solo {estado.semanas_historia} semanas de historia la confianza es baja."
    elif confianza == "baja":
        texto += " La confianza es baja: el ingreso esperado es muy variable."
    return texto


def decidir(estado: EstadoPersona, pronostico: Pronostico, cfg: Config) -> Decision:
    horizontes = tuple(cfg["horizontes_dias"])
    ultimo = max(horizontes)
    nombre = _atributo(float(cfg["cuantil_conservador"]))
    colchon = estado.colchon

    puntos = sorted({p.dia for p in estado.pagos} | {ultimo})
    perm = {d: _numerador(estado, pronostico, d, nombre, horizontes, colchon) / max(d, 1) for d in puntos}
    d_lim = min(perm, key=perm.get)  # punto que limita (el más cercano si hay empate)
    numero = int(math.floor(max(0.0, perm[d_lim])))  # siempre hacia abajo

    faltante = mensaje = None
    if perm[d_lim] < 0:
        faltante = int(math.ceil(-_numerador(estado, pronostico, d_lim, nombre, horizontes, colchon)))
        mensaje = f"no alcanza para el pago del dia {d_lim}: faltan S/{faltante}"

    umbral_historia = int(cfg["umbral_historia_semanas"])
    poca_historia = estado.semanas_historia < umbral_historia
    confianza = _confianza(estado, pronostico, cfg, horizontes)
    propuestas = [] if poca_historia else _proponer(estado, pronostico, cfg, horizontes, puntos, numero, confianza)
    limites = list(_LIMITES)
    if poca_historia:
        limites.append(
            f"Hay menos de {umbral_historia} semanas de historia: solo se muestra el número de hoy, sin propuestas.")

    r = pronostico.por_horizonte[ultimo]
    return Decision(
        numero_hoy=numero,
        por_pago=[DecisionPago(pago_id=p.pago_id, dia=p.dia, monto=p.monto, permitido=round(perm[p.dia], 2),
                               semaforo=_semaforo(estado, pronostico, p.dia, horizontes)) for p in estado.pagos],
        confianza=confianza,
        desglose={
            "saldo": float(estado.saldo), "colchon": float(colchon), "cuantil": nombre,
            "puntos_de_control": [
                {"dia": d, "ingreso_conservador": _ingreso(pronostico, d, nombre, horizontes),
                 "pagos_acumulados": float(sum(p.monto for p in estado.pagos if p.dia <= d)),
                 "permitido": round(perm[d], 2)} for d in puntos],
            "dia_limitante": d_lim},
        limites=limites,
        supuestos=_supuestos(estado),
        evidencia={"semanas_historia": estado.semanas_historia, "pagos_detectados": len(estado.pagos),
                   "rango_14d": {"p5": r.p5, "p20": r.p20, "p50": r.p50, "p80": r.p80},
                   "cuantil": nombre, "dia_limitante": d_lim},
        propuestas=propuestas,
        mensaje_falta=mensaje,
        explicacion=_explicar(estado, numero, faltante, d_lim, ultimo, confianza, poca_historia),
    )


__all__ = ["decidir"]
