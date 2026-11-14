"""Pantalla Plan propuesto: propuesta, efecto antes/después, confianza y botones Aprobar/Rechazar."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/

import streamlit as st  # noqa: E402

from app import componentes as c  # noqa: E402
from app import estado  # noqa: E402

ETIQUETAS = {"numero_hoy": "Número de hoy (S/ por día)", "cubierto_en_p5": "Pago cubierto en una semana muy mala"}


def _valor(k, v):
    if isinstance(v, bool):
        return "Sí" if v else "No"
    return c.soles(v) if k == "numero_hoy" else str(v)


def _responder(propuesta_id: str, accion: str) -> None:
    clave = f"resp_{propuesta_id}"
    if clave in st.session_state:  # una sola respuesta por propuesta
        return
    try:
        st.session_state[clave] = estado.responder(propuesta_id, accion)
    except Exception as e:  # noqa: BLE001
        st.session_state[clave] = {"ok": False, "mensaje": estado.mensaje_error(e)}


def _sin_propuesta(d) -> str:
    if d.numero_hoy == 0:
        return "No hay propuesta: ni gastando S/0 alcanza para el pago. " + (d.mensaje_falta or "")
    if d.confianza == "baja":
        return "No hay propuesta: con tan poca historia solo se muestra el número de hoy."
    return "No hay propuesta: tus pagos ya están cubiertos en una semana mala."


c.pagina("Plan")
st.title("Plan propuesto")
d = c.decision_de_sesion()

if not d.propuestas:
    st.info(_sin_propuesta(d))
else:
    p = d.propuestas[0]
    st.subheader(p.texto)
    st.markdown(f"**Confianza {p.confianza}.**")
    claves = [k for k in p.antes if k in p.despues] or list(p.antes)
    st.table(
        {
            "": [ETIQUETAS.get(k, k) for k in claves],
            "Antes": [_valor(k, p.antes.get(k, "-")) for k in claves],
            "Después": [_valor(k, p.despues.get(k, "-")) for k in claves],
        }
    )
    st.write("Evidencia:")
    ev = d.evidencia
    st.write(f"- Semanas de historia: {ev.get('semanas_historia', '-')}")
    rango = ev.get("rango_14d")
    if rango:
        st.write("- Ingreso esperado en 14 días: " + ", ".join(f"{k.upper()} {c.soles(v)}" for k, v in rango.items()))

    resp = st.session_state.get(f"resp_{p.propuesta_id}")
    col1, col2 = st.columns(2)
    col1.button("Aprobar", on_click=_responder, args=(p.propuesta_id, "aprobar"),
                disabled=resp is not None, key=f"ap_{p.propuesta_id}")
    col2.button("Rechazar", on_click=_responder, args=(p.propuesta_id, "rechazar"),
                disabled=resp is not None, key=f"re_{p.propuesta_id}")
    if resp:
        (st.success if resp.get("ok") else st.warning)(resp.get("mensaje", ""))

with st.expander("Límites", expanded=True):
    for t in d.limites:
        st.write("- " + t)
c.aviso()
