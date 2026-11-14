"""Cada módulo expone sus funciones con la firma exacta (Anexo A de la v7, Anexo 5 de los planes).

Los esqueletos existen desde V0 con `raise NotImplementedError`: el dueño cambia el
cuerpo, nunca el nombre ni los parámetros. Si esta prueba falla, revisa la firma o
pide el cambio a Anderson y Gino (DECISIONES.md).
"""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

import pytest

from contratos.firmas import FIRMAS, NOMBRES_PUBLICOS

CASOS = [(mod, fn, params) for mod, fns in FIRMAS.items() for fn, params in fns.items()]
SRC = Path(__file__).resolve().parents[2] / "src"


def _resolver(modulo: str, nombre: str):
    objeto = importlib.import_module(modulo)
    for parte in nombre.split("."):
        objeto = getattr(objeto, parte, None)
        if objeto is None:
            return None
    return objeto


@pytest.mark.parametrize("modulo,funcion,parametros", CASOS, ids=[f"{m}.{f}" for m, f, _ in CASOS])
def test_firma_publica(modulo, funcion, parametros):
    fn = _resolver(modulo, funcion)
    assert fn is not None, f"{modulo}.{funcion} no existe: no borres el esqueleto, reemplaza su cuerpo"
    reales = tuple(p for p in inspect.signature(fn).parameters if p not in ("self", "cls"))
    assert reales == parametros, f"{modulo}.{funcion}{reales} no coincide con el Anexo A {parametros}"


@pytest.mark.parametrize(
    "modulo,nombre",
    [(m, n) for m, ns in NOMBRES_PUBLICOS.items() for n in ns],
    ids=[f"{m}.{n}" for m, ns in NOMBRES_PUBLICOS.items() for n in ns],
)
def test_nombres_publicos(modulo, nombre):
    assert _resolver(modulo, nombre) is not None, f"{modulo}.{nombre} debe existir (Anexo 5)"


def test_modelo_cargar_es_classmethod():
    from modelo import Modelo

    assert isinstance(inspect.getattr_static(Modelo, "cargar"), classmethod)


def _raices_importadas(archivo: Path) -> set[str]:
    raices: set[str] = set()
    for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
        if isinstance(nodo, ast.Import):
            nombres = [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            nombres = [nodo.module] + [f"{nodo.module}.{a.name}" for a in nodo.names]
        else:
            continue
        for n in nombres:
            partes = n.split(".")
            raices.add(partes[1] if partes[0] == "src" and len(partes) > 1 else partes[0])
    return raices


def test_app_no_importa_capas_internas():
    """La interfaz solo llama a servicio.*; nunca importa modelo, motor, ingesta, reglas ni datos."""
    prohibidos = {"modelo", "motor", "ingesta", "reglas", "datos", "generativa"}
    for archivo in (SRC / "app").rglob("*.py"):
        malos = _raices_importadas(archivo) & prohibidos
        assert not malos, f"{archivo.name} importa {malos}: la app solo puede usar servicio y contratos"
