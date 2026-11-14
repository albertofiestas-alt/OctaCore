"""Comandos del proyecto, en Python puro para que funcionen igual en Windows, macOS y Linux.

    python tareas.py setup   instala el entorno (.venv + requirements.txt)
    python tareas.py datos   genera los datos con la semilla de config/base.yaml
    python tareas.py test    corre todas las pruebas
    python tareas.py eval    produce la tabla de resultados y su hash
    python tareas.py demo    levanta la interfaz

Quien tenga make puede usar `make setup`, `make test`, etc.: el Makefile llama a este archivo.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
VENV = RAIZ / ".venv"
PY_VENV = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
PYTHON_REQUERIDO = (3, 11)


def _correr(*args: str | Path, env_extra: dict[str, str] | None = None) -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(RAIZ / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("PYTHONHASHSEED", "0")
    env.update(env_extra or {})
    print("$", " ".join(str(a) for a in args), flush=True)
    return subprocess.call([str(a) for a in args], cwd=RAIZ, env=env)


def _python() -> Path:
    if not PY_VENV.exists():
        sys.exit("No existe .venv. Corre primero: python tareas.py setup")
    return PY_VENV


def _pendiente(ruta: Path, duenio: str) -> bool:
    if ruta.exists():
        return False
    print(f"Pendiente: falta {ruta.relative_to(RAIZ)} (dueño: {duenio}).")
    return True


def setup() -> int:
    if sys.version_info[:2] != PYTHON_REQUERIDO:
        sys.exit(
            f"Necesitas Python {PYTHON_REQUERIDO[0]}.{PYTHON_REQUERIDO[1]} "
            f"(tienes {sys.version.split()[0]}). En Windows: py -3.11 tareas.py setup"
        )
    if not PY_VENV.exists():
        print("Creando .venv ...")
        venv.create(VENV, with_pip=True)
    py = _python()
    return (
        _correr(py, "-m", "pip", "install", "--upgrade", "pip")
        or _correr(py, "-m", "pip", "install", "-r", "requirements.txt")
        or _correr(py, "-m", "pip", "install", "-e", ".", "--no-deps")
    )


def datos() -> int:
    if _pendiente(RAIZ / "src/datos/__main__.py", "Rafael"):
        return 1
    return _correr(_python(), "-m", "datos")


def test() -> int:
    return _correr(_python(), "-m", "pytest", *sys.argv[2:])


def eval_() -> int:
    script = RAIZ / "eval/correr.py"
    if _pendiente(script, "Rafael y Gino"):
        return 1
    return _correr(_python(), script)


def demo() -> int:
    app = RAIZ / "src/app/main.py"
    if _pendiente(app, "Jesús y Alberto"):
        return 1
    return _correr(_python(), "-m", "streamlit", "run", app)


TAREAS = {"setup": setup, "datos": datos, "test": test, "eval": eval_, "demo": demo}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in TAREAS:
        print(__doc__)
        sys.exit(2)
    sys.exit(TAREAS[sys.argv[1]]())
