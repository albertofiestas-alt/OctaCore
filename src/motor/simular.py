"""Simulación de escenarios hipotéticos (opción C): "¿y si cobro S/200 el día 5?". Dueño: Sebastián.

simular devuelve una Decision completa calculada con la misma fórmula que decidir, con dos cambios:
- el saldo baja en escenario.gasto_hoy;
- cada ingreso extra se trata como ingreso CONOCIDO (sin cuantiles) que suma desde su día.

La firma de motor.decidir NO cambia (contratos/firmas.py): ambos comparten decidir_con_extras.
Escenario ya valida los rangos del plan (día 0..14, monto 0..10000, máximo 3 ingresos extra), así que
un escenario fuera de rango se rechaza antes de llegar al motor.

Con un escenario vacío el resultado es idéntico a decidir. Si el escenario no está vacío, la Decision
lo declara en evidencia["escenario"] y en los supuestos, y su propuesta (si hay) termina en ':simulada'.
Función pura: no lee archivos ni la hora y no cambia sus entradas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from motor.decidir import decidir, decidir_con_extras

if TYPE_CHECKING:
    from contratos import Config, Decision, Escenario, EstadoPersona, Pronostico


def simular(estado: EstadoPersona, pronostico: Pronostico, escenario: Escenario, cfg: Config) -> Decision:
    """Una Decision completa con el saldo menos gasto_hoy y los ingresos extra como ingreso CONOCIDO (sin cuantiles)."""
    if not escenario.ingresos_extra and not escenario.gasto_hoy:
        return decidir(estado, pronostico, cfg)
    estado_sim = estado.model_copy(update={"saldo": estado.saldo - escenario.gasto_hoy})
    extras = tuple((i.dia, i.monto) for i in escenario.ingresos_extra)
    declarado = {
        "gasto_hoy": float(escenario.gasto_hoy),
        "ingresos_extra": [{"dia": int(i.dia), "monto": float(i.monto)} for i in escenario.ingresos_extra],
    }
    return decidir_con_extras(estado_sim, pronostico, cfg, ingresos_extra=extras, escenario=declarado)


__all__ = ["simular"]
