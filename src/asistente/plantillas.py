"""Respuestas de plantilla por intención (modo 1 y respaldo del modo 2). Dueño: Sebastián.

Hecho por delegación de Gino (DECISIONES #34). `resultados` es un dict plano que arma `resultados_de` desde la
Decision (y, si hay, el Escenario y la Decision simulada); la plantilla no calcula nada: solo da formato.
Las cifras se escriben sin separador de miles (S/1200) para que el verificador las compare igual.
"""

from __future__ import annotations

import re
from typing import Any

ETIQUETA = {"verde": "Cubierto", "ambar": "Con riesgo", "rojo": "No cubierto"}
SUGERENCIAS = [
    "¿Por qué puedo gastar este monto hoy?",
    "¿Estoy cubierto para mis pagos?",
    "¿Qué pasa si recibo un ingreso extra?",
]
_NO_ENTENDI = "No estoy seguro de haber entendido tu pregunta. Puedo ayudarte con tu número de hoy, tus pagos y escenarios de ingresos."
_FALTAN = re.compile(r"faltan S/(\d+(?:\.\d+)?)")


def _s(x: float) -> str:
    return f"S/{x:.0f}" if float(x).is_integer() else f"S/{x:.2f}"


def resultados_de(decision, *, escenario=None, simulada=None, parametros=None, pasajes=()) -> dict[str, Any]:
    """Dict serializable con lo que las plantillas pueden decir. No muta sus entradas."""
    d = decision
    faltan = _FALTAN.search(d.mensaje_falta or "")
    pagos = [p.model_dump() for p in d.por_pago]
    limitante = next((p for p in pagos if p["dia"] == d.desglose.get("dia_limitante")), None)
    prop = d.propuestas[0] if d.propuestas else None
    return {
        "numero_hoy": d.numero_hoy,
        "confianza": d.confianza,
        "respaldo": d.respaldo,
        "saldo": d.desglose.get("saldo"),
        "colchon": d.desglose.get("colchon"),
        "dia_limitante": d.desglose.get("dia_limitante"),
        "pago_limitante": limitante,
        "pagos": pagos,
        "faltante": float(faltan.group(1)) if faltan else None,
        "propuesta": None if prop is None else {
            "texto": prop.texto, "monto": prop.monto,
            "antes": prop.antes.get("numero_hoy"), "despues": prop.despues.get("numero_hoy"),
        },
        "escenario": None if escenario is None else escenario.model_dump(mode="json"),
        "despues": None if simulada is None else {
            "numero_hoy": simulada.numero_hoy, "pagos": [p.model_dump() for p in simulada.por_pago]},
        "parametros": dict(parametros or {}),
        "pasajes": [{"id": p["id"], "texto": p["texto"]} for p in pasajes],
    }


def _cita(res: dict[str, Any], defecto: str) -> str:
    p = (res.get("pasajes") or [None])[0]
    return f"{p['texto']} [{p['id']}]" if p else defecto


def _bloques(datos: str, significa: str, acciones: list[str]) -> tuple[str, list[str]]:
    hacer = "; ".join(acciones) if acciones else "Nada por ahora."
    return f"Datos: {datos}\nQué significa: {significa}\nQué puedes hacer: {hacer}", acciones


def _explicar(res):
    datos = f"Hoy puedes gastar hasta {_s(res['numero_hoy'])} (confianza {res['confianza']})."
    if res.get("saldo") is not None:
        datos += f" Saldo {_s(res['saldo'])}, colchón {_s(res.get('colchon') or 0)}."
    if res.get("pago_limitante"):
        p = res["pago_limitante"]
        datos += f" Limita el pago del día {p['dia']} por {_s(p['monto'])}."
    sig = _cita(res, "Es lo máximo que puedes gastar hoy sin fallar a tus pagos con fecha, con un ingreso conservador.")
    return _bloques(datos, sig, ["Ver el detalle en la pantalla Por qué", "Preguntar qué pasa si recibes un ingreso"])


