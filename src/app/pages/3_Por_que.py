"""Pantalla Por qué: rango de ingreso, pagos reservados, cálculo, confianza, supuestos, límites."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import componentes as c  # noqa: E402

PALABRA = {"alta": "alta", "media": "media", "baja": "baja"}

c.pagina("Por qué")
st.title("Por qué este número")
d = c.decision_de_sesion()
ev = d.evidencia

st.subheader("Cuánto se espera que entre en 14 días")
rango = ev.get("rango_14d")
if rango:
    escenarios = {"p5": "Semana muy mala (P5)", "p20": "Semana mala (P20)",
                  "p50": "Semana típica (P50)", "p80": "Semana buena (P80)"}
    df = pd.DataFrame({"Escenario": [escenarios.get(k, k) for k in rango], "Ingreso (S/)": list(rango.values())})
    st.bar_chart(df, x="Escenario", y="Ingreso (S/)", sort=False)
    st.dataframe(df, hide_index=True)
else:
    st.info("Este resultado no trae el rango de ingreso.")

st.subheader("Pagos reservados")
for pago in d.por_pago:
    c.semaforo(pago)
if not d.por_pago:
    st.write("No hay pagos con fecha en los próximos 14 días.")

with st.expander("Cómo se calculó"):
    puntos = d.desglose.get("puntos_de_control", [])
    limitante = d.desglose.get("dia_limitante")
    if puntos:
        tabla = pd.DataFrame(puntos).rename(columns={
            "dia": "Día", "ingreso_conservador": "Ingreso conservador (S/)",
            "pagos_acumulados": "Pagos acumulados (S/)", "permitido": "Permitido por día (S/)"})
        tabla["Limita"] = ["◀ limita" if p.get("dia") == limitante else "" for p in puntos]
        st.dataframe(tabla, hide_index=True)
        st.write(f"El punto que limita el número de hoy es el día {limitante}.")
    st.write(f"Saldo: {c.soles(d.desglose.get('saldo', 0))} · Colchón: {c.soles(d.desglose.get('colchon', 0))}")

st.subheader("Confianza: " + PALABRA[d.confianza])
sem = ev.get("semanas_historia")
razon = f"Se basa en {sem} semanas de historia" if sem is not None else "Historia no informada"
if rango:
    razon += f" y el ingreso de 14 días puede ir de {c.soles(rango['p5'])} a {c.soles(rango['p80'])}."
st.write(razon)

st.subheader("Supuestos y evidencia")
for t in d.supuestos:
    st.write("- " + t)
st.write(f"- Semanas de historia: {sem if sem is not None else '-'}")
st.write(f"- Ingresos observados: {ev.get('ingresos_observados', '-')}")

st.subheader("Límites")
for t in d.limites:
    st.write("- " + t)
c.aviso()
