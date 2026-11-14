"""Verificador de cifras de los textos del motor. Dueño: Sebastián.

Plan de Sebastián, sección 4 tarea 5: toda cifra que aparece en supuestos, límites,
explicación, mensaje de falta o textos de propuesta debe existir en el estado, el
desglose, la evidencia o la propia Decision (número de hoy, por pago, propuestas).

Función pura: no lee archivos ni cambia sus entradas. Las etiquetas de cuantil
(P5, P20, P50, P80) son nombres, no cifras, y se ignoran.
"""

from __future__ import annotations

import math
import re
from typing import Any

from contratos import Decision, EstadoPersona

# Etiquetas de cuantil: P5, P20, P50, P80 (también en minúscula), como palabra completa.
_ETIQUETA_CUANTIL = re.compile(r"(?<![^\W_])[Pp](?:5|20|50|80)(?![\w])")

# Número: no pegado a una letra ni a otro número/decimal por la izquierda.
# Miles con coma solo si son grupos exactos de 3 ("1,234.50"); "3,7,14" son tres números.
# El punto decimal exige dígitos después: "S/200." es 200.
_NUMERO = re.compile(r"(?<![^\W\d])(?<![\d.])\d+(?:,\d{3}(?!\d))*(?:\.\d+)?")

DECIMALES = 2


def cifras_en_texto(texto: str) -> list[float]:
    """Números del texto en orden ("S/1,234.50" -> 1234.5, "día 14" -> 14). Sin signo."""
    if not texto:
        return []
    limpio = _ETIQUETA_CUANTIL.sub(" ", texto)
    return [float(m.group().replace(",", "")) for m in _NUMERO.finditer(limpio)]


def _variantes(x: float) -> set[float]:
    """El valor y sus redondeos (floor, ceil, 2 decimales), con y sin signo."""
    salida: set[float] = set()
    for v in (x, abs(x)):
        salida |= {float(v), float(math.floor(v)), float(math.ceil(v)), round(v, DECIMALES)}
    return {round(v, DECIMALES) for v in salida}


def _numeros(obj: Any) -> set[float]:
    """Todos los números dentro de obj (recursivo en dict, list, tuple y modelos)."""
    if obj is None or isinstance(obj, (bool, str)):
        return set()
    if isinstance(obj, (int, float)):
        x = float(obj)
        return _variantes(x) if math.isfinite(x) else set()
    if isinstance(obj, dict):
        return set().union(*(_numeros(v) for v in obj.values()))
    if isinstance(obj, (list, tuple, set, frozenset)):
        return set().union(*(_numeros(v) for v in obj))
    if hasattr(obj, "model_dump"):
        return _numeros(obj.model_dump(mode="python"))
    return set()


def cifras_permitidas(estado: EstadoPersona, decision: Decision) -> set[float]:
    """Números con origen conocido (redondeados a 2 decimales, con sus variantes)."""
    total: set[float] = set()
    total |= _numeros(estado.saldo)
    total |= _numeros(estado.colchon)
    total |= _numeros(estado.semanas_historia)
    total |= _numeros(len(estado.pagos))
    for p in estado.pagos:
        total |= _numeros(p.dia) | _numeros(p.monto)
    total |= _numeros(decision.numero_hoy)
    total |= _numeros(decision.desglose)
    total |= _numeros(decision.evidencia)
    total |= _numeros(decision.por_pago)
    for prop in decision.propuestas:
        total |= _numeros(prop.monto) | _numeros(prop.antes) | _numeros(prop.despues)
    return total


def _textos(decision: Decision) -> list[str]:
    textos = [*decision.supuestos, *decision.limites, decision.explicacion]
    if decision.mensaje_falta:
        textos.append(decision.mensaje_falta)
    textos.extend(p.texto for p in decision.propuestas)
    return [t for t in textos if t]


def _formato(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:.2f}"


def textos_sin_origen(estado: EstadoPersona, decision: Decision) -> list[str]:
    """Una entrada "cifra en: texto" por cada cifra sin origen. Lista vacía = OK."""
    permitidas = cifras_permitidas(estado, decision)
    problemas: list[str] = []
    for texto in _textos(decision):
        for c in cifras_en_texto(texto):
            if round(c, DECIMALES) not in permitidas:
                problemas.append(f"{_formato(c)} en: {texto}")
    return problemas


__all__ = ["cifras_en_texto", "cifras_permitidas", "textos_sin_origen"]
