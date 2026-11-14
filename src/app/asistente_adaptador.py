"""Adaptador de la página del asistente: llama a asistente.flujo.preguntar; si aún no existe, responde de EJEMPLO.

La respuesta de ejemplo usa el clasificador, el RAG y las plantillas reales sobre una Decision de ejemplo
(servicio_falso). No simula: sin servicio.simular el escenario queda sin calcular. La página la rotula MODO DE EJEMPLO.
"""

from __future__ import annotations

from datetime import date

from app import estado
from asistente import flujo, intenciones, plantillas
from asistente.rag import BaseConocimiento
from contratos import Escenario, Respuesta, cargar_config

# Motivos fijos de asistente.guardia.revisar -> frase amable.
MOTIVOS = {
    "vacio": "Escribe una pregunta para que pueda ayudarte.",
    "control": "Tu pregunta trae caracteres que no puedo leer. Escríbela de nuevo con texto sencillo.",
    "largo": "Tu pregunta es muy larga (máximo {max} caracteres). Acórtala e inténtalo de nuevo.",
    "pii": "Parece que incluiste datos personales. No los escribas aquí; pregunta sin ellos.",
    "url": "No puedo abrir enlaces ni direcciones. Pregunta sin ellos.",
    "inyeccion": "No puedo seguir esa instrucción. Puedo ayudarte con tu número de hoy, tus pagos y escenarios de ingresos.",
    "otra_persona": "Solo puedo hablar de tu propia situación, no de otra persona.",
}
_NUMERICAS = ("explicar_numero", "estado_pago", "que_pasa_si", "propuesta")


def motivo_amable(motivo: str, cfg=None) -> str:
    cfg = cfg or cargar_config()
    return MOTIVOS.get(motivo, "No pude procesar esa pregunta. Reformúlala.").format(max=cfg["asistente"]["max_caracteres"])


def _guardia(texto: str, cfg) -> tuple[bool, str]:
    try:
        from asistente import guardia

        return guardia.revisar(texto, cfg)
    except NotImplementedError:  # ponytail: respaldo mínimo (vacío y largo) mientras la guardia real no exista
        if not texto.strip():
            return False, "vacio"
        return (False, "largo") if len(texto) > cfg["asistente"]["max_caracteres"] else (True, "")


def _rechazo(motivo: str, cfg) -> Respuesta:
    return Respuesta(texto=motivo_amable(motivo, cfg), intencion="rechazo", fuente="rechazo", datos={"motivo": motivo})


def _ejemplo(persona: str, fecha: date, texto: str) -> Respuesta:
    cfg = cargar_config()
    ok, motivo = _guardia(texto, cfg)
    if not ok:
        return _rechazo(motivo, cfg)
    intent = intenciones.clasificar(texto, cfg)
    if intent.confianza < cfg["asistente"]["umbral_intencion"]:
        cuerpo, acciones = plantillas.plantilla("reformular", {})
        return Respuesta(texto=cuerpo, intencion="reformular", fuente="plantilla", acciones=acciones)
    if intent.nombre == "fuera_de_alcance":
        return Respuesta(texto=plantillas.plantilla("fuera_de_alcance", {})[0], intencion=intent.nombre, fuente="rechazo")
    try:
        params = intenciones.parametros(texto, intent, cfg)
    except ValueError:
        return Respuesta(texto="Ese día o monto está fuera de lo que puedo simular (días 0 a 14, montos hasta 10000).",
                         intencion=intent.nombre, fuente="rechazo")
    decision = estado.consultar(persona, fecha)
    pasajes = [] if intent.nombre in ("estado_pago", "que_pasa_si") else BaseConocimiento().buscar(texto, k=1)
    esc = Escenario(**params) if intent.nombre == "que_pasa_si" else None
    res = plantillas.resultados_de(decision, escenario=esc, parametros=params if intent.nombre != "que_pasa_si" else None, pasajes=pasajes)
    cuerpo, acciones = plantillas.plantilla(intent.nombre, res)
    numerica = intent.nombre in _NUMERICAS
    citas = (["decision#1"] if numerica else []) + [p["id"] for p in pasajes]
    return Respuesta(texto=cuerpo, intencion=intent.nombre, fuente="motor" if numerica else "kb", citas=citas, acciones=acciones)


def responder(persona: str, fecha: date, texto: str) -> tuple[Respuesta, bool]:
    """(respuesta, es_ejemplo). Llama a asistente.flujo.preguntar(servicio, ...); sin flujo real o con APP_FAKE=1: ejemplo."""
    if not estado.es_ejemplo():
        try:
            return flujo.preguntar(estado._real(), persona, fecha, texto, None), False
        except NotImplementedError:
            pass
    return _ejemplo(persona, fecha, texto), True
