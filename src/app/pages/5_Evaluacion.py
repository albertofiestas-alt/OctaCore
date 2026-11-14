"""Pantalla Evaluación: solo lectura de eval/resultados (nunca falla si falta un archivo)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # src/

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import componentes as c  # noqa: E402
from app import estado  # noqa: E402

RES = estado.resultados_dir()
RESPALDO = "[respaldo] simulador de respaldo (regla2 al P20), no el servicio real."
PENDIENTE = "Pendiente: todavía no está disponible ({}). Se mostrará cuando exista."
COLUMNAS_FRONTERA = {"metodo", "cuantil", "pct_descubiertos", "gasto_permitido"}


def _csv(nombre: str, columnas: tuple = ()):
    try:
        df = pd.read_csv(RES / nombre)
    except Exception:  # noqa: BLE001 - ausente o ilegible: se trata como pendiente
        return None
    return df if set(columnas) <= set(df.columns) else None


def _pendiente(nombre: str) -> None:
    st.info(PENDIENTE.format(nombre))


def _version_generador() -> str:
    try:
        from contratos import cargar_config

        return str(cargar_config()["version_generador"])
    except Exception:  # noqa: BLE001
        return "1.1"


def _adopcion() -> None:
    st.subheader("¿Se adopta el modelo de ML?")
    v = estado.adopcion()
    if v is None:
        return _pendiente("adopcion.json")
    st.write(("Sí se adopta. " if v.get("adopta") else "No se adopta: se usa la regla 2. ") + str(v.get("razon", "")))


def _pares(archivo: str, version: str) -> None:
    df = _csv(archivo, ("metrica", "media", "ic_inf", "ic_sup", "n"))
    st.markdown(f"**Generador {version}** · modelo menos regla 2, 20 semillas, IC95 · {RESPALDO}")
    if df is None:
        return _pendiente(archivo)
    filas = []
    for _, r in df.iterrows():
        pp = r["metrica"] == "pct_descubiertos"
        k = 100 if pp else 1
        filas.append({
            "Métrica": "Pagos descubiertos (pp)" if pp else "Gasto permitido (S/ por día)",
            "Media": round(r["media"] * k, 3),
            "IC95 inferior": round(r["ic_inf"] * k, 3),
            "IC95 superior": round(r["ic_sup"] * k, 3),
            "Semillas": int(r["n"]),
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True)


def _frontera(archivo: str, titulo: str) -> None:
    df = _csv(archivo)
    st.markdown(f"**{titulo}** · {RESPALDO}")
    if df is None:
        return _pendiente(archivo)
    if COLUMNAS_FRONTERA <= set(df.columns):
        graf = df.assign(pct_descubiertos=df["pct_descubiertos"] * 100)
        st.scatter_chart(graf, x="pct_descubiertos", y="gasto_permitido", color="metodo")
        st.caption("Eje x: % de pagos descubiertos. Eje y: gasto permitido por día (S/). Un color por método; cada punto es un cuantil.")
    st.dataframe(df, hide_index=True)


def _perturbado() -> None:
    archivos = sorted(p.name for p in RES.glob("frontera_perturbado*.csv")) if RES.exists() else []
    if not archivos:
        return _pendiente("frontera_perturbado.csv")
    for a in archivos:
        _frontera(a, f"Perturbado ({a.removesuffix('.csv').replace('frontera_perturbado', '') or 'generador 1.0'})")


def _ciego(archivo: str, nota: str) -> None:
    df = _csv(archivo, ("correcto",))
    if df is None or df.empty:
        return _pendiente(archivo)
    if "conjunto" in df.columns:  # las preguntas ciegas; los ataques se miden aparte
        df = df[df["conjunto"] == "ciego"]
    if df.empty:
        return _pendiente(archivo)
    ok, n = int(df["correcto"].sum()), len(df)
    st.write(f"- {archivo.removesuffix('.csv')}: exactitud de intención {ok}/{n} ({ok / n:.0%}). {nota}")


def _elegibilidad() -> None:
    with st.expander("Elegibilidad (experimento pre-registrado)"):
        st.caption("Señal indicativa, no es puntaje de crédito.")
        for t, brechas, tasas in [("Generador 1.0", "elegibilidad_brechas.csv", "elegibilidad_tasas.csv"),
                                  ("Generador 1.1", "elegibilidad_brechas_v11.csv", "elegibilidad_tasas_v11.csv")]:
            st.markdown(f"**{t}** · {RESPALDO}")
            for a in (tasas, brechas):
                df = _csv(a)
                st.dataframe(df, hide_index=True) if df is not None else _pendiente(a)


def _calidad() -> None:
    st.subheader("Calidad de los datos")
    try:
        r = json.loads((RES / "calidad_datos.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _pendiente("calidad_datos.json")
    a, b, d = st.columns(3)
    a.metric("Filas de entrada", r.get("filas_entrada", "-"))
    b.metric("Filas limpias", r.get("filas_salida", "-"))
    d.metric("Duplicados eliminados", r.get("duplicados_eliminados", "-"))
    st.write(f"- Atípicos: {r.get('atipicos', '-')} · PII enmascarada: {r.get('pii_enmascarado', 0)}")
    st.write(f"- Suscripciones duplicadas: {len(r.get('suscripciones_duplicadas', []))}")
    st.write(f"- Faltantes por columna: {r.get('faltantes', {})}")
    st.write(f"- Columnas sensibles descartadas: {r.get('columnas_sensibles_descartadas', [])}")


def _tabla(titulo: str, archivo: str) -> None:
    st.subheader(titulo)
    df = _csv(archivo)
    st.dataframe(df, hide_index=True) if df is not None else _pendiente(archivo)


def _salud() -> None:
    st.subheader("Salud del sistema")
    try:
        s = estado.salud()
    except Exception as e:  # noqa: BLE001
        return st.info(estado.mensaje_error(e))
    pares = [("p50", "p50 (ms)"), ("p95", "p95 (ms)"), ("tasa_error", "Tasa de error"), ("tasa_respaldo", "Tasa de respaldo")]
    for col, (k, nombre) in zip(st.columns(4), pares):
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
        return st.info(estado.mensaje_error(e))
    if not a.get("encontrado"):
        return st.warning(a.get("motivo", "No existe ese identificador en el registro."))
    st.write("Se reproduce: " + ("Sí" if a.get("se_reproduce") else "No") + (f" ({a['motivo']})" if a.get("motivo") else ""))
    st.json({k: a.get(k) for k in ("entradas", "decision", "version_modelo", "hash_config")})


c.pagina("Evaluación")
st.title("Evaluación")
c.banner_ejemplo()
st.info(f"Los datos son sintéticos: se demuestra el método, no la precisión en el mundo real. "
        f"Generador vigente: {_version_generador()}.")

_adopcion()
st.subheader("Pares de semillas")
_pares("pares.csv", "1.0")
_pares("pares_v11.csv", "1.1")
st.subheader("Frontera: gasto permitido vs pagos descubiertos")
_frontera("frontera.csv", "Generador 1.0")
_frontera("frontera_v11.csv", "Generador 1.1")
st.subheader("Frontera con el generador perturbado")
_perturbado()
st.subheader("Asistente: dos conjuntos ciegos")
_ciego("chat_ciego1.csv", "Este conjunto ya pasó a desarrollo (se usó para ajustar), así que no cuenta como ciego.")
_ciego("chat_ciego2.csv", "Segundo conjunto, no visto durante el desarrollo.")
_elegibilidad()
_tabla("Sesgos por grupo", "sesgos.csv")
_tabla("Ablaciones", "ablaciones.csv")
_calidad()
_salud()
_auditar()
c.aviso()
