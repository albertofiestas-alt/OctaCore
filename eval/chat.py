"""Evaluación del asistente (opción C): 30 preguntas ciegas y 12 ataques, en modo 1 y modo 2. Dueño: Gino.

Alcance de esta versión (solo la capa de intención, modo 1):
- exactitud de intención sobre data/chat/ciego_*.csv (o un conjunto PROVISIONAL propio si aún no existen),
- rechazo correcto sobre data/chat/ataques.csv y sobre las preguntas fuera de alcance,
- latencia p50/p95 de guardia + intención + parámetros (sin el entrenamiento inicial).
Modo 2, cifras verificadas, citas y plantillas necesitan flujo/verificador/proveedor: no se miden aquí.
Los umbrales de aprobación van en config/preregistro.yaml; esta evaluación NO emite veredicto pasa/no pasa.
"""

from __future__ import annotations

import glob
import sys
import time
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ / "src") not in sys.path:  # permite `python eval/chat.py`
    sys.path.insert(0, str(RAIZ / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from asistente import guardia, intenciones  # noqa: E402
from contratos import cargar_config  # noqa: E402

MAX_TEXTO_CSV = 80  # el CSV guarda solo el comienzo de cada pregunta

# PROVISIONAL: 18 preguntas de Gino (3 por intención) para probar la tubería; NO sustituyen al conjunto ciego.
CIEGO_PROVISIONAL = (
    ("¿Por qué hoy me sale tan poco para gastar?", "explicar_numero"),
    ("Cuéntame de dónde sale la cifra que veo en pantalla", "explicar_numero"),
    ("¿Cómo se armó mi número de esta mañana?", "explicar_numero"),
    ("¿Llego al pago de la luz del día 8?", "estado_pago"),
    ("¿Mi renta del día 2 queda cubierta?", "estado_pago"),
    ("¿Voy bien para el pago del colegio el día 11?", "estado_pago"),
    ("¿Qué pasaría si me cae S/120 el día 4?", "que_pasa_si"),
    ("Y si hoy hago una compra de S/90", "que_pasa_si"),
    ("Simula que cobro S/300 el día 9", "que_pasa_si"),
    ("¿Qué me aconsejas separar para llegar al pago?", "propuesta"),
    ("Dime cómo no quedarme corto esta semana", "propuesta"),
    ("¿Hay alguna acción para mejorar mi semáforo?", "propuesta"),
    ("¿Qué significa tener confianza baja?", "concepto"),
    ("Explícame qué es un cuantil", "concepto"),
    ("¿Qué quiere decir semáforo ámbar?", "concepto"),
    ("¿Dónde conviene invertir mis ahorros?", "fuera_de_alcance"),
    ("Pídeme un taxi al aeropuerto", "fuera_de_alcance"),
    ("¿Quién ganó el partido de ayer?", "fuera_de_alcance"),
)

COLUMNAS = ("conjunto", "texto", "esperado", "intencion_pred", "confianza", "rechazado", "capa_rechazo", "correcto", "latencia_ms")


def _ruta(p: str) -> str:
    return p if Path(p).is_absolute() else str(RAIZ / p)


def _cargar_ciegos(a: Any) -> tuple[str, list[tuple[str, str]]]:
    archivos = sorted(glob.glob(_ruta(a["ruta_ciegos"])))
    if not archivos:
        return "PROVISIONAL", list(CIEGO_PROVISIONAL)
    filas = pd.concat([pd.read_csv(f) for f in archivos], ignore_index=True)
    return Path(a["ruta_ciegos"]).name, list(zip(filas["texto"], filas["intencion"], strict=True))


def _responder(texto: str, cfg: Any) -> dict[str, Any]:
    """Guardia, intención y parámetros (modo 1). Devuelve la intención y la capa que rechazó, si alguna."""
    t0 = time.perf_counter()
    capa, guardia_ok, nombre, confianza = None, True, None, None
    try:
        ok, _motivo = guardia.revisar(texto, cfg)
        if not ok:
            capa = "guardia"
    except NotImplementedError:
        guardia_ok = False  # se declara; no se reimplementa la guardia de Mathias
    if capa is None:
        intent = intenciones.clasificar(texto, cfg)
        nombre, confianza = intent.nombre, intent.confianza
        if nombre == "fuera_de_alcance":
            capa = "intencion"
        else:
            try:
                intenciones.parametros(texto, intent, cfg)
            except ValueError:
                capa = "parametros"
    return {
        "intencion_pred": nombre,
        "confianza": confianza,
        "rechazado": capa is not None,
        "capa_rechazo": capa,
        "guardia_disponible": guardia_ok,
        "latencia_ms": (time.perf_counter() - t0) * 1000,
    }


def evaluar_chat(cfg: Any | None = None) -> dict[str, Any]:
    """Exactitud de intención, % de cifras verificadas, rechazo correcto, % con cita, cifras inventadas antes del
    verificador, latencia p50 y p95 y fallback a plantilla. Guarda eval/resultados/chat.csv.

    Devuelve el resumen (dict). Lo que necesita flujo, verificador o proveedor queda en `no_medido`."""
    cfg = cfg or cargar_config()
    a = cfg["asistente"]
    origen, ciegos = _cargar_ciegos(a)
    ataques = pd.read_csv(_ruta(a["ruta_ataques"]))
    intenciones.clasificar("calentamiento", cfg)  # entrena una vez fuera de la medición de latencia

    filas = []
    for texto, esperado in ciegos:
        r = _responder(texto, cfg)
        correcto = r["intencion_pred"] == esperado if r["intencion_pred"] else (esperado == "fuera_de_alcance" and r["rechazado"])
        filas.append({"conjunto": "ciego" if origen != "PROVISIONAL" else "provisional", "texto": texto, "esperado": esperado, **r, "correcto": correcto})
    for texto, esperado in zip(ataques["texto"], ataques["esperado"], strict=True):
        r = _responder(texto, cfg)
        filas.append({"conjunto": "ataque", "texto": texto, "esperado": esperado, **r, "correcto": r["rechazado"]})
    df = pd.DataFrame(filas)

    ciego = df[df.conjunto != "ataque"]
    ataque = df[df.conjunto == "ataque"]
    fuera = ciego[ciego.esperado == "fuera_de_alcance"]
    dentro = ciego[ciego.esperado != "fuera_de_alcance"]
    resumen = {
        "ciego_origen": origen,
        "n_ciegos": len(ciego),
        "exactitud_intencion": float(ciego.correcto.mean()),
        "n_ataques": len(ataque),
        "rechazo_correcto_ataques": float(ataque.rechazado.mean()),
        "rechazo_correcto_fuera_de_alcance": float(fuera.rechazado.mean()) if len(fuera) else None,
        "falso_rechazo_dentro_de_alcance": float(dentro.rechazado.mean()) if len(dentro) else None,
        "rechazo_por_capa_ataques": {k: int(v) for k, v in ataque.capa_rechazo.fillna("ninguna").value_counts().items()},
        "guardia_disponible": bool(df.guardia_disponible.all()),
        "latencia_p50_ms": float(np.percentile(df.latencia_ms, 50)),
        "latencia_p95_ms": float(np.percentile(df.latencia_ms, 95)),
        "latencia_alcance": "guardia + intención + parámetros, modo 1, sin entrenamiento inicial",
        "modo2": "no corrido (sin proveedor autorizado ni flujo)",
        "no_medido": ["cifras_verificadas", "citas", "cifras_inventadas_antes_del_verificador", "fallback_a_plantilla"],
    }

    df["texto"] = df["texto"].str.slice(0, MAX_TEXTO_CSV)
    salida = Path(_ruta(a["ruta_resultados_chat"]))
    salida.parent.mkdir(parents=True, exist_ok=True)
    df[list(COLUMNAS)].to_csv(salida, index=False, encoding="utf-8")
    return resumen


if __name__ == "__main__":
    for clave, valor in evaluar_chat().items():
        print(f"{clave}: {valor}")
