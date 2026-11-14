"""Firmas de las funciones públicas de cada módulo (Anexo A de la v7 y Anexo 5 de los planes).

Cada paquete de src/ ya tiene estas funciones con su firma exacta y el cuerpo
`raise NotImplementedError`. El dueño reemplaza el cuerpo, nunca la firma.
tests/contract/test_firmas.py falla si un nombre o un parámetro cambia.

`historia` y `movimientos_limpios` son un pandas.DataFrame con las columnas
COLUMNAS_MOVIMIENTO (más ingreso_recurrente y atipico_detectado si existen) y
SIN etiquetas de referencia. Ver contratos.historia.validar_historia.
`cfg` es el resultado de contratos.cargar_config(): se lee como cfg["clave"].
"""

from __future__ import annotations

# Módulo -> función (o Clase.metodo) -> nombres de parámetros, en orden (sin self/cls).
# Fuente única para la prueba de contrato. Cambiarla: Anderson y Gino + DECISIONES.md.
FIRMAS: dict[str, dict[str, tuple[str, ...]]] = {
    "datos": {
        "generar": ("n_personas", "meses", "semilla", "perturbado", "parametros"),
        "particion": ("df", "semilla"),
    },
    "ingesta": {
        "cargar": ("origen", "cfg"),
        "proximos_pagos": ("pagos_inferidos", "customer_id", "fecha_corte", "ventana"),
        "semanas_historia": ("movimientos", "customer_id", "fecha_corte"),
        "cargar_etiquetas": ("origen",),
        "detectar_pii": ("texto", "cfg"),
        "enmascarar_pii": ("df", "cfg"),
    },
    "reglas": {
        "regla1": ("historia", "fecha", "cfg"),
        "regla2": ("historia", "fecha", "cfg"),
    },
    "modelo": {
        "construir_features": ("historia", "fecha", "cfg"),
        "entrenar": ("movimientos_train", "cfg", "semilla"),
        "Modelo.predecir": ("historia", "fecha"),
        "Modelo.guardar": ("ruta",),
        "Modelo.cargar": ("ruta",),
    },
    "motor": {
        "decidir": ("estado", "pronostico", "cfg"),
    },
    "servicio": {
        "cargar_archivo": ("origen",),
        "consultar": ("customer_id", "fecha", "metodo"),
        "responder": ("propuesta_id", "accion"),
        "salud": (),
        "auditar": ("registro_id",),
    },
}

# Excepciones y constantes públicas que cada módulo debe exponer.
NOMBRES_PUBLICOS: dict[str, tuple[str, ...]] = {
    "ingesta": ("ErrorIngesta",),
    "modelo": ("HistoriaInsuficiente", "Modelo", "FEATURES"),
    "servicio": ("ErrorServicio",),
}
