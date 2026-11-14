"""Orquestación: guardia, intención, parámetros, herramientas, RAG, redacción, verificación y registro. Dueño: Anderson.
Respaldo hecho por delegación de Gino (DECISIONES #33), modo 1 (sin LLM). Si Anderson sube el suyo, lo reemplaza.

    guardia -> intención (bajo umbral_intencion pide reformular) -> parámetros (fuera de rango = rechazo amable)
    -> herramienta (servicio.consultar; que_pasa_si calcula el escenario) -> rag -> plantilla -> verificador -> registro

Usa las piezas de otros dueños: plantillas.resultados_de/plantilla (Sebastián), rag.BaseConocimiento/kb_dinamica (Rafael).
Único punto de enchufe pendiente: servicio.simular (Anderson). Si existe se usa; si no, _escenario_temporal calcula el
número del escenario con la fórmula del diseño sobre el desglose de la Decision (solo P20).

Convención de la página: todo rechazo lleva Respuesta.datos["motivo"] (fijo) y ["capa"] (guardia, intencion, parametros,
servicio, flujo); Respuesta.texto ya es un mensaje amable. Las citas van en Respuesta.citas.
"""

from __future__ import annotations

import logging
import math
import time
from datetime import date, datetime
from typing import Any

from asistente import guardia, intenciones, plantillas, rag
from asistente.verificador import verificar_respuesta
from contratos import Escenario, Respuesta, cargar_config
from servicio.registro import agregar_jsonl, nuevo_id

log = logging.getLogger(__name__)

_SEGURA = ("No pude verificar esta respuesta con tus datos, así que prefiero no mostrarla. "
           "Revisa la pantalla Hoy o reformula tu pregunta.")
_USAN_CONOCIMIENTO = ("explicar_numero", "propuesta")


def _s(x: Any) -> str:
    v = float(x)
    return str(int(v)) if v.is_integer() else f"{v:.2f}"


# --------------------------------------------------------------------------- #
# Rechazos y mensajes
# --------------------------------------------------------------------------- #


def _mensajes(a: Any) -> dict[str, str]:
    return {
        "vacio": "Escribe una pregunta sobre tu número de hoy, tus pagos o un escenario de ingresos.",
        "control": "Tu mensaje tiene caracteres que no puedo leer. Escríbelo de nuevo en texto simple.",
        "largo": f"Tu pregunta es muy larga: resúmela en una o dos frases (máximo {a['max_caracteres']} caracteres).",
        "pii": "Por tu seguridad no escribas DNI, teléfonos, correos ni tarjetas. Hazme la pregunta sin esos datos.",
        "url": "No abro enlaces. Hazme la pregunta sin direcciones web.",
        "inyeccion": "No puedo hacer eso. Solo ayudo con tu número de hoy, tus pagos y escenarios de ingresos.",
        "otra_persona": "Solo puedo hablar de tus propios datos, no de los de otras personas.",
        "fuera_de_alcance": plantillas.plantilla("fuera_de_alcance", {})[0],
        "dia_fuera_de_rango": f"Por ahora solo veo hasta {a['dia_maximo']} dias hacia adelante. "
                              f"Dime un día entre {a['dia_minimo']} (hoy) y {a['dia_maximo']}.",
        "monto_fuera_de_rango": f"Los montos que puedo simular van de S/{_s(a['monto_minimo'])} a "
                                f"S/{_s(a['monto_maximo'])}. Prueba con otro monto.",
        "demasiados_ingresos": f"Puedo simular hasta {a['max_ingresos_extra']} ingresos a la vez. Prueba con menos.",
        "parametros_invalidos": "No pude entender los montos o los días de tu pregunta. Prueba con algo como "
                                "«¿y si cobro S/200 el día 5?».",
        "error_interno": "Algo salió mal de mi lado. Intenta de nuevo en un momento.",
    }


def _rechazo(motivo: str, capa: str, a: Any, intencion: str = "fuera_de_alcance", texto: str | None = None) -> Respuesta:
    return Respuesta(texto=texto or _mensajes(a)[motivo], intencion=intencion, fuente="rechazo",
                     datos={"motivo": motivo, "capa": capa})


def _reformular() -> Respuesta:
    texto, acciones = plantillas.plantilla("reformular", {})
    return Respuesta(texto=texto, intencion="reformular", fuente="plantilla",
                     datos={"motivo": "baja_confianza", "capa": "intencion"}, acciones=acciones)


# --------------------------------------------------------------------------- #
# Escenario de que_pasa_si
# --------------------------------------------------------------------------- #


def _sin_cubrir(dia: int, monto: float, numerador: float) -> dict[str, Any]:
    return {"dia": dia, "monto": monto, "falta": int(math.ceil(-numerador))}


