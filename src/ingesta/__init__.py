"""Capa 1: ingesta y calidad.

Dueño: Mathias. Esqueleto V0 (Anexo E): reemplaza el cuerpo, NO la firma.
`cfg` es contratos.cargar_config(); tus parámetros van en config/ingesta.yaml -> cfg["ingesta"].
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

from . import esquema, inferencia, lectura, limpieza
from .auxiliares import cargar_etiquetas, proximos_pagos, semanas_historia
from .errores import ErrorIngesta
from .pii import detectar_pii, enmascarar_pii

if TYPE_CHECKING:
    import pandas as pd

    from contratos import Config, ReporteCalidad


def cargar(
    origen: str | Path | BinaryIO, cfg: Config
) -> tuple[pd.DataFrame, ReporteCalidad, list[dict[str, Any]]]:
    """(movimientos_limpios con atipico_detectado, ReporteCalidad, pagos_inferidos como dicts).

    No modifica `origen`. Hacia afuera solo sale `ErrorIngesta`: cualquier otro fallo interno se
    traduce a un mensaje para la persona y `detalle` lleva solo el nombre del tipo de excepción,
    nunca su texto (puede contener el valor de una celda).
    """
    try:
        return _cargar(origen, cfg)
    except ErrorIngesta:
        raise
    except Exception as exc:  # noqa: BLE001 - hacia afuera solo sale ErrorIngesta (contrato con la interfaz)
        raise ErrorIngesta(
            "No se pudo procesar el archivo. Revisa que cumpla el formato del contrato e inténtalo de nuevo.",
            type(exc).__name__,
        ) from None


def _cargar(origen: Any, cfg: Any) -> tuple[Any, Any, list[dict[str, Any]]]:
    from contratos import ReporteCalidad, validar_historia

    df = lectura.leer(origen, cfg)
    filas_entrada = len(df)
    df, sensibles = esquema.descartar_sensibles(df, cfg)
    df, _etiquetas = esquema.separar_etiquetas(df)  # las etiquetas no viajan; solo cargar_etiquetas
    df, _extra = esquema.validar_esquema(df)
    df, rechazos, _signos = esquema.validar_tipos(df)
    df, faltantes = limpieza.aplicar_defaults(df, cfg)
    df, n_pii = enmascarar_pii(df, cfg)
    df, n_dup, _detalle = limpieza.quitar_duplicados(df)
    df, n_atip = inferencia.marcar_atipicos(df, cfg)
    avisos = inferencia.suscripciones_duplicadas(df, cfg)
    pagos = inferencia.pagos_inferidos(df, cfg)

    df = df.reset_index(drop=True)
    validar_historia(df)  # columnas del contrato, anti fuga y tipos
    reporte = ReporteCalidad(
        filas_entrada=filas_entrada,
        filas_salida=len(df),
        duplicados_eliminados=n_dup,
        faltantes=faltantes,
        atipicos=n_atip,
        suscripciones_duplicadas=avisos,
        pagos_inferidos=pagos,
        pii_enmascarado=n_pii,
        columnas_sensibles_descartadas=sensibles,
        rechazos=rechazos,
    )
    return df, reporte, pagos


__all__ = [
    "ErrorIngesta",
    "cargar",
    "cargar_etiquetas",
    "detectar_pii",
    "enmascarar_pii",
    "proximos_pagos",
    "semanas_historia",
]
