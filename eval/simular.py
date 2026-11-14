"""Simulación día a día de la decisión sobre los meses de prueba (21 a 24). Dueño: Rafael.

Para cada día: estado con lo que se sabía ese día (sin mirar el futuro), el método da el número de hoy, la persona
gasta exactamente ese número [SUPUESTO], el saldo avanza con ingresos y pagos reales y un pago queda descubierto si
el saldo es menor que cero el día del pago. Los gastos discrecionales observados se reemplazan por el gasto permitido.
"""

from __future__ import annotations


def simular_persona(historia_completa, etiquetas, cfg, metodo: str, cuantil: float, modelo=None) -> dict:
    """{"pagos_descubiertos": n, "pagos_totales": m, "gasto_permitido_dia": promedio}."""
    raise NotImplementedError("eval.simular.simular_persona (Rafael)")