def _estado(res):
    pagos, dia = res.get("pagos", []), res.get("parametros", {}).get("dia")
    if dia is not None:
        pagos = [p for p in pagos if p["dia"] == dia]
        if not pagos:
            return _bloques(f"No hay un pago con fecha el día {dia}.", "Solo reviso los pagos que se detectaron en tu historial.",
                            ["Preguntar por otro día", "Revisar la lista de pagos en la pantalla Hoy"])
    if not pagos:
        return _bloques("No hay pagos con fecha por ahora.", "No hay nada que cubrir en este periodo.", ["Preguntar por tu número de hoy"])
    datos = " ".join(f"Pago del día {p['dia']}, {_s(p['monto'])}: {ETIQUETA[p['semaforo']]}." for p in pagos)
    if res.get("faltante") is not None:
        datos += f" Con lo que hay hoy faltan S/{res['faltante']:.0f}." if float(res["faltante"]).is_integer() else f" Faltan {_s(res['faltante'])}."
    sig = "Cubierto: queda atendido aun con un ingreso conservador. Con riesgo: depende de que el ingreso llegue. No cubierto: no se alcanza hoy."
    return _bloques(datos, sig, ["Ver la propuesta de apartar", "Simular un ingreso extra"])


def _escenario_txt(esc) -> str:
    partes = [f"un ingreso de {_s(i['monto'])} el día {i['dia']}" for i in esc.get("ingresos_extra", [])]
    if esc.get("gasto_hoy"):
        partes.append(f"un gasto de {_s(esc['gasto_hoy'])} hoy")
    return " y ".join(partes) if partes else "ningún cambio"


def _que_pasa_si(res):
    esc = res.get("escenario") or {}
    if not res.get("despues"):
        return _bloques(f"Escenario: {_escenario_txt(esc)}. No pude calcular la simulación ahora; tu número de hoy sigue en {_s(res['numero_hoy'])}.",
                        "Sin el cálculo no puedo decirte cómo cambia.", ["Intentar de nuevo más tarde"])
    datos = f"Con {_escenario_txt(esc)}, tu número de hoy pasa de {_s(res['numero_hoy'])} a {_s(res['despues']['numero_hoy'])}."
    sig = "Es una simulación con un ingreso que tú indicas como conocido: no se mueve dinero ni cambian tus datos."
    return _bloques(datos, sig, ["Probar otro escenario", "Ver el plan en la pantalla Plan"])


def _propuesta(res):
    p = res.get("propuesta")
    if not p:
        return _bloques(f"Hoy puedes gastar hasta {_s(res['numero_hoy'])} y no hay una propuesta de apartar para tu caso.",
                        "El motor no encontró una forma de cubrir el pago con los datos disponibles.", ["Preguntar por el estado de tus pagos"])
    datos = f"{p['texto']} Tu número de hoy pasaría de {_s(p['antes'])} a {_s(p['despues'])}." if p["antes"] is not None and p["despues"] is not None else p["texto"]
    sig = _cita(res, "Apartar es una sugerencia simulada: aceptarla o rechazarla no mueve dinero.")
    return _bloques(datos, sig, ["Aceptar o rechazar la propuesta en la pantalla Plan (simulado)"])


def _concepto(res):
    if not res.get("pasajes"):
        return ("No encontré ese concepto en mi base de conocimiento. Prueba con otra palabra, por ejemplo semáforo o confianza.",
                SUGERENCIAS)
    return _cita(res, ""), ["Preguntar por tu número de hoy"]


_RECHAZO = ("Solo puedo ayudarte con tu número de hoy, tus pagos y escenarios de ingresos. No doy asesoría financiera "
            "ni hago operaciones.")


def plantilla(intencion: str, resultados: dict[str, Any]) -> tuple[str, list[str]]:
    """(texto, acciones) con tres bloques: Datos, Qué significa, Qué puedes hacer (acciones simuladas, nunca operaciones).
    Toda cifra del texto sale de `resultados`. Intención desconocida o 'reformular': pide reformular con 3 sugerencias."""
    f = {"explicar_numero": _explicar, "estado_pago": _estado, "que_pasa_si": _que_pasa_si,
         "propuesta": _propuesta, "concepto": _concepto}.get(intencion)
    if intencion == "fuera_de_alcance":
        return _RECHAZO, []
    if f is None:
        return _NO_ENTENDI, list(SUGERENCIAS)
    return f(resultados)


__all__ = ["plantilla", "resultados_de"]
