"""Regla de adopción pre-registrada. Dueño: Gino. El umbral se fija ANTES de la primera evaluación completa."""

from __future__ import annotations


def decidir_adopcion(frontera_prueba, frontera_perturbado, pares, prereg) -> dict:
    """Adopta el modelo solo si, con el mismo % de pagos descubiertos que regla2, permite al menos
    prereg["umbral_adopcion_mejora"] más gasto, en la prueba Y en el perturbado.
    Escribe eval/resultados/adopcion.json -> {"adopta": bool, "razon": str}. Si no adopta, el servicio usa regla2."""
    raise NotImplementedError("eval.adopcion.decidir_adopcion (Gino)")