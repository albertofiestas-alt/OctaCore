"""Piezas visuales compartidas (Hoy, Plan, Por qué, Evaluación)."""

from __future__ import annotations

import streamlit as st

from app import estado, tema

AVISO = (
    "Orientación educativa basada en una simulación con datos ficticios. "
    "No es asesoría financiera ni ejecuta operaciones."
)


def soles(x: float) -> str:
    return f"S/{x:,.0f}" if float(x).is_integer() else f"S/{x:,.2f}"


def aviso() -> None:
    st.caption(AVISO)


def banner_ejemplo() -> None:
    if estado.es_ejemplo():
        st.warning("DATOS DE EJEMPLO: el servicio real aún no responde; no son cifras de una persona.")


def banner_respaldo(decision) -> None:
    if decision.respaldo:
        st.warning("Se está usando la regla sencilla porque el modelo no está disponible.")


def numero_hoy(decision) -> None:
    if decision.numero_hoy == 0 and decision.mensaje_falta:
        st.error(decision.mensaje_falta[:1].upper() + decision.mensaje_falta[1:])
    st.markdown(
        '<div class="numero-hoy"><small>Hoy puedes gastar hasta</small>'
        f"{soles(decision.numero_hoy)}</div>",
        unsafe_allow_html=True,
    )


def semaforo(pago) -> None:
    """Texto + símbolo + color (nunca solo color)."""
    s = pago.semaforo
    st.markdown(
        f'<div class="estado {s}"><b>{tema.SIMBOLO[s]} {tema.ETIQUETA[s]}</b> · '
        f"Día {pago.dia} · {soles(pago.monto)}</div>",
        unsafe_allow_html=True,
    )


def selector() -> tuple[str, object]:
    """Persona y fecha compartidas entre páginas (viven en session_state)."""
    ss = st.session_state
    prev = ss.get("persona", estado.PERSONAS[0])
    persona = st.selectbox(
        "Persona de demo", estado.PERSONAS, index=estado.PERSONAS.index(prev), key="w_persona"
    )
    fecha = st.date_input("Fecha de corte", value=ss.get("fecha", estado.FECHA_DEMO), key="w_fecha")
    ss["persona"], ss["fecha"] = persona, fecha
    return persona, fecha


def pagina(titulo: str) -> None:
    st.set_page_config(page_title=f"Ukku · {titulo}", layout="centered")
    tema.aplicar()


def decision_de_sesion():
    """Pinta selector, consulta y devuelve la Decision (o detiene la página con un mensaje)."""
    persona, fecha = selector()
    try:
        with st.spinner("Calculando…"):
            d = estado.consultar(persona, fecha)
    except Exception as e:  # noqa: BLE001 - la UI nunca muestra traceback
        st.error(estado.mensaje_error(e))
        aviso()
        st.stop()
    banner_ejemplo()
    banner_respaldo(d)
    return d