def _escenario_temporal(d: Any, esc: Escenario) -> tuple[int, list[dict[str, Any]]]:
    """TEMPORAL: la fórmula del diseño (saldo - gasto + ingreso conservador + ingresos conocidos - pagos - colchón) sobre
    los puntos de control del desglose de la Decision, solo en el escenario del número de hoy (P20)."""
    des = d.desglose
    nums = {}
    for p in des["puntos_de_control"]:
        extra = sum(i.monto for i in esc.ingresos_extra if i.dia <= p["dia"])
        nums[p["dia"]] = (des["saldo"] - esc.gasto_hoy + p["ingreso_conservador"] + extra - p["pagos_acumulados"]
                          - des["colchon"])
    minimo = min(n / max(dia, 1) for dia, n in nums.items())
    sin = [_sin_cubrir(p.dia, p.monto, nums[p.dia]) for p in d.por_pago if p.dia in nums and nums[p.dia] < 0]
    return int(math.floor(max(0.0, minimo))), sin


# --------------------------------------------------------------------------- #
# Conocimiento (RAG)
# --------------------------------------------------------------------------- #

_KB: list[Any] = []  # caché: [] sin intentar, [BaseConocimiento] lista, [None] no disponible


def _buscar(texto: str, k: int) -> list[dict[str, Any]]:
    """Pasajes kb:archivo#n con score >= 0.15 (el umbral es el de rag.buscar); lista vacía si no hay evidencia."""
    if not _KB:
        try:
            _KB.append(rag.BaseConocimiento())
        except Exception:  # noqa: BLE001
            log.warning("asistente: base de conocimiento no disponible")
            _KB.append(None)
    if _KB[0] is None:
        return []
    try:
        return _KB[0].buscar(texto, k=k)
    except Exception:  # noqa: BLE001
        return []


# --------------------------------------------------------------------------- #
# Flujo
# --------------------------------------------------------------------------- #


def _cerrar(r: Respuesta, resultados: dict[str, Any], pasajes: list[dict[str, Any]], cfg: Any) -> Respuesta:
    ok, motivos = verificar_respuesta({"respuesta": r.texto, "citas": r.citas}, resultados, pasajes, cfg)
    if ok:
        return r.model_copy(update={"datos": {**r.datos, "verificacion": "ok"}})
    return Respuesta(texto=_SEGURA, intencion=r.intencion, fuente="plantilla", datos={**r.datos, "verificacion": motivos},
                     acciones=["Ver la pantalla Hoy"])


def _concepto(texto: str, cfg: Any) -> Respuesta:
    pasajes = _buscar(texto, 3)[:1]
    res = {"intencion": "concepto", "pasajes": [{"id": p["id"], "texto": p["texto"]} for p in pasajes]}
    cuerpo, acciones = plantillas.plantilla("concepto", res)  # sin pasajes: dice que no tiene información
    citas = [p["id"] for p in pasajes]
    r = Respuesta(texto=cuerpo, intencion="concepto", fuente="kb" if citas else "plantilla", citas=citas,
                  datos={"capa": "conocimiento"}, acciones=acciones)
    return _cerrar(r, res, pasajes, cfg)


def _con_decision(servicio: Any, cfg: Any, intencion: str, params: dict[str, Any], texto: str, decision: Any,
                  customer_id: str, fecha: date) -> Respuesta:
    pasajes = _buscar(texto, 1) if intencion in _USAN_CONOCIMIENTO else []
    datos: dict[str, Any] = {"numero_hoy": int(decision.numero_hoy), "confianza": decision.confianza}
    if intencion == "que_pasa_si":
        esc = Escenario(**params)
        simular = getattr(servicio, "simular", None)
        if callable(simular):  # punto de enchufe: servicio.simular(customer_id, fecha, escenario) -> Decision
            simulada = simular(customer_id, fecha, esc)
            despues = int(simulada.numero_hoy)
            sin = [_sin_cubrir(p.dia, p.monto, p.permitido * max(p.dia, 1)) for p in simulada.por_pago if p.permitido < 0]
            res = plantillas.resultados_de(decision, escenario=esc, simulada=simulada)
        else:
            despues, sin = _escenario_temporal(decision, esc)
            res = plantillas.resultados_de(decision, escenario=esc)
            res["despues"] = {"numero_hoy": despues, "pagos": []}
        datos = {"antes": {"numero_hoy": int(decision.numero_hoy)},
                 "despues": {"numero_hoy": despues, "pagos_sin_cubrir": sin}}
        clave = despues
    else:
        res = plantillas.resultados_de(decision, parametros=params, pasajes=pasajes)
        clave = res["numero_hoy"]
        if intencion == "estado_pago":  # la plantilla nombra los pagos, no el número de hoy: su cifra clave es el monto
            dia = params.get("dia")
            nombrados = [p for p in res["pagos"] if dia is None or p["dia"] == dia]
            clave = nombrados[0]["monto"] if nombrados else None
    cuerpo, acciones = plantillas.plantilla(intencion, res)
    citas = ["decision#1"] + [p["id"] for p in pasajes if f"[{p['id']}]" in cuerpo]
    r = Respuesta(texto=cuerpo, intencion=intencion, fuente="motor", citas=citas, datos=datos, acciones=acciones)
    permitidos = rag.kb_dinamica(decision) + pasajes
    return _cerrar(r, {**res, "intencion": intencion, "cifra_clave": clave}, permitidos, cfg)


