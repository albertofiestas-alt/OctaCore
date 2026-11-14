"""Verificador de salida del asistente (extiende al de la opción B). Dueño: Sebastián. Respaldo por delegación de Gino
(DECISIONES #33): si Sebastián sube el suyo, lo reemplaza.

Reutiliza el verificador de cifras del motor (motor.verificador): mismas reglas de qué es una cifra (las etiquetas
P5/P20/P50/P80 no cuentan; "S/1,234.50" es 1234.5) y mismas variantes de redondeo (valor, floor, ceil, 2 decimales).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from asistente.guardia import PATRON_URL
from ingesta.pii import detectar_pii
from motor.verificador import DECIMALES, _numeros, cifras_en_texto

if TYPE_CHECKING:
    from contratos import Config

INTENCIONES_CON_CIFRA_CLAVE = ("explicar_numero", "estado_pago", "que_pasa_si")
# Palabras que el asistente nunca debe decir (promesas, inversión, crédito).
PROHIBIDAS = ("garantizado", "garantizamos", "garantia", "sin riesgo", "seguro que", "invierte", "invertir",
              "prestamo", "credito")
_CITA = re.compile(r"\[[^\]]*\]")
_INTERNO = tuple(re.compile(p) for p in (
    r"\b[a-z]+_[a-z0-9_]+\b",  # numero_hoy, pago_id, customer_id...
    r"\b\w+\.(?:py|yaml|csv|json|jsonl)\b",
    r"\b(?:src|eval|config|tests)/",
    r"\b(?:motor|servicio|asistente|ingesta|contratos)\.\w+",
))


def _soles(x: Any) -> str:
    v = float(x)
    return str(int(v)) if v.is_integer() else f"{v:.2f}"


def verificar_respuesta(
    obj: dict[str, Any], resultados: dict[str, Any], pasajes: list[dict[str, Any]], cfg: Config
) -> tuple[bool, list[str]]:
    """(ok, motivos). Motivos: largo, cifra_inventada, cita_inexistente, falta_cita, nombre_interno,
    prohibida_o_pii, falta_cifra_clave. Si falla, el flujo usa la plantilla."""
    texto = obj.get("respuesta") if isinstance(obj, dict) else None
    if not isinstance(texto, str) or not texto.strip():
        return False, ["respuesta_vacia"]
    citas = obj.get("citas") or []
    motivos: list[str] = []

    if len(texto.split()) > cfg["asistente"]["max_palabras"]:
        motivos.append("largo")

    sin_citas = _CITA.sub(" ", texto)  # "[kb:glosario#2]" es una etiqueta, no una cifra ni un nombre interno
    permitidas = set(_numeros(resultados))
    for p in pasajes:
        permitidas |= {round(c, DECIMALES) for c in cifras_en_texto(p.get("texto", ""))}
    if any(round(c, DECIMALES) not in permitidas for c in cifras_en_texto(sin_citas)):
        motivos.append("cifra_inventada")

    ids = {p["id"] for p in pasajes}
    if any(c not in ids for c in citas):
        motivos.append("cita_inexistente")
    if pasajes and not citas:
        motivos.append("falta_cita")

    minusculas = sin_citas.lower()
    if any(rx.search(minusculas) for rx in _INTERNO):
        motivos.append("nombre_interno")
    if PATRON_URL.search(texto) or detectar_pii(texto, cfg) or any(p in minusculas for p in PROHIBIDAS):
        motivos.append("prohibida_o_pii")

    if resultados.get("intencion") in INTENCIONES_CON_CIFRA_CLAVE and f"S/{_soles(resultados['numero_hoy'])}" not in texto:
        motivos.append("falta_cifra_clave")
    return not motivos, motivos


__all__ = ["verificar_respuesta"]
