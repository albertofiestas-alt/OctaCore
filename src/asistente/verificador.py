"""Verificador de salida del asistente (extiende al de la opción B). Dueño: Sebastián.

Reutiliza el verificador de cifras del motor (motor.verificador): mismas reglas de qué es una cifra (las etiquetas
P5/P20/P50/P80 no cuentan; "S/1,234.50" es 1234.5) y mismas variantes de redondeo (valor, floor, ceil, 2 decimales).

Plan de Sebastián, sección 8. Cada comprobación agrega SU motivo (no corta en la primera):

    respuesta_vacia   no hay texto
    largo             más palabras que cfg["asistente"]["max_palabras"]
    cifra_inventada   una cifra que no está en los resultados ni en un pasaje recuperado
    cita_inexistente  una cita (en obj["citas"] o [entre corchetes] en el texto) que no está entre los ids recuperados
    falta_cita        hay pasajes recuperados y no se cita ninguno, o se usa una cifra que solo sale de un pasaje
                      que no se cita
    nombre_interno    funciones, campos, rutas, archivos, módulos o nombres de herramientas
    url / pii / prohibida   cada uno con su motivo; además "prohibida_o_pii" agrupa los tres (compatibilidad)
    falta_cifra_clave la cifra clave de la intención no aparece como "S/<cifra>"

Una cita es una etiqueta [algo#n] (p. ej. [kb:glosario#2], [decision#1]): no cuenta como cifra ni como nombre interno.
Cualquier otro texto entre corchetes se revisa como el resto ("[S/999]" es una cifra inventada).
"""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING, Any

from asistente.guardia import PATRON_URL
from ingesta.pii import detectar_pii
from motor.verificador import DECIMALES, _numeros, cifras_en_texto

if TYPE_CHECKING:
    from contratos import Config

INTENCIONES_CON_CIFRA_CLAVE = ("explicar_numero", "estado_pago", "que_pasa_si")

# Palabras o frases que el asistente nunca debe decir (promesas, inversión, crédito). Sin tildes y en minúsculas:
# se buscan como palabra completa sobre el texto sin tildes.
PROHIBIDAS = ("garantizado", "garantizada", "garantizamos", "garantia", "sin riesgo", "seguro que", "te aseguro",
              "asegurado", "100% seguro", "invierte en", "te recomiendo invertir", "pide un prestamo", "pide prestado",
              "saca un prestamo", "compra acciones")

# Cita: [id#n] sin espacios dentro. Solo esto se quita antes de buscar cifras y nombres internos.
_CITA = re.compile(r"\[([^\[\]\s]+#\d+)\]")

# Nombres internos. Los de _INTERNO van sobre el texto en minúsculas; los de _INTERNO_CASO sobre el original.
_INTERNO = tuple(re.compile(p) for p in (
    r"\b[a-z0-9]+_[a-z0-9_]+\b",                                    # numero_hoy, pago_id, kb_dinamica...
    r"\b\w+\.(?:py|pyc|yaml|yml|csv|json|jsonl|md|txt|toml|ipynb|parquet|pkl|joblib|log)\b",
    r"(?:^|[\s(\"'])(?:\.{0,2}/)?(?:src|eval|config|tests|data|fixtures|kb|registros|asignaciones|docs|app)/",
    r"\b[a-z]:\\|\b\w+\\\w+",                                       # rutas de Windows
    r"\b(?:motor|servicio|asistente|ingesta|contratos|generativa|modelo|rag|guardia|flujo|plantillas|verificador"
    r"|intenciones|cfg|self|st)\.\w+",                              # servicio.consultar, motor.decidir...
    r"\b[a-z_]\w*\(\)",                                             # decidir()
    r"\b[a-z_]\w*\(\s*[a-z_]\w*\s*(?:,\s*[a-z_]\w*\s*)+\)",          # simular(estado, pron, ...)
    r"\[\s*[\"'][\w ]+[\"']\s*\]",                                  # desglose["saldo"]
    r"(?<![\[\w])(?:kb:\w|decision#\d)",                            # id de pasaje fuera de una cita
    r"\b__\w+__\b",
))
_INTERNO_CASO = (re.compile(r"\b[a-z]+[A-Z][A-Za-z0-9]*\b|\b[A-Z][a-z0-9]+[A-Z][A-Za-z0-9]*\b"),)  # numeroHoy, EstadoPersona

_CORREO = re.compile(r"\S+@\S+")

