"""Capa de datos: generador sintético, arquetipos, escenarios difíciles, perturbado, muestra.

Dueño: Rafael. Salida: data/*.csv con el contrato de datos (sección 6).
La implementación vive en datos/generador.py (y datos/chat.py) y se reexporta aquí con las firmas del Anexo A:
generar(n_personas, meses, semilla, perturbado, parametros) y particion(df, semilla).
semilla=None usa cfg["semilla_generador"] de config/base.yaml.
"""

from __future__ import annotations

from datos.generador import generar, mes_indice, muestra_de, particion, verificar

__all__ = ["generar", "mes_indice", "muestra_de", "particion", "verificar"]