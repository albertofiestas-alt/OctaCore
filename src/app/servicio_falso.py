"""Servicio de ejemplo: misma firma que `servicio`, devuelve las fixtures de tests/fixtures.

Se usa con APP_FAKE=1 o cuando servicio.consultar aún no está implementado.
Todo lo que devuelve es DATO DE EJEMPLO y la interfaz lo rotula así.
"""

from __future__ import annotations

import json
from pathlib import Path

from contratos import Decision

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
MENSAJE_SIMULACION = "Simulación: no se movió ningún dinero."
PERSONAS = {  # persona de demo -> fixture
    "P0001": "decision_verde",
    "P0002": "decision_rojo",
    "P0003": "decision_confianza_baja",
    "P0005": "decision_sin_alcance",
    "P0006": "decision_verde",
}


def consultar(customer_id, fecha, metodo="modelo") -> Decision:
    nombre = PERSONAS.get(customer_id, "decision_verde")
    return Decision.model_validate_json((FIXTURES / f"{nombre}.json").read_text(encoding="utf-8"))


def responder(propuesta_id, accion) -> dict:
    return {"ok": True, "propuesta_id": propuesta_id, "accion": accion,
            "registro_id": "", "mensaje": MENSAJE_SIMULACION}


def salud() -> dict:
    return {"consultas": 10, "p50": 120, "p95": 300, "tasa_error": 0.0,
            "tasa_respaldo": 0.0, "unidad": "ms"}


def auditar(registro_id) -> dict:
    ejemplo = json.loads((FIXTURES / "registro.json").read_text(encoding="utf-8"))
    if registro_id != ejemplo["registro_id"]:
        return {"registro_id": registro_id, "encontrado": False, "se_reproduce": False,
                "motivo": "No existe ese identificador en el registro."}
    return {**ejemplo, "encontrado": True, "misma_config": True, "mismos_datos": True,
            "diferencias": [], "se_reproduce": True}
