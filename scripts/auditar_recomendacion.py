"""Reconstruye una recomendación desde su identificador (trazabilidad auditable, Challenge pack).

    python scripts/auditar_recomendacion.py R-1a2b3c4d5e6f

Muestra entradas, decisión, versiones, hash de la configuración y si se reproduce.
Sale con código 0 si se reproduce, 1 si no y 2 si el identificador no existe.
Dueño: Anderson.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import servicio  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("registro_id", help="identificador que trae Decision.registro_id (R-...)")
    args = parser.parse_args(argv)

    resultado = servicio.auditar(args.registro_id)
    print(json.dumps(resultado, indent=2, ensure_ascii=False, sort_keys=True))
    if not resultado["encontrado"]:
        return 2
    return 0 if resultado["se_reproduce"] else 1


if __name__ == "__main__":
    sys.exit(main())
