"""Entrada de la app: streamlit run src/app/main.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # src/

import streamlit as st  # noqa: E402

from app import componentes as c  # noqa: E402

c.pagina("Inicio")
st.title("¿Cuánto puedo gastar hoy sin fallar a un pago con fecha?")
c.banner_ejemplo()
st.write("Elige una pantalla:")
st.page_link("pages/1_Hoy.py", label="Hoy: tu número y tus pagos")
st.page_link("pages/2_Plan.py", label="Plan propuesto")
st.page_link("pages/3_Por_que.py", label="Por qué este número")
st.page_link("pages/4_Asistente.py", label="Asistente: pregunta con citas")
st.page_link("pages/5_Evaluacion.py", label="Evaluación")
c.aviso()
