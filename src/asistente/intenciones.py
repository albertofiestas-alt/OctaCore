"""Intención y parámetros de la pregunta (clasificador ML de TF-IDF y regresión logística, o LLM). Dueño: Gino.

Rechazo de parámetros: `parametros` lanza `ValueError` con un motivo fijo (`dia_fuera_de_rango`,
`monto_fuera_de_rango`, `demasiados_ingresos`); el flujo lo convierte en una respuesta de rechazo.
Todos los umbrales viven en config/asistente.yaml.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold, train_test_split
from sklearn.pipeline import FeatureUnion, make_pipeline

from asistente.prompts import SISTEMA_CLASIFICADOR
from contratos.config import RAIZ

if TYPE_CHECKING:
    from contratos import Config

log = logging.getLogger(__name__)

INTENCIONES = ("explicar_numero", "estado_pago", "que_pasa_si", "propuesta", "concepto", "fuera_de_alcance")
_CLAVES_LLM = frozenset({"intencion", "monto", "dia", "pago_ref"})


@dataclass(frozen=True)
class Intencion:
    nombre: str
    confianza: float
    monto: float | None = None
    dia: int | None = None


# --------------------------------------------------------------------------- #
# Clasificador ML
# --------------------------------------------------------------------------- #


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sin_tildes.lower()


def _ruta(csv: str | Path) -> Path:
    p = Path(csv)
    return p if p.is_absolute() or not (RAIZ / p).exists() else RAIZ / p


def _nuevo_pipe():
    return make_pipeline(
        FeatureUnion(
            [
                ("pal", TfidfVectorizer(strip_accents="unicode", ngram_range=(1, 2))),
                ("car", TfidfVectorizer(strip_accents="unicode", analyzer="char_wb", ngram_range=(2, 4))),
            ]
        ),
        LogisticRegression(max_iter=1000),
    )


def entrenar_clasificador(csv: str = "data/chat/preguntas.csv", semilla: int = 20261114) -> tuple[Any, float]:
    """(pipeline, exactitud en la partición de prueba 80/20 estratificada)."""
    df = pd.read_csv(_ruta(csv))
    x_tr, x_te, y_tr, y_te = train_test_split(
        df.texto, df.intencion, test_size=0.2, stratify=df.intencion, random_state=semilla
    )
    pipe = _nuevo_pipe().fit(x_tr, y_tr)
    return pipe, float(pipe.score(x_te, y_te))


def _plantilla(texto: str) -> str:
    """Forma de la pregunta sin tildes, mayúsculas, signos ni cifras: las gemelas de plantilla comparten grupo."""
    return " ".join(re.sub(r"[^a-z# ]", " ", re.sub(r"\d+", "#", _normalizar(texto))).split())


def exactitud_sin_fuga(csv: str = "data/chat/preguntas.csv", semilla: int = 20261114) -> tuple[float, int]:
    """(exactitud, n de prueba) con ~20 % de prueba agrupado por plantilla: ninguna gemela cae en entrenamiento."""
    df = pd.read_csv(_ruta(csv))
    grupos = df.texto.map(_plantilla)
    corte = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=semilla)
    tr, te = next(corte.split(df.texto, df.intencion, grupos))
    pipe = _nuevo_pipe().fit(df.texto.iloc[tr], df.intencion.iloc[tr])
    return float(pipe.score(df.texto.iloc[te], df.intencion.iloc[te])), len(te)


@lru_cache(maxsize=4)
def _entrenado(csv: str, semilla: int):
    return entrenar_clasificador(csv, semilla)[0]


# --------------------------------------------------------------------------- #
# Validación de rangos (sirve al texto y al LLM)
# --------------------------------------------------------------------------- #


def _numero(valor: Any) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError("tipo_invalido")
    return float(valor)


def _validar_monto(valor: Any, a: Config) -> float:
    monto = _numero(valor)
    if not a["monto_minimo"] <= monto <= a["monto_maximo"]:
        raise ValueError("monto_fuera_de_rango")
    return monto


def _validar_dia(valor: Any, a: Config) -> int:
    dia = _numero(valor)
    if not dia.is_integer() or not a["dia_minimo"] <= dia <= a["dia_maximo"]:
        raise ValueError("dia_fuera_de_rango")
    return int(dia)


# --------------------------------------------------------------------------- #
# Clasificar
# --------------------------------------------------------------------------- #


def _con_llm(texto: str, proveedor: Any, cfg: Config) -> Intencion:
    a = cfg["asistente"]
    crudo = proveedor.generar(SISTEMA_CLASIFICADOR, json.dumps({"pregunta_dato": texto}, ensure_ascii=False))
    obj = json.loads(crudo)
    if not isinstance(obj, dict) or set(obj) != _CLAVES_LLM:
        raise ValueError("claves_invalidas")
    if obj["intencion"] not in INTENCIONES:
        raise ValueError("intencion_fuera_de_lista")
    if obj["pago_ref"] is not None and not isinstance(obj["pago_ref"], str):
        raise ValueError("pago_ref_invalido")
    monto = None if obj["monto"] is None else _validar_monto(obj["monto"], a)
    dia = None if obj["dia"] is None else _validar_dia(obj["dia"], a)
    return Intencion(obj["intencion"], float(a["confianza_llm"]), monto, dia)


def _ajustar_con_palabras_clave(intent: Intencion, texto: str, cfg: Config) -> Intencion:
    """Respaldo: con confianza ML baja, la primera intención (por prioridad) cuyas palabras aparezcan manda.
    La confianza del ML no se toca: el flujo decide con ella si pide reformular."""
    a = cfg["asistente"]
    if intent.confianza >= a["confianza_reglas"]:
        return intent
    t = _normalizar(texto)
    for nombre, claves in a["palabras_clave"].items():
        if any(re.search(r"\b" + re.escape(c.strip()) + r"\b", t) for c in claves):
            return replace(intent, nombre=nombre)
    return intent


def clasificar(texto: str, cfg: Config, proveedor: Any | None = None) -> Intencion:
    """Modo 2 con LLM (JSON cerrado, validado en código); si falla o no hay proveedor: clasificador ML y palabras clave."""
    a = cfg["asistente"]
    if proveedor is not None and a["modo"] == 2:
        try:
            return _con_llm(texto, proveedor, cfg)
        except Exception as e:  # cualquier fallo del proveedor o del JSON cae al ML; no se registra el texto
            log.info("clasificar: LLM descartado (%s)", type(e).__name__)
    pipe = _entrenado(a["csv_preguntas"], a["semilla_clasificador"])
    probas = pipe.predict_proba([texto])[0]
    mejor = int(probas.argmax())
    intent = Intencion(str(pipe.classes_[mejor]), float(probas[mejor]))
    return _ajustar_con_palabras_clave(intent, texto, cfg)


# --------------------------------------------------------------------------- #
# Parámetros: monto y día por expresiones regulares
# --------------------------------------------------------------------------- #

_RE_DIA = re.compile(r"\bdia\s+(\d{1,2})\b|\bel\s+(\d{1,2})\b|\b(hoy)\b")
_RE_MONTO = re.compile(r"(?<![a-z\d])(?:s/\.?\s*)?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:[.,]\d{1,2})?)")
_RE_MILES = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?")


def _a_numero(crudo: str) -> float:
    return float(crudo.replace(",", "") if _RE_MILES.fullmatch(crudo) else crudo.replace(",", "."))


def _distancia(ini_a: int, fin_a: int, ini_b: int, fin_b: int) -> int:
    return max(ini_a - fin_b, ini_b - fin_a, 0)


def _dias(t: str) -> list[tuple[int, int, int]]:
    """(día, inicio, fin) de cada mención de día; 'hoy' = 0. Puede traer días fuera de rango: se validan al usarlos."""
    return [(0 if m.group(3) else int(m.group(1) or m.group(2)), m.start(), m.end()) for m in _RE_DIA.finditer(t)]


def _es_gasto(palabras: list[str], a: Config) -> bool:
    """La palabra de gasto o de ingreso más cercana al monto (la última antes de él) decide; sin ninguna: ingreso."""
    for p in reversed(palabras):
        if p in a["ingreso_palabras"]:
            return False
        if p in a["gasto_palabras"]:
            return True
    return False


def _montos(t: str, dias: list[tuple[int, int, int]], a: Config) -> list[dict[str, Any]]:
    """Montos (sin contar los números que son días) con su día y si son gasto.

    Gasto o ingreso: la palabra más cercana antes del monto, entre el monto anterior y este. El día de un monto es la mención de día
    más cercana a él, y cada mención de día se le da solo a su monto más cercano.
    """
    limpio = t
    for _, ini, fin in dias:
        limpio = limpio[:ini] + " " * (fin - ini) + limpio[fin:]
    montos, previo = [], 0
    for m in _RE_MONTO.finditer(limpio):
        gasto = _es_gasto(re.findall(r"[a-z]+", limpio[previo : m.start()]), a)
        montos.append({"monto": _a_numero(m.group(1)), "gasto": gasto, "dia": None, "ini": m.start(), "fin": m.end()})
        previo = m.end()
    for dia, ini, fin in dias:
        if montos:
            dueno = min(montos, key=lambda o: _distancia(ini, fin, o["ini"], o["fin"]))
            if dueno["dia"] is None:
                dueno["dia"] = dia
    return montos


def parametros(texto: str, intent: Intencion, cfg: Config) -> dict[str, Any]:
    """Escenario validado: día 0..14, monto 0..10000, máximo 3 ingresos extra; gasto_hoy 0..10000.

    que_pasa_si -> {"ingresos_extra": [{"dia", "monto"}], "gasto_hoy"} (encaja en `Escenario`).
    otra intención -> {"dia", "monto"} (None si no se dicen). Lanza ValueError si algo está fuera de rango.
    """
    a = cfg["asistente"]
    t = _normalizar(texto)
    dias = _dias(t)
    encontrados = _montos(t, dias, a)
    if not encontrados and intent.monto is not None:  # los que extrajo el LLM, validados igual
        encontrados = [{"monto": intent.monto, "gasto": _es_gasto(re.findall(r"[a-z]+", t), a), "dia": intent.dia}]
    for e in encontrados:
        _validar_monto(e["monto"], a)

    if intent.nombre != "que_pasa_si":
        primer_dia = dias[0][0] if dias else intent.dia
        return {
            "dia": None if primer_dia is None else _validar_dia(primer_dia, a),
            "monto": encontrados[0]["monto"] if encontrados else None,
        }

    ingresos = [e for e in encontrados if not e["gasto"]]
    if len(ingresos) > a["max_ingresos_extra"]:
        raise ValueError("demasiados_ingresos")
    ingresos_extra = [
        {"dia": _validar_dia(a["dia_por_defecto"] if e["dia"] is None else e["dia"], a), "monto": e["monto"]}
        for e in ingresos
    ]
    gasto_hoy = _validar_monto(sum(e["monto"] for e in encontrados if e["gasto"]), a)
    return {"ingresos_extra": ingresos_extra, "gasto_hoy": gasto_hoy}


__all__ = ["INTENCIONES", "Intencion", "clasificar", "entrenar_clasificador", "exactitud_sin_fuga", "parametros"]
