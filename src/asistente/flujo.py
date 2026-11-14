"""Orquestación: guardia, intención, parámetros, herramientas, RAG, redacción, verificación y registro. Dueño: Anderson.
Respaldo hecho por delegación de Gino (DECISIONES #33), modo 1 (sin LLM). Si Anderson sube el suyo, lo reemplaza.

    guardia -> intención (bajo umbral_intencion pide reformular) -> parámetros (fuera de rango = rechazo amable)
    -> herramienta (servicio.consultar; que_pasa_si calcula el escenario) -> plantilla -> verificador -> registro

Puntos de enchufe (todo lo TEMPORAL se reemplaza sin tocar el resto):
    asistente.plantillas.plantilla   Sebastián. Si lanza NotImplementedError se usan las _PLANTILLAS_TEMPORAL de aquí.
    asistente.rag.BaseConocimiento   Rafael. Si falla se usa el _GLOSARIO_TEMPORAL de aquí.
    servicio.simular                 Anderson. Si existe se usa; si no, _escenario_temporal (misma fórmula del diseño).
"""

from __future__ import annotations

import logging
import math
import time
import unicodedata
from datetime import date, datetime
from typing import Any

from asistente import guardia, intenciones, plantillas, rag
from asistente.verificador import verificar_respuesta
from contratos import Escenario, Respuesta, cargar_config
from servicio.registro import agregar_jsonl, nuevo_id

log = logging.getLogger(__name__)

SUGERENCIAS = ["¿Por qué puedo gastar hoy lo que me dices?", "¿Estoy cubierto para mis próximos pagos?",
               "¿Y si cobro S/200 el día 5?"]
_SEGURA = ("No pude verificar esta respuesta con tus datos, así que prefiero no mostrarla. "
           "Revisa la pantalla Hoy o reformula tu pregunta.")


def _s(x: Any) -> str:
    v = float(x)
    return str(int(v)) if v.is_integer() else f"{v:.2f}"


