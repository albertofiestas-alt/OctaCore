"""Pantalla Evaluación (solo lectura de eval/resultados) + calidad de datos, salud y auditoría."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import componentes as c  # noqa: E402
from app import estado  # noqa: E402

RAIZ = Path(__file__).resolve().parents[3]
RESULTADOS = RAIZ / "eval" / "resultados"
FALTA = "Genera los resultados con: python tareas.py eval"


def _csv(nombre: str):
    ruta = RESULTADOS / nombre
    if not ruta.exists():
        return None
    try:
        return pd.read_csv(ruta)
    except Exception:  # noqa: BLE001 - archivo ilegible: se trata como ausente
        return None


def _tabla(titulo: str, nombre: str):
    st.subheader(titulo)
    df = _csv(nombre)
    if df is None:
        st.info(FALTA)
    else:
        st.dataframe(df, hide_index=True)
    return df


def _frontera(df) -> None:
    # ponytail: busca columnas por nombre aproximado; formato final de frontera.csv lo define Rafael.
    x = next((k for k in df.columns if "descub" in k.lower()), None)
    y = next((k for k in df.columns if "gasto" in k.lower()), None)
    m = next((k for k in df.columns if "metodo" in k.lower() or "método" in k.lower()), None)
    if x and y:
        st.scatter_chart(df, x=x, y=y, color=m)
    st.dataframe(df, hide_index=True)


def _calidad() -> None:
    st.subheader("Calidad de los datos")
    ruta = RESULTADOS / "calidad_datos.json"
    if not ruta.exists():
        st.info(FALTA)
        return
    r = json.loads(ruta.read_text(encoding="utf-8"))
    a, b, d = st.columns(3)
    a.metric("Filas de entrada", r.get("filas_entrada", "-"))
    b.metric("Filas limpias", r.get("filas_salida", "-"))
    d.metric("Duplicados eliminados", r.get("duplicados_eliminados", "-"))
    st.write(f"- Atípicos: {r.get('atipicos', '-')}")
    st.write(f"- Suscripciones duplicadas: {len(r.get('suscripciones_duplicadas', []))}")
    st.write(f"- Faltantes por columna: {r.get('faltantes', {})}")
    st.write(f"- PII enmascarada: {r.get('pii_enmascarado', 0)}")
    st.write(f"- Columnas sensibles descartadas: {r.get('columnas_sensibles_descartadas', [])}")


def _salud() -> None:
    st.subheader("Salud del sistema")
    try:
        s = estado.salud()
    except Exception as e:  # noqa: BLE001
        st.info(estado.mensaje_error(e))
        return
    cols = st.columns(4)
    for col, (k, nombre) in zip(cols, [("p50", "p50 (ms)"), ("p95", "p95 (ms)"),
                                       ("tasa_error", "Tasa de error"), ("tasa_respaldo", "Tasa de respaldo")]):
        v = s.get(k)
        col.metric(nombre, "sin datos" if v is None else v)
    st.caption(f"Consultas registradas: {s.get('consultas', 0)}")


def _auditar() -> None:
    st.subheader("Auditar una recomendación")
    rid = st.text_input("registro_id", placeholder="R-000000000001")
    if not rid:
        return
    try:
        a = estado.auditar(rid.strip())
    except Exception as e:  # noqa: BLE001
        st.info(estado.mensaje_error(e))
        return
    if not a.get("encontrado"):
        st.warning(a.get("motivo", "No existe ese identificador en el registro."))
        return
    st.write("Se reproduce: " + ("Sí" if a.get("se_reproduce") else "No") + (f" ({a['motivo']})" if a.get("motivo") else ""))
    st.json({k: a.get(k) for k in ("entradas", "decision", "version_modelo", "hash_config")})


c.pagina("Evaluación")
st.title("Evaluación")
c.banner_ejemplo()
st.info("Los datos son sintéticos: se demuestra el método, no la precisión en el mundo real.")

_tabla("Métricas", "resultados.csv")
st.subheader("Frontera: gasto permitido vs pagos descubiertos")
df = _csv("frontera.csv")
_frontera(df) if df is not None else st.info(FALTA)
_tabla("Robustez (generador perturbado)", "robustez.csv")
_tabla("Sesgos por grupo", "sesgos.csv")
_calidad()
_salud()
_auditar()
c.aviso()
