"""Cada módulo, cuando ya expone su función pública, debe usar la firma del Anexo A.

Mientras un módulo no tenga su función, la prueba se marca como 'skip' (no rompe
make test). En cuanto la función existe, la firma se vuelve obligatoria.
"""

from __future__ import annotations

import importlib
import inspect

import pytest

from contratos.firmas import FIRMAS

CASOS = [(mod, fn, params) for mod, fns in FIRMAS.items() for fn, params in fns.items()]


@pytest.mark.parametrize("modulo,funcion,parametros", CASOS, ids=[f"{m}.{f}" for m, f, _ in CASOS])
def test_firma_publica(modulo, funcion, parametros):
    mod = importlib.import_module(modulo)
    fn = getattr(mod, funcion, None)
    if fn is None:
        pytest.skip(f"{modulo}.{funcion} aún no existe")
    reales = tuple(inspect.signature(fn).parameters)
    assert reales == parametros, f"{modulo}.{funcion}{reales} no coincide con el Anexo A {parametros}"


def test_app_no_importa_capas_internas():
    """La interfaz solo llama a servicio.*; nunca importa modelo, motor ni ingesta."""
    import ast
    from pathlib import Path

    prohibidos = {"modelo", "motor", "ingesta", "reglas", "datos"}
    app = Path(__file__).resolve().parents[2] / "src" / "app"
    for archivo in app.rglob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                raices = {a.name.split(".")[0] for a in nodo.names}
            elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
                raices = {nodo.module.split(".")[0]}
            else:
                continue
            malos = raices & prohibidos
            assert not malos, f"{archivo.name} importa {malos}: la app solo puede usar servicio"