def _sin_tildes(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()


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
        "fuera_de_alcance": "Solo ayudo con tu número de hoy, tus pagos y escenarios de ingresos; no doy asesoría "
                            "financiera ni muevo dinero.",
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
    return Respuesta(
        texto="No estoy seguro de haber entendido tu pregunta. ¿Puedes reformularla? Prueba con una de estas:",
        intencion="no_entendida", fuente="plantilla", datos={"motivo": "baja_confianza", "capa": "intencion"},
        acciones=list(SUGERENCIAS))


# --------------------------------------------------------------------------- #
# Resultados de las herramientas
# --------------------------------------------------------------------------- #


def _base(intencion: str, d: Any) -> dict[str, Any]:
    des = d.desglose
    pagos = [{"dia": p.dia, "monto": p.monto, "permitido": p.permitido, "semaforo": p.semaforo} for p in d.por_pago]
    faltante = des.get("faltante")
    return {
        "intencion": intencion, "numero_hoy": int(d.numero_hoy), "confianza": d.confianza, "saldo": des.get("saldo"),
        "dia_limitante": des.get("dia_limitante"), "pagos": pagos,
        "pago_limite": next((p for p in pagos if p["dia"] == des.get("dia_limitante")), None),
        "faltante": None if faltante is None else int(faltante),
        "propuesta": next((p.model_dump(mode="json") for p in d.propuestas), None),
        "rango_14d": d.evidencia.get("rango_14d"),
    }


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


def _escenario(servicio: Any, customer_id: str, fecha: date, d: Any, params: dict[str, Any]):
    esc = Escenario(**params)
    simular = getattr(servicio, "simular", None)
    if callable(simular):  # punto de enchufe: servicio.simular(customer_id, fecha, escenario) -> Decision
        despues = simular(customer_id, fecha, esc)
        sin = [_sin_cubrir(p.dia, p.monto, p.permitido * max(p.dia, 1)) for p in despues.por_pago if p.permitido < 0]
        return int(despues.numero_hoy), sin
    return _escenario_temporal(d, esc)


# --------------------------------------------------------------------------- #
# Plantillas TEMPORALES (modo 1). Las de Sebastián entran por plantillas.plantilla
# --------------------------------------------------------------------------- #


def _t_explicar(r: dict[str, Any]) -> tuple[str, list[str]]:
    pl = r["pago_limite"]
    limita = (f"el pago de S/{_s(pl['monto'])} del día {pl['dia']}" if pl else f"llegar al día {r['dia_limitante']}")
    texto = (f"Datos: hoy puedes gastar hasta S/{r['numero_hoy']}. Confianza {r['confianza']}. Lo que más limita es "
             f"{limita}. Qué significa: es el menor de los montos diarios que dejan cubiertos tus pagos con fecha "
             "usando un ingreso prudente (escenario P20). Qué puedes hacer: abre la pantalla Por qué para ver cada "
             "punto de control. Es una simulación.")
    return texto, ["Ver la pantalla Por qué", "Preguntar si un pago está cubierto"]


def _elegir_pago(r: dict[str, Any], dia: int | None, monto: float | None) -> dict[str, Any] | None:
    pagos = r["pagos"]
    if dia is None:
        return min(pagos, key=lambda p: p["permitido"]) if pagos else None
    return next((p for p in pagos if p["dia"] == dia and (monto is None or abs(p["monto"] - monto) < 1)), None)


_SEMAFORO = {
    "verde": "está en verde: se cubre incluso en una semana muy mala (P5)",
    "ambar": "está en ámbar: se cubre con un ingreso normal (P50) pero no en una semana muy mala (P5)",
    "rojo": "está en rojo: con el ingreso esperado no alcanza",
}


def _t_estado(r: dict[str, Any]) -> tuple[str, list[str]]:
    p = r["pago_elegido"]
    if p is None:
        dias = " y ".join(str(x["dia"]) for x in r["pagos"])
        extra = f" Tus pagos próximos caen los días {dias}." if r["pagos"] else " No veo pagos con fecha próximos."
        dia = r["dia_pedido"]
        cabeza = f"No veo un pago el día {dia} en los próximos 14 días." if dia is not None else "No veo pagos."
        datos = f"{cabeza}{extra}"
    else:
        datos = f"El pago de S/{_s(p['monto'])} del día {p['dia']} {_SEMAFORO[p['semaforo']]}."
        if p["semaforo"] == "rojo" and p["dia"] == r["dia_limitante"] and r["faltante"]:
            datos += f" Faltan S/{r['faltante']}."
    texto = (f"Datos: {datos} Hoy puedes gastar hasta S/{r['numero_hoy']}. Qué puedes hacer: abre la pantalla Plan "
             "para ver tus pagos. Es una simulación.")
    return texto, ["Ver la pantalla Plan", "Preguntar qué pasa si cobro algo más"]


def _t_propuesta(r: dict[str, Any]) -> tuple[str, list[str]]:
    if r["propuesta"]:
        datos = f"{r['propuesta']['texto']} Hoy puedes gastar hasta S/{r['numero_hoy']}."
        signif = "Qué significa: la propuesta aguanta una semana muy mala (P5)."
    elif r["faltante"]:
        datos = (f"No hay una propuesta para ti ahora. Con tu saldo y el ingreso esperado faltan S/{r['faltante']} "
                 f"para el pago del día {r['dia_limitante']}. Hoy puedes gastar hasta S/{r['numero_hoy']}.")
        signif = "Qué significa: sin ese monto no hay cómo apartar dinero para ese pago."
    else:
        datos = f"No hay una propuesta para ti ahora. Hoy puedes gastar hasta S/{r['numero_hoy']}."
        signif = ("Qué significa: la confianza es baja y por eso no propongo apartar dinero."
                  if r["confianza"] == "baja" else "Qué significa: no hace falta apartar más para tus pagos.")
    return (f"Datos: {datos} {signif} Qué puedes hacer: tú decides; es una simulación y no se mueve dinero.",
            ["Ver la pantalla Plan"])


def _t_que_pasa_si(r: dict[str, Any]) -> tuple[str, list[str]]:
    partes = []
    if r["gasto_hoy"]:
        partes.append(f"gastas S/{_s(r['gasto_hoy'])} hoy")
    partes += [f"cobras S/{_s(i['monto'])} el día {i['dia']}" for i in r["ingresos_extra"]]
    sin = r["pagos_sin_cubrir"]
    signif = ("con ese escenario " + "; ".join(
        f"el pago de S/{_s(p['monto'])} del día {p['dia']} no queda cubierto (faltan S/{p['falta']})" for p in sin[:2])
        if sin else "con ese escenario tus pagos con fecha siguen cubiertos con el ingreso prudente (P20)")
    texto = (f"Datos: si {' y '.join(partes)}, tu número de hoy pasa de S/{r['numero_hoy_antes']} a "
             f"S/{r['numero_hoy']}. Qué significa: {signif}. Qué puedes hacer: es una simulación, no se mueve "
             "dinero; prueba otro monto u otro día.")
    return texto, ["Probar otro monto", "Probar otro día"]


_PLANTILLAS_TEMPORAL = {"explicar_numero": _t_explicar, "estado_pago": _t_estado, "propuesta": _t_propuesta,
                        "que_pasa_si": _t_que_pasa_si}


def _plantilla(intencion: str, resultados: dict[str, Any]) -> tuple[str, list[str]]:
    try:
        return plantillas.plantilla(intencion, resultados)  # punto de enchufe (Sebastián)
    except NotImplementedError:
        return _PLANTILLAS_TEMPORAL[intencion](resultados)


_GLOSARIO_TEMPORAL = (
    (("confianza",), "La confianza (alta, media o baja) dice qué tan estable es tu ingreso reciente: depende del ancho "
                     "del rango pronosticado y de cuántas semanas de historia hay. Con confianza baja conviene tomar "
                     "el número con más cautela."),
    (("p5", "p20", "p50", "p80", "cuantil", "percentil", "escenario"),
     "Los escenarios P5, P20, P50 y P80 son cuantiles del ingreso esperado: P20 es una semana mala moderada y P5 una "
     "semana muy mala. El número de hoy usa P20 para ser prudente."),
    (("semaforo", "verde", "ambar", "rojo"),
     "El semáforo mira cada pago con fecha: verde se cubre incluso en una semana muy mala, ámbar solo con un ingreso "
     "normal y rojo no se cubre con el ingreso esperado. No es una probabilidad."),
    (("colchon",), "El colchón es un monto que se reserva y no se cuenta como dinero disponible para gastar."),
    (("pagos con fecha", "pago con fecha"),
     "Son pagos que se repiten en una fecha (alquiler, servicios, cuotas) y que la herramienta detecta en tu historial."),
    (("supuesto",), "Los supuestos: gastas cada día lo que indica el número de hoy, el ingreso futuro se parece al "
                    "reciente y no hay gastos imprevistos."),
    (("simulacion", "orientacion", "educativa"),
     "Es una orientación educativa en simulación: no mueve dinero ni sustituye asesoría financiera."),
    (("numero de hoy", "numero hoy"),
     "El número de hoy es lo máximo que puedes gastar por día sin fallar a un pago con fecha, usando un ingreso "
     "prudente."),
)
_KB: list[Any] = []  # caché de la base de conocimiento: [] sin intentar, [obj] lista, [None] no disponible


def _conocimiento(texto: str) -> tuple[str, list[str], list[dict[str, Any]]]:
    """(texto, citas, pasajes). Punto de enchufe: asistente.rag; si no está, el glosario TEMPORAL."""
    if not _KB:
        try:
            _KB.append(rag.BaseConocimiento())
        except Exception:  # noqa: BLE001 - la base de Rafael aún no existe: se usa el glosario
            _KB.append(None)
    if _KB[0] is not None:
        try:
            pasajes = _KB[0].buscar(texto)
        except Exception:  # noqa: BLE001
            pasajes = []
        if pasajes:
            return " ".join(pasajes[0]["texto"].split()[:80]), [pasajes[0]["id"]], pasajes[:1]
    t = _sin_tildes(texto)
    for claves, respuesta in _GLOSARIO_TEMPORAL:
        if any(c in t for c in claves):
            return respuesta, [], []
    return ("No tengo información sobre eso en mi base de conocimiento. Puedo explicarte tu número de hoy, un pago o "
            "un escenario de ingresos."), [], []


# --------------------------------------------------------------------------- #
# Flujo
# --------------------------------------------------------------------------- #


def _cerrar(r: Respuesta, resultados: dict[str, Any], pasajes: list[dict[str, Any]], cfg: Any) -> Respuesta:
    ok, motivos = verificar_respuesta({"respuesta": r.texto, "citas": r.citas}, resultados, pasajes, cfg)
    if ok:
        return r.model_copy(update={"datos": {**r.datos, "verificacion": "ok"}})
    return Respuesta(texto=_SEGURA, intencion=r.intencion, fuente="plantilla", datos={**r.datos, "verificacion": motivos},
                     acciones=["Ver la pantalla Hoy"])


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
        respuesta, citas, pasajes = _conocimiento(texto)
        r = Respuesta(texto=f"Qué significa: {respuesta}", intencion="concepto", fuente="kb" if citas else "plantilla",
                      citas=citas, datos={"capa": "conocimiento"}, acciones=["Preguntar por mi número de hoy"])
        return _cerrar(r, {"intencion": "concepto"}, pasajes, cfg), info

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

    resultados = _base(intent.nombre, decision)
    datos: dict[str, Any] = {"numero_hoy": resultados["numero_hoy"], "confianza": decision.confianza}
    if intent.nombre == "estado_pago":
        resultados["dia_pedido"] = params["dia"]
        resultados["pago_elegido"] = _elegir_pago(resultados, params["dia"], params["monto"])
    elif intent.nombre == "que_pasa_si":
        despues, sin = _escenario(servicio, customer_id, fecha, decision, params)
        resultados |= {"numero_hoy_antes": resultados["numero_hoy"], "numero_hoy": despues, "pagos_sin_cubrir": sin,
                       "gasto_hoy": params["gasto_hoy"], "ingresos_extra": params["ingresos_extra"]}
        datos = {"antes": {"numero_hoy": resultados["numero_hoy_antes"]},
                 "despues": {"numero_hoy": despues, "pagos_sin_cubrir": sin}}
    texto_r, acciones = _plantilla(intent.nombre, resultados)
    r = Respuesta(texto=texto_r, intencion=intent.nombre, fuente="motor", datos=datos, acciones=acciones)
    return _cerrar(r, resultados, [], cfg), info


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