def _responder(servicio: Any, cfg: Any, customer_id: str, fecha: date, texto: str, ctx: dict[str, Any]):
    a = cfg["asistente"]
    ok, motivo = guardia.revisar(texto, cfg)
    if not ok:
        return _rechazo(motivo, "guardia", a), {}

    intent = intenciones.clasificar(texto, cfg, ctx.get("proveedor"))
    info = {"intencion": intent.nombre, "confianza": round(float(intent.confianza), 3)}
    if intent.confianza < a["umbral_intencion"]:
        return _reformular(), info
    if intent.nombre == "fuera_de_alcance":
        return _rechazo("fuera_de_alcance", "intencion", a), info
    try:
        params = intenciones.parametros(texto, intent, cfg)
    except ValueError as e:
        motivo = str(e) if str(e) in _mensajes(a) else "parametros_invalidos"
        return _rechazo(motivo, "parametros", a, intent.nombre), info

    if intent.nombre == "concepto":
        return _concepto(texto, cfg), info

    if intent.nombre == "que_pasa_si" and not params["ingresos_extra"] and not params["gasto_hoy"]:
        ejemplos = ["¿Y si cobro S/200 el día 5?", "¿Y si gasto S/80 hoy?"]
        texto_r = f"Para simular necesito un monto: por ejemplo «{ejemplos[0]}» o «{ejemplos[1]}»."
        return (Respuesta(texto=texto_r, intencion="que_pasa_si", fuente="plantilla",
                          datos={"motivo": "sin_monto", "capa": "parametros"}, acciones=ejemplos), info)

    try:
        decision = servicio.consultar(customer_id, fecha, "modelo")
    except Exception as e:  # noqa: BLE001
        mensaje = getattr(e, "mensaje_usuario", None)
        if not mensaje:
            raise
        return Respuesta(texto=mensaje, intencion=intent.nombre, fuente="rechazo",
                         datos={"motivo": "servicio", "capa": "servicio"}), info
    info["decision_registro_id"] = decision.registro_id
    return _con_decision(servicio, cfg, intent.nombre, params, texto, decision, customer_id, fecha), info


def _registrar(cfg: Any, r: Respuesta, info: dict[str, Any], customer_id: str, fecha: date, texto: Any, ms: float) -> None:
    ruta = cfg["asistente"].get("ruta_registro_chat")
    if not ruta:
        return
    agregar_jsonl({
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"), "registro_id": r.registro_id,
        "customer_id": customer_id, "fecha": str(fecha),
        "pregunta": guardia.enmascarar_para_registro(texto, cfg), "intencion": r.intencion,
        "confianza": info.get("confianza"), "fuente": r.fuente, "capa": r.datos.get("capa"),
        "motivo": r.datos.get("motivo"), "verificacion": r.datos.get("verificacion", "no_aplica"),
        "citas": r.citas, "latencia_ms": round(ms, 1), "decision_registro_id": info.get("decision_registro_id"),
    }, ruta)


def preguntar(servicio: Any, customer_id: str, fecha: date, texto: str, contexto: dict[str, Any] | None = None) -> Respuesta:
    """Una pregunta, una Respuesta. Nunca lanza hacia la app: cualquier fallo es un rechazo o una plantilla."""
    t0 = time.perf_counter()
    cfg: Any = None
    try:
        cfg = servicio._cfg() if callable(getattr(servicio, "_cfg", None)) else cargar_config()
        r, info = _responder(servicio, cfg, customer_id, fecha, texto, contexto or {})
    except Exception as e:  # noqa: BLE001 - nada llega a la app
        log.warning("asistente: fallo interno (%s)", type(e).__name__)
        r, info = Respuesta(texto="Algo salió mal de mi lado. Intenta de nuevo en un momento.", intencion="fuera_de_alcance",
                            fuente="rechazo", datos={"motivo": "error_interno", "capa": "flujo"}), {}
    r = r.model_copy(update={"registro_id": nuevo_id()})
    try:
        if cfg is not None:
            _registrar(cfg, r, info, customer_id, fecha, texto, (time.perf_counter() - t0) * 1000)
    except Exception as e:  # noqa: BLE001 - el registro nunca rompe la respuesta
        log.warning("asistente: no se pudo registrar (%s)", type(e).__name__)
    return r


__all__ = ["preguntar"]
