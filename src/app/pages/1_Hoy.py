"""Pantalla Hoy: el número de hoy, el semáforo de pagos de 14 días, supuestos y límites."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/

import streamlit as st  # noqa: E402

from app import componentes as c  # noqa: E402

c.pagina("Hoy")
st.title("Hoy")
d = c.decision_de_sesion()

c.numero_hoy(d)
st.markdown(f"**Confianza {d.confianza}.**")
if d.explicacion:
    st.write(d.explicacion)

st.subheader("Tus pagos de los próximos 14 días")
if d.por_pago:
    for pago in d.por_pago:
        c.semaforo(pago)
else:
    st.info("No hay pagos con fecha en los próximos 14 días.")

with st.expander("Supuestos y límites", expanded=True):
    for texto in [*d.supuestos, *d.limites]:
        st.write("- " + texto)

c.aviso()
