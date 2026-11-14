"""Textos del motor: supuestos, límites, explicación y propuestas. Dueño: Sebastián.

Reglas (plan de Sebastián, secciones 4 y 5.3):
- Texto en soles y días, sin tasas ni porcentajes.
- Toda cifra del texto sale del estado, del desglose o de la evidencia (motor/verificador.py lo comprueba).
- Un registro por tipo de propuesta: agregar un tipo nuevo no toca el resto (prueba de evolución).

INTERFAZ FIJADA POR EL ORQUESTADOR. Se reemplazan los cuerpos, no las firmas.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contratos import DecisionPago, EstadoPersona

# Sección 4, tarea 3: frases fijas que van en TODA Decision.
LIMITES_FIJOS: tuple[str, ...] = (
    "Es una orientación educativa y no sustituye asesoría financiera.",
    "No promete resultados.",
    "El futuro puede diferir del pronóstico.",
)

TIPOS_PROPUESTA: dict[str, Callable[[dict[str, Any]], str]] = {}


def _soles(x: float) -> str:
    """Monto para el texto: entero si es entero (300), si no 2 decimales (45.56)."""
    x = float(x)
    if x.is_integer():
        return str(int(x))
    return f"{x:.2f}"


def _en_dias(dia: int) -> str:
    """'hoy', 'en 1 día' o 'en N días'."""
    if dia <= 0:
        return "hoy"
    return "en 1 día" if dia == 1 else f"en {dia} días"


def _pago_limite(estado: EstadoPersona, dia: int | None) -> Any:
    """Pago que limita: el de mayor monto en el día limitante. None si no hay pago ese día."""
    if dia is None:
        return None
    candidatos = [p for p in estado.pagos if p.dia == dia]
    return max(candidatos, key=lambda p: p.monto) if candidatos else None


def supuestos(estado: EstadoPersona, evidencia: dict[str, Any]) -> list[str]:
    """Sección 4, tarea 1. Nunca vacía; cada cifra sale del estado o de la evidencia."""
    n_pagos = evidencia.get("pagos_detectados", len(estado.pagos))
    semanas = evidencia.get("semanas_historia", estado.semanas_historia)
    salida = [
        "Gastas cada día lo que indica el número de hoy.",
        f"Los pagos con fecha son los {n_pagos} detectados en tu historial.",
        f"El ingreso futuro se parece al de las últimas {semanas} semanas.",
        "No se consideran gastos imprevistos.",
        "El escenario P20 es una semana mala y el P5 una semana muy mala.",
    ]
    return salida + _supuestos_simulacion(evidencia.get("escenario"))


def _supuestos_simulacion(escenario: dict[str, Any] | None) -> list[str]:
    """Opción C: qué se simuló, con las cifras de evidencia["escenario"]. Nada si no es una simulación."""
    if not escenario:
        return []
    salida = []
    if escenario.get("gasto_hoy"):
        salida.append(f"Simulación: gastas S/{_soles(escenario['gasto_hoy'])} hoy.")
    for ingreso in escenario.get("ingresos_extra", []):
        salida.append(
            f"Simulación: recibes un ingreso extra seguro de S/{_soles(ingreso['monto'])} el día {ingreso['dia']}."
        )
    if not salida:
        salida.append("Simulación sin cambios respecto a tu situación actual.")
    return salida


def limites(evidencia: dict[str, Any], cfg: Any) -> list[str]:
    """Sección 4, tarea 3 + sección 5.3. LIMITES_FIJOS primero, luego los límites de contexto."""
    salida = list(LIMITES_FIJOS)
    salida.append("El ingreso futuro es un rango, no una cifra exacta.")
    salida.append("Los datos son ficticios.")
    # Sin dato de historia se asume poca historia (lado prudente).
    if evidencia.get("semanas_historia", 0) < cfg["umbral_historia_semanas"]:
        salida.append("Con pocas semanas de historia la confianza es baja.")
    return salida


def explicar(
    estado: EstadoPersona,
    numero_hoy: int,
    mensaje_falta: str | None,
    por_pago: list[DecisionPago],
    confianza: str,
    desglose: dict[str, Any],
) -> str:
    """Explicación en lenguaje simple (Decision.explicacion).

    Solo soles y días. Toda cifra sale del estado (montos y días de pagos) o del
    desglose (numero_hoy, dia_limitante, faltante). Nunca se escribe el registro_id.
    """
    dia_lim = desglose.get("dia_limitante")
    pago = _pago_limite(estado, dia_lim)
    cierre = f"Confianza: {confianza}."

    if mensaje_falta:
        faltante = desglose.get("faltante")
        if faltante is None:
            # Sin faltante en el desglose se usa el mensaje del motor tal cual.
            return f"Hoy no conviene gastar: {mensaje_falta}. {cierre}"
        if pago is not None:
            cuerpo = (
                f"el pago de S/{_soles(pago.monto)} de {pago.categoria} vence {_en_dias(pago.dia)}"
                f" y, con lo que se espera que entre, faltan S/{_soles(faltante)}."
            )
        else:
            cuerpo = (
                f"con lo que se espera que entre, {_en_dias(dia_lim)} faltan S/{_soles(faltante)}"
                " para cubrir tus pagos."
            )
        return f"Hoy no conviene gastar: {cuerpo} {cierre}"

    if not estado.pagos:
        dias = [p["dia"] for p in desglose.get("puntos_de_control", []) if "dia" in p]
        ventana = f"los próximos {max(dias)} días" if dias else "los próximos días"
        inicio = (
            f"Puedes gastar hasta S/{_soles(numero_hoy)} hoy."
            if numero_hoy > 0
            else "Hoy no conviene gastar."
        )
        return f"{inicio} No hay pagos con fecha en {ventana}. {cierre}"

    if numero_hoy > 0:
        inicio = f"Puedes gastar hasta S/{_soles(numero_hoy)} hoy."
    else:
        inicio = "Hoy no conviene gastar: lo que tienes alcanza justo para tus pagos."
    if pago is not None:
        limita = (
            f" El pago que más limita es el de S/{_soles(pago.monto)} de {pago.categoria},"
            f" {_en_dias(pago.dia)}."
        )
    elif dia_lim is not None:
        limita = f" Lo que más limita es lo que debe quedar cubierto {_en_dias(dia_lim)}."
    else:
        limita = ""
    return f"{inicio}{limita} {cierre}"


def registrar_tipo(nombre: str) -> Callable[[Callable[[dict[str, Any]], str]], Callable[[dict[str, Any]], str]]:
    """Decorador: registra la plantilla de un tipo de propuesta en TIPOS_PROPUESTA.

    Agregar un tipo nuevo = definir una función con @registrar_tipo("nuevo"). Un
    nombre repetido falla (ValueError) para no pisar un tipo existente en silencio.
    """

    def _decorar(funcion: Callable[[dict[str, Any]], str]) -> Callable[[dict[str, Any]], str]:
        if nombre in TIPOS_PROPUESTA:
            raise ValueError(f"tipo de propuesta ya registrado: {nombre}")
        TIPOS_PROPUESTA[nombre] = funcion
        return funcion

    return _decorar


def texto_propuesta(tipo: str, datos: dict[str, Any]) -> str:
    """Texto de una propuesta del tipo registrado. KeyError si el tipo no existe."""
    return TIPOS_PROPUESTA[tipo](datos)


@registrar_tipo("apartar_p5")
def _apartar_p5(datos: dict[str, Any]) -> str:
    return (
        f"Gasta hasta S/{_soles(datos['g5'])} por día en vez de S/{_soles(datos['numero_hoy'])}"
        f" y aparta S/{_soles(datos['apartar'])} por día para {datos['categoria']}"
        f" de S/{_soles(datos['monto'])} del día {datos['dia']}."
    )


__all__ = [
    "LIMITES_FIJOS",
    "TIPOS_PROPUESTA",
    "explicar",
    "limites",
    "registrar_tipo",
    "supuestos",
    "texto_propuesta",
]
