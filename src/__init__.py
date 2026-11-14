"""Raíz del código. Forma recomendada de importar: `import servicio`, `from contratos import Decision`.

Con `python tareas.py setup` el proyecto queda instalado y esos imports funcionan en
pytest, en scripts y en Streamlit sin tocar sys.path.

Si alguien importa con el prefijo `src.` (p. ej. `from src import servicio`), este
archivo hace que reciba EL MISMO módulo, y no una segunda copia con otro estado
(otro registro de salud, otras clases de contrato).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

_SRC = str(Path(__file__).resolve().parent)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

PAQUETES = ("contratos", "datos", "ingesta", "reglas", "modelo", "motor", "servicio", "app", "generativa")

# Los que la app usa se enlazan ya, para que `import src.contratos` no cree un duplicado.
for _nombre in ("contratos", "servicio", "app"):
    sys.modules.setdefault(f"{__name__}.{_nombre}", importlib.import_module(_nombre))


def __getattr__(nombre: str) -> ModuleType:
    if nombre in PAQUETES:
        modulo = importlib.import_module(nombre)
        sys.modules.setdefault(f"{__name__}.{nombre}", modulo)
        return modulo
    raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")
