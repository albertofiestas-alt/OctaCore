"""Pantalla Asistente: chat con citas. Solo llama a asistente.flujo.preguntar (vía el adaptador)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import asistente_adaptador as adaptador  # noqa: E402
from app import componentes as c  # noqa: E402
from contratos.config import RAIZ  # noqa: E402

INTENCIONES_EJEMPLO = ("explicar_numero", "estado_pago", "que_pasa_si")
ETIQUETA_FUENTE = {"motor": "cálculo del motor", "kb": "base de conocimiento", "plantilla": "plantilla",
                   "generativa": "texto generado y verificado", "rechazo": "rechazo"}


def ejemplos() -> list[str]:
    df = pd.read_csv(RAIZ / "data" / "chat" / "preguntas.csv")
    return [df[df.intencion == i].texto.iloc[0] for i in INTENCIONES_EJEMPLO]


def pedir(texto: str) -> None:
    st.session_state["pendiente"] = texto


def pintar(r, ejemplo: bool) -> None:
    cuerpo = r.texto or adaptador.motivo_amable((r.datos or {}).get("motivo", ""))
    cuerpo = cuerpo.replace("\n", "  \n")
    if r.fuente == "rechazo":
        st.warning("No puedo responder eso. " + cuerpo)
    elif r.intencion == "reformular":
        st.info("¿Puedes reformularlo? " + cuerpo)
    else:
        st.markdown(cuerpo)
    if r.citas:
        st.caption("Fuentes: " + ", ".join(r.citas))
    st.caption(f"Origen: {ETIQUETA_FUENTE.get(r.fuente, r.fuente)}" + (" · MODO DE EJEMPLO" if ejemplo else ""))


c.pagina("Asistente")
st.title("Asistente")
st.caption("Pregunta sobre tu número de hoy, tus pagos o un escenario de ingresos. No es asesoría financiera.")
persona, fecha = c.selector()
ss = st.session_state
historial = ss.setdefault("chat", [])

st.write("Prueba con un ejemplo:")
for col, texto in zip(st.columns(len(INTENCIONES_EJEMPLO)), ejemplos()):
    col.button(texto, on_click=pedir, args=(texto,), key=f"ej_{texto}")

pregunta = st.chat_input("Escribe tu pregunta (máximo 200 caracteres)") or ss.pop("pendiente", None)
if pregunta:
    try:
        with st.spinner("Pensando…"):
            respuesta, ejemplo = adaptador.responder(persona, fecha, pregunta)
        historial.append({"pregunta": pregunta, "respuesta": respuesta, "ejemplo": ejemplo})
    except Exception:  # noqa: BLE001 - la UI nunca muestra traceback
        st.error("No pude responder ahora. Intenta de nuevo o reformula tu pregunta.")

if any(h["ejemplo"] for h in historial):
    st.warning("MODO DE EJEMPLO: el asistente real aún no responde; esta respuesta usa datos ficticios de ejemplo.")
for h in historial:
    with st.chat_message("user"):
        st.write(h["pregunta"])
    with st.chat_message("assistant"):
        pintar(h["respuesta"], h["ejemplo"])
c.aviso()
