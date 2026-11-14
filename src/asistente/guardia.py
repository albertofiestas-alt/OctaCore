"""Guardia de entrada: ahora SÍ entra texto libre. Dueño: Mathias. Respaldo hecho por delegación de Gino (DECISIONES #33).

Primera capa del flujo: rechaza antes de clasificar. Devuelve (ok, motivo) con un motivo FIJO:
vacio, control, largo, pii, url, inyeccion, otra_persona. El orden es el de esa lista (el correo es PII y no URL).
La PII sale de ingesta.pii con cfg["patrones_pii"]: no se duplican los patrones.
"""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING

import pandas as pd

from ingesta.pii import MASCARA, detectar_pii, enmascarar_pii

if TYPE_CHECKING:
    from contratos import Config

_TLD = "com|net|org|pe|io|co|app|xyz|dev|example|ly|gob|info|me"
_URL = re.compile(rf"(?:https?://|www\.)\S+|\b[\w-]+\.(?:{_TLD})\b\S*", re.IGNORECASE)

PATRON_URL = _URL  # público: lo reutiliza el verificador de salida

_PERSONAS = (
    r"(?:vecin[oa]|jef[ea]|cunad[oa]|suegr[oa]|hermano|hermana|amig[oa]|primo|prima|tio|tia|novi[oa]|espos[oa]|"
    r"pareja|socio|socia|companer[oa]|otra persona|otro usuario|otro cliente|cliente)"
)

# Sobre el texto sin tildes y en minúsculas.
_INYECCION = tuple(re.compile(p) for p in (
    r"\b(?:ignora|ignore|olvida|omite|desobedece)\b.{0,30}\b(?:instrucciones|anterior|anteriores|reglas|todo)\b",
    r"\bolvida (?:todo|lo anterior)\b",
    r"\bprompt\b",
    r"\beres ahora\b",
    r"\b(?:actua|actue|finge|pretende|hazte pasar)\s+(?:como|por|ser)\b",
    r"\bapi\s*key\b|\bapikey\b|\bcontrasena\b|\bpassword\b|\btoken\b",
    r"\binstrucciones (?:internas|ocultas|del sistema)\b",
    r"\bnombres? de tus (?:herramientas|funciones)\b",
    r"\b(?:revela|muestra|imprime|repite|filtra)\b.{0,25}\b(?:instrucciones|configuracion|reglas internas)\b",
    r"\b(?:jailbreak|modo desarrollador|developer mode|dan mode)\b",
))
_OTRA_PERSONA = tuple(re.compile(p) for p in (
    rf"\b(?:saldo|sueldo|salario|deudas?|cuenta|datos|movimientos|ingresos|gastos|pagos)\b.{{0,15}}"
    rf"\b(?:de|del)\s+(?:mi|su|la|el)?\s*{_PERSONAS}\b",
    rf"\bcuanto (?:gana|debe|tiene|paga|cobra|gasta)\b.{{0,10}}\b(?:mi|el|la|su)\s+{_PERSONAS}\b",
    r"\bp\d{4}\b",
    r"\bde (?:otra persona|otro usuario|otros clientes|alguien mas)\b",
))


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sin_tildes.lower().split())


def revisar(texto: str, cfg: Config) -> tuple[bool, str]:
    """(ok, motivo). Rechaza: vacio, control, largo (cfg["asistente"]["max_caracteres"] y max_palabras), pii, url,
    inyeccion y otra_persona. Con ok el motivo es la cadena vacía."""
    a = cfg["asistente"]
    if not isinstance(texto, str) or not texto.strip():
        return False, "vacio"
    if any(unicodedata.category(c) == "Cc" for c in texto):
        return False, "control"
    if len(texto) > a["max_caracteres"] or len(texto.split()) > a["max_palabras"]:
        return False, "largo"
    if detectar_pii(texto, cfg):
        return False, "pii"
    if _URL.search(texto):
        return False, "url"
    t = _normalizar(texto)
    if any(rx.search(t) for rx in _INYECCION):
        return False, "inyeccion"
    if any(rx.search(t) for rx in _OTRA_PERSONA):
        return False, "otra_persona"
    return True, ""


def enmascarar_para_registro(texto: str, cfg: Config) -> str:
    """La pregunta con *** en lugar de PII y de URLs, antes de guardarla en el registro."""
    if not isinstance(texto, str):
        return ""
    enmascarado, _ = enmascarar_pii(pd.DataFrame({"comercio": [texto]}), cfg)
    return _URL.sub(MASCARA, str(enmascarado["comercio"].iloc[0]))


__all__ = ["enmascarar_para_registro", "revisar"]
