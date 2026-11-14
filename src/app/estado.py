"""Persona, fecha y método en la sesión + adaptador al servicio.

La app solo habla con `servicio` y `contratos`. Si servicio lanza NotImplementedError
(la capa real aún no existe) o APP_FAKE=1, se usa servicio_falso y la UI muestra
el aviso 'DATOS DE EJEMPLO' (es_ejemplo()).
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

import streamlit as st

from app import servicio_falso

PERSONAS = list(servicio_falso.PERSONAS)
FECHA_DEMO = date(2025, 11, 14)


def es_ejemplo() -> bool:
    return os.environ.get("APP_FAKE") == "1" or bool(st.session_state.get("ejemplo", False))


def _real():
    import servicio  # forma recomendada en docs/arranque.md

    return servicio


def _llamar(nombre: str, *args):
    """Llama al servicio real; si no está implementado, cae al de ejemplo."""
    if not es_ejemplo():
        try:
            return getattr(_real(), nombre)(*args)
        except NotImplementedError:
            st.session_state["ejemplo"] = True
    return getattr(servicio_falso, nombre)(*args)


def resultados_dir() -> Path:
    """eval/resultados (UKKU_RESULTADOS lo reemplaza, para pruebas)."""
    return Path(os.environ.get("UKKU_RESULTADOS") or Path(__file__).resolve().parents[2] / "eval" / "resultados")


def adopcion() -> dict | None:
    """Veredicto pre-registrado de adopción del modelo, o None si no se puede leer."""
    try:
        return json.loads((resultados_dir() / "adopcion.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# Por diseño el producto usa regla2: el modelo de ML no superó a la regla (adopcion.json).
def consultar(persona, fecha, metodo="regla2"):
    return _llamar("consultar", persona, fecha, metodo)


def responder(propuesta_id, accion):
    return _llamar("responder", propuesta_id, accion)


def salud():
    return _llamar("salud")


def auditar(registro_id):
    return _llamar("auditar", registro_id)


def mensaje_error(e: Exception) -> str:
    return getattr(e, "mensaje_usuario", None) or (
        "No pudimos calcular tu número. Intenta con otra persona o fecha."
    )