# Cifra precedida de "S/" (con o sin espacio): la forma en que se nombra un monto.
_SOLES = re.compile(r"S/\s?(\d+(?:,\d{3}(?!\d))*(?:\.\d+)?)")


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _redondeadas(cifras: list[float]) -> set[float]:
    return {round(c, DECIMALES) for c in cifras}


def _lista_citas(citas: Any) -> list[str]:
    if isinstance(citas, str):
        return [citas]
    if isinstance(citas, (list, tuple, set)):
        return [str(c) for c in citas]
    return []


def _soles_en(texto: str) -> set[float]:
    return {round(float(m.group(1).replace(",", "")), DECIMALES) for m in _SOLES.finditer(texto)}


def verificar_respuesta(
    obj: dict[str, Any], resultados: dict[str, Any], pasajes: list[dict[str, Any]], cfg: Config
) -> tuple[bool, list[str]]:
    """(ok, motivos). Motivos posibles en el docstring del módulo. Si falla, el flujo usa la respuesta segura."""
    texto = obj.get("respuesta") if isinstance(obj, dict) else None
    if not isinstance(texto, str) or not texto.strip():
        return False, ["respuesta_vacia"]
    pasajes = [p for p in (pasajes or []) if isinstance(p, dict) and "id" in p]
    ids = {str(p["id"]) for p in pasajes}
    en_texto = _CITA.findall(texto)
    citadas = set(_lista_citas(obj.get("citas"))) | set(en_texto)
    motivos: list[str] = []

    # 1. largo
    if len(texto.split()) > cfg["asistente"]["max_palabras"]:
        motivos.append("largo")

    # 2. cifras: de los resultados, o de un pasaje recuperado (que entonces debe citarse)
    sin_citas = _CITA.sub(" ", texto)
    permitidas = set(_numeros(resultados))
    de_citados: set[float] = set()
    de_no_citados: set[float] = set()
    for p in pasajes:
        cifras_p = _redondeadas(cifras_en_texto(str(p.get("texto", ""))))
        (de_citados if str(p["id"]) in citadas else de_no_citados).update(cifras_p)
    usa_sin_citar = False
    for c in _redondeadas(cifras_en_texto(sin_citas)):
        if c in permitidas or c in de_citados:
            continue
        if c in de_no_citados:
            usa_sin_citar = True
        elif "cifra_inventada" not in motivos:
            motivos.append("cifra_inventada")

    # 3. citas reales y cita obligatoria
    if any(c not in ids for c in citadas):
        motivos.append("cita_inexistente")
    if (pasajes and not citadas) or usa_sin_citar:
        motivos.append("falta_cita")

    # 4. cero nombres internos (las citas ya no están en sin_citas)
    minusculas = sin_citas.lower()
    if any(rx.search(minusculas) for rx in _INTERNO) or any(rx.search(sin_citas) for rx in _INTERNO_CASO):
        motivos.append("nombre_interno")

    # 5. URL, PII y palabras prohibidas: cada una con su motivo, y el motivo agrupado de siempre
    plano = _sin_tildes(minusculas)
    propios = []
    if PATRON_URL.search(_CORREO.sub(" ", texto)):  # un correo es PII, no URL (como en la guardia)
        propios.append("url")
    if detectar_pii(texto, cfg):
        propios.append("pii")
    if any(re.search(rf"(?<!\w){re.escape(p)}(?!\w)", plano) for p in PROHIBIDAS):
        propios.append("prohibida")
    if propios:
        motivos += ["prohibida_o_pii", *propios]

    # 6. cifra clave: el número de hoy; en que_pasa_si, el número DESPUÉS del escenario (resultados["cifra_clave"]).
    # Un cifra_clave explícito en None desactiva la regla (estado_pago sin ningún pago que nombrar).
    # Se compara la cifra completa: la clave 1 no se cumple con "S/150".
    intencion = resultados.get("intencion")
    por_defecto = resultados.get("numero_hoy") if intencion in ("explicar_numero", "que_pasa_si") else None
    clave = resultados.get("cifra_clave", por_defecto)
    if (intencion in INTENCIONES_CON_CIFRA_CLAVE and clave is not None
            and round(float(clave), DECIMALES) not in _soles_en(sin_citas)):
        motivos.append("falta_cifra_clave")
    return not motivos, motivos


__all__ = ["PROHIBIDAS", "verificar_respuesta"]